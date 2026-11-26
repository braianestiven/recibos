"""Motores de SQLAlchemy para MySQL y Oracle: TLS, tiempos de espera y pools (logical-components.md §2.4).

- Las contraseñas no van en la URL: se ponen al abrir cada conexión (`do_connect`), desde el `SecretStr`.
- Al crear los motores no se conecta a ninguna base; los pools abren conexiones cuando hacen falta (§7.5).
- `codigo_de_error` da el código de la base para los registros, nunca el mensaje: el de MySQL puede
  traer valores (NFR-S08).
"""

from __future__ import annotations

import ssl
from dataclasses import dataclass
from typing import Any

from pydantic import SecretStr
from sqlalchemy import URL, create_engine, event
from sqlalchemy.engine import Engine

MYSQL_CONEXION_S = 3
MYSQL_LECTURA_S = 10
MYSQL_ESCRITURA_S = 10
ESPERA_BLOQUEO_FILAS_S = 5  # innodb_lock_wait_timeout
ORACLE_CONEXION_S = 5
ORACLE_LLAMADA_POR_DEFECTO_MS = 20_000
ARRAYSIZE_ORACLE = 1000
ESPERA_POOL_S = 5
RECICLADO_S = 1800
RESERVA_MYSQL = 2
CONEXIONES_FIJAS_ORACLE = 2


@dataclass(frozen=True)
class DatosConexion:
    host: str
    puerto: int
    base: str  # base de MySQL o servicio de Oracle
    usuario: str
    clave: SecretStr
    ca: str | None = None  # certificado de la CA (D14); sin él, las CA del sistema


def contexto_tls(ca: str | None) -> ssl.SSLContext:
    """Verifica el certificado y el nombre del servidor, con TLS 1.2 o superior (NFR-S01, SECURITY-01)."""
    contexto = ssl.create_default_context(cafile=ca)
    contexto.minimum_version = ssl.TLSVersion.TLSv1_2
    return contexto


def _clave_al_conectar(motor: Engine, clave: SecretStr) -> None:
    @event.listens_for(motor, "do_connect")
    def poner_clave(_dialecto: Any, _registro: Any, _cargs: Any, cparams: dict[str, Any]) -> None:
        cparams["password"] = clave.get_secret_value()


def motor_mysql(datos: DatosConexion, hilos: int) -> Engine:
    url = URL.create(
        "mysql+pymysql",
        username=datos.usuario,
        host=datos.host,
        port=datos.puerto,
        database=datos.base,
        query={"charset": "utf8mb4"},
    )
    motor = create_engine(
        url,
        connect_args={
            "ssl": contexto_tls(datos.ca),
            "connect_timeout": MYSQL_CONEXION_S,
            "read_timeout": MYSQL_LECTURA_S,
            "write_timeout": MYSQL_ESCRITURA_S,
            "init_command": f"SET SESSION innodb_lock_wait_timeout = {ESPERA_BLOQUEO_FILAS_S}",
        },
        pool_size=hilos,
        max_overflow=RESERVA_MYSQL,
        pool_timeout=ESPERA_POOL_S,
        pool_recycle=RECICLADO_S,
        pool_pre_ping=True,
    )
    _clave_al_conectar(motor, datos.clave)
    return motor


def motor_oracle(datos: DatosConexion, hilos: int) -> Engine:
    """Modo thin de python-oracledb, con TCPS. `call_timeout` lo fija el repositorio antes de cada llamada."""
    motor = create_engine(
        URL.create("oracle+oracledb", username=datos.usuario),
        arraysize=ARRAYSIZE_ORACLE,
        connect_args={
            "host": datos.host,
            "port": datos.puerto,
            "service_name": datos.base,
            "protocol": "tcps",
            "ssl_context": contexto_tls(datos.ca),
            "ssl_server_dn_match": True,
            "tcp_connect_timeout": ORACLE_CONEXION_S,
        },
        pool_size=CONEXIONES_FIJAS_ORACLE,
        max_overflow=max(0, hilos - CONEXIONES_FIJAS_ORACLE),
        pool_timeout=ESPERA_POOL_S,
        pool_recycle=RECICLADO_S,
        pool_pre_ping=True,
    )
    _clave_al_conectar(motor, datos.clave)
    event.listen(motor, "connect", limite_por_defecto)
    event.listen(motor, "checkin", limite_por_defecto)
    return motor


def limite_por_defecto(conexion: Any, _registro: Any) -> None:
    """Al abrir y al devolver cada conexión de Oracle: el pre-ping y la primera llamada nunca quedan sin límite."""
    if conexion is not None:  # una conexión invalidada llega al pool sin la conexión del driver
        conexion.call_timeout = ORACLE_LLAMADA_POR_DEFECTO_MS


def codigo_de_error(error: BaseException) -> str:
    """`ORA-12541`, `DPY-4024` o el número de MySQL (2013); el nombre del tipo si no hay código."""
    original = getattr(error, "orig", None) or error
    argumentos = getattr(original, "args", ())
    if argumentos:
        primero = argumentos[0]
        codigo = getattr(primero, "full_code", None)  # error de python-oracledb
        if isinstance(codigo, str) and codigo:
            return codigo
        if isinstance(primero, int) and not isinstance(primero, bool):  # error de PyMySQL
            return str(primero)
    return type(original).__name__
