"""Festivos de weboffice según la configuración de D5 (BR-L13, F9, F10)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pytest

from app.application.errores import DependenciaNoDisponible
from app.application.presupuesto import Plazo, PlazoVencido
from app.infrastructure.festivos.fuente_festivos import FuenteFestivosWeboffice, como_fecha, fecha_de_partes
from tests.infrastructure.bd_falsa import Motor, Resultado, error_mysql, error_oracle
from tests.interfaces.dobles import registros

DESDE, HASTA = date(2027, 1, 1), date(2027, 12, 31)


def _plazo(motor: Motor, restante: float = 100.0) -> Plazo:
    return Plazo(motor.tiempo + restante, motor.reloj)


def _fuente(motor: Motor, tipo: str = "mysql", tabla: str = "festivos", columnas: tuple[str, ...] = ("fecha",)) -> Any:
    return FuenteFestivosWeboffice(motor, tipo, tabla, columnas)  # type: ignore[arg-type]


def test_una_columna_en_mysql() -> None:
    filas = [(date(2027, 1, 1),), (datetime(2027, 1, 11, 0, 0),), ("2027-03-22",), (None,), (date(2028, 1, 1),), ("x",)]
    motor = Motor(lambda _t, _p: Resultado(filas=filas))
    with registros("app.infrastructure.festivos.fuente_festivos") as eventos:
        festivos = _fuente(motor, tabla="weboffice.festivos").festivos(DESDE, HASTA, _plazo(motor))
    assert festivos == frozenset({date(2027, 1, 1), date(2027, 1, 11), date(2027, 3, 22)})
    (sentencia,) = motor.sentencias
    assert sentencia.texto == "SELECT `fecha` FROM `weboffice`.`festivos` WHERE `fecha` >= :desde AND `fecha` < :hasta"
    assert sentencia.parametros == {"desde": DESDE, "hasta": date(2028, 1, 1)}
    assert sentencia.call_timeout == 0  # MySQL usa su tiempo de lectura, no call_timeout
    assert [e.datos for e in eventos] == [{"filas": 2}]


def test_tres_columnas_en_oracle() -> None:
    filas = [(1, 1, 2027), ("6", "1", "2027"), (31, 2, 2027), (25, 12, 2026)]
    motor = Motor(lambda _t, _p: Resultado(filas=filas))
    fuente = _fuente(motor, "oracle", "acfestivos", ("fes_dia", "fes_mes", "fes_anio"))
    assert fuente.festivos(DESDE, HASTA, _plazo(motor, restante=12.0)) == frozenset({date(2027, 1, 1), date(2027, 1, 6)})
    (sentencia,) = motor.sentencias
    assert sentencia.texto == (
        "SELECT fes_dia, fes_mes, fes_anio FROM acfestivos WHERE fes_anio BETWEEN :anio_desde AND :anio_hasta"
    )
    assert sentencia.parametros == {"anio_desde": 2027, "anio_hasta": 2027}
    assert sentencia.call_timeout == 12_000


@pytest.mark.parametrize(("tipo", "restante"), [("mysql", 13.0), ("oracle", 5.0)])
def test_sin_tiempo_no_consulta(tipo: str, restante: float) -> None:
    motor = Motor()
    with pytest.raises(PlazoVencido):
        _fuente(motor, tipo).festivos(DESDE, HASTA, _plazo(motor, restante=restante))
    assert motor.eventos == []


@pytest.mark.parametrize("error", [error_mysql(1146), error_oracle("ORA-00942")])
def test_error_de_la_base(error: Exception) -> None:
    motor = Motor(lambda _t, _p: error)
    with pytest.raises(DependenciaNoDisponible) as capturado:
        _fuente(motor).festivos(DESDE, HASTA, _plazo(motor))
    assert capturado.value.dependencia == "festivos"
    assert "invalidate 1" in motor.eventos


def test_configuracion_de_columnas_invalida() -> None:
    with pytest.raises(ValueError, match="columna"):
        _fuente(Motor(), columnas=("dia", "mes"))


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (date(2027, 1, 1), date(2027, 1, 1)),
        (datetime(2027, 1, 1, 13, 5), date(2027, 1, 1)),
        ("2027-01-01 00:00:00", date(2027, 1, 1)),
        ("01/01/2027", None),
        (20270101, None),
        (None, None),
    ],
)
def test_como_fecha(valor: Any, esperado: date | None) -> None:
    assert como_fecha(valor) == esperado


def test_fecha_de_partes() -> None:
    assert fecha_de_partes(29, 2, 2028) == date(2028, 2, 29)
    assert fecha_de_partes(29, 2, 2027) is None
    assert fecha_de_partes(None, 1, 2027) is None
    assert fecha_de_partes(1, 1, 10**30) is None
