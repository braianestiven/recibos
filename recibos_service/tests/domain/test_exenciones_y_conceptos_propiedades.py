"""Propiedades de exenciones y conceptos (business-logic-model.md §9; PBT-03 y oráculo PBT-05)."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from app.domain import conceptos, exenciones
from app.domain.modelos import FallaFila, FilaPlantilla, MotivoRechazo, TipoPlantilla
from app.domain.plantillas import ESPECIFICACIONES, EspecificacionPlantilla
from app.domain.reglas import ReglasLiquidacion
from tests.estrategias import filas_de_datos, reglas

REINGRESO = 18


@st.composite
def casos(draw: st.DrawFn) -> tuple[FilaPlantilla, EspecificacionPlantilla, ReglasLiquidacion, bool]:
    espec = draw(st.sampled_from(ESPECIFICACIONES))
    return draw(filas_de_datos(espec)), espec, draw(reglas()), draw(st.booleans())


def oraculo(fila: FilaPlantilla, espec: EspecificacionPlantilla, r: ReglasLiquidacion, cert: bool) -> object:
    """Tabla de decisión de §4.6 escrita como reglas simples."""
    ids = {r.exencion_de_columna(espec.tipo, c) for c in espec.columnas_exencion if fila.marcada(c)} - {None}
    descuentos = sorted(i for i in ids if i not in {r.id_exencion_votacion, r.id_exencion_secretaria})
    if len(descuentos) > 1:
        return MotivoRechazo.DESCUENTOS_NO_ACUMULABLES
    secretaria = r.id_exencion_secretaria in ids
    votacion = r.id_exencion_votacion in ids or (cert and (bool(descuentos) or secretaria))
    if votacion and descuentos:
        votacion = r.porcentaje_exencion(descuentos[0]) + r.porcentaje_exencion(r.id_exencion_votacion) <= 100
    return (
        ([r.id_exencion_votacion] if votacion else [])
        + descuentos
        + ([r.id_exencion_secretaria] if secretaria else [])
    )


@given(casos())
def test_exenciones_coinciden_con_la_tabla_de_decision(caso: tuple) -> None:
    fila, espec, r, cert = caso
    resultado = exenciones.seleccionar(fila, espec, r, cert)
    esperado = oraculo(fila, espec, r, cert)
    if isinstance(resultado, FallaFila):
        assert esperado is resultado.motivo
    else:
        assert list(resultado) == esperado


@given(casos())
def test_invariantes_de_las_exenciones(caso: tuple) -> None:
    fila, espec, r, cert = caso
    resultado = exenciones.seleccionar(fila, espec, r, cert)
    if isinstance(resultado, FallaFila):
        return
    especiales = {r.id_exencion_votacion, r.id_exencion_secretaria}
    descuentos = [i for i in resultado if i not in especiales]
    assert len(descuentos) <= 1
    assert resultado.count(r.id_exencion_votacion) <= 1
    assert REINGRESO not in resultado
    if r.id_exencion_votacion in resultado and descuentos:
        assert r.porcentaje_exencion(descuentos[0]) + r.porcentaje_exencion(r.id_exencion_votacion) <= 100
    orden = {r.id_exencion_votacion: 0, r.id_exencion_secretaria: 2}
    posiciones = [orden.get(i, 1) for i in resultado]
    assert posiciones == sorted(posiciones)
    votacion_marcada = fila.marcada(espec.columna_votacion)
    if r.id_exencion_votacion in resultado and not votacion_marcada:
        assert cert
        assert descuentos or r.id_exencion_secretaria in resultado


@given(casos())
def test_invariantes_de_los_conceptos(caso: tuple) -> None:
    fila, espec, r, _ = caso
    resultado = conceptos.seleccionar(fila, espec, r)
    assert resultado[0] == r.concepto_matricula
    assert len(set(resultado)) == len(resultado)
    if espec.tipo is TipoPlantilla.PREGRADO:
        assert resultado[1] == r.concepto_exclusivo_pregrado
    else:
        assert r.concepto_exclusivo_pregrado not in resultado
    marcados = [
        r.concepto_de_columna(espec.tipo, c) for c in espec.columnas_concepto if fila.marcada(c)
    ]
    assert [c for c in resultado if c in marcados] == [c for c in marcados if c is not None]
