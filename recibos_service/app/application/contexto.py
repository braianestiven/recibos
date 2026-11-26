"""Contexto de la petición que comparten las capas.

- `request_id`: identificador para los registros (NFR-O02).
- `token_usuario`: token del usuario, que la lectura de reglas reenvía a "parametros" (A11). Solo vive
  mientras dura la petición y nunca se registra (NFR-S08).
"""

from __future__ import annotations

from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="-")
token_usuario: ContextVar[str | None] = ContextVar("token_usuario", default=None)
