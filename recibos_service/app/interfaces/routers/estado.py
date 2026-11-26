"""Blueprint sin prefijo: `GET /` y `GET /health`."""

from __future__ import annotations

from flask import Blueprint

from app.interfaces.controllers import estado_controller

estado = Blueprint("estado", __name__)
estado.add_url_rule("/", view_func=estado_controller.raiz, methods=["GET"])
estado.add_url_rule("/health", view_func=estado_controller.salud, methods=["GET"])
