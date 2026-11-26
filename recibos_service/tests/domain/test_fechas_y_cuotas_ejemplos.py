"""Pruebas de ejemplo de las fechas y las cuotas (US-07, US-08; BR-Q01 a BR-Q04, BR-D05, BR-S04, BR-L13)."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from app.domain import cuotas, fechas, mensajes
from app.domain.modelos import Cuota, DatosPosgrado, FallaFila, FechasPago, MotivoRechazo
from tests import fabricas

REGLAS = fabricas.reglas_actuales()


def test_extraordinaria_sin_festivo() -> None:
    # Ejemplo de business-logic-model.md §4.5: jueves 2027-01-07 → viernes 2027-01-15
    assert fechas.fecha_extraordinaria(date(2027, 1, 7), 8, frozenset()) == date(2027, 1, 15)


def test_extraordinaria_que_cae_en_festivo_avanza() -> None:
    festivos = frozenset({date(2027, 1, 11), date(2027, 1, 12)})
    assert fechas.fecha_extraordinaria(date(2027, 1, 3), 8, festivos) == date(2027, 1, 13)


def test_un_domingo_que_no_esta_en_la_tabla_no_mueve_la_fecha() -> None:
    assert fechas.fecha_extraordinaria(date(2027, 1, 9), 8, frozenset()) == date(2027, 1, 17)  # domingo


def test_timestamp_de_la_medianoche_en_bogota() -> None:
    # 2027-01-15T00:00:00-05:00 = 2027-01-15T05:00:00Z
    assert fechas.timestamp_medianoche(date(2027, 1, 15)) == 1_799_989_200
    assert fechas.timestamp_medianoche(date(1970, 1, 1)) == 5 * 3600
    assert fechas.fecha_de_timestamp(5 * 3600) == date(1970, 1, 1)


def test_timestamp_de_un_momento() -> None:
    momento = datetime(2027, 1, 15, 10, 0, tzinfo=fechas.ZONA_BOGOTA)
    assert fechas.timestamp(momento) == int(momento.timestamp())
    with pytest.raises(ValueError, match="zona horaria"):
        fechas.timestamp(datetime(2027, 1, 15, 10, 0))


def test_rango_y_anios_de_festivos() -> None:
    ordinarias = [date(2027, 12, 28), date(2027, 2, 1)]
    assert fechas.rango_de_festivos(ordinarias, 8) == (date(2027, 2, 9), date(2028, 2, 4))
    assert fechas.anios_a_revisar(ordinarias, 8) == frozenset({2027, 2028})
    assert fechas.rango_de_festivos([], 8) is None


def test_cuota_de_pregrado() -> None:
    resultado = cuotas.cuotas_pregrado(date(2027, 1, 7), REGLAS, frozenset())
    assert resultado == (Cuota(1, 100, FechasPago(date(2027, 1, 7), date(2027, 1, 15))),)


def test_cuotas_de_posgrado_con_porcentajes_por_defecto() -> None:
    datos = DatosPosgrado(3, "12", (date(2027, 2, 1), date(2027, 3, 1), date(2027, 4, 1)), (None, None, None))
    resultado = cuotas.cuotas_posgrado(datos, REGLAS, frozenset())
    assert isinstance(resultado, tuple)
    assert [c.porcentaje for c in resultado] == [40, 30, 30]
    assert [c.numero for c in resultado] == [1, 2, 3]
    assert resultado[2].fechas == FechasPago(date(2027, 4, 1), date(2027, 4, 9))


def test_cuotas_de_posgrado_que_no_suman_100() -> None:
    datos = DatosPosgrado(2, "12", (date(2027, 2, 1), date(2027, 3, 1)), (50, None))
    assert cuotas.cuotas_posgrado(datos, REGLAS, frozenset()) == FallaFila(
        MotivoRechazo.PORCENTAJES_NO_SUMAN_100, mensajes.porcentajes_no_suman_100(90)
    )
