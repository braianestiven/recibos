"""Cabeceras de seguridad de `utils_oas/security/security_headers.go` en todas las respuestas (SECURITY-04).

La cabecera `Server` vacía la pone `gunicorn.conf.py`, porque gunicorn agrega la suya (AD-36).
"""

from __future__ import annotations

from flask import Flask, Response, request

CABECERAS = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cross-Origin-Resource-Policy": "cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "X-XSS-Protection": "1; mode=block",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-Permitted-Cross-Domain-Policies": "none",
}


def registrar(app: Flask) -> None:
    @app.after_request
    def agregar_cabeceras(respuesta: Response) -> Response:
        for nombre, valor in CABECERAS.items():
            respuesta.headers[nombre] = valor
        if request.path.startswith("/v1/"):
            respuesta.headers["Cache-Control"] = "no-store"  # el reporte trae códigos de estudiantes (AD-36)
        return respuesta
