"""Errores de aplicación. `middlewares/errores` los convierte en el sobre institucional (services.md)."""

from __future__ import annotations

from collections.abc import Mapping

MENSAJE_DEPENDENCIA = "Un servicio que necesita la carga no está disponible. Intente más tarde."


class ErrorAplicacion(Exception):
    """Base: `status` es el código HTTP y `mensaje` el texto para el usuario, sin detalles internos."""

    status = 500

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ArchivoNoPermitido(ErrorAplicacion):
    """Campo, nombre, tamaño o tipo del archivo (BR-L01 a BR-L03): 400, 413 o 415."""

    def __init__(self, status: int, mensaje: str) -> None:
        super().__init__(mensaje)
        self.status = status


class ArchivoNoLegible(ErrorAplicacion):
    """El lector no pudo abrir el libro (BR-L08). El caso de uso lo convierte en 422 con el lote registrado."""

    status = 422


class FormatoPlantillaInvalido(ErrorAplicacion):
    """La plantilla no tiene el formato esperado; el lote ya quedó registrado (P-9)."""

    status = 422

    def __init__(self, id_lote: int, mensaje: str, auditoria: Mapping[str, object] | None = None) -> None:
        super().__init__(mensaje)
        self.id_lote = id_lote
        self.auditoria: dict[str, object] = dict(auditoria or {})


class DependenciaNoDisponible(ErrorAplicacion):
    """Una dependencia no respondió a tiempo: 503. `dependencia` va al registro, no al usuario."""

    status = 503

    def __init__(self, dependencia: str, mensaje: str = MENSAJE_DEPENDENCIA) -> None:
        super().__init__(mensaje)
        self.dependencia = dependencia


class RespuestaInvalida(ErrorAplicacion):
    """Una dependencia respondió con datos que no sirven: 502. El mensaje nombra la regla o la exención."""

    status = 502


class NoAutenticado(ErrorAplicacion):
    status = 401

    def __init__(self, mensaje: str = "No autorizado") -> None:
        super().__init__(mensaje)


class AccesoDenegado(ErrorAplicacion):
    status = 403

    def __init__(self, mensaje: str = "Prohibido") -> None:
        super().__init__(mensaje)


class ParametrosConsultaInvalidos(ErrorAplicacion):
    status = 400


class ErrorPersistencia(Exception):
    """Falla de la base durante una operación (BR-T02, BR-T03)."""


class ErrorConexionBD(ErrorPersistencia):
    """La conexión con MySQL se perdió o no respondió: cuenta para el corte del lote (BR-T04, AD-35)."""


class BloqueoNoObtenido(ErrorPersistencia):
    """El bloqueo del estudiante no llegó a tiempo (BR-T05); no cuenta para el corte."""
