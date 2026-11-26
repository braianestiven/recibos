"""Presupuesto de tiempo de un lote (AD-34, nfr-design-patterns.md §3)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


class PlazoVencido(Exception):
    """Se acabó el tiempo: la llamada no empieza o la sentencia no sale."""


@dataclass(frozen=True)
class Plazo:
    """Momento en que vence un tiempo, en segundos de un reloj monotónico (`Reloj.segundos`)."""

    vence_en: float
    segundos: Callable[[], float]

    def restante(self) -> float:
        """Segundos que quedan; nunca negativo."""
        return max(0.0, self.vence_en - self.segundos())

    def vigente(self) -> bool:
        return self.restante() > 0

    def exigir(self, segundos: float = 0.0) -> None:
        """Lanza `PlazoVencido` si quedan `segundos` o menos: así una llamada de tiempo fijo solo empieza si cabe."""
        if self.restante() <= segundos:
            raise PlazoVencido

    def para(self, maximo: float) -> float:
        """Tiempo de espera para una llamada: el menor entre `maximo` y lo que queda."""
        restante = self.restante()
        if restante <= 0:
            raise PlazoVencido
        return min(maximo, restante)

    def hasta(self, otro: Plazo) -> Plazo:
        """El plazo que vence primero."""
        return self if self.vence_en <= otro.vence_en else otro
