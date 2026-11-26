"""Token obligatorio en `/v1/*`, validado en WSO2 IS en cada petición, y rol de ARC (BR-A01 a BR-A04)."""

from __future__ import annotations

import re

from flask import Flask, g, request

from app.application import contexto
from app.application.autorizar_usuario import AutorizarUsuario
from app.application.errores import NoAutenticado
from app.application.puertos import ProveedorIdentidad

_TOKEN = re.compile(r"[A-Za-z0-9\-._~+/]+=*")  # b64token de RFC 6750
_LARGO_MAXIMO_TOKEN = 8192


def token_bearer(cabecera: str | None) -> str | None:
    if not cabecera:
        return None
    esquema, _, token = cabecera.strip().partition(" ")
    token = token.strip()
    if esquema.lower() != "bearer" or not token or len(token) > _LARGO_MAXIMO_TOKEN:
        return None
    if _TOKEN.fullmatch(token) is None:
        return None
    return token


def registrar(app: Flask, proveedor: ProveedorIdentidad, autorizar: AutorizarUsuario) -> None:
    @app.before_request
    def autenticar() -> None:
        if not request.path.startswith("/v1/") or request.method == "OPTIONS":
            return
        token = token_bearer(request.headers.get("Authorization"))
        if token is None:
            raise NoAutenticado
        usuario = proveedor.usuario(token)  # NoAutenticado o DependenciaNoDisponible: falla cerrada
        autorizar.ejecutar(usuario)  # AccesoDenegado
        g.usuario = usuario
        g.token_usuario = contexto.token_usuario.set(token)  # lo reenvía la lectura de reglas (A11)

    @app.teardown_request
    def olvidar_token(_error: BaseException | None) -> None:
        marca = g.pop("token_usuario", None)
        if marca is not None:
            contexto.token_usuario.reset(marca)
