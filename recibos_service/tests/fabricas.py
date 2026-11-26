"""Objetos de prueba con los valores actuales del negocio (business-rules.md §11)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal

from app.domain.modelos import ContextoCarrera, Estudiante, FilaPlantilla, HojaPlantilla, Periodo, crear_hoja
from app.domain.plantillas import EspecificacionPlantilla
from app.domain.reglas import ReglasLiquidacion

HOY = date(2027, 1, 4)

EXENCIONES_PREGRADO = {5: 1, 6: 2, 7: 3, 8: 4, 9: 5, 10: 6, 11: 7, 12: 8, 13: 9}
EXENCIONES_POSGRADO = {7: 1, 8: 10, 9: 11, 10: 12, 11: 5, 12: 13, 13: 14, 14: 15, 15: 2, 16: 16, 17: 17}
PORCENTAJES_EXENCION = {
    1: Decimal(10),
    2: Decimal(50),
    3: Decimal(50),
    4: Decimal(20),
    5: Decimal(100),
    6: Decimal(100),
    7: Decimal(90),
    8: Decimal(30),
    9: Decimal(60),
    10: Decimal(50),
    11: Decimal(30),
    12: Decimal(50),
    13: Decimal(100),
    14: Decimal(100),
    15: Decimal(100),
    16: Decimal(70),
    17: Decimal(90),
}


def reglas_actuales(**cambios: object) -> ReglasLiquidacion:
    valores: dict[str, object] = {
        "estados_permitidos": frozenset("VJTAQB"),
        "estados_terminacion": frozenset("TH"),
        "evento_periodo": 80,
        "evento_terminacion": 82,
        "proyectos_excluidos": frozenset({0, 999}),
        "nivel_pregrado": "PREGRADO",
        "niveles_posgrado": frozenset({"POSGRADO", "ESPECIALIZACION", "MAESTRIA", "DOCTORADO"}),
        "concepto_matricula": 1,
        "concepto_exclusivo_pregrado": 19,
        "conceptos_columna_pregrado": {2: 2, 3: 3, 4: 4},
        "conceptos_columna_posgrado": {4: 2, 5: 3, 6: 4},
        "exenciones_columna_pregrado": EXENCIONES_PREGRADO,
        "exenciones_columna_posgrado": EXENCIONES_POSGRADO,
        "id_exencion_votacion": 1,
        "id_exencion_secretaria": 16,
        "porcentajes_por_defecto": {1: (100,), 2: (60, 40), 3: (40, 30, 30)},
        "dias_fecha_extraordinaria": 8,
    }
    valores.update(cambios)
    reglas = ReglasLiquidacion(**valores)  # type: ignore[arg-type]
    return reglas.con_porcentajes(PORCENTAJES_EXENCION)


def fila(numero: int = 5, **celdas: str) -> FilaPlantilla:
    """Fila con celdas `c<columna>="texto"`; por ejemplo, fila(c1="2027", c7="x")."""
    return FilaPlantilla(numero=numero, celdas={int(nombre[1:]): texto for nombre, texto in celdas.items()})


def celdas_fecha(terna: tuple[int, int, int], fecha: date) -> dict[str, str]:
    dia, mes, anio = terna
    return {f"c{dia}": str(fecha.day), f"c{mes}": str(fecha.month), f"c{anio}": str(fecha.year)}


def estudiante(codigo: int = 20271020001, estado: str = "A", carrera: int = 20, matricula: bool = True) -> Estudiante:
    return Estudiante(codigo=codigo, estado=estado, codigo_carrera=carrera, tiene_valor_matricula=matricula)


PERIODO_VIGENTE = Periodo(2027, 1)


def contexto(
    codigo: int = 20,
    activa: bool = True,
    nivel: str = "PREGRADO",
    periodo: Periodo | None = PERIODO_VIGENTE,
    terminacion: bool = False,
) -> ContextoCarrera:
    return ContextoCarrera(codigo=codigo, activa=activa, nivel=nivel, periodo=periodo, terminacion_activa=terminacion)


def hoja_para(
    espec: EspecificacionPlantilla,
    filas: Mapping[int, Mapping[int, str]] | None = None,
    encabezados: Mapping[int, str] | None = None,
    texto_a1: str | None = None,
    columnas: int | None = None,
) -> HojaPlantilla:
    """Hoja con el texto de A1 y los encabezados de la especificación, más las filas de datos dadas."""
    celdas: dict[tuple[int, int], str] = {(1, 1): texto_a1 if texto_a1 is not None else espec.texto_a1}
    fila_encabezado = espec.fila_inicial - 1
    total = columnas if columnas is not None else espec.num_columnas
    textos = dict(espec.encabezados)
    textos.update(encabezados or {})
    for columna in range(1, total + 1):
        celdas[(fila_encabezado, columna)] = textos.get(columna, f"Columna {columna}")
    for numero, valores in (filas or {}).items():
        for columna, texto in valores.items():
            celdas[(numero, columna)] = texto
    return crear_hoja(celdas)
