"""Dobles de los casos de uso y del proveedor de identidad para probar la capa HTTP con el cliente de Flask."""

from __future__ import annotations

import io
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime

from flask import Flask
from flask.testing import FlaskClient

from app.application import contexto
from app.application.autorizar_usuario import AutorizarUsuario
from app.application.errores import NoAutenticado
from app.application.procesar_lote import CargarLoteComando, ResultadoLote
from app.domain.fechas import ZONA_BOGOTA
from app.domain.modelos import Lote, MotivoRechazo, Pagina, Procesado, Rechazo, ResumenLote, TipoPlantilla, Usuario
from app.interfaces.aplicacion import crear_aplicacion
from app.interfaces.controllers.lotes_controller import FIRMA_OLE2
from app.interfaces.servicios import Servicios

TOKEN = "eyJ0eXAi.eyJzdWIi.firma-de-prueba"
ROL = "ARC"
USUARIO_ARC = Usuario(documento="79123456", sub="arc@udistrital.edu.co", roles=frozenset({ROL, "Internal/everyone"}))
ORIGEN = "https://recibos.portaloas.udistrital.edu.co"
CODIGO_RECHAZADO = "20271020045"
CONTENIDO_XLS = FIRMA_OLE2 + b"\x00" * 512

RESUMEN = ResumenLote(
    id_lote=1532,
    tipo=TipoPlantilla.PREGRADO,
    procesados=(Procesado(4, 20271020001), Procesado(5, 20271020017)),
    rechazados=(
        Rechazo(6, CODIGO_RECHAZADO, MotivoRechazo.ESTADO_NO_PERMITIDO, "El estado del estudiante no permite"),
    ),
)
AUDITORIA = {
    "id_lote": 1532,
    "tamano_bytes": len(CONTENIDO_XLS),
    "tipo_plantilla": "PREGRADO",
    "total_filas": 3,
    "procesados": 2,
    "rechazados": 1,
    "solicitudes_creadas": [901, 902],
    "solicitudes_canceladas": {"estado_anterior": 0, "estado_nuevo": 2, "ids": [77]},
}


class ProveedorDePrueba:
    def __init__(self, usuarios: dict[str, Usuario] | None = None, error: Exception | None = None) -> None:
        self.usuarios = usuarios if usuarios is not None else {TOKEN: USUARIO_ARC}
        self.error = error
        self.tokens: list[str] = []

    def usuario(self, token: str) -> Usuario:
        self.tokens.append(token)
        if self.error is not None:
            raise self.error
        try:
            return self.usuarios[token]
        except KeyError:
            raise NoAutenticado from None


class ProcesarLoteDePrueba:
    def __init__(self, resultado: ResultadoLote | None = None, error: Exception | None = None) -> None:
        self.resultado = resultado or ResultadoLote(resumen=RESUMEN, auditoria=dict(AUDITORIA))
        self.error = error
        self.comandos: list[CargarLoteComando] = []
        self.tokens_vistos: list[str | None] = []

    def ejecutar(self, comando: CargarLoteComando) -> ResultadoLote:
        self.comandos.append(comando)
        self.tokens_vistos.append(contexto.token_usuario.get())
        if self.error is not None:
            raise self.error
        return self.resultado


class ConsultarLotesDePrueba:
    def __init__(self, lotes: tuple[Lote, ...] = (), total: int | None = None, error: Exception | None = None) -> None:
        self.lotes = lotes
        self.total = total
        self.error = error
        self.consultas: list[tuple[int, int]] = []

    def ejecutar(self, limite: int, desplazamiento: int) -> Pagina[Lote]:
        self.consultas.append((limite, desplazamiento))
        if self.error is not None:
            raise self.error
        elementos = self.lotes[desplazamiento : desplazamiento + limite]
        total = self.total if self.total is not None else len(self.lotes)
        return Pagina(elementos=elementos, total=total, limite=limite, desplazamiento=desplazamiento)


def lote(id_lote: int = 1533) -> Lote:
    return Lote(
        id=id_lote,
        documento_usuario="79123456",
        nombre_original="pregrado_2027_1.xls",
        ip="10.20.30.40",
        fecha=datetime(2026, 12, 1, 10, 15, tzinfo=ZONA_BOGOTA),
    )


class Sentencias:
    def __init__(self) -> None:
        self.inicios = 0
        self.textos: list[str] = []

    def iniciar(self) -> None:
        self.inicios += 1
        self.textos = []

    def sentencias(self) -> list[str]:
        return list(self.textos)


def servicios(**cambios: object) -> Servicios:
    sentencias = Sentencias()
    base = Servicios(
        procesar_lote=ProcesarLoteDePrueba(),
        consultar_lotes=ConsultarLotesDePrueba(),
        proveedor_identidad=ProveedorDePrueba(),
        autorizar_usuario=AutorizarUsuario(ROL),
        segundos=lambda: 500.0,
        iniciar_captura_sql=sentencias.iniciar,
        sentencias_sql=sentencias.sentencias,
        max_archivo_bytes=2 * 1024 * 1024,
        max_nombre_archivo=255,
        cors_origenes=(ORIGEN,),
        proxies_confianza=0,
    )
    return replace(base, **cambios)  # type: ignore[arg-type]


def cliente(servicios_app: Servicios | None = None) -> FlaskClient:
    app: Flask = crear_aplicacion(servicios_app or servicios())
    return app.test_client()


def autorizacion(token: str = TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def archivo(contenido: bytes = CONTENIDO_XLS, nombre: str = "lote.xls") -> dict[str, object]:
    return {"archivo": (io.BytesIO(contenido), nombre)}


@contextmanager
def registros(nombre: str) -> Iterator[list[logging.LogRecord]]:
    """Registros de un logger durante el bloque, sin depender de `caplog` (sirve dentro de Hypothesis)."""
    capturados: list[logging.LogRecord] = []

    class _Lista(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            capturados.append(record)

    manejador = _Lista(level=logging.DEBUG)
    registro = logging.getLogger(nombre)
    nivel_anterior = registro.level
    registro.addHandler(manejador)
    registro.setLevel(logging.DEBUG)
    try:
        yield capturados
    finally:
        registro.removeHandler(manejador)
        registro.setLevel(nivel_anterior)
