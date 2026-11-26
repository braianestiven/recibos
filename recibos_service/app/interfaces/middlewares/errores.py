"""Convierte cualquier error en el sobre institucional, sin trazas ni detalles internos (SECURITY-09, SECURITY-15)."""

from __future__ import annotations

import logging
import traceback

from flask import Flask, Response, current_app, g
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from app.application.errores import DependenciaNoDisponible, ErrorAplicacion, FormatoPlantillaInvalido
from app.interfaces.schemas.respuesta import error
from app.interfaces.servicios import CLAVE_EXTENSION, Servicios

registro = logging.getLogger("recibos_service.errores")
MENSAJE_INESPERADO = "Ocurrió un error inesperado. Intente más tarde."


def mensaje_tamano(max_bytes: int) -> str:
    return f"El archivo supera el tamaño máximo de {max_bytes / (1024 * 1024):g} MB."


def registrar(app: Flask) -> None:
    @app.errorhandler(ErrorAplicacion)
    def error_de_aplicacion(excepcion: ErrorAplicacion) -> Response:
        if isinstance(excepcion, DependenciaNoDisponible):
            registro.error(
                "dependencia_no_disponible",
                extra={"evento": "dependencia_no_disponible", "datos": {"dependencia": excepcion.dependencia}},
            )
        if isinstance(excepcion, FormatoPlantillaInvalido):
            g.datos_auditoria = excepcion.auditoria
            return error(excepcion.status, excepcion.mensaje, data={"id_lote": excepcion.id_lote})
        if excepcion.status in {401, 403}:
            registro.warning(
                "acceso_rechazado", extra={"evento": "acceso_rechazado", "datos": {"status": excepcion.status}}
            )
        return error(excepcion.status, excepcion.mensaje)

    @app.errorhandler(RequestEntityTooLarge)
    def cuerpo_demasiado_grande(_excepcion: RequestEntityTooLarge) -> Response:
        servicios: Servicios = current_app.extensions[CLAVE_EXTENSION]
        return error(413, mensaje_tamano(servicios.max_archivo_bytes))

    @app.errorhandler(HTTPException)
    def error_http(excepcion: HTTPException) -> Response:
        return error(excepcion.code or 500)

    @app.errorhandler(Exception)
    def error_inesperado(excepcion: Exception) -> Response:
        # Solo el tipo y los marcos de la pila: el mensaje de la excepción puede traer valores (NFR-S08)
        marcos = "".join(traceback.TracebackException.from_exception(excepcion).stack.format())
        registro.error(
            "error_inesperado",
            extra={"evento": "error_inesperado", "datos": {"tipo": type(excepcion).__name__, "pila": marcos}},
        )
        return error(500, MENSAJE_INESPERADO)
