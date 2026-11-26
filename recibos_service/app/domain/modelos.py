"""Entidades y objetos de valor del dominio (domain-entities.md §2)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum, IntEnum


class TipoPlantilla(IntEnum):
    """Tipo de plantilla. El valor es el que se guarda en `solicitudRecibo.tipoPlantilla`."""

    PREGRADO = 1
    POSGRADO_CREDITOS = 2
    POSGRADO_SMLV = 3

    @property
    def es_posgrado(self) -> bool:
        return self is not TipoPlantilla.PREGRADO


class MotivoRechazo(Enum):
    """Motivo por el que una fila no se sube (domain-entities.md §2.16)."""

    CODIGO_INVALIDO = "CODIGO_INVALIDO"
    CODIGO_REPETIDO = "CODIGO_REPETIDO"
    ESTUDIANTE_NO_ENCONTRADO = "ESTUDIANTE_NO_ENCONTRADO"
    SIN_VALOR_MATRICULA = "SIN_VALOR_MATRICULA"
    ESTADO_NO_PERMITIDO = "ESTADO_NO_PERMITIDO"
    CARRERA_INACTIVA = "CARRERA_INACTIVA"
    NO_TERMINACION_MATERIAS = "NO_TERMINACION_MATERIAS"
    SIN_PERIODO_VIGENTE = "SIN_PERIODO_VIGENTE"
    NIVEL_NO_CORRESPONDE = "NIVEL_NO_CORRESPONDE"
    CUOTAS_INVALIDAS = "CUOTAS_INVALIDAS"
    UNIDAD_INVALIDA = "UNIDAD_INVALIDA"
    FECHA_INVALIDA = "FECHA_INVALIDA"
    PORCENTAJE_INVALIDO = "PORCENTAJE_INVALIDO"
    PORCENTAJES_NO_SUMAN_100 = "PORCENTAJES_NO_SUMAN_100"
    DESCUENTOS_NO_ACUMULABLES = "DESCUENTOS_NO_ACUMULABLES"
    TIEMPO_AGOTADO = "TIEMPO_AGOTADO"
    ERROR_GUARDADO = "ERROR_GUARDADO"


@dataclass(frozen=True)
class HojaPlantilla:
    """Primera hoja del libro: (fila, columna) → texto, solo celdas con contenido (F4).

    Las filas y columnas empiezan en 1, como en Excel. Use `crear_hoja` para armarla: descarta las
    celdas vacías o con solo espacios.
    """

    celdas: Mapping[tuple[int, int], str]

    def valor(self, fila: int, columna: int) -> str | None:
        return self.celdas.get((fila, columna))

    def ultima_fila(self) -> int:
        return max((fila for fila, _ in self.celdas), default=0)

    def ultima_columna(self, hasta_fila: int | None = None) -> int:
        """Última columna con contenido; si se da `hasta_fila`, solo cuenta las filas anteriores a ella."""
        return max(
            (col for fila, col in self.celdas if hasta_fila is None or fila < hasta_fila),
            default=0,
        )


def crear_hoja(celdas: Mapping[tuple[int, int], str]) -> HojaPlantilla:
    """Arma la hoja sin las celdas vacías ni las que solo tienen espacios (F4)."""
    return HojaPlantilla({clave: texto for clave, texto in celdas.items() if texto.strip()})


@dataclass(frozen=True)
class FilaPlantilla:
    """Fila de datos: número de fila de Excel y columna → texto, sin celdas vacías."""

    numero: int
    celdas: Mapping[int, str]

    def texto(self, columna: int) -> str | None:
        return self.celdas.get(columna)

    def marcada(self, columna: int) -> bool:
        """Verdadero si la celda tiene contenido (BR-X01, BR-C01)."""
        return columna in self.celdas


@dataclass(frozen=True)
class Usuario:
    documento: str
    sub: str
    roles: frozenset[str]


@dataclass(frozen=True)
class Estudiante:
    codigo: int
    estado: str
    codigo_carrera: int
    tiene_valor_matricula: bool


@dataclass(frozen=True)
class Periodo:
    anio: int
    numero: int


@dataclass(frozen=True)
class ContextoCarrera:
    """Contexto del proyecto curricular. `activa` es `cra_estado = 'A'`; los excluidos los aplica el dominio."""

    codigo: int
    activa: bool
    nivel: str
    periodo: Periodo | None
    terminacion_activa: bool


@dataclass(frozen=True)
class FechasPago:
    ordinaria: date
    extraordinaria: date


@dataclass(frozen=True)
class Cuota:
    numero: int
    porcentaje: int
    fechas: FechasPago


@dataclass(frozen=True)
class DatosPosgrado:
    numero_cuotas: int
    unidad: str
    fechas_ordinarias: tuple[date, ...]
    porcentajes: tuple[int | None, ...]


@dataclass(frozen=True)
class Solicitud:
    codigo_estudiante: int
    codigo_carrera: int
    periodo: Periodo
    tipo: TipoPlantilla
    unidad: str
    cuotas: tuple[Cuota, ...]
    exenciones: tuple[int, ...]
    conceptos: tuple[int, ...]

    @property
    def cuota(self) -> int:
        """Valor de `solicitudRecibo.cuota`: 1 en pregrado y N en posgrado (BR-S03)."""
        return len(self.cuotas)


@dataclass(frozen=True)
class FallaFila:
    """Motivo y mensaje de una regla que falla; el caso de uso le agrega la fila y el código."""

    motivo: MotivoRechazo
    mensaje: str


@dataclass(frozen=True)
class Rechazo:
    fila: int
    codigo: str | None
    motivo: MotivoRechazo
    mensaje: str


@dataclass(frozen=True)
class Procesado:
    fila: int
    codigo: int


@dataclass(frozen=True)
class ResumenLote:
    id_lote: int
    tipo: TipoPlantilla
    procesados: tuple[Procesado, ...]
    rechazados: tuple[Rechazo, ...]

    @property
    def total_filas(self) -> int:
        """Procesados más rechazados: cada fila con datos aparece una vez (BR-R01)."""
        return len(self.procesados) + len(self.rechazados)


@dataclass(frozen=True)
class NuevoLote:
    documento_usuario: str
    nombre_original: str
    nombre_interno: str
    ip: str
    fecha: datetime


@dataclass(frozen=True)
class Lote:
    id: int
    documento_usuario: str
    nombre_original: str
    ip: str
    fecha: datetime


@dataclass(frozen=True)
class Pagina[T]:
    elementos: tuple[T, ...]
    total: int
    limite: int
    desplazamiento: int = field(default=0)
