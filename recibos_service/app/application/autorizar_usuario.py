"""UC-03: el usuario tiene el rol de ARC y trae su documento (BR-A02 a BR-A04)."""

from __future__ import annotations

from app.application.errores import AccesoDenegado
from app.domain.modelos import Usuario


class AutorizarUsuario:
    def __init__(self, rol_autorizado: str) -> None:
        if not rol_autorizado.strip():
            raise ValueError("El rol autorizado no puede estar vacío")
        self._rol = rol_autorizado.strip()

    def ejecutar(self, usuario: Usuario) -> None:
        """El rol sale de `/oauth2/userinfo`, nunca de la petición (BR-A04)."""
        if self._rol not in usuario.roles:
            raise AccesoDenegado
        if not usuario.documento.strip():  # BR-A03: sin documento no se puede registrar `id_usuario`
            raise AccesoDenegado
