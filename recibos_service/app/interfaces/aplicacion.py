"""Arma la aplicación Flask con sus middlewares, en el orden de nfr-design-patterns.md §7.1.

Flask ejecuta los `before_request` en el orden en que se registran y los `after_request` al revés: por
eso la auditoría se registra antes que CORS y las cabeceras, y escribe el código final de la respuesta.
"""

from __future__ import annotations

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.interfaces.middlewares import auditoria, autenticacion, cabeceras_seguridad, contexto_peticion, cors, errores
from app.interfaces.routers.estado import estado
from app.interfaces.routers.lotes import lotes
from app.interfaces.servicios import CLAVE_EXTENSION, Servicios

SOBRE_MULTIPART_BYTES = 64 * 1024
MAX_FORM_PARTS = 4
MAX_FORM_MEMORY_SIZE = 16 * 1024


def crear_aplicacion(servicios: Servicios) -> Flask:
    app = Flask("recibos_service")
    app.config.update(
        DEBUG=False,
        PROPAGATE_EXCEPTIONS=False,
        MAX_CONTENT_LENGTH=servicios.max_archivo_bytes + SOBRE_MULTIPART_BYTES,  # Werkzeug corta con 413
        MAX_FORM_PARTS=MAX_FORM_PARTS,
        MAX_FORM_MEMORY_SIZE=MAX_FORM_MEMORY_SIZE,
    )
    app.json.ensure_ascii = False  # type: ignore[attr-defined]
    app.json.sort_keys = False  # type: ignore[attr-defined]
    app.extensions[CLAVE_EXTENSION] = servicios
    # IP del cliente: la que agrega el último proxy de confianza (AD-29, D13); con 0, la de la conexión
    app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
        app.wsgi_app, x_for=servicios.proxies_confianza, x_proto=0, x_host=0, x_port=0, x_prefix=0
    )
    contexto_peticion.registrar(app, servicios.segundos)
    auditoria.registrar(app, servicios.iniciar_captura_sql, servicios.sentencias_sql)
    cors.registrar(app, servicios.cors_origenes)
    autenticacion.registrar(app, servicios.proveedor_identidad, servicios.autorizar_usuario)
    cabeceras_seguridad.registrar(app)
    errores.registrar(app)
    app.register_blueprint(estado)
    app.register_blueprint(lotes)
    return app
