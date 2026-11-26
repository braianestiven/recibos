"""Lo que la capa HTTP recibe de `api.py`: casos de uso, adaptadores de identidad y límites."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from app.application.autorizar_usuario import AutorizarUsuario
from app.application.procesar_lote import CargarLoteComando, ResultadoLote
from app.application.puertos import ProveedorIdentidad
from app.domain.modelos import Lote, Pagina


class CasoProcesarLote(Protocol):
    def ejecutar(self, comando: CargarLoteComando) -> ResultadoLote: ...


class CasoConsultarLotes(Protocol):
    def ejecutar(self, limite: int, desplazamiento: int) -> Pagina[Lote]: ...


@dataclass(frozen=True)
class Servicios:
    procesar_lote: CasoProcesarLote
    consultar_lotes: CasoConsultarLotes
    proveedor_identidad: ProveedorIdentidad
    autorizar_usuario: AutorizarUsuario
    segundos: Callable[[], float]  # reloj monotónico: hora de llegada de cada petición (AD-34)
    iniciar_captura_sql: Callable[[], None]
    sentencias_sql: Callable[[], list[str]]
    max_archivo_bytes: int
    max_nombre_archivo: int
    cors_origenes: tuple[str, ...]
    proxies_confianza: int


CLAVE_EXTENSION = "recibos_service"
