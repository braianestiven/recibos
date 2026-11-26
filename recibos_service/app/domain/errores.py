"""Errores del dominio. El caso de uso los traduce a errores de aplicación."""

from __future__ import annotations


class ErrorDominio(Exception):
    """Base de los errores del dominio. `mensaje` es el texto para ARC (business-rules.md §10)."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class FormatoInvalido(ErrorDominio):
    """La hoja no tiene el formato de una plantilla vigente (BR-L08 a BR-L11): 422."""


class ReglaInvalida(ErrorDominio):
    """Una regla de "parametros" falta o su valor no sirve (BR-L04): 502."""

    def __init__(self, regla: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.regla = regla


class ExencionSinPorcentaje(ErrorDominio):
    """A una exención de los mapas le falta el porcentaje en la tabla `exencion` (BR-L05): 502."""

    def __init__(self, id_exencion: int, mensaje: str) -> None:
        super().__init__(mensaje)
        self.id_exencion = id_exencion
