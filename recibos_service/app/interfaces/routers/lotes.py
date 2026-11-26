"""Blueprint `/v1/lotes`: `POST` carga y procesa un lote; `GET` lista el historial."""

from __future__ import annotations

from flask import Blueprint

from app.interfaces.controllers import lotes_controller

lotes = Blueprint("lotes", __name__, url_prefix="/v1/lotes")
lotes.add_url_rule("", view_func=lotes_controller.crear_lote, methods=["POST"], strict_slashes=False)
lotes.add_url_rule("", view_func=lotes_controller.listar_lotes, methods=["GET"], strict_slashes=False)
