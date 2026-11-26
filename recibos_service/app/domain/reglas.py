"""Reglas de liquidación: instantánea leída al inicio de cada lote (domain-entities.md §2.8)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from decimal import Decimal

from app.domain import mensajes
from app.domain.errores import ExencionSinPorcentaje, ReglaInvalida
from app.domain.modelos import TipoPlantilla


@dataclass(frozen=True)
class ReglasLiquidacion:
    """Valores que llegan de "parametros" (business-rules.md §11) y porcentajes de la tabla `exencion`.

    Ningún valor queda fijo en el código (RF-09 CA1). Se valida al crearse: si una regla no sirve, el
    lote no empieza (BR-L04).
    """

    estados_permitidos: frozenset[str]
    estados_terminacion: frozenset[str]
    evento_periodo: int
    evento_terminacion: int
    proyectos_excluidos: frozenset[int]
    nivel_pregrado: str
    niveles_posgrado: frozenset[str]
    concepto_matricula: int
    concepto_exclusivo_pregrado: int
    conceptos_columna_pregrado: Mapping[int, int]
    conceptos_columna_posgrado: Mapping[int, int]
    exenciones_columna_pregrado: Mapping[int, int]
    exenciones_columna_posgrado: Mapping[int, int]
    id_exencion_votacion: int
    id_exencion_secretaria: int
    porcentajes_por_defecto: Mapping[int, tuple[int, ...]]
    dias_fecha_extraordinaria: int
    porcentaje_por_exencion: Mapping[int, Decimal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for numero in (1, 2, 3):
            valores = self.porcentajes_por_defecto.get(numero)
            if valores is None or len(valores) != numero or sum(valores) != 100 or min(valores) < 0:
                raise ReglaInvalida("porcentajes_por_defecto", mensajes.regla_invalida("porcentajes_por_defecto"))
        if self.dias_fecha_extraordinaria < 0:
            raise ReglaInvalida("dias_fecha_extraordinaria", mensajes.regla_invalida("dias_fecha_extraordinaria"))
        if not self.estados_permitidos:
            raise ReglaInvalida("estados_permitidos", mensajes.regla_invalida("estados_permitidos"))

    def exencion_de_columna(self, tipo: TipoPlantilla, columna: int) -> int | None:
        mapa = self.exenciones_columna_posgrado if tipo.es_posgrado else self.exenciones_columna_pregrado
        return mapa.get(columna)

    def concepto_de_columna(self, tipo: TipoPlantilla, columna: int) -> int | None:
        mapa = self.conceptos_columna_posgrado if tipo.es_posgrado else self.conceptos_columna_pregrado
        return mapa.get(columna)

    def ids_de_los_mapas(self) -> frozenset[int]:
        """Ids de exención de los dos mapas de columna: todos necesitan porcentaje (BR-L05)."""
        return frozenset(self.exenciones_columna_pregrado.values()) | frozenset(
            self.exenciones_columna_posgrado.values()
        )

    def con_porcentajes(self, porcentajes: Mapping[int, Decimal]) -> ReglasLiquidacion:
        """Agrega los porcentajes de la tabla `exencion` (F11); si falta uno, el lote no empieza."""
        requeridos = self.ids_de_los_mapas() | {self.id_exencion_votacion}
        faltantes = sorted(requeridos - porcentajes.keys())
        if faltantes:
            raise ExencionSinPorcentaje(faltantes[0], mensajes.exencion_sin_porcentaje(faltantes[0]))
        return replace(self, porcentaje_por_exencion=dict(porcentajes))

    def porcentaje_exencion(self, id_exencion: int) -> Decimal:
        try:
            return self.porcentaje_por_exencion[id_exencion]
        except KeyError:
            raise ExencionSinPorcentaje(id_exencion, mensajes.exencion_sin_porcentaje(id_exencion)) from None

    def porcentaje_por_defecto(self, numero_cuotas: int, posicion: int) -> int:
        """Porcentaje de la cuota `posicion` (desde 1) cuando la celda está vacía (BR-Q03)."""
        return self.porcentajes_por_defecto[numero_cuotas][posicion - 1]
