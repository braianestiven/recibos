"""Estructura de las plantillas oficiales, identificación, formato y extracción de filas (BR-L08 a BR-L11).

Provisional hasta tener los archivos oficiales (README, "Insumos pendientes"):
- D1, pregrado: las 13 columnas de la plantilla anterior sin "Reingreso" y la fecha ordinaria en las
  columnas 14, 15 y 16.
- D2, posgrado SMLV: la misma estructura de créditos, con "SMLV" en la columna 2 (supuesto A6).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass

from app.domain import mensajes
from app.domain.errores import FormatoInvalido
from app.domain.modelos import FilaPlantilla, HojaPlantilla, TipoPlantilla


def normalizar(texto: str) -> str:
    """Mayúsculas, sin tildes y con un solo espacio entre palabras, para comparar encabezados."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_tildes.upper().split())


@dataclass(frozen=True)
class EspecificacionPlantilla:
    tipo: TipoPlantilla
    texto_a1: str
    fila_encabezados: int  # primera fila de los encabezados; llegan hasta la fila anterior a los datos
    fila_inicial: int
    num_columnas: int
    encabezados: Mapping[int, str]  # columna → palabra que debe aparecer en su encabezado (normalizada)
    columnas_concepto: tuple[int, ...]
    columnas_exencion: tuple[int, ...]
    columna_votacion: int
    columna_unidad: int | None
    columna_cuotas: int | None
    columnas_fecha: tuple[tuple[int, int, int], ...]  # ternas (día, mes, año) de la fecha ordinaria
    columnas_porcentaje: tuple[int, ...]

    @property
    def max_cuotas(self) -> int:
        return len(self.columnas_fecha)


_ENCABEZADOS_PREGRADO_BASE: dict[int, str] = {
    1: "CODIGO",
    2: "SEGURO",
    3: "CARNET",
    4: "SISTEMATIZACION",
    5: "VOTACION",
    6: "HERMANO",
    7: "HERMANO",
    8: "TERMINACION",
    9: "BENEFICIARIO",
    10: "HONOR",
    11: "DEPORTISTA",
    12: "DISTINGUIDO",
    13: "MERITO",
}

_ENCABEZADOS_POSGRADO: dict[int, str] = {
    1: "CODIGO",
    3: "CUOTA",
    4: "SEGURO",
    5: "CARNET",
    6: "SISTEMATIZACION",
    7: "VOTACION",
    8: "MONITOR",
    9: "EGRESADO",
    10: "DOCENTE",
    11: "BENEFICIARIO",
    12: "BECA",
    13: "ECAES",
    14: "HONOR",
    15: "HERMANO",
    16: "SECRETARIA",
    17: "DOCTORADO",
    **{columna: palabra for inicio in (18, 21, 24) for columna, palabra in zip(
        (inicio, inicio + 1, inicio + 2), ("DIA", "MES", "ANO"), strict=True)},
    # "Porcentaje de Cada Cuota" es una celda combinada que solo queda en la columna 27 del archivo oficial
    27: "CUOTA 1",
    28: "CUOTA 2",
    29: "CUOTA 3",
}

PREGRADO = EspecificacionPlantilla(
    tipo=TipoPlantilla.PREGRADO,
    texto_a1="PLANTILLA GENERAL PREGRADOS",
    fila_encabezados=2,
    fila_inicial=4,
    num_columnas=16,  # provisional hasta D1
    encabezados={**_ENCABEZADOS_PREGRADO_BASE, 14: "DIA", 15: "MES", 16: "ANO"},
    columnas_concepto=(2, 3, 4),
    columnas_exencion=tuple(range(5, 14)),
    columna_votacion=5,
    columna_unidad=None,
    columna_cuotas=None,
    columnas_fecha=((14, 15, 16),),  # provisional hasta D1
    columnas_porcentaje=(),
)

POSGRADO_CREDITOS = EspecificacionPlantilla(
    tipo=TipoPlantilla.POSGRADO_CREDITOS,
    texto_a1="PLANTILLA GENERAL POSTGRADOS CREDITOS",
    fila_encabezados=2,
    fila_inicial=5,
    num_columnas=29,
    encabezados={**_ENCABEZADOS_POSGRADO, 2: "CREDITOS"},
    columnas_concepto=(4, 5, 6),
    columnas_exencion=tuple(range(7, 18)),
    columna_votacion=7,
    columna_unidad=2,
    columna_cuotas=3,
    columnas_fecha=((18, 19, 20), (21, 22, 23), (24, 25, 26)),
    columnas_porcentaje=(27, 28, 29),
)

POSGRADO_SMLV = EspecificacionPlantilla(
    tipo=TipoPlantilla.POSGRADO_SMLV,
    texto_a1="PLANTILLA GENERAL POSTGRADOS SALARIOS MINIMOS LEGALES",
    fila_encabezados=2,
    fila_inicial=5,
    num_columnas=29,
    encabezados={**_ENCABEZADOS_POSGRADO, 2: "SMLV"},  # provisional hasta D2
    columnas_concepto=(4, 5, 6),
    columnas_exencion=tuple(range(7, 18)),
    columna_votacion=7,
    columna_unidad=2,
    columna_cuotas=3,
    columnas_fecha=((18, 19, 20), (21, 22, 23), (24, 25, 26)),
    columnas_porcentaje=(27, 28, 29),
)

ESPECIFICACIONES: tuple[EspecificacionPlantilla, ...] = (PREGRADO, POSGRADO_CREDITOS, POSGRADO_SMLV)

_COLUMNAS_PREGRADO_ANTERIOR = 14
_COLUMNA_REINGRESO = 14


def identificar(hoja: HojaPlantilla) -> EspecificacionPlantilla:
    """Tipo de plantilla por el texto de A1 (BR-L09)."""
    texto = hoja.valor(1, 1)
    if texto is not None:
        normalizado = normalizar(texto)
        for espec in ESPECIFICACIONES:
            if normalizado == normalizar(espec.texto_a1):
                return espec
    raise FormatoInvalido(mensajes.PLANTILLA_NO_RECONOCIDA)


def encabezado(hoja: HojaPlantilla, espec: EspecificacionPlantilla, columna: int) -> str:
    """Texto normalizado de los encabezados de una columna, de arriba hacia abajo."""
    partes = (hoja.valor(fila, columna) for fila in range(espec.fila_encabezados, espec.fila_inicial))
    return " ".join(normalizar(parte) for parte in partes if parte is not None)


def validar_formato(hoja: HojaPlantilla, espec: EspecificacionPlantilla) -> None:
    """Número de columnas y encabezados (BR-L10); la plantilla de pregrado con "Reingreso" tiene su mensaje."""
    columnas = hoja.ultima_columna(hasta_fila=espec.fila_inicial)
    if (
        espec.tipo is TipoPlantilla.PREGRADO
        and columnas == _COLUMNAS_PREGRADO_ANTERIOR
        and "REINGRESO" in encabezado(hoja, espec, _COLUMNA_REINGRESO)
    ):
        raise FormatoInvalido(mensajes.PLANTILLA_CON_REINGRESO)
    if columnas != espec.num_columnas:
        detalle = f"trae {columnas} columnas y deben ser {espec.num_columnas}"
        raise FormatoInvalido(mensajes.columnas_distintas(espec.tipo, detalle))
    for columna, palabra in sorted(espec.encabezados.items()):
        if palabra not in encabezado(hoja, espec, columna):
            detalle = f"el encabezado de la columna {columna} no es el oficial"
            raise FormatoInvalido(mensajes.columnas_distintas(espec.tipo, detalle))


def extraer_filas(hoja: HojaPlantilla, espec: EspecificacionPlantilla) -> list[FilaPlantilla]:
    """Filas con datos desde la fila inicial, en orden; omite las vacías (BR-L11, F4).

    Solo se miran las columnas de la especificación. Una fila con datos y sin código se devuelve, para
    que la validación del código la rechace (F3).
    """
    filas: list[FilaPlantilla] = []
    for numero in range(espec.fila_inicial, hoja.ultima_fila() + 1):
        celdas = {
            columna: texto
            for columna in range(1, espec.num_columnas + 1)
            if (texto := hoja.valor(numero, columna)) is not None
        }
        if celdas:
            filas.append(FilaPlantilla(numero=numero, celdas=celdas))
    return filas
