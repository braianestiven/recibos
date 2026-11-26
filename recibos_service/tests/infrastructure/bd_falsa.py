"""Motor y conexión falsos con la parte de la API de SQLAlchemy que usan los repositorios.

Registran cada sentencia con sus parámetros, el `call_timeout` vigente y la hora del reloj de prueba, y
responden según una función. Sirven para probar el SQL, los parámetros enlazados, los plazos y el
manejo de errores sin una base de datos.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pymysql
from sqlalchemy import exc as sa_exc


@dataclass
class Resultado:
    filas: list[tuple[Any, ...]] = field(default_factory=list)
    escalar: Any = None
    lastrowid: int = 0

    def all(self) -> list[tuple[Any, ...]]:
        return list(self.filas)

    def scalar(self) -> Any:
        return self.escalar

    def scalar_one(self) -> Any:
        return self.escalar

    def scalars(self) -> list[Any]:
        return [fila[0] for fila in self.filas]


@dataclass
class Sentencia:
    texto: str
    parametros: Any
    call_timeout: int
    momento: float
    conexion: int


Respuesta = Resultado | BaseException


class Conexion:
    def __init__(self, motor: Motor, numero: int) -> None:
        self.motor = motor
        self.numero = numero
        self.invalidated = False
        self.closed = False
        self.connection = SimpleNamespace(driver_connection=SimpleNamespace(call_timeout=0))

    def _registrar(self, texto: str, parametros: Any) -> None:
        limite = self.connection.driver_connection.call_timeout
        self.motor.sentencias.append(Sentencia(texto, parametros, limite, self.motor.reloj(), self.numero))
        self.motor.avanzar()

    def execute(self, sentencia: Any, parametros: Any = None) -> Resultado:
        texto = " ".join(str(sentencia).split())
        self._registrar(texto, parametros)
        respuesta = self.motor.responder(texto, parametros)
        if isinstance(respuesta, BaseException):
            raise respuesta
        return respuesta

    def commit(self) -> None:
        self._registrar("COMMIT", None)
        respuesta = self.motor.responder("COMMIT", None)
        if isinstance(respuesta, BaseException):
            raise respuesta

    def rollback(self) -> None:
        self.motor.eventos.append(f"rollback {self.numero}")
        if self.motor.error_al_revertir is not None:
            raise self.motor.error_al_revertir

    def invalidate(self) -> None:
        self.invalidated = True
        self.motor.eventos.append(f"invalidate {self.numero}")
        if self.motor.error_al_invalidar is not None:
            raise self.motor.error_al_invalidar

    def close(self) -> None:
        self.motor.eventos.append(f"close {self.numero}")
        if self.motor.error_al_cerrar is not None:
            raise self.motor.error_al_cerrar
        self.closed = True

    def __enter__(self) -> Conexion:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class Motor:
    """`responder(texto, parametros)` devuelve un `Resultado` o una excepción para lanzar."""

    def __init__(self, responder: Callable[[str, Any], Respuesta] | None = None) -> None:
        self.responder: Callable[[str, Any], Respuesta] = responder or (lambda _texto, _parametros: Resultado())
        self.sentencias: list[Sentencia] = []
        self.eventos: list[str] = []
        self.conexiones: list[Conexion] = []
        self.error_al_conectar: BaseException | None = None
        self.error_al_revertir: BaseException | None = None
        self.error_al_invalidar: BaseException | None = None
        self.error_al_cerrar: BaseException | None = None
        self.tiempo = 0.0
        self.segundos_por_sentencia = 0.0

    def reloj(self) -> float:
        return self.tiempo

    def avanzar(self) -> None:
        self.tiempo += self.segundos_por_sentencia

    def connect(self) -> Conexion:
        if self.error_al_conectar is not None:
            raise self.error_al_conectar
        conexion = Conexion(self, len(self.conexiones) + 1)
        self.conexiones.append(conexion)
        self.eventos.append(f"connect {conexion.numero}")
        return conexion

    @contextmanager
    def begin(self) -> Iterator[Conexion]:
        with self.connect() as conexion:
            yield conexion
            conexion.commit()

    def textos(self) -> list[str]:
        return [s.texto for s in self.sentencias]


def error_mysql(codigo: int, invalidada: bool = False) -> sa_exc.DBAPIError:
    """Error de SQLAlchemy con el error de PyMySQL adentro; el mensaje trae un valor que no debe registrarse."""
    original = pymysql.err.OperationalError(codigo, "Duplicate entry '20271020001' o conexión perdida")
    return sa_exc.OperationalError("SQL", {}, original, connection_invalidated=invalidada)


class ErrorOracle(Exception):
    """Imita un error de python-oracledb: `args[0]` tiene `full_code`."""

    def __init__(self, codigo: str) -> None:
        super().__init__(SimpleNamespace(full_code=codigo, message=f"{codigo}: detalle con datos"))


def error_oracle(codigo: str = "ORA-12541") -> sa_exc.DBAPIError:
    return sa_exc.DatabaseError("SELECT", {}, ErrorOracle(codigo))
