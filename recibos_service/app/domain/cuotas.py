"""Cuotas de la solicitud (BR-Q01 a BR-Q04 y BR-D05)."""

from __future__ import annotations

from datetime import date

from app.domain import mensajes
from app.domain.fechas import fecha_extraordinaria
from app.domain.modelos import Cuota, DatosPosgrado, FallaFila, FechasPago, MotivoRechazo
from app.domain.reglas import ReglasLiquidacion


def _fechas(ordinaria: date, reglas: ReglasLiquidacion, festivos: frozenset[date]) -> FechasPago:
    return FechasPago(
        ordinaria=ordinaria,
        extraordinaria=fecha_extraordinaria(ordinaria, reglas.dias_fecha_extraordinaria, festivos),
    )


def cuotas_pregrado(ordinaria: date, reglas: ReglasLiquidacion, festivos: frozenset[date]) -> tuple[Cuota]:
    """Una sola cuota, número 1, al 100%, con la fecha ordinaria de la plantilla (BR-Q01, F8)."""
    return (Cuota(numero=1, porcentaje=100, fechas=_fechas(ordinaria, reglas, festivos)),)


def cuotas_posgrado(
    datos: DatosPosgrado, reglas: ReglasLiquidacion, festivos: frozenset[date]
) -> tuple[Cuota, ...] | FallaFila:
    """N cuotas numeradas de 1 a N; un porcentaje vacío toma el de su posición (BR-Q02, BR-Q03).

    Después de completar los vacíos, los porcentajes deben sumar 100 (BR-D05).
    """
    porcentajes = [
        valor if valor is not None else reglas.porcentaje_por_defecto(datos.numero_cuotas, posicion)
        for posicion, valor in enumerate(datos.porcentajes, start=1)
    ]
    suma = sum(porcentajes)
    if suma != 100:
        return FallaFila(MotivoRechazo.PORCENTAJES_NO_SUMAN_100, mensajes.porcentajes_no_suman_100(suma))
    return tuple(
        Cuota(numero=numero, porcentaje=porcentaje, fechas=_fechas(ordinaria, reglas, festivos))
        for numero, (porcentaje, ordinaria) in enumerate(
            zip(porcentajes, datos.fechas_ordinarias, strict=True), start=1
        )
    )
