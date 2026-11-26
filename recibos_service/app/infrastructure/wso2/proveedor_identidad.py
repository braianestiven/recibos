"""Usuario del token según `/oauth2/userinfo` de WSO2 IS, en cada petición y sin caché (AD-09, BR-A01 a BR-A04).

Claims que se usan: `sub`, `documento` (se guarda como `id_usuario`, A8) y `role`, que WSO2 puede enviar
como lista o como texto separado por comas (D8). El token nunca se registra.
"""

from __future__ import annotations

import json
from typing import Any

from app.application.errores import DependenciaNoDisponible, NoAutenticado
from app.domain.modelos import Usuario
from app.infrastructure.http import ClienteHttp

TIEMPO_CONEXION_S = 2.0
TIEMPO_RESPUESTA_S = 5.0
_LARGO_MAXIMO_CLAIM = 256
_MAXIMO_ROLES = 200


def _texto(valor: object) -> str:
    """Un claim de texto; un número (un documento como 79123456) se acepta como su texto."""
    if isinstance(valor, bool) or not isinstance(valor, str | int):
        return ""
    texto = str(valor).strip()
    return texto if len(texto) <= _LARGO_MAXIMO_CLAIM else ""


def roles_de(valor: object) -> frozenset[str]:
    if isinstance(valor, str):
        partes: list[object] = list(valor.split(","))
    elif isinstance(valor, list):
        partes = list(valor[:_MAXIMO_ROLES])
    else:
        return frozenset()
    return frozenset(texto for parte in partes if (texto := _texto(parte)))


def usuario_de(datos: dict[str, Any]) -> Usuario:
    return Usuario(
        documento=_texto(datos.get("documento")),
        sub=_texto(datos.get("sub")),
        roles=roles_de(datos.get("role")),
    )


class ProveedorIdentidadWso2:
    def __init__(self, url_userinfo: str, cliente: ClienteHttp) -> None:
        self._url = url_userinfo
        self._cliente = cliente

    def usuario(self, token: str) -> Usuario:
        cabeceras = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        respuesta = self._cliente.obtener(self._url, cabeceras, TIEMPO_CONEXION_S, TIEMPO_RESPUESTA_S, "wso2")
        if respuesta.status in {400, 401, 403}:  # token vencido, revocado o de otro emisor
            raise NoAutenticado
        if respuesta.status != 200:
            raise DependenciaNoDisponible("wso2")
        try:
            datos = json.loads(respuesta.cuerpo)
        except ValueError:  # incluye UnicodeDecodeError
            raise DependenciaNoDisponible("wso2") from None
        if not isinstance(datos, dict):
            raise DependenciaNoDisponible("wso2")
        usuario = usuario_de(datos)
        if not usuario.sub:
            raise NoAutenticado
        return usuario
