"""Cliente HTTP común: tiempos de espera, un reintento de conexión, sin redirecciones y cuerpo acotado (§2.3)."""

from __future__ import annotations

import http.server
import json
import socket
import threading
import time
from collections.abc import Iterator

import pytest

from app.application.errores import DependenciaNoDisponible
from app.infrastructure.http import LARGO_MAXIMO_RESPUESTA, ClienteHttp, _nueva_sesion


class _Manejador(http.server.BaseHTTPRequestHandler):
    def _responder(self, status: int, cuerpo: bytes, cabeceras: dict[str, str] | None = None) -> None:
        try:
            self.send_response(status)
            for nombre, valor in (cabeceras or {}).items():
                self.send_header(nombre, valor)
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
        except (BrokenPipeError, ConnectionResetError):  # el cliente dejó de leer a propósito
            pass

    def do_GET(self) -> None:  # noqa: N802 - nombre que exige http.server
        if self.path == "/eco":
            self._responder(200, json.dumps({"authorization": self.headers.get("Authorization")}).encode())
        elif self.path == "/lento":
            time.sleep(1.5)
            self._responder(200, b"{}")
        elif self.path == "/grande":
            self._responder(200, b"x" * (LARGO_MAXIMO_RESPUESTA + 1))
        elif self.path == "/redirige":
            self._responder(302, b"", {"Location": "/eco"})
        else:
            self._responder(404, b"")

    def log_message(self, *_args: object) -> None:
        return


@pytest.fixture(scope="module")
def servidor() -> Iterator[str]:
    servidor_http = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Manejador)
    hilo = threading.Thread(target=servidor_http.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{servidor_http.server_address[1]}"
    servidor_http.shutdown()
    servidor_http.server_close()


def test_respuesta_con_las_cabeceras_dadas(servidor: str) -> None:
    respuesta = ClienteHttp().obtener(f"{servidor}/eco", {"Authorization": "Bearer t"}, 2, 3, "prueba")
    assert respuesta.status == 200
    assert json.loads(respuesta.cuerpo) == {"authorization": "Bearer t"}


def test_no_sigue_redirecciones(servidor: str) -> None:
    respuesta = ClienteHttp().obtener(f"{servidor}/redirige", {"Authorization": "Bearer t"}, 2, 3, "prueba")
    assert respuesta.status == 302  # el token no sale hacia otro destino


def test_respuesta_que_tarda_demasiado(servidor: str) -> None:
    inicio = time.monotonic()
    with pytest.raises(DependenciaNoDisponible) as error:
        ClienteHttp().obtener(f"{servidor}/lento", {}, 1, 0.3, "parametros")
    assert error.value.dependencia == "parametros"
    assert time.monotonic() - inicio < 1.2  # no se reintenta una lectura vencida


def test_cuerpo_demasiado_grande(servidor: str) -> None:
    with pytest.raises(DependenciaNoDisponible):
        ClienteHttp().obtener(f"{servidor}/grande", {}, 2, 3, "wso2")


def test_sin_conexion() -> None:
    with socket.socket() as libre:
        libre.bind(("127.0.0.1", 0))
        puerto = libre.getsockname()[1]
    with pytest.raises(DependenciaNoDisponible):
        ClienteHttp().obtener(f"http://127.0.0.1:{puerto}/eco", {}, 0.5, 0.5, "wso2")


def test_reintentos_y_redirecciones_de_la_sesion() -> None:
    reintentos = _nueva_sesion().get_adapter("https://servicio").max_retries  # type: ignore[attr-defined]
    assert (reintentos.total, reintentos.connect, reintentos.read, reintentos.status, reintentos.redirect) == (
        1,
        1,
        0,
        0,
        0,
    )
    assert reintentos.allowed_methods == frozenset({"GET"})


def test_una_sesion_por_hilo() -> None:
    cliente = ClienteHttp()
    propia = cliente._sesion()
    assert cliente._sesion() is propia
    otras: list[object] = []
    hilo = threading.Thread(target=lambda: otras.append(cliente._sesion()))
    hilo.start()
    hilo.join()
    assert otras[0] is not propia
