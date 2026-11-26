"""Primer middleware: hora de llegada y `request_id` de cada petición (AD-33, AD-34, NFR-O02)."""

from __future__ import annotations

import re
import uuid
from collections.abc import Callable

from flask import Flask, Response, g, request

from app.application import contexto

# Formato que pone el balanceador en `X-Amzn-Trace-Id`: Root=1-<8 hex>-<24 hex>
_RAIZ_TRAZA = re.compile(r"(?:^|;)\s*Root=(1-[0-9a-f]{8}-[0-9a-f]{24})\s*(?:;|$)")
_LARGO_MAXIMO_CABECERA = 256


def identificador_de(cabecera: str | None) -> str:
    """La parte `Root` de `X-Amzn-Trace-Id` si tiene el formato del balanceador; si no, un UUID nuevo.

    Un cliente puede elegir su `Root`: el identificador sirve para buscar en los registros, no prueba nada.
    """
    if cabecera and len(cabecera) <= _LARGO_MAXIMO_CABECERA:
        coincidencia = _RAIZ_TRAZA.search(cabecera)
        if coincidencia:
            return coincidencia.group(1)
    return uuid.uuid4().hex


def registrar(app: Flask, segundos: Callable[[], float]) -> None:
    @app.before_request
    def iniciar_contexto() -> None:
        g.recibida_en = segundos()
        g.request_id = identificador_de(request.headers.get("X-Amzn-Trace-Id"))
        g.token_request_id = contexto.request_id.set(g.request_id)

    @app.after_request
    def agregar_request_id(respuesta: Response) -> Response:
        respuesta.headers["X-Request-Id"] = g.get("request_id", "-")
        return respuesta

    @app.teardown_request
    def limpiar_contexto(_error: BaseException | None) -> None:
        token = g.pop("token_request_id", None)
        if token is not None:
            contexto.request_id.reset(token)
