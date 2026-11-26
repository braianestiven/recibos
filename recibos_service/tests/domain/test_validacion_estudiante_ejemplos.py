"""Pruebas de ejemplo de las validaciones del estudiante (US-06; BR-E02 a BR-E07)."""

from __future__ import annotations

import pytest

from app.domain import mensajes, validacion_estudiante
from app.domain.modelos import FallaFila, MotivoRechazo, TipoPlantilla
from tests import fabricas

REGLAS = fabricas.reglas_actuales()


def _validar(**kwargs: object) -> FallaFila | None:
    estudiante = kwargs.pop("estudiante", fabricas.estudiante())
    contexto = kwargs.pop("contexto", fabricas.contexto())
    tipo = kwargs.pop("tipo", TipoPlantilla.PREGRADO)
    return validacion_estudiante.validar(estudiante, contexto, tipo, REGLAS)  # type: ignore[arg-type]


def test_estudiante_que_pasa_todas_las_reglas() -> None:
    assert _validar() is None
    assert _validar(contexto=fabricas.contexto(nivel="maestría"), tipo=TipoPlantilla.POSGRADO_CREDITOS) is None


def test_sin_valor_de_matricula() -> None:
    assert _validar(estudiante=fabricas.estudiante(matricula=False)) == FallaFila(
        MotivoRechazo.SIN_VALOR_MATRICULA, mensajes.SIN_VALOR_MATRICULA
    )


def test_estado_no_permitido_dice_el_estado() -> None:
    falla = _validar(estudiante=fabricas.estudiante(estado=" e "))
    assert falla == FallaFila(MotivoRechazo.ESTADO_NO_PERMITIDO, mensajes.estado_no_permitido("E"))


@pytest.mark.parametrize(
    "contexto",
    [None, fabricas.contexto(activa=False), fabricas.contexto(codigo=999), fabricas.contexto(codigo=0)],
)
def test_carrera_inactiva_o_excluida(contexto: object) -> None:
    assert _validar(contexto=contexto) == FallaFila(MotivoRechazo.CARRERA_INACTIVA, mensajes.CARRERA_INACTIVA)


def test_terminacion_de_materias() -> None:
    contexto = fabricas.contexto(terminacion=True)
    assert _validar(contexto=contexto, estudiante=fabricas.estudiante(estado="A")) == FallaFila(
        MotivoRechazo.NO_TERMINACION_MATERIAS, mensajes.NO_TERMINACION_MATERIAS
    )
    assert _validar(contexto=contexto, estudiante=fabricas.estudiante(estado="T")) is None


def test_sin_periodo_vigente() -> None:
    assert _validar(contexto=fabricas.contexto(periodo=None)) == FallaFila(
        MotivoRechazo.SIN_PERIODO_VIGENTE, mensajes.SIN_PERIODO_VIGENTE
    )


@pytest.mark.parametrize(
    ("nivel", "tipo"),
    [("POSGRADO", TipoPlantilla.PREGRADO), ("PREGRADO", TipoPlantilla.POSGRADO_SMLV), ("", TipoPlantilla.PREGRADO)],
)
def test_nivel_que_no_corresponde_a_la_plantilla(nivel: str, tipo: TipoPlantilla) -> None:
    falla = _validar(contexto=fabricas.contexto(nivel=nivel), tipo=tipo)
    assert falla == FallaFila(MotivoRechazo.NIVEL_NO_CORRESPONDE, mensajes.nivel_no_corresponde(nivel, tipo))


def test_el_orden_de_hoy_va_primero() -> None:
    falla = _validar(estudiante=fabricas.estudiante(estado="X"), contexto=fabricas.contexto(periodo=None))
    assert falla is not None
    assert falla.motivo is MotivoRechazo.ESTADO_NO_PERMITIDO
