"""Reloj de America/Bogota y reloj monotónico para los plazos (A10, AD-34)."""

from __future__ import annotations

import time
from datetime import datetime

from app.domain.fechas import ZONA_BOGOTA


class RelojBogota:
    def ahora(self) -> datetime:
        return datetime.now(ZONA_BOGOTA)

    def segundos(self) -> float:
        return time.monotonic()
