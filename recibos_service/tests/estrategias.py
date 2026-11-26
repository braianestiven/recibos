"""Generadores de Hypothesis para los tipos del dominio, en un solo lugar (PBT-07).

Respetan las restricciones del negocio: códigos de 1 a 15 dígitos, fechas con fin de mes, 29 de
febrero y cambio de año, porcentajes de 0 a 100, reglas coherentes y festivos con días seguidos.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from hypothesis import strategies as st

from app.domain.modelos import ContextoCarrera, Estudiante, FilaPlantilla, Periodo
from app.domain.plantillas import EspecificacionPlantilla
from app.domain.reglas import ReglasLiquidacion
from tests import fabricas

DIGITOS = "0123456789"
ESPACIOS = st.sampled_from(["", " ", "  ", "\t"])
MARCAS = st.sampled_from(["x", "X", "1", "si", "✓"])
FECHA_MINIMA = date(2026, 1, 1)
FECHA_MAXIMA = date(2031, 12, 31)


@st.composite
def codigos_validos(draw: st.DrawFn) -> str:
    """Texto de 1 a 15 dígitos, con o sin espacios alrededor."""
    digitos = draw(st.text(alphabet=DIGITOS, min_size=1, max_size=15))
    return draw(ESPACIOS) + digitos + draw(ESPACIOS)


@st.composite
def codigos_invalidos(draw: st.DrawFn) -> str:
    """Texto con algo que no es un dígito, o con más de 15 dígitos."""
    opcion = draw(st.integers(0, 1))
    if opcion == 0:
        return draw(st.text(alphabet=DIGITOS, min_size=16, max_size=25))
    base = draw(st.text(alphabet=DIGITOS, max_size=10))
    otro = draw(st.characters(exclude_categories=("Nd", "Cs"), exclude_characters=" \t\n\r\x0b\x0c"))
    posicion = draw(st.integers(0, len(base)))
    return base[:posicion] + otro + base[posicion:]


def fechas(desde: date = FECHA_MINIMA, hasta: date = FECHA_MAXIMA) -> st.SearchStrategy[date]:
    """Fechas con preferencia por los bordes: fin de mes, 29 de febrero y fin de año."""
    bordes = st.sampled_from(
        [date(2028, 2, 29), date(2027, 12, 31), date(2027, 1, 31), date(2027, 4, 30), date(2028, 3, 1)]
    ).filter(lambda d: desde <= d <= hasta)
    return st.one_of(st.dates(min_value=desde, max_value=hasta), bordes)


@st.composite
def festivos(draw: st.DrawFn, desde: date = FECHA_MINIMA, hasta: date = FECHA_MAXIMA) -> frozenset[date]:
    """Conjuntos de festivos, a veces con varios días seguidos."""
    sueltos = draw(st.lists(st.dates(min_value=desde, max_value=hasta), max_size=20))
    tramos = draw(st.lists(st.tuples(st.dates(min_value=desde, max_value=hasta), st.integers(1, 6)), max_size=3))
    dias = set(sueltos)
    for inicio, largo in tramos:
        dias.update(inicio + timedelta(days=i) for i in range(largo))
    return frozenset(d for d in dias if d <= hasta)


@st.composite
def reglas(draw: st.DrawFn) -> ReglasLiquidacion:
    """Reglas coherentes: los mapas de siempre, con porcentajes y valores por defecto al azar."""
    porcentajes = {
        id_exencion: Decimal(draw(st.integers(0, 100))) for id_exencion in fabricas.PORCENTAJES_EXENCION
    }
    dos = draw(st.integers(0, 100))
    tres_a = draw(st.integers(0, 100))
    tres_b = draw(st.integers(0, 100 - tres_a))
    base = fabricas.reglas_actuales(
        porcentajes_por_defecto={1: (100,), 2: (dos, 100 - dos), 3: (tres_a, tres_b, 100 - tres_a - tres_b)},
        dias_fecha_extraordinaria=draw(st.integers(0, 15)),
    )
    return base.con_porcentajes(porcentajes)


@st.composite
def estudiantes(draw: st.DrawFn) -> Estudiante:
    return Estudiante(
        codigo=draw(st.integers(1, 10**15 - 1)),
        estado=draw(st.sampled_from(list("VJTAQBHEIXN"))),
        codigo_carrera=draw(st.sampled_from([0, 5, 20, 77, 999])),
        tiene_valor_matricula=draw(st.booleans()),
    )


@st.composite
def contextos(draw: st.DrawFn) -> ContextoCarrera | None:
    if draw(st.integers(0, 9)) == 0:
        return None
    periodo = draw(st.one_of(st.none(), st.builds(Periodo, st.integers(2020, 2035), st.integers(1, 3))))
    return ContextoCarrera(
        codigo=draw(st.sampled_from([0, 5, 20, 77, 999])),
        activa=draw(st.booleans()),
        nivel=draw(st.sampled_from(["PREGRADO", "POSGRADO", "MAESTRIA", "DOCTORADO", "", "TECNOLOGIA"])),
        periodo=periodo,
        terminacion_activa=draw(st.booleans()),
    )


@st.composite
def marcas_de(draw: st.DrawFn, columnas: tuple[int, ...]) -> dict[int, str]:
    elegidas = draw(st.lists(st.sampled_from(columnas), unique=True, max_size=len(columnas))) if columnas else []
    return {columna: draw(MARCAS) for columna in elegidas}


@st.composite
def filas_de_datos(draw: st.DrawFn, espec: EspecificacionPlantilla, numero: int = 5) -> FilaPlantilla:
    """Fila de una plantilla con código, marcas, cuotas, fechas y porcentajes, válidos o no."""
    celdas: dict[int, str] = {1: draw(st.one_of(codigos_validos(), codigos_invalidos())).strip() or "x"}
    celdas.update(draw(marcas_de(espec.columnas_concepto)))
    celdas.update(draw(marcas_de(espec.columnas_exencion)))
    if espec.columna_unidad is not None:
        celdas[espec.columna_unidad] = draw(st.sampled_from(["3", "12", "0", "4,5", "x", "1000"]))
    if espec.columna_cuotas is not None:
        celdas[espec.columna_cuotas] = draw(st.sampled_from(["1", "2", "3", "0", "4", "dos"]))
    for terna in espec.columnas_fecha:
        if draw(st.booleans()):
            fecha = draw(fechas())
            for columna, valor in zip(terna, (fecha.day, fecha.month, fecha.year), strict=True):
                celdas[columna] = str(valor)
    for columna in espec.columnas_porcentaje:
        if draw(st.booleans()):
            celdas[columna] = draw(st.sampled_from(["0", "30", "40", "60", "100", "101", "0,6"]))
    return FilaPlantilla(numero=numero, celdas=celdas)
