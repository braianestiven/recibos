"""Lectura de celdas y reglas de la fila: código (BR-F01) y datos de la plantilla (BR-D01 a BR-D04)."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from enum import Enum

from app.domain import mensajes
from app.domain.modelos import DatosPosgrado, FallaFila, FilaPlantilla, MotivoRechazo, Rechazo, TipoPlantilla
from app.domain.plantillas import EspecificacionPlantilla

_ENTERO = re.compile(r"[0-9]+")
_CODIGO = re.compile(r"[0-9]{1,15}")
_CREDITOS = re.compile(r"[0-9]{1,3}")
_SMLV = re.compile(r"([0-9]{1,3})(?:[.,]([0-9]{1,2}))?")
_ANIO_MINIMO = 1000
_ANIO_MAXIMO = 9999


class _Fecha(Enum):
    VACIA = "vacia"
    INVALIDA = "invalida"


def leer_entero(texto: str | None) -> int | None:
    """Entero sin signo; el lector entrega `20271020001` para una celda numérica 20271020001,0 (BR-F01)."""
    if texto is None:
        return None
    limpio = texto.strip()
    if _ENTERO.fullmatch(limpio) is None:
        return None
    return int(limpio)


def validar_codigo(fila: FilaPlantilla) -> int | Rechazo:
    """Código de 1 a 15 dígitos en la columna 1 (BR-F01). Una fila con datos y sin código también falla (F3)."""
    texto = fila.texto(1)
    if texto is None:
        return mensajes.rechazo_simple(fila, MotivoRechazo.CODIGO_INVALIDO, mensajes.FALTA_CODIGO)
    limpio = texto.strip()
    if _CODIGO.fullmatch(limpio) is None:
        return mensajes.rechazo_simple(fila, MotivoRechazo.CODIGO_INVALIDO, mensajes.CODIGO_INVALIDO)
    return int(limpio)


def formatear_unidad(valor: Decimal) -> str:
    """Decimal con punto y sin ceros sobrantes: Decimal('4.50') → '4.5'; Decimal('7.00') → '7' (BR-D02)."""
    return format(valor.normalize(), "f")


def leer_unidad(texto: str | None, tipo: TipoPlantilla) -> str | None:
    """Créditos: entero de 1 a 999. SMLV: mayor que 0, hasta 3 enteros y 2 decimales (BR-D02, DF-03)."""
    if texto is None:
        return None
    limpio = texto.strip()
    if tipo is TipoPlantilla.POSGRADO_CREDITOS:
        if _CREDITOS.fullmatch(limpio) is None or int(limpio) == 0:
            return None
        return str(int(limpio))
    coincidencia = _SMLV.fullmatch(limpio)
    if coincidencia is None:
        return None
    enteros, decimales = coincidencia.group(1), coincidencia.group(2)
    valor = Decimal(f"{enteros}.{decimales}") if decimales else Decimal(enteros)
    if valor <= 0:
        return None
    return formatear_unidad(valor)


def _leer_fecha(fila: FilaPlantilla, terna: tuple[int, int, int]) -> date | _Fecha:
    textos = [fila.texto(columna) for columna in terna]
    if all(texto is None for texto in textos):
        return _Fecha.VACIA
    dia, mes, anio = (leer_entero(texto) for texto in textos)
    if dia is None or mes is None or anio is None or not _ANIO_MINIMO <= anio <= _ANIO_MAXIMO:
        return _Fecha.INVALIDA
    try:
        return date(anio, mes, dia)
    except ValueError:
        return _Fecha.INVALIDA


def leer_fecha_ordinaria(
    fila: FilaPlantilla, terna: tuple[int, int, int], cuota: int | None, hoy: date
) -> date | FallaFila:
    """Fecha ordinaria de una cuota (BR-D03): existe, con año de 4 cifras, y no es anterior a hoy.

    `cuota` es None en pregrado, donde el mensaje no lleva "Cuota n:".
    """
    fecha = _leer_fecha(fila, terna)
    if fecha is _Fecha.VACIA:
        return FallaFila(MotivoRechazo.FECHA_INVALIDA, mensajes.fecha_faltante(cuota))
    if fecha is _Fecha.INVALIDA:
        return FallaFila(MotivoRechazo.FECHA_INVALIDA, mensajes.fecha_inexistente(cuota))
    assert isinstance(fecha, date)  # noqa: S101 - acota el tipo para mypy
    if fecha < hoy:
        return FallaFila(MotivoRechazo.FECHA_INVALIDA, mensajes.fecha_anterior_a_hoy(cuota))
    return fecha


def fechas_ordinarias_legibles(fila: FilaPlantilla, espec: EspecificacionPlantilla) -> list[date]:
    """Fechas que se pueden leer, para calcular el rango de festivos del lote (BR-L13).

    En posgrado se miran las cuotas que indica la columna 3 si es válida; si no, todas las ternas.
    """
    ternas = espec.columnas_fecha
    if espec.columna_cuotas is not None:
        cuotas = leer_entero(fila.texto(espec.columna_cuotas))
        if cuotas is not None and 1 <= cuotas <= espec.max_cuotas:
            ternas = ternas[:cuotas]
    return [fecha for terna in ternas if isinstance(fecha := _leer_fecha(fila, terna), date)]


def porcentaje_valido(texto: str | None) -> tuple[bool, int | None]:
    """Vacío o entero de 0 a 100 (BR-D04). Una fracción de Excel (0,6) no vale. Devuelve (válido, valor)."""
    if texto is None:
        return True, None
    valor = leer_entero(texto)
    if valor is None or valor > 100:
        return False, None
    return True, valor


def validar_posgrado(fila: FilaPlantilla, espec: EspecificacionPlantilla, hoy: date) -> DatosPosgrado | FallaFila:
    """Datos de posgrado en el orden BR-D01, BR-D02, BR-D03 y BR-D04. La suma (BR-D05) va en `cuotas`."""
    if espec.columna_cuotas is None or espec.columna_unidad is None:
        raise ValueError("La especificación no es de una plantilla de posgrado")

    numero_cuotas = leer_entero(fila.texto(espec.columna_cuotas))
    if numero_cuotas is None or not 1 <= numero_cuotas <= espec.max_cuotas:
        return FallaFila(MotivoRechazo.CUOTAS_INVALIDAS, mensajes.CUOTAS_INVALIDAS)

    unidad = leer_unidad(fila.texto(espec.columna_unidad), espec.tipo)
    if unidad is None:
        mensaje = (
            mensajes.UNIDAD_INVALIDA_CREDITOS
            if espec.tipo is TipoPlantilla.POSGRADO_CREDITOS
            else mensajes.UNIDAD_INVALIDA_SMLV
        )
        return FallaFila(MotivoRechazo.UNIDAD_INVALIDA, mensaje)

    fechas: list[date] = []
    for numero, terna in enumerate(espec.columnas_fecha[:numero_cuotas], start=1):
        fecha = leer_fecha_ordinaria(fila, terna, numero, hoy)
        if isinstance(fecha, FallaFila):
            return fecha
        if fechas and fecha <= fechas[-1]:
            return FallaFila(MotivoRechazo.FECHA_INVALIDA, mensajes.fecha_fuera_de_orden(numero))
        fechas.append(fecha)

    porcentajes: list[int | None] = []
    for numero, columna in enumerate(espec.columnas_porcentaje[:numero_cuotas], start=1):
        valido, valor = porcentaje_valido(fila.texto(columna))
        if not valido:
            return FallaFila(MotivoRechazo.PORCENTAJE_INVALIDO, mensajes.porcentaje_invalido(numero))
        porcentajes.append(valor)

    return DatosPosgrado(
        numero_cuotas=numero_cuotas,
        unidad=unidad,
        fechas_ordinarias=tuple(fechas),
        porcentajes=tuple(porcentajes),
    )
