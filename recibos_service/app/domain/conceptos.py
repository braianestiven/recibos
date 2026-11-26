"""Conceptos de la solicitud (BR-C01, BR-C02)."""

from __future__ import annotations

from app.domain.modelos import FilaPlantilla, TipoPlantilla
from app.domain.plantillas import EspecificacionPlantilla
from app.domain.reglas import ReglasLiquidacion


def seleccionar(fila: FilaPlantilla, espec: EspecificacionPlantilla, reglas: ReglasLiquidacion) -> tuple[int, ...]:
    """Matrícula, exclusivo de pregrado (solo en pregrado) y los marcados en el orden de las columnas."""
    conceptos = [reglas.concepto_matricula]
    if espec.tipo is TipoPlantilla.PREGRADO:
        conceptos.append(reglas.concepto_exclusivo_pregrado)
    for columna in espec.columnas_concepto:
        if fila.marcada(columna):
            concepto = reglas.concepto_de_columna(espec.tipo, columna)
            if concepto is not None and concepto not in conceptos:
                conceptos.append(concepto)
    return tuple(conceptos)
