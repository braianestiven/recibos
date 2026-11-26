"""Propiedad de oráculo de las validaciones del estudiante (business-logic-model.md §9; PBT-05, orientativa)."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from app.domain import validacion_estudiante
from app.domain.modelos import ContextoCarrera, Estudiante, MotivoRechazo, TipoPlantilla
from app.domain.reglas import ReglasLiquidacion
from tests.estrategias import contextos, estudiantes, reglas


def modelo_simple(
    estudiante: Estudiante, contexto: ContextoCarrera | None, tipo: TipoPlantilla, r: ReglasLiquidacion
) -> MotivoRechazo | None:
    """Evalúa BR-E02 a BR-E07 una por una, sin atajos, como dice business-rules.md §4."""
    condiciones = [
        (estudiante.tiene_valor_matricula, MotivoRechazo.SIN_VALOR_MATRICULA),
        (estudiante.estado in r.estados_permitidos, MotivoRechazo.ESTADO_NO_PERMITIDO),
        (
            contexto is not None and contexto.activa and contexto.codigo not in r.proyectos_excluidos,
            MotivoRechazo.CARRERA_INACTIVA,
        ),
        (
            contexto is not None and (not contexto.terminacion_activa or estudiante.estado in r.estados_terminacion),
            MotivoRechazo.NO_TERMINACION_MATERIAS,
        ),
        (contexto is not None and contexto.periodo is not None, MotivoRechazo.SIN_PERIODO_VIGENTE),
        (
            contexto is not None
            and (
                contexto.nivel in r.niveles_posgrado if tipo.es_posgrado else contexto.nivel == r.nivel_pregrado
            ),
            MotivoRechazo.NIVEL_NO_CORRESPONDE,
        ),
    ]
    for cumple, motivo in condiciones:
        if not cumple:
            return motivo
    return None


@given(estudiantes(), contextos(), st.sampled_from(list(TipoPlantilla)), reglas())
def test_el_motivo_es_el_de_la_primera_condicion_que_falla(
    estudiante: Estudiante, contexto: ContextoCarrera | None, tipo: TipoPlantilla, r: ReglasLiquidacion
) -> None:
    falla = validacion_estudiante.validar(estudiante, contexto, tipo, r)
    assert (falla.motivo if falla else None) == modelo_simple(estudiante, contexto, tipo, r)
