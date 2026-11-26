"""Usuario del token según `/oauth2/userinfo` de WSO2 IS (AD-09; BR-A01 a BR-A04)."""

from __future__ import annotations

import json
import string

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.application.errores import DependenciaNoDisponible, NoAutenticado
from app.domain.modelos import Usuario
from app.infrastructure.http import RespuestaHttp
from app.infrastructure.wso2.proveedor_identidad import ProveedorIdentidadWso2, roles_de, usuario_de

URL = "https://autenticacion.portaloas.udistrital.edu.co/oauth2/userinfo"


class ClienteFalso:
    def __init__(self, status: int = 200, cuerpo: object = None, error: Exception | None = None) -> None:
        self.status = status
        self.cuerpo = cuerpo if isinstance(cuerpo, bytes) else json.dumps(cuerpo).encode()
        self.error = error
        self.llamadas: list[tuple[str, dict[str, str], float, float, str]] = []

    def obtener(
        self, url: str, cabeceras: dict[str, str], conectar: float, responder: float, dependencia: str
    ) -> RespuestaHttp:
        self.llamadas.append((url, cabeceras, conectar, responder, dependencia))
        if self.error is not None:
            raise self.error
        return RespuestaHttp(self.status, self.cuerpo)


def _usuario(cliente: ClienteFalso, token: str = "abc.def") -> Usuario:
    return ProveedorIdentidadWso2(URL, cliente).usuario(token)  # type: ignore[arg-type]


def test_usuario_de_arc() -> None:
    cliente = ClienteFalso(cuerpo={"sub": "arc@udistrital.edu.co", "documento": "79123456", "role": ["ARC", "x"]})
    assert _usuario(cliente) == Usuario("79123456", "arc@udistrital.edu.co", frozenset({"ARC", "x"}))
    assert cliente.llamadas == [
        (URL, {"Authorization": "Bearer abc.def", "Accept": "application/json"}, 2.0, 5.0, "wso2")
    ]


@pytest.mark.parametrize(
    ("datos", "esperado"),
    [
        (
            {"sub": "s", "documento": 79123456, "role": "ARC,Internal/everyone"},
            Usuario("79123456", "s", frozenset({"ARC", "Internal/everyone"})),
        ),
        ({"sub": "s"}, Usuario("", "s", frozenset())),
        ({"sub": "s", "documento": True, "role": 7}, Usuario("", "s", frozenset())),
        ({"sub": "s", "documento": "1" * 300, "role": [" ARC ", "", None]}, Usuario("", "s", frozenset({"ARC"}))),
    ],
)
def test_claims_con_otros_tipos(datos: dict[str, object], esperado: Usuario) -> None:
    assert usuario_de(datos) == esperado


@pytest.mark.parametrize("status", [400, 401, 403])
def test_token_que_no_sirve(status: int) -> None:
    with pytest.raises(NoAutenticado):
        _usuario(ClienteFalso(status=status, cuerpo={"error": "invalid_token"}))


def test_sin_sub_no_hay_usuario() -> None:
    with pytest.raises(NoAutenticado):
        _usuario(ClienteFalso(cuerpo={"documento": "79123456", "role": "ARC"}))


@pytest.mark.parametrize(
    "cliente",
    [
        ClienteFalso(status=500, cuerpo={}),
        ClienteFalso(status=302, cuerpo=b""),
        ClienteFalso(cuerpo=b"<html>no es json</html>"),
        ClienteFalso(cuerpo=b"\xff\xfe"),
        ClienteFalso(cuerpo=["no", "es", "un", "objeto"]),
        ClienteFalso(error=DependenciaNoDisponible("wso2")),
    ],
)
def test_wso2_no_responde_bien(cliente: ClienteFalso) -> None:
    with pytest.raises(DependenciaNoDisponible):
        _usuario(cliente)


ROL = st.text(alphabet=string.ascii_letters + string.digits + "/_-", min_size=1, max_size=40)


@given(st.lists(ROL, max_size=20))
def test_roles_en_lista_o_separados_por_comas(roles: list[str]) -> None:
    assert roles_de(roles) == frozenset(roles)
    assert roles_de(",".join(roles)) == frozenset(roles)
