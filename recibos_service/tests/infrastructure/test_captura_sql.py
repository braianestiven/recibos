"""Texto SQL para `sql_statement` de la auditoría, sin valores y con tamaño acotado (AD-10)."""

from __future__ import annotations

import threading

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.infrastructure.db.captura_sql import LARGO_MAXIMO_SENTENCIA, MAXIMO_SENTENCIAS, CapturaSql


def _motor() -> tuple[Engine, CapturaSql]:
    motor = create_engine("sqlite://")
    captura = CapturaSql()
    captura.registrar(motor)
    return motor, captura


def _ejecutar(motor: Engine, *sentencias: str, **parametros: object) -> None:
    with motor.connect() as conexion:
        for sentencia in sentencias:
            conexion.execute(text(sentencia), parametros)


def test_sin_iniciar_no_captura() -> None:
    motor, captura = _motor()
    _ejecutar(motor, "SELECT 1")
    assert captura.sentencias() == []


def test_cada_texto_una_vez_y_sin_valores() -> None:
    motor, captura = _motor()
    captura.iniciar()
    _ejecutar(motor, "SELECT 1", "SELECT 1", "SELECT   2\n   FROM (SELECT 1)")
    _ejecutar(motor, "SELECT :codigo", codigo="20271020001")
    assert captura.sentencias() == ["SELECT 1", "SELECT 2 FROM (SELECT 1)", "SELECT ?"]
    captura.iniciar()
    assert captura.sentencias() == []


def test_textos_largos_y_maximo_de_textos() -> None:
    motor, captura = _motor()
    captura.iniciar()
    _ejecutar(motor, "SELECT " + "1 + " * 600 + "1")
    _ejecutar(motor, *[f"SELECT {i}" for i in range(MAXIMO_SENTENCIAS + 10)])
    sentencias = captura.sentencias()
    assert len(sentencias) == MAXIMO_SENTENCIAS
    assert len(sentencias[0]) == LARGO_MAXIMO_SENTENCIA
    assert sentencias[-1] == f"SELECT {MAXIMO_SENTENCIAS - 2}"


def test_cada_peticion_tiene_su_lista() -> None:
    motor, captura = _motor()
    resultados: dict[str, list[str]] = {}

    def peticion(nombre: str, sentencia: str) -> None:
        captura.iniciar()
        _ejecutar(motor, sentencia)
        resultados[nombre] = captura.sentencias()

    for nombre, sentencia in (("a", "SELECT 1"), ("b", "SELECT 2")):
        hilo = threading.Thread(target=peticion, args=(nombre, sentencia))
        hilo.start()
        hilo.join()
    assert resultados == {"a": ["SELECT 1"], "b": ["SELECT 2"]}
    assert captura.sentencias() == []  # el hilo principal nunca inició una captura
