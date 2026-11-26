"""Pruebas de ejemplo de las plantillas (US-03, US-04, US-05; BR-L08 a BR-L11)."""

from __future__ import annotations

import pytest

from app.domain import mensajes, plantillas
from app.domain.errores import FormatoInvalido
from app.domain.modelos import FilaPlantilla, TipoPlantilla, crear_hoja
from tests import fabricas


def test_normalizar_quita_tildes_espacios_y_mayusculas() -> None:
    assert plantillas.normalizar("  Código   del\testudiante ") == "CODIGO DEL ESTUDIANTE"
    assert plantillas.normalizar("Año") == "ANO"


@pytest.mark.parametrize("espec", plantillas.ESPECIFICACIONES)
def test_identifica_cada_plantilla_por_el_texto_de_a1(espec: plantillas.EspecificacionPlantilla) -> None:
    hoja = fabricas.hoja_para(espec, texto_a1="  " + espec.texto_a1.lower() + " ")
    assert plantillas.identificar(hoja) is espec


@pytest.mark.parametrize("texto", [None, "PLANTILLA GENERAL", "Otra cosa"])
def test_a1_no_reconocido(texto: str | None) -> None:
    celdas = {(3, 1): "Código"} if texto is None else {(1, 1): texto}
    with pytest.raises(FormatoInvalido) as error:
        plantillas.identificar(crear_hoja(celdas))
    assert error.value.mensaje == mensajes.PLANTILLA_NO_RECONOCIDA


@pytest.mark.parametrize("espec", plantillas.ESPECIFICACIONES)
def test_plantilla_con_el_formato_de_la_especificacion(espec: plantillas.EspecificacionPlantilla) -> None:
    plantillas.validar_formato(fabricas.hoja_para(espec), espec)


def test_pregrado_anterior_con_reingreso_tiene_su_mensaje() -> None:
    espec = plantillas.PREGRADO
    hoja = fabricas.hoja_para(espec, columnas=14, encabezados={14: "Reingreso"})
    with pytest.raises(FormatoInvalido) as error:
        plantillas.validar_formato(hoja, espec)
    assert error.value.mensaje == mensajes.PLANTILLA_CON_REINGRESO


def test_pregrado_de_14_columnas_sin_reingreso_es_un_formato_distinto() -> None:
    espec = plantillas.PREGRADO
    hoja = fabricas.hoja_para(espec, columnas=14, encabezados={14: "Otra"})
    with pytest.raises(FormatoInvalido) as error:
        plantillas.validar_formato(hoja, espec)
    assert "trae 14 columnas y deben ser 16" in error.value.mensaje


def test_posgrado_con_menos_columnas() -> None:
    espec = plantillas.POSGRADO_CREDITOS
    with pytest.raises(FormatoInvalido) as error:
        plantillas.validar_formato(fabricas.hoja_para(espec, columnas=28), espec)
    assert error.value.mensaje == mensajes.columnas_distintas(
        TipoPlantilla.POSGRADO_CREDITOS, "trae 28 columnas y deben ser 29"
    )


def test_encabezado_distinto() -> None:
    espec = plantillas.POSGRADO_SMLV
    hoja = fabricas.hoja_para(espec, encabezados={2: "Créditos"})
    with pytest.raises(FormatoInvalido) as error:
        plantillas.validar_formato(hoja, espec)
    assert "columna 2" in error.value.mensaje


def test_encabezado_en_varias_filas() -> None:
    espec = plantillas.POSGRADO_CREDITOS
    hoja = fabricas.hoja_para(espec, encabezados={18: "Día"})
    celdas = dict(hoja.celdas)
    celdas[(3, 18)] = "Cuota 1"
    hoja = crear_hoja(celdas)
    assert plantillas.encabezado(hoja, espec, 18) == "CUOTA 1 DIA"
    plantillas.validar_formato(hoja, espec)


def test_extraer_filas_omite_vacias_y_columnas_de_mas() -> None:
    espec = plantillas.PREGRADO
    hoja = fabricas.hoja_para(
        espec,
        filas={
            4: {1: "20271020001", 5: "x"},
            5: {2: "   "},
            6: {20: "fuera de la plantilla"},
            7: {3: "x"},
        },
    )
    filas = plantillas.extraer_filas(hoja, espec)
    assert filas == [
        FilaPlantilla(numero=4, celdas={1: "20271020001", 5: "x"}),
        FilaPlantilla(numero=7, celdas={3: "x"}),
    ]


def test_hoja_sin_filas_de_datos() -> None:
    espec = plantillas.POSGRADO_CREDITOS
    assert plantillas.extraer_filas(fabricas.hoja_para(espec), espec) == []


def test_numero_maximo_de_cuotas() -> None:
    assert plantillas.PREGRADO.max_cuotas == 1
    assert plantillas.POSGRADO_CREDITOS.max_cuotas == 3
