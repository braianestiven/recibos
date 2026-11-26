"""Raíz de composición de recibos_service: gunicorn carga `api:create_app()` (gunicorn.conf.py).

Cada proceso de gunicorn llama a `create_app()`, porque `preload_app` está apagado: valida las variables,
lee los secretos de SSM, arma los motores sin conectar a las bases y registra los middlewares y las rutas
(logical-components.md §7). Si algo falla, deja el evento en el registro sin valores y el proceso no
arranca: gunicorn se detiene con "Worker failed to boot" y ECS reemplaza la tarea.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from typing import Any

import boto3
from flask import Flask
from pydantic import ValidationError

from app.application.autorizar_usuario import AutorizarUsuario
from app.application.consultar_lotes import ConsultarLotes
from app.application.procesar_lote import ConfiguracionLote, ProcesarLote
from app.infrastructure.config import ssm
from app.infrastructure.db.captura_sql import CapturaSql
from app.infrastructure.db.motores import DatosConexion, motor_mysql, motor_oracle
from app.infrastructure.festivos.fuente_festivos import FuenteFestivosWeboffice
from app.infrastructure.http import ClienteHttp
from app.infrastructure.mysql.repositorio_solicitudes import RepositorioSolicitudesMySQL, SentenciasMySQL
from app.infrastructure.oracle.repositorio_academico import RepositorioAcademicoOracle
from app.infrastructure.parametros.fuente_reglas import FuenteReglasParametros, ReglasMalConfiguradas
from app.infrastructure.parametros.modelos import EspecificacionParametro
from app.infrastructure.registro import configurar_registro
from app.infrastructure.reloj import RelojBogota
from app.infrastructure.s3 import almacenamiento_s3
from app.infrastructure.wso2.proveedor_identidad import ProveedorIdentidadWso2
from app.infrastructure.xls.lector_xlrd import LectorXlrd
from app.interfaces.aplicacion import crear_aplicacion
from app.interfaces.servicios import Servicios
from conf.conf import PREFIJO, Configuracion, ConfiguracionInvalida, Secretos, cargar_configuracion

registro = logging.getLogger("recibos_service.arranque")


def leer_secretos(conf: Configuracion, cliente_ssm: Any | None = None) -> Secretos:
    """Usuarios y contraseñas de las bases desde SSM; solo en `dev` pueden venir de variables (NFR-S11)."""
    if conf.secretos_locales is not None:
        return conf.secretos_locales
    cliente = cliente_ssm if cliente_ssm is not None else boto3.client("ssm", config=ssm.CONFIGURACION_CLIENTE)
    try:
        return Secretos.model_validate(ssm.LectorSsm(cliente, conf.ssm_ruta).secretos())
    except ValidationError:
        raise ssm.SecretosNoDisponibles("Los secretos de SSM no tienen el formato esperado") from None


def construir_servicios(conf: Configuracion, secretos: Secretos, cliente_s3: Any | None = None) -> Servicios:
    reloj = RelojBogota()
    http = ClienteHttp()
    captura = CapturaSql()
    mysql = motor_mysql(
        DatosConexion(
            conf.mysql.host,
            conf.mysql.puerto,
            conf.mysql.base,
            secretos.mysql_usuario,
            secretos.mysql_clave,
            conf.mysql.ca,
        ),
        conf.hilos,
    )
    oracle = motor_oracle(
        DatosConexion(
            conf.oracle.host,
            conf.oracle.puerto,
            conf.oracle.servicio,
            secretos.oracle_usuario,
            secretos.oracle_clave,
            conf.oracle.ca,
        ),
        conf.hilos,
    )
    captura.registrar(mysql)
    captura.registrar(oracle)
    especificaciones = {
        regla: EspecificacionParametro(espec.id, espec.campo, espec.formato)
        for regla, espec in conf.parametros_reglas.items()
    }
    try:
        fuente_reglas = FuenteReglasParametros(conf.parametros_url, especificaciones, http)
    except ReglasMalConfiguradas as error:
        registro.error(
            "reglas_mal_configuradas",
            extra={"evento": "reglas_mal_configuradas", "datos": {"problemas": error.problemas}},
        )
        raise ConfiguracionInvalida([PREFIJO + "PARAMETROS_REGLAS"]) from None
    repositorio = RepositorioSolicitudesMySQL(mysql, SentenciasMySQL(conf.mysql.prefijo, conf.mysql.llave_lote))
    festivos = FuenteFestivosWeboffice(
        mysql if conf.festivos.motor == "mysql" else oracle,
        conf.festivos.motor,
        conf.festivos.tabla,
        conf.festivos.columnas,
    )
    s3 = cliente_s3 if cliente_s3 is not None else boto3.client("s3", config=almacenamiento_s3.CONFIGURACION_CLIENTE)
    procesar_lote = ProcesarLote(
        fuente_reglas=fuente_reglas,
        repositorio=repositorio,
        almacenamiento=almacenamiento_s3.AlmacenamientoS3(s3, conf.s3_bucket),
        lector=LectorXlrd(),
        academico=RepositorioAcademicoOracle(oracle),
        fuente_festivos=festivos,
        reloj=reloj,
        configuracion=ConfiguracionLote(
            limite_lote_s=conf.limite_lote_s, max_filas=conf.max_filas, corte_mysql=conf.corte_mysql
        ),
    )
    return Servicios(
        procesar_lote=procesar_lote,
        consultar_lotes=ConsultarLotes(repositorio),
        proveedor_identidad=ProveedorIdentidadWso2(conf.userinfo_url, http),
        autorizar_usuario=AutorizarUsuario(conf.rol_autorizado),
        segundos=reloj.segundos,
        iniciar_captura_sql=captura.iniciar,
        sentencias_sql=captura.sentencias,
        max_archivo_bytes=conf.max_archivo_bytes,
        max_nombre_archivo=conf.mysql.max_nombre_archivo,
        cors_origenes=conf.cors_origenes,
        proxies_confianza=conf.proxies_confianza,
    )


def create_app(entorno: Mapping[str, str] | None = None) -> Flask:
    """Aplicación WSGI. Lanza `ConfiguracionInvalida` o `SecretosNoDisponibles` si no puede arrancar."""
    configurar_registro()
    try:
        conf = cargar_configuracion(os.environ if entorno is None else entorno)
        servicios = construir_servicios(conf, leer_secretos(conf))
    except ConfiguracionInvalida as error:
        registro.critical(
            "configuracion_invalida",
            extra={"evento": "configuracion_invalida", "datos": {"variables": error.variables}},
        )
        raise
    except ssm.SecretosNoDisponibles as error:
        registro.critical(
            "secretos_no_disponibles", extra={"evento": "secretos_no_disponibles", "datos": {"motivo": str(error)}}
        )
        raise
    registro.info("aplicacion_lista", extra={"evento": "aplicacion_lista", "datos": {"ambiente": conf.ambiente}})
    return crear_aplicacion(servicios)
