"""Pruebas de ejemplo de exenciones y conceptos (US-07, US-08; BR-X01 a BR-X07, BR-C01, BR-C02).

La tabla de decisión es la de business-logic-model.md §4.6 (posgrado, votación al 10%).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain import conceptos, exenciones, mensajes
from app.domain.modelos import FallaFila, MotivoRechazo
from app.domain.plantillas import POSGRADO_CREDITOS, PREGRADO
from tests import fabricas

VOTACION, SECRETARIA = 1, 16
DESCUENTO_50, DESCUENTO_90, DESCUENTO_100, DESCUENTO_30 = 2, 17, 15, 11
COLUMNA = {VOTACION: 7, DESCUENTO_50: 15, DESCUENTO_90: 17, DESCUENTO_100: 14, DESCUENTO_30: 9, SECRETARIA: 16}
REGLAS = fabricas.reglas_actuales()


def _posgrado(*ids: int, certificado: bool) -> tuple[int, ...] | FallaFila:
    fila = fabricas.fila(c1="1", **{f"c{COLUMNA[i]}": "x" for i in ids})
    return exenciones.seleccionar(fila, POSGRADO_CREDITOS, REGLAS, certificado)


@pytest.mark.parametrize(
    ("marcadas", "certificado", "esperado"),
    [
        ((), True, ()),
        ((VOTACION,), False, (VOTACION,)),
        ((DESCUENTO_50,), True, (VOTACION, DESCUENTO_50)),
        ((DESCUENTO_50,), False, (DESCUENTO_50,)),
        ((VOTACION, DESCUENTO_90), False, (VOTACION, DESCUENTO_90)),
        ((VOTACION, DESCUENTO_100), False, (DESCUENTO_100,)),
        ((DESCUENTO_100,), True, (DESCUENTO_100,)),
        ((SECRETARIA,), True, (VOTACION, SECRETARIA)),
        ((VOTACION, DESCUENTO_30, SECRETARIA), False, (VOTACION, DESCUENTO_30, SECRETARIA)),
        ((DESCUENTO_30, SECRETARIA), True, (VOTACION, DESCUENTO_30, SECRETARIA)),
        ((DESCUENTO_100, SECRETARIA), True, (DESCUENTO_100, SECRETARIA)),
    ],
)
def test_tabla_de_decision(marcadas: tuple[int, ...], certificado: bool, esperado: tuple[int, ...]) -> None:
    assert _posgrado(*marcadas, certificado=certificado) == esperado


def test_dos_descuentos_no_se_suben() -> None:
    assert _posgrado(DESCUENTO_50, DESCUENTO_30, certificado=False) == FallaFila(
        MotivoRechazo.DESCUENTOS_NO_ACUMULABLES, mensajes.DESCUENTOS_POSGRADO
    )
    fila = fabricas.fila(c1="1", c6="x", c9="x")
    assert exenciones.seleccionar(fila, PREGRADO, REGLAS, False) == FallaFila(
        MotivoRechazo.DESCUENTOS_NO_ACUMULABLES, mensajes.DESCUENTOS_PREGRADO
    )


def test_pregrado_con_votacion_marcada_y_un_descuento_de_las_columnas_8_a_13() -> None:
    fila = fabricas.fila(c1="1", c5="x", c12="x")  # votación 10% + exención 8 (30%)
    assert exenciones.seleccionar(fila, PREGRADO, REGLAS, False) == (1, 8)


def test_columnas_sin_id_y_dos_columnas_con_el_mismo_id() -> None:
    reglas = fabricas.reglas_actuales(exenciones_columna_posgrado={7: 1, 8: 10, 9: 10, 16: 16})
    fila = fabricas.fila(c1="1", c8="x", c9="x", c13="x")
    assert exenciones.seleccionar(fila, POSGRADO_CREDITOS, reglas, False) == (10,)


def test_tope_exacto_de_100_se_permite() -> None:
    reglas = fabricas.reglas_actuales().con_porcentajes({**fabricas.PORCENTAJES_EXENCION, 17: Decimal(90)})
    fila = fabricas.fila(c1="1", c7="x", c17="x")
    assert exenciones.seleccionar(fila, POSGRADO_CREDITOS, reglas, False) == (VOTACION, 17)


class TestConceptos:
    def test_pregrado(self) -> None:
        fila = fabricas.fila(c1="1", c4="x", c2="x")
        assert conceptos.seleccionar(fila, PREGRADO, REGLAS) == (1, 19, 2, 4)

    def test_posgrado(self) -> None:
        fila = fabricas.fila(c1="1", c5="x")
        assert conceptos.seleccionar(fila, POSGRADO_CREDITOS, REGLAS) == (1, 3)

    def test_sin_repetidos_y_columnas_sin_concepto(self) -> None:
        reglas = fabricas.reglas_actuales(conceptos_columna_posgrado={4: 1, 5: 3})
        fila = fabricas.fila(c1="1", c4="x", c5="x", c6="x")
        assert conceptos.seleccionar(fila, POSGRADO_CREDITOS, reglas) == (1, 3)
