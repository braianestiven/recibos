"""Health checks públicos, sin auditoría y sin consultar bases (AD-11, AD-12, NFR-A05)."""

from __future__ import annotations

from flask import Response, jsonify


def raiz() -> Response:
    return jsonify({"status": "ok"})


def salud() -> Response:
    return jsonify({"status": "UP"})
