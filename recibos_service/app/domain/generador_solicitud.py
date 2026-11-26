"""Arma la solicitud de un estudiante válido o el motivo por el que su fila no se sube.

Orden de las reglas: datos de la plantilla (BR-D01 a BR-D05) y después los descuentos (BR-X02). Las del
estudiante (BR-E02 a BR-E07) ya se revisaron en `validacion_estudiante`.
"""

from __future__ import annotations

from datetime import date

from app.domain import conceptos, cuotas, exenciones
from app.domain.modelos import (
    ContextoCarrera,
    Cuota,
    Estudiante,
    FallaFila,
    FilaPlantilla,
    Solicitud,
    TipoPlantilla,
)
from app.domain.plantillas import EspecificacionPlantilla
from app.domain.reglas import ReglasLiquidacion
from app.domain.validacion_filas import leer_fecha_ordinaria, validar_posgrado

UNIDAD_PREGRADO = "0"


def generar(
    fila: FilaPlantilla,
    espec: EspecificacionPlantilla,
    codigo: int,
    estudiante: Estudiante,
    contexto: ContextoCarrera,
    reglas: ReglasLiquidacion,
    festivos: frozenset[date],
    hoy: date,
    tiene_certificado: bool,
) -> Solicitud | FallaFila:
    if contexto.periodo is None:
        raise ValueError("El periodo vigente ya debía estar validado (BR-E06)")

    unidad: str
    lista_cuotas: tuple[Cuota, ...]
    if espec.tipo is TipoPlantilla.PREGRADO:
        ordinaria = leer_fecha_ordinaria(fila, espec.columnas_fecha[0], None, hoy)  # BR-D03
        if isinstance(ordinaria, FallaFila):
            return ordinaria
        unidad = UNIDAD_PREGRADO  # BR-S02, RE-07
        lista_cuotas = cuotas.cuotas_pregrado(ordinaria, reglas, festivos)  # BR-Q01
    else:
        datos = validar_posgrado(fila, espec, hoy)  # BR-D01 a BR-D04
        if isinstance(datos, FallaFila):
            return datos
        resultado_cuotas = cuotas.cuotas_posgrado(datos, reglas, festivos)  # BR-Q02, BR-Q03, BR-D05
        if isinstance(resultado_cuotas, FallaFila):
            return resultado_cuotas
        unidad = datos.unidad
        lista_cuotas = resultado_cuotas

    lista_exenciones = exenciones.seleccionar(fila, espec, reglas, tiene_certificado)  # BR-X01 a BR-X06
    if isinstance(lista_exenciones, FallaFila):
        return lista_exenciones

    return Solicitud(
        codigo_estudiante=codigo,
        codigo_carrera=estudiante.codigo_carrera,  # BR-S01
        periodo=contexto.periodo,
        tipo=espec.tipo,
        unidad=unidad,
        cuotas=lista_cuotas,
        exenciones=lista_exenciones,
        conceptos=conceptos.seleccionar(fila, espec, reglas),  # BR-C01, BR-C02
    )
