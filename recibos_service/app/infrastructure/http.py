"""Cliente HTTP común para WSO2 IS y "parametros" (AD-08, AD-34; logical-components.md §2.3).

Una sesión de requests por hilo (una sesión no es segura entre hilos), un solo reintento si falla la
conexión, sin seguir redirecciones y con certificados verificados. Las respuestas se leen hasta 1 MB.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.application.errores import DependenciaNoDisponible

LARGO_MAXIMO_RESPUESTA = 1024 * 1024


@dataclass(frozen=True)
class RespuestaHttp:
    status: int
    cuerpo: bytes


class RespuestaDemasiadoGrande(Exception):
    pass


def _nueva_sesion() -> requests.Session:
    reintentos = Retry(
        total=1, connect=1, read=0, status=0, other=0, redirect=0, allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    sesion = requests.Session()
    adaptador = HTTPAdapter(max_retries=reintentos, pool_connections=2, pool_maxsize=2)
    sesion.mount("https://", adaptador)
    sesion.mount("http://", adaptador)
    return sesion


class ClienteHttp:
    def __init__(self) -> None:
        self._local = threading.local()

    def _sesion(self) -> requests.Session:
        sesion = getattr(self._local, "sesion", None)
        if sesion is None:
            sesion = _nueva_sesion()
            self._local.sesion = sesion
        return sesion

    def obtener(
        self, url: str, cabeceras: dict[str, str], conectar: float, responder: float, dependencia: str
    ) -> RespuestaHttp:
        """GET con tiempo de espera. `DependenciaNoDisponible` si no hay conexión o no responde a tiempo."""
        try:
            with self._sesion().get(
                url, headers=cabeceras, timeout=(conectar, responder), allow_redirects=False, stream=True
            ) as respuesta:
                cuerpo = self._leer(respuesta)
                return RespuestaHttp(respuesta.status_code, cuerpo)
        except requests.RequestException as error:  # conexión, tiempo de espera o cuerpo cortado
            raise DependenciaNoDisponible(dependencia) from error
        except RespuestaDemasiadoGrande:
            raise DependenciaNoDisponible(dependencia) from None

    @staticmethod
    def _leer(respuesta: requests.Response) -> bytes:
        partes: list[bytes] = []
        total = 0
        for parte in respuesta.iter_content(chunk_size=65536):
            total += len(parte)
            if total > LARGO_MAXIMO_RESPUESTA:
                raise RespuestaDemasiadoGrande
            partes.append(parte)
        return b"".join(partes)
