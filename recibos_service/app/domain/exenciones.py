"""Exenciones de la solicitud (BR-X01 a BR-X07; tabla de decisión en business-logic-model.md §4.6)."""

from __future__ import annotations

from decimal import Decimal

from app.domain import mensajes
from app.domain.modelos import FallaFila, FilaPlantilla, MotivoRechazo
from app.domain.plantillas import EspecificacionPlantilla
from app.domain.reglas import ReglasLiquidacion

TOPE_EXENCIONES = Decimal(100)
"""Límite de "Solicitados": el descuento más la votación no pasan de 100% (C7). No es una regla del periodo."""


def seleccionar(
    fila: FilaPlantilla,
    espec: EspecificacionPlantilla,
    reglas: ReglasLiquidacion,
    tiene_certificado: bool,
) -> tuple[int, ...] | FallaFila:
    """Exenciones en el orden votación, descuento y Secretaría de Educación (BR-X06)."""
    ids: list[int] = []
    for columna in espec.columnas_exencion:
        if fila.marcada(columna):
            id_exencion = reglas.exencion_de_columna(espec.tipo, columna)
            if id_exencion is not None and id_exencion not in ids:
                ids.append(id_exencion)

    votacion_marcada = reglas.id_exencion_votacion in ids
    secretaria = reglas.id_exencion_secretaria in ids
    descuentos = [i for i in ids if i not in {reglas.id_exencion_votacion, reglas.id_exencion_secretaria}]
    if len(descuentos) > 1:  # BR-X02
        mensaje = mensajes.DESCUENTOS_POSGRADO if espec.tipo.es_posgrado else mensajes.DESCUENTOS_PREGRADO
        return FallaFila(MotivoRechazo.DESCUENTOS_NO_ACUMULABLES, mensaje)
    descuento = descuentos[0] if descuentos else None

    # BR-X03 y BR-X04: marcada, o automática con certificado y un descuento o la Secretaría
    votacion = votacion_marcada or (tiene_certificado and (descuento is not None or secretaria))
    if votacion and descuento is not None:  # BR-X05: la Secretaría no entra en la suma (F14)
        suma = reglas.porcentaje_exencion(descuento) + reglas.porcentaje_exencion(reglas.id_exencion_votacion)
        if suma > TOPE_EXENCIONES:
            votacion = False

    resultado: list[int] = []
    if votacion:
        resultado.append(reglas.id_exencion_votacion)
    if descuento is not None:
        resultado.append(descuento)
    if secretaria:
        resultado.append(reglas.id_exencion_secretaria)
    return tuple(resultado)
