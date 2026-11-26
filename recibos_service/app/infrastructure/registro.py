"""Registro de la aplicación en JSON hacia stdout, con `request_id` (AD-24, NFR-O01, SECURITY-03).

Solo salen los campos de la lista: `evento`, `datos` y `auditoria`. Nunca se registran tokens, secretos
ni datos personales; quien llama decide qué va en `datos` (NFR-S08).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

from app.application import contexto

CAMPOS_EXTRA = ("evento", "datos", "auditoria")


class FiltroRequestId(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = contexto.request_id.get()
        return True


class FormateadorJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entrada: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "request_id": getattr(record, "request_id", contexto.request_id.get()),
        }
        for campo in CAMPOS_EXTRA:
            if hasattr(record, campo):
                entrada[campo] = getattr(record, campo)
        if record.exc_info and record.exc_info[0] is not None:
            entrada["excepcion"] = record.exc_info[0].__name__  # sin el mensaje: puede traer valores
        return json.dumps(entrada, ensure_ascii=False, default=str)


def configurar_registro(nivel: str = "INFO") -> None:
    """Un solo manejador hacia stdout para la aplicación; gunicorn usa el mismo formato (gunicorn.conf.py)."""
    manejador = logging.StreamHandler(sys.stdout)
    manejador.setFormatter(FormateadorJson())
    manejador.addFilter(FiltroRequestId())
    raiz = logging.getLogger()
    raiz.handlers = [manejador]
    raiz.setLevel(nivel)
