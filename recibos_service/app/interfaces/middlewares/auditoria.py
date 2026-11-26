"""Registro de auditoría de cada petición a `/v1/*`, con los campos de `utils_oas/auditoria` (BR-U01 a BR-U03).

`data` lleva solo lo que deja el controller (tipo de plantilla, tamaño, `id_lote`, totales e ids de
solicitudes); nunca códigos ni nombres de estudiantes. `sql_statement` lleva el texto SQL, sin valores.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from flask import Flask, Response, g, request

from app.domain.fechas import ZONA_BOGOTA

NOMBRE_APLICACION = "recibos_service"
registro = logging.getLogger("recibos_service.auditoria")
_LARGO_AGENTE = 256
_LARGO_CONSULTA = 512


def registrar(app: Flask, iniciar_captura: Callable[[], None], sentencias: Callable[[], list[str]]) -> None:
    @app.before_request
    def iniciar_auditoria() -> None:
        if request.path.startswith("/v1/"):
            iniciar_captura()

    @app.after_request
    def registrar_auditoria(respuesta: Response) -> Response:
        if request.path.startswith("/v1/"):
            usuario = g.get("usuario")
            entrada = {
                "app_name": NOMBRE_APLICACION,
                "agent": (request.user_agent.string or "")[:_LARGO_AGENTE],
                "data": g.get("datos_auditoria", {}),
                "date": datetime.now(ZONA_BOGOTA).isoformat(timespec="seconds"),
                "host": request.host,
                "ip_user": request.remote_addr or "",
                "method": request.method,
                "path": request.path,
                "query": request.query_string.decode("latin-1")[:_LARGO_CONSULTA],
                "schema": request.scheme,
                "sql_statement": "; ".join(sentencias()),
                "status": respuesta.status_code,
                "trace_id": g.get("request_id", ""),
                "user": usuario.sub if usuario is not None else "",
            }
            registro.info("auditoria", extra={"auditoria": entrada})
        return respuesta
