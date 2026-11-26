"""Pruebas de propiedades de las plantillas (business-logic-model.md §9; PBT-03)."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain import plantillas
from app.domain.errores import FormatoInvalido
from app.domain.modelos import crear_hoja
from tests import fabricas
from tests.estrategias import MARCAS

ESPECS = st.sampled_from(plantillas.ESPECIFICACIONES)


@st.composite
def hojas_con_datos(draw: st.DrawFn) -> tuple[plantillas.EspecificacionPlantilla, dict[int, dict[int, str]]]:
    espec = draw(ESPECS)
    numeros = draw(st.lists(st.integers(espec.fila_inicial, espec.fila_inicial + 40), unique=True, max_size=12))
    filas: dict[int, dict[int, str]] = {}
    for numero in numeros:
        columnas = draw(st.lists(st.integers(1, espec.num_columnas), unique=True, max_size=6))
        filas[numero] = {columna: draw(st.one_of(MARCAS, st.just("   "))) for columna in columnas}
    return espec, filas


@given(hojas_con_datos())
def test_ninguna_fila_vacia_y_numeros_crecientes(datos: tuple[plantillas.EspecificacionPlantilla, dict]) -> None:
    espec, filas = datos
    extraidas = plantillas.extraer_filas(fabricas.hoja_para(espec, filas=filas), espec)
    numeros = [fila.numero for fila in extraidas]
    assert numeros == sorted(set(numeros))
    assert all(fila.celdas for fila in extraidas)
    assert all(texto.strip() for fila in extraidas for texto in fila.celdas.values())


@given(hojas_con_datos(), st.lists(st.integers(1, 60), max_size=8))
def test_filas_vacias_o_con_espacios_no_cambian_el_resultado(
    datos: tuple[plantillas.EspecificacionPlantilla, dict], vacias: list[int]
) -> None:
    espec, filas = datos
    original = plantillas.extraer_filas(fabricas.hoja_para(espec, filas=filas), espec)
    con_ruido = {numero: dict(celdas) for numero, celdas in filas.items()}
    for desplazamiento in vacias:
        numero = espec.fila_inicial + 40 + desplazamiento
        con_ruido.setdefault(numero, {})[1] = "  "
    assert plantillas.extraer_filas(fabricas.hoja_para(espec, filas=con_ruido), espec) == original


@given(ESPECS, st.data())
def test_hoja_armada_con_la_especificacion_se_acepta_y_un_encabezado_cambiado_no(
    espec: plantillas.EspecificacionPlantilla, data: st.DataObject
) -> None:
    hoja = fabricas.hoja_para(espec)
    plantillas.validar_formato(hoja, espec)
    columna = data.draw(st.sampled_from(sorted(espec.encabezados)))
    celdas = {clave: valor for clave, valor in hoja.celdas.items() if clave[1] != columna or clave[0] == 1}
    celdas[(espec.fila_inicial - 1, columna)] = "ZZZ"
    with pytest.raises(FormatoInvalido):
        plantillas.validar_formato(crear_hoja(celdas), espec)
