"""Fechas de pago: fecha extraordinaria (BR-Q04) y timestamps de America/Bogota (BR-S04)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ZONA_BOGOTA = ZoneInfo("America/Bogota")


def fecha_extraordinaria(ordinaria: date, dias: int, festivos: frozenset[date]) -> date:
    """La ordinaria más `dias` días calendario; mientras caiga en festivo, un día más.

    Solo mueven la fecha los festivos de la tabla; un sábado o un domingo que no esté en ella no (F10).
    """
    fecha = ordinaria + timedelta(days=dias)
    while fecha in festivos:
        fecha += timedelta(days=1)
    return fecha


def timestamp_medianoche(fecha: date) -> int:
    """Timestamp Unix de la medianoche de la fecha en America/Bogota (A10, AD-15)."""
    return int(datetime.combine(fecha, time.min, tzinfo=ZONA_BOGOTA).timestamp())


def fecha_de_timestamp(timestamp: int) -> date:
    """Inversa de `timestamp_medianoche`."""
    return datetime.fromtimestamp(timestamp, tz=ZONA_BOGOTA).date()


def timestamp(momento: datetime) -> int:
    """Timestamp Unix de un momento con zona horaria (`solicitudLote.fecha`, `solicitudRecibo.fecha`)."""
    if momento.tzinfo is None:
        raise ValueError("El momento debe tener zona horaria")
    return int(momento.timestamp())


def anios_a_revisar(fechas_ordinarias: Iterable[date], dias: int) -> frozenset[int]:
    """Años de cada fecha ordinaria más `dias` días: cada uno debe tener festivos (BR-L13)."""
    return frozenset((fecha + timedelta(days=dias)).year for fecha in fechas_ordinarias)


def rango_de_festivos(
    fechas_ordinarias: Iterable[date], dias: int, margen: int = 30
) -> tuple[date, date] | None:
    """Desde la menor ordinaria más `dias` hasta la mayor más `dias` y un margen (BR-L13)."""
    desplazadas = sorted(fecha + timedelta(days=dias) for fecha in fechas_ordinarias)
    if not desplazadas:
        return None
    return desplazadas[0], desplazadas[-1] + timedelta(days=margen)
