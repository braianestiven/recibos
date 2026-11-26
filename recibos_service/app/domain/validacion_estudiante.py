"""Validaciones académicas del estudiante, en el orden de hoy y después las nuevas (BR-E02 a BR-E07).

La existencia (BR-E01) la revisa el caso de uso antes, porque decide si se cancelan solicitudes.
"""

from __future__ import annotations

from app.domain import mensajes
from app.domain.modelos import ContextoCarrera, Estudiante, FallaFila, MotivoRechazo, TipoPlantilla
from app.domain.plantillas import normalizar
from app.domain.reglas import ReglasLiquidacion


def carrera_activa(contexto: ContextoCarrera | None, reglas: ReglasLiquidacion) -> bool:
    """Proyecto con `cra_estado = 'A'` y fuera de `proyectos_excluidos` (BR-E04)."""
    return contexto is not None and contexto.activa and contexto.codigo not in reglas.proyectos_excluidos


def nivel_corresponde(nivel: str, tipo: TipoPlantilla, reglas: ReglasLiquidacion) -> bool:
    """El nivel del proyecto corresponde a la plantilla (BR-E07). Un nivel vacío no corresponde a ninguna."""
    normalizado = normalizar(nivel)
    if not normalizado:
        return False
    if tipo.es_posgrado:
        return normalizado in {normalizar(n) for n in reglas.niveles_posgrado}
    return normalizado == normalizar(reglas.nivel_pregrado)


def validar(
    estudiante: Estudiante,
    contexto: ContextoCarrera | None,
    tipo: TipoPlantilla,
    reglas: ReglasLiquidacion,
) -> FallaFila | None:
    """Primera regla del estudiante que falla, o None si pasan todas."""
    if not estudiante.tiene_valor_matricula:
        return FallaFila(MotivoRechazo.SIN_VALOR_MATRICULA, mensajes.SIN_VALOR_MATRICULA)  # BR-E02
    estado = estudiante.estado.strip().upper()
    if estado not in reglas.estados_permitidos:
        return FallaFila(MotivoRechazo.ESTADO_NO_PERMITIDO, mensajes.estado_no_permitido(estado))  # BR-E03
    if contexto is None or not carrera_activa(contexto, reglas):
        return FallaFila(MotivoRechazo.CARRERA_INACTIVA, mensajes.CARRERA_INACTIVA)  # BR-E04
    if contexto.terminacion_activa and estado not in reglas.estados_terminacion:
        return FallaFila(MotivoRechazo.NO_TERMINACION_MATERIAS, mensajes.NO_TERMINACION_MATERIAS)  # BR-E05
    if contexto.periodo is None:
        return FallaFila(MotivoRechazo.SIN_PERIODO_VIGENTE, mensajes.SIN_PERIODO_VIGENTE)  # BR-E06
    if not nivel_corresponde(contexto.nivel, tipo, reglas):
        return FallaFila(  # BR-E07
            MotivoRechazo.NIVEL_NO_CORRESPONDE, mensajes.nivel_no_corresponde(contexto.nivel, tipo)
        )
    return None
