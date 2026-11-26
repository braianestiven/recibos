"""Pruebas del generador de solicitudes: ejemplos (US-07, US-08, US-11) y propiedades (§9, PBT-03)."""

from __future__ import annotations

from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain import generador_solicitud, mensajes
from app.domain.modelos import FallaFila, MotivoRechazo, Periodo, Solicitud, TipoPlantilla
from app.domain.plantillas import ESPECIFICACIONES, POSGRADO_CREDITOS, POSGRADO_SMLV, PREGRADO
from tests import fabricas
from tests.estrategias import filas_de_datos, reglas
from tests.fabricas import HOY, celdas_fecha

REGLAS = fabricas.reglas_actuales()
CUOTA1, CUOTA2, _ = POSGRADO_CREDITOS.columnas_fecha


def _generar(fila: object, espec: object = PREGRADO, contexto: object = None, cert: bool = False) -> object:
    return generador_solicitud.generar(
        fila,  # type: ignore[arg-type]
        espec,  # type: ignore[arg-type]
        20271020001,
        fabricas.estudiante(),
        contexto or fabricas.contexto(),  # type: ignore[arg-type]
        REGLAS,
        frozenset({date(2027, 2, 9)}),
        HOY,
        cert,
    )


def test_solicitud_de_pregrado() -> None:
    fila = fabricas.fila(c1="20271020001", c2="x", c5="x", **celdas_fecha((14, 15, 16), date(2027, 2, 1)))
    solicitud = _generar(fila)
    assert isinstance(solicitud, Solicitud)
    assert solicitud.unidad == "0"
    assert solicitud.cuota == 1
    assert solicitud.cuotas[0].fechas.extraordinaria == date(2027, 2, 10)  # el 9 es festivo
    assert solicitud.exenciones == (1,)
    assert solicitud.conceptos == (1, 19, 2)
    assert solicitud.tipo is TipoPlantilla.PREGRADO
    assert solicitud.periodo == Periodo(2027, 1)
    assert solicitud.codigo_carrera == 20


def test_pregrado_sin_fecha() -> None:
    assert _generar(fabricas.fila(c1="1")) == FallaFila(MotivoRechazo.FECHA_INVALIDA, mensajes.fecha_faltante(None))


def test_solicitud_de_posgrado_smlv() -> None:
    celdas = {"c1": "1", "c2": "4,50", "c3": "2", "c27": "70", "c28": "30"}
    celdas.update(celdas_fecha(CUOTA1, date(2027, 2, 1)))
    celdas.update(celdas_fecha(CUOTA2, date(2027, 3, 1)))
    contexto = fabricas.contexto(nivel="MAESTRIA")
    solicitud = _generar(fabricas.fila(**celdas), POSGRADO_SMLV, contexto)
    assert isinstance(solicitud, Solicitud)
    assert (solicitud.unidad, solicitud.cuota) == ("4.5", 2)
    assert [c.porcentaje for c in solicitud.cuotas] == [70, 30]


@pytest.mark.parametrize(
    ("cambios", "motivo"),
    [
        ({"c3": "5"}, MotivoRechazo.CUOTAS_INVALIDAS),
        ({"c27": "70", "c28": "40"}, MotivoRechazo.PORCENTAJES_NO_SUMAN_100),
        ({"c8": "x", "c9": "x"}, MotivoRechazo.DESCUENTOS_NO_ACUMULABLES),
    ],
)
def test_motivos_de_posgrado(cambios: dict[str, str], motivo: MotivoRechazo) -> None:
    celdas = {"c1": "1", "c2": "12", "c3": "2"}
    celdas.update(celdas_fecha(CUOTA1, date(2027, 2, 1)))
    celdas.update(celdas_fecha(CUOTA2, date(2027, 3, 1)))
    celdas.update(cambios)
    falla = _generar(fabricas.fila(**celdas), POSGRADO_CREDITOS, fabricas.contexto(nivel="POSGRADO"))
    assert isinstance(falla, FallaFila)
    assert falla.motivo is motivo


def test_sin_periodo_es_un_error_de_programacion() -> None:
    with pytest.raises(ValueError, match="BR-E06"):
        _generar(fabricas.fila(c1="1"), contexto=fabricas.contexto(periodo=None))


@given(st.sampled_from(ESPECIFICACIONES).flatmap(lambda e: st.tuples(st.just(e), filas_de_datos(e))), reglas())
def test_unidad_cuota_y_periodo(caso: tuple, r: object) -> None:
    espec, fila = caso
    contexto = fabricas.contexto(periodo=Periodo(2027, 2))
    resultado = generador_solicitud.generar(
        fila, espec, 1, fabricas.estudiante(), contexto, r, frozenset(), HOY, True  # type: ignore[arg-type]
    )
    if isinstance(resultado, FallaFila):
        return
    assert (resultado.unidad == "0") == (espec.tipo is TipoPlantilla.PREGRADO)
    assert resultado.cuota == len(resultado.cuotas)
    if espec.tipo.es_posgrado:
        assert resultado.cuota == int(fila.texto(3) or 0)
    assert resultado.periodo == Periodo(2027, 2)
