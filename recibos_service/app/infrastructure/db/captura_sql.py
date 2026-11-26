"""Texto SQL de cada petición para `sql_statement` de la auditoría, sin valores (AD-10, BR-U01).

Un listener `before_cursor_execute` guarda el texto de cada sentencia en una lista de la petición
(`ContextVar`). Los valores van enlazados y no pasan por aquí. Un lote de 1000 filas repite las mismas
sentencias miles de veces: se guarda cada texto una vez, en el orden en que aparece, recortado y con
un máximo de textos distintos, para que la línea de auditoría tenga un tamaño acotado.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

MAXIMO_SENTENCIAS = 50
LARGO_MAXIMO_SENTENCIA = 1000


class CapturaSql:
    def __init__(self) -> None:
        self._sentencias: ContextVar[dict[str, None] | None] = ContextVar("sentencias_sql", default=None)

    def registrar(self, motor: Engine) -> None:
        event.listen(motor, "before_cursor_execute", self._al_ejecutar)

    def iniciar(self) -> None:
        """Empieza una captura nueva para la petición en curso."""
        self._sentencias.set({})

    def sentencias(self) -> list[str]:
        return list(self._sentencias.get() or {})

    def _al_ejecutar(
        self, _conexion: Any, _cursor: Any, sentencia: str, _parametros: Any, _contexto: Any, _executemany: bool
    ) -> None:
        capturadas = self._sentencias.get()
        if capturadas is None:
            return
        texto = " ".join(sentencia.split())[:LARGO_MAXIMO_SENTENCIA]
        if texto in capturadas or len(capturadas) < MAXIMO_SENTENCIAS:
            capturadas[texto] = None
