"""Sobre institucional `{Success, Status, Message, Data}` con `Metadata` en los listados (AD-04, L31)."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify

# Mensajes por defecto de `utils_oas/requestresponse/responses_format.go` para los códigos que usa la API
MENSAJES_POR_DEFECTO = {
    200: "Solicitud exitosa",
    201: "Recurso creado con éxito",
    400: "Solicitud incorrecta",
    401: "No autorizado",
    403: "Prohibido",
    404: "Recurso no encontrado",
    405: "Método no permitido",
    413: "Entidad de solicitud demasiado grande",
    415: "Tipo de medio no soportado",
    422: "Entidad no procesable",
    429: "Demasiadas solicitudes",
    500: "Error interno del servidor",
    502: "Mal gateway",
    503: "Servicio no disponible",
}


def sobre(status: int, data: Any = None, mensaje: str | None = None, metadata: Any = None) -> Response:
    cuerpo: dict[str, Any] = {
        "Success": status < 400,
        "Status": status,
        "Message": mensaje or MENSAJES_POR_DEFECTO.get(status, "Operación exitosa" if status < 400 else "Error"),
        "Data": data,
    }
    if metadata is not None:
        cuerpo["Metadata"] = metadata
    respuesta = jsonify(cuerpo)
    respuesta.status_code = status
    return respuesta


def exito(status: int, data: Any, metadata: Any = None, mensaje: str | None = None) -> Response:
    return sobre(status, data=data, mensaje=mensaje, metadata=metadata)


def error(status: int, mensaje: str | None = None, data: Any = None) -> Response:
    return sobre(status, data=data, mensaje=mensaje)
