"""Secretos de SSM Parameter Store (`SecureString`), leídos al arrancar cada proceso (NFR-S11, N18).

Nombres debajo de `RECIBOS_SERVICE_SSM_RUTA` (provisional hasta D7): `oracle/username`,
`oracle/password`, `mysql/username` y `mysql/password`. Un cambio de contraseña se toma con un
despliegue nuevo (nfr-design-patterns.md §7.5).
"""

from __future__ import annotations

from typing import Any

from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import SecretStr

NOMBRES = {
    "oracle_usuario": "oracle/username",
    "oracle_clave": "oracle/password",
    "mysql_usuario": "mysql/username",
    "mysql_clave": "mysql/password",
}
CONFIGURACION_CLIENTE = Config(connect_timeout=2, read_timeout=5, retries={"mode": "standard", "max_attempts": 3})


class SecretosNoDisponibles(Exception):
    """Faltan secretos o SSM no respondió. Nombra los parámetros, nunca sus valores."""


class LectorSsm:
    def __init__(self, cliente: Any, ruta: str) -> None:
        self._cliente = cliente
        self._ruta = ruta

    def secretos(self) -> dict[str, str | SecretStr]:
        nombres = {campo: f"{self._ruta}/{sufijo}" for campo, sufijo in NOMBRES.items()}
        try:
            respuesta = self._cliente.get_parameters(Names=list(nombres.values()), WithDecryption=True)
        except (BotoCoreError, ClientError) as error:
            raise SecretosNoDisponibles("No se pudieron leer los secretos de SSM") from error
        faltantes = respuesta.get("InvalidParameters", [])
        if faltantes:
            raise SecretosNoDisponibles("Faltan parámetros en SSM: " + ", ".join(sorted(faltantes)))
        valores = {parametro["Name"]: parametro["Value"] for parametro in respuesta.get("Parameters", [])}
        resultado: dict[str, str | SecretStr] = {}
        for campo, nombre in nombres.items():
            if nombre not in valores:
                raise SecretosNoDisponibles("Faltan parámetros en SSM: " + nombre)
            valor = valores[nombre]
            resultado[campo] = SecretStr(valor) if campo.endswith("clave") else valor
        return resultado
