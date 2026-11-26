"""Lector de plantillas `.xls` con xlrd 2.x, en memoria (BR-L08, SECURITY-13).

xlrd 2 solo lee libros de Excel 97-2003 y no ejecuta macros ni fórmulas. Se lee solo la primera hoja.
Una celda numérica con valor entero se entrega como ese entero en texto (20271020001,0 → "20271020001").
"""

from __future__ import annotations

import xlrd

from app.application.errores import ArchivoNoLegible
from app.domain.modelos import HojaPlantilla, crear_hoja

_TIPOS_NUMERICOS = {xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_DATE}


def texto_de_celda(tipo: int, valor: object) -> str:
    if tipo in _TIPOS_NUMERICOS and isinstance(valor, float):
        return str(int(valor)) if valor.is_integer() else repr(valor)
    if tipo == xlrd.XL_CELL_BOOLEAN:
        return "1" if valor else "0"
    if tipo == xlrd.XL_CELL_ERROR:
        return "#ERROR"
    return str(valor)


class LectorXlrd:
    def leer(self, contenido: bytes) -> HojaPlantilla:
        try:
            libro = xlrd.open_workbook(file_contents=contenido, on_demand=True)
            try:
                hoja = libro.sheet_by_index(0)
                celdas: dict[tuple[int, int], str] = {}
                for fila in range(hoja.nrows):
                    for columna in range(hoja.ncols):
                        celda = hoja.cell(fila, columna)
                        if celda.ctype not in {xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK}:
                            celdas[(fila + 1, columna + 1)] = texto_de_celda(celda.ctype, celda.value)
            finally:
                libro.release_resources()
        except Exception as error:  # un archivo dañado puede fallar de muchas formas dentro de xlrd
            raise ArchivoNoLegible("No se pudo leer la plantilla") from error
        return crear_hoja(celdas)
