"""Propiedades de las fechas y las cuotas (business-logic-model.md §9; PBT-02, PBT-03)."""

from __future__ import annotations

from datetime import date, timedelta

from hypothesis import assume, given
from hypothesis import strategies as st

from app.domain import cuotas, fechas
from app.domain.modelos import DatosPosgrado, FallaFila
from app.domain.reglas import ReglasLiquidacion
from tests.estrategias import fechas as fechas_st
from tests.estrategias import festivos, reglas


@given(fechas_st(), st.integers(0, 15), festivos())
def test_extraordinaria_no_cae_en_festivo_y_los_dias_saltados_son_festivos(
    ordinaria: date, dias: int, conjunto: frozenset[date]
) -> None:
    extra = fechas.fecha_extraordinaria(ordinaria, dias, conjunto)
    base = ordinaria + timedelta(days=dias)
    assert extra >= base
    assert extra not in conjunto
    assert all(base + timedelta(days=i) in conjunto for i in range((extra - base).days))


@given(fechas_st(), st.integers(0, 15))
def test_sin_festivos_la_extraordinaria_es_la_ordinaria_mas_los_dias(ordinaria: date, dias: int) -> None:
    assert fechas.fecha_extraordinaria(ordinaria, dias, frozenset()) == ordinaria + timedelta(days=dias)


@given(st.dates(min_value=date(1971, 1, 1), max_value=date(2100, 12, 31)))
def test_ida_y_vuelta_del_timestamp_de_la_medianoche(fecha: date) -> None:
    assert fechas.fecha_de_timestamp(fechas.timestamp_medianoche(fecha)) == fecha


@st.composite
def datos_posgrado(draw: st.DrawFn) -> DatosPosgrado:
    numero = draw(st.integers(1, 3))
    inicio = draw(fechas_st(desde=date(2027, 1, 1), hasta=date(2029, 12, 31)))
    saltos = draw(st.lists(st.integers(1, 60), min_size=numero - 1, max_size=numero - 1))
    ordinarias = [inicio]
    for salto in saltos:
        ordinarias.append(ordinarias[-1] + timedelta(days=salto))
    porcentajes = draw(st.lists(st.one_of(st.none(), st.integers(0, 100)), min_size=numero, max_size=numero))
    return DatosPosgrado(numero, "12", tuple(ordinarias), tuple(porcentajes))


@given(datos_posgrado(), reglas(), festivos())
def test_cuotas_de_posgrado_numeradas_que_suman_100_con_fechas_crecientes(
    datos: DatosPosgrado, r: ReglasLiquidacion, conjunto: frozenset[date]
) -> None:
    resultado = cuotas.cuotas_posgrado(datos, r, conjunto)
    completados = [
        valor if valor is not None else r.porcentaje_por_defecto(datos.numero_cuotas, posicion)
        for posicion, valor in enumerate(datos.porcentajes, start=1)
    ]
    if sum(completados) != 100:
        assert isinstance(resultado, FallaFila)
        return
    assert not isinstance(resultado, FallaFila)
    assert [c.numero for c in resultado] == list(range(1, datos.numero_cuotas + 1))
    assert sum(c.porcentaje for c in resultado) == 100
    assert [c.porcentaje for c in resultado] == completados
    ordinarias = [c.fechas.ordinaria for c in resultado]
    assert ordinarias == sorted(ordinarias)
    assert len(set(ordinarias)) == len(ordinarias)


@given(fechas_st(), reglas(), festivos())
def test_pregrado_tiene_una_sola_cuota_al_100(ordinaria: date, r: ReglasLiquidacion, conjunto: frozenset[date]) -> None:
    assume(ordinaria.year < 2031)
    (cuota,) = cuotas.cuotas_pregrado(ordinaria, r, conjunto)
    assert (cuota.numero, cuota.porcentaje, cuota.fechas.ordinaria) == (1, 100, ordinaria)
