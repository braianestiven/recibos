"""Motores de MySQL y Oracle: TLS, tiempos, pools y contraseña fuera de la URL (logical-components.md §2.4)."""

from __future__ import annotations

import ssl
from types import SimpleNamespace
from typing import Any

import certifi
import pymysql
import pytest
from pydantic import SecretStr
from sqlalchemy import event
from sqlalchemy import exc as sa_exc
from sqlalchemy.engine import Engine

from app.infrastructure.db.motores import (
    ORACLE_LLAMADA_POR_DEFECTO_MS,
    DatosConexion,
    codigo_de_error,
    contexto_tls,
    limite_por_defecto,
    motor_mysql,
    motor_oracle,
)
from tests.infrastructure.bd_falsa import error_mysql, error_oracle

CLAVE = "clave-que-no-va-en-la-url"


class Conectando(Exception):
    def __init__(self, cparams: dict[str, Any]) -> None:
        super().__init__("conexión de prueba")
        self.cparams = cparams


def _parametros_de_conexion(motor: Engine, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Lo que el motor le pasaría al driver al abrir una conexión, sin abrirla."""

    def conectar(*_cargs: Any, **cparams: Any) -> None:
        raise Conectando(dict(cparams))

    monkeypatch.setattr(motor.dialect, "connect", conectar)
    with pytest.raises(Conectando) as capturado:
        motor.connect()
    return capturado.value.cparams


def _verificado(contexto: object) -> None:
    assert isinstance(contexto, ssl.SSLContext)
    assert contexto.verify_mode == ssl.CERT_REQUIRED
    assert contexto.check_hostname
    assert contexto.minimum_version >= ssl.TLSVersion.TLSv1_2


def test_mysql(monkeypatch: pytest.MonkeyPatch) -> None:
    datos = DatosConexion("mysql.udistrital.edu.co", 3307, "weboffice", "recibos", SecretStr(CLAVE), certifi.where())
    motor = motor_mysql(datos, hilos=4)
    assert motor.url.password is None
    assert CLAVE not in motor.url.render_as_string(hide_password=False)
    pool: Any = motor.pool
    assert (pool.size(), pool._max_overflow, pool._timeout, pool._recycle, pool._pre_ping) == (4, 2, 5, 1800, True)
    cparams = _parametros_de_conexion(motor, monkeypatch)
    assert cparams["password"] == CLAVE
    assert (cparams["host"], cparams["port"], cparams["database"], cparams["user"]) == (
        "mysql.udistrital.edu.co",
        3307,
        "weboffice",
        "recibos",
    )
    assert (cparams["charset"], cparams["connect_timeout"], cparams["read_timeout"], cparams["write_timeout"]) == (
        "utf8mb4",
        3,
        10,
        10,
    )
    assert cparams["init_command"] == "SET SESSION innodb_lock_wait_timeout = 5"
    _verificado(cparams["ssl"])


def test_oracle(monkeypatch: pytest.MonkeyPatch) -> None:
    datos = DatosConexion("oracle.udistrital.edu.co", 2484, "ACADEMICA", "lector", SecretStr(CLAVE))
    motor = motor_oracle(datos, hilos=6)
    pool: Any = motor.pool
    assert (pool.size(), pool._max_overflow, pool._timeout, pool._recycle, pool._pre_ping) == (2, 4, 5, 1800, True)
    assert motor.dialect.arraysize == 1000  # type: ignore[attr-defined]
    cparams = _parametros_de_conexion(motor, monkeypatch)
    assert (cparams["user"], cparams["password"]) == ("lector", CLAVE)
    assert (cparams["host"], cparams["port"], cparams["service_name"], cparams["protocol"]) == (
        "oracle.udistrital.edu.co",
        2484,
        "ACADEMICA",
        "tcps",
    )
    assert (cparams["ssl_server_dn_match"], cparams["tcp_connect_timeout"]) == (True, 5)
    assert "dsn" not in cparams
    _verificado(cparams["ssl_context"])
    assert event.contains(motor, "connect", limite_por_defecto)
    assert event.contains(motor, "checkin", limite_por_defecto)


def test_oracle_con_dos_hilos_no_tiene_reserva() -> None:
    motor = motor_oracle(DatosConexion("h", 2484, "s", "u", SecretStr("c")), hilos=2)
    assert motor.pool._max_overflow == 0  # type: ignore[attr-defined]


def test_limite_por_defecto_de_oracle() -> None:
    conexion = SimpleNamespace(call_timeout=1)
    limite_por_defecto(conexion, None)
    assert conexion.call_timeout == ORACLE_LLAMADA_POR_DEFECTO_MS == 20_000
    limite_por_defecto(None, None)  # una conexión invalidada no tiene la del driver


def test_contexto_tls_con_las_ca_del_sistema() -> None:
    _verificado(contexto_tls(None))


@pytest.mark.parametrize(
    ("error", "codigo"),
    [
        (error_oracle("ORA-12541"), "ORA-12541"),
        (error_mysql(2013), "2013"),
        (pymysql.err.OperationalError(1205, "Lock wait timeout"), "1205"),
        (sa_exc.TimeoutError("QueuePool limit"), "TimeoutError"),
        (ValueError("texto"), "ValueError"),
        (RuntimeError(), "RuntimeError"),
        (pymysql.err.OperationalError(True, ""), "OperationalError"),
    ],
)
def test_codigo_de_error(error: BaseException, codigo: str) -> None:
    assert codigo_de_error(error) == codigo
