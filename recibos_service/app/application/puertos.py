"""Puertos que implementa la infraestructura (component-methods.md §2.1, ajustado en U1 NFR Design)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from app.application.presupuesto import Plazo
from app.domain.modelos import ContextoCarrera, Estudiante, HojaPlantilla, Lote, NuevoLote, Pagina, Solicitud, Usuario
from app.domain.reglas import ReglasLiquidacion


class LectorPlantilla(Protocol):
    def leer(self, contenido: bytes) -> HojaPlantilla:
        """Primera hoja del libro. `ArchivoNoLegible` si no es un Excel 97-2003 que se pueda leer."""
        ...


class AlmacenamientoArchivos(Protocol):
    def guardar(self, contenido: bytes, nombre_interno: str) -> None:
        """Guarda el archivo; `DependenciaNoDisponible` si no se puede."""
        ...


class RepositorioAcademico(Protocol):
    """Oracle, solo lectura. Cada llamada usa `plazo.para(...)` como tiempo de espera (AD-34)."""

    def estudiantes(self, codigos: Sequence[int], plazo: Plazo) -> Mapping[int, Estudiante]: ...

    def contextos_carrera(
        self, codigos_carrera: frozenset[int], evento_periodo: int, evento_terminacion: int, plazo: Plazo
    ) -> Mapping[int, ContextoCarrera]: ...

    def con_certificado_electoral(self, codigos: Sequence[int], plazo: Plazo) -> frozenset[int]: ...


class SesionFilas(Protocol):
    """Una conexión de MySQL para todas las filas de un lote (AD-35).

    Antes de cada sentencia revisa el plazo: si venció, no la envía, cierra la conexión y lanza
    `PlazoVencido`. Una conexión perdida lanza `ErrorConexionBD`; cualquier otro error de la base,
    `ErrorPersistencia`.
    """

    def bloqueo_estudiante(self, codigo_estudiante: int) -> AbstractContextManager[None]:
        """Bloqueo con nombre por estudiante, 5 s como máximo (AD-32); `BloqueoNoObtenido` si no llega.

        Al salir suelta el bloqueo. Si no puede, cierra la conexión (MySQL lo suelta) y no lanza errores.
        """
        ...

    def cancelar_sin_imprimir(self, codigo_estudiante: int) -> tuple[int, ...]:
        """Transacción propia: estado 0 → 2 de las sin imprimir, de cualquier periodo (C8); devuelve los ids."""
        ...

    def guardar_solicitud(self, solicitud: Solicitud, documento_usuario: str, creada_en: datetime) -> int:
        """Una transacción: recibo, cuotas, exenciones y conceptos; devuelve el id. No revierte la cancelación."""
        ...


class RepositorioSolicitudes(Protocol):
    def registrar_lote(self, lote: NuevoLote) -> int: ...

    def filas(self, plazo: Plazo) -> AbstractContextManager[SesionFilas]: ...

    def listar_lotes(self, limite: int, desplazamiento: int) -> Pagina[Lote]: ...

    def porcentajes_exencion(self, ids: frozenset[int]) -> Mapping[int, Decimal]:
        """Solo lectura de la tabla `exencion` (F11)."""
        ...


class FuenteReglas(Protocol):
    def obtener(self, plazo: Plazo) -> ReglasLiquidacion:
        """Las reglas de "parametros" en paralelo, 10 s como máximo (AD-34).

        `DependenciaNoDisponible` si no responde; `RespuestaInvalida` si una regla no sirve.
        """
        ...


class FuenteFestivos(Protocol):
    def festivos(self, desde: date, hasta: date, plazo: Plazo) -> frozenset[date]: ...


class ProveedorIdentidad(Protocol):
    def usuario(self, token: str) -> Usuario:
        """`NoAutenticado` si el token no sirve; `DependenciaNoDisponible` si WSO2 IS no responde."""
        ...


class Reloj(Protocol):
    def ahora(self) -> datetime:
        """Hora actual en America/Bogota."""
        ...

    def segundos(self) -> float:
        """Reloj monotónico para los plazos (AD-31, AD-34)."""
        ...
