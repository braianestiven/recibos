"""Configuración de gunicorn para recibos_service (logical-components.md §2.1; AD-17, AD-34, AD-36).

Los tiempos de espera son eslabones de la cadena de nfr-design-patterns.md §3.1: cada uno espera más
que el anterior, para que un lote de unos 100 s siempre termine y ARC reciba su reporte.
"""

from __future__ import annotations

import os

import gunicorn.http.wsgi


def _entero(nombre: str, por_defecto: int, minimo: int, maximo: int) -> int:
    """Variable entera con su rango; si no sirve, gunicorn no arranca y el error nombra la variable."""
    texto = os.environ.get(nombre, "").strip()
    if not texto:
        return por_defecto
    if not texto.isdigit() or not minimo <= int(texto) <= maximo:
        raise ValueError(f"{nombre} debe ser un entero de {minimo} a {maximo}")
    return int(texto)


# AD-36: gunicorn siempre envía `Server: gunicorn` y no tiene una opción para quitarla; el contrato de
# cabeceras de utils_oas la pide vacía. tests/test_gunicorn_conf.py revisa que siga funcionando.
gunicorn.http.wsgi.SERVER = ""

bind = f"0.0.0.0:{_entero('RECIBOS_SERVICE_PORT', 8080, 1, 65535)}"
wsgi_app = "api:create_app()"
worker_class = "gthread"
workers = _entero("RECIBOS_SERVICE_WORKERS", 2, 1, 4)
threads = _entero("RECIBOS_SERVICE_HILOS", 4, 2, 8)

timeout = 120  # latido del proceso; no corta peticiones
graceful_timeout = 110  # más que la petición más larga (unos 100 s)
keepalive = 125  # más que el tiempo de inactividad del balanceador (120 s)
max_requests = 1000
max_requests_jitter = 100
worker_tmp_dir = "/dev/shm"  # el latido no escribe en el disco, que puede ser de solo lectura
preload_app = False  # cada proceso crea sus pools y lee SSM después de nacer

accesslog = "-"
errorlog = "-"
access_log_format = '%(m)s %(U)s %(s)s %(B)s %(D)s %({x-request-id}o)s'  # método, ruta, código, bytes, µs, id
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "app.infrastructure.registro.FiltroRequestId"}},
    "formatters": {"json": {"()": "app.infrastructure.registro.FormateadorJson"}},
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
            "filters": ["request_id"],
        },
    },
    "loggers": {
        "gunicorn.error": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
        "gunicorn.access": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
    },
    "root": {"handlers": ["stdout"], "level": "INFO"},
}
