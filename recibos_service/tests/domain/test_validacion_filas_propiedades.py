"""Pruebas de propiedades de la lectura de celdas (business-logic-model.md §9; PBT-02, PBT-03, PBT-04)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from hypothesis import assume, given
from hypothesis import strategies as st

from app.domain import validacion_filas
from app.domain.modelos import FallaFila, MotivoRechazo, Rechazo, TipoPlantilla
from tests import fabricas
from tests.estrategias import codigos_invalidos, codigos_validos, fechas

TERNA = (14, 15, 16)
SMLV = st.decimals(min_value=Decimal("0.01"), max_value=Decimal("999.99"), places=2)


@given(codigos_validos())
def test_todo_codigo_de_1_a_15_digitos_se_acepta(texto: str) -> None:
    assert validacion_filas.validar_codigo(fabricas.fila(c1=texto)) == int(texto.strip())


@given(codigos_invalidos())
def test_todo_codigo_con_otro_caracter_o_demasiado_largo_se_rechaza(texto: str) -> None:
    assume(texto.strip())
    resultado = validacion_filas.validar_codigo(fabricas.fila(c1=texto))
    assert isinstance(resultado, Rechazo)
    assert resultado.motivo is MotivoRechazo.CODIGO_INVALIDO


@given(SMLV)
def test_ida_y_vuelta_de_la_unidad_smlv(valor: Decimal) -> None:
    escrito = validacion_filas.formatear_unidad(valor)
    leido = validacion_filas.leer_unidad(escrito, TipoPlantilla.POSGRADO_SMLV)
    assert leido == escrito
    assert Decimal(leido) == valor


@given(st.one_of(st.integers(0, 2000).map(str), SMLV.map(str), st.text(max_size=6)), st.sampled_from(
    [TipoPlantilla.POSGRADO_CREDITOS, TipoPlantilla.POSGRADO_SMLV]))
def test_leer_dos_veces_da_lo_mismo_que_leer_una(texto: str, tipo: TipoPlantilla) -> None:
    una = validacion_filas.leer_unidad(texto, tipo)
    if una is not None:
        assert validacion_filas.leer_unidad(una, tipo) == una
    entero = validacion_filas.leer_entero(texto)
    if entero is not None:
        assert validacion_filas.leer_entero(str(entero)) == entero


@given(fechas(desde=fabricas.HOY))
def test_toda_fecha_que_existe_y_no_es_anterior_a_hoy_se_acepta(fecha: date) -> None:
    fila = fabricas.fila(**fabricas.celdas_fecha(TERNA, fecha))
    assert validacion_filas.leer_fecha_ordinaria(fila, TERNA, None, fabricas.HOY) == fecha


@given(st.integers(1, 40), st.integers(1, 14), st.integers(2026, 2031))
def test_toda_terna_que_no_forma_una_fecha_se_rechaza(dia: int, mes: int, anio: int) -> None:
    try:
        date(anio, mes, dia)
    except ValueError:
        pass
    else:
        assume(False)
    fila = fabricas.fila(c14=str(dia), c15=str(mes), c16=str(anio))
    resultado = validacion_filas.leer_fecha_ordinaria(fila, TERNA, 1, fabricas.HOY)
    assert isinstance(resultado, FallaFila)
    assert resultado.motivo is MotivoRechazo.FECHA_INVALIDA
