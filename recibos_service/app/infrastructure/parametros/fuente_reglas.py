"""Reglas de liquidación desde "parametros", al inicio de cada lote y sin caché (AD-20 a AD-22, US-15).

Las 17 reglas se leen en paralelo en un grupo de 8 hilos por proceso, que se crea la primera vez que se
usa. Cada llamada tiene 2 s para conectar y 3 s de respuesta, recortados por lo que quede, y todas juntas
10 s como máximo (nfr-design-patterns.md §3.2). La llamada reenvía el token del usuario (A11), que se lee
en el hilo de la petición.
"""

from __future__ import annotations

import contextvars
import logging
import threading
from collections.abc import Mapping
from concurrent.futures import Future, ThreadPoolExecutor, wait
from typing import Any

from app.application import contexto
from app.application.errores import DependenciaNoDisponible, RespuestaInvalida
from app.application.presupuesto import Plazo, PlazoVencido
from app.domain import mensajes
from app.domain.reglas import ReglasLiquidacion
from app.infrastructure.http import ClienteHttp
from app.infrastructure.parametros.modelos import (
    FORMAS,
    EspecificacionParametro,
    RespuestaParametros,
    convertir,
    dar_forma,
    problemas_de_configuracion,
)

registro = logging.getLogger(__name__)

HILOS = 8
TIEMPO_TOTAL_S = 10.0
TIEMPO_CONEXION_S = 2.0
TIEMPO_RESPUESTA_S = 3.0


class ReglasMalConfiguradas(Exception):
    """La configuración de las reglas no sirve; `api.py` la convierte en `ConfiguracionInvalida`."""

    def __init__(self, problemas: list[str]) -> None:
        super().__init__("; ".join(problemas))
        self.problemas = problemas


class FuenteReglasParametros:
    def __init__(
        self,
        url_base: str,
        especificaciones: Mapping[str, EspecificacionParametro],
        cliente: ClienteHttp,
        hilos: int = HILOS,
    ) -> None:
        problemas = problemas_de_configuracion(especificaciones)
        if problemas:
            raise ReglasMalConfiguradas(problemas)
        self._url = url_base.rstrip("/")
        self._especificaciones = {regla: especificaciones[regla] for regla in FORMAS}
        self._cliente = cliente
        self._hilos = hilos
        self._grupo: ThreadPoolExecutor | None = None
        self._candado = threading.Lock()

    def _grupo_de_hilos(self) -> ThreadPoolExecutor:
        with self._candado:
            if self._grupo is None:
                self._grupo = ThreadPoolExecutor(max_workers=self._hilos, thread_name_prefix="parametros")
            return self._grupo

    def obtener(self, plazo: Plazo) -> ReglasLiquidacion:
        plazo_reglas = Plazo(plazo.segundos() + TIEMPO_TOTAL_S, plazo.segundos).hasta(plazo)
        plazo_reglas.exigir()
        cabeceras = {"Accept": "application/json"}
        token = contexto.token_usuario.get()
        if token:
            cabeceras["Authorization"] = f"Bearer {token}"
        grupo = self._grupo_de_hilos()
        futuros: dict[str, Future[object]] = {
            regla: grupo.submit(contextvars.copy_context().run, self._leer, regla, espec, cabeceras, plazo_reglas)
            for regla, espec in self._especificaciones.items()
        }
        _, pendientes = wait(futuros.values(), timeout=plazo_reglas.restante())
        if pendientes:
            for futuro in pendientes:
                futuro.cancel()
            raise DependenciaNoDisponible("parametros")
        valores: dict[str, Any] = {regla: futuro.result() for regla, futuro in futuros.items()}  # el primer error
        return ReglasLiquidacion(**valores)  # ReglaInvalida si los valores no cumplen sus reglas

    def _leer(
        self, regla: str, espec: EspecificacionParametro, cabeceras: dict[str, str], plazo: Plazo
    ) -> object:
        try:
            conectar, responder = plazo.para(TIEMPO_CONEXION_S), plazo.para(TIEMPO_RESPUESTA_S)
        except PlazoVencido:
            raise DependenciaNoDisponible("parametros") from None
        url = f"{self._url}/v1/parametro/{espec.id}"
        respuesta = self._cliente.obtener(url, cabeceras, conectar, responder, "parametros")
        if respuesta.status >= 500:
            raise DependenciaNoDisponible("parametros")
        try:
            if respuesta.status != 200:
                raise ValueError("código HTTP")
            sobre = RespuestaParametros.model_validate_json(respuesta.cuerpo)
            parametro = sobre.Data
            if not sobre.exitosa() or parametro is None or parametro.Id != espec.id or not parametro.Activo:
                raise ValueError("parámetro inexistente o inactivo")  # AD-22
            return dar_forma(convertir(getattr(parametro, espec.campo), espec.formato), FORMAS[regla])
        except ValueError:  # incluye ValidationError de pydantic y JSONDecodeError
            registro.warning(
                "regla_invalida",
                extra={"evento": "regla_invalida", "datos": {"regla": regla, "status": respuesta.status}},
            )
            raise RespuestaInvalida(mensajes.regla_invalida(regla)) from None
