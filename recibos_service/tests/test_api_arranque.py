"""Arranque de cada proceso: `api.create_app()` (logical-components.md §7; NFR-S11)."""

from __future__ import annotations

import json
from typing import Any

import boto3
import pytest
from botocore.stub import Stubber
from pydantic import SecretStr

import api
from app.infrastructure.config.ssm import SecretosNoDisponibles
from conf.conf import PREFIJO, ConfiguracionInvalida, Secretos, cargar_configuracion
from tests.interfaces.dobles import registros
from tests.test_conf import REGLAS, entorno

LOCALES = {"ORACLE_USUARIO": "u1", "ORACLE_CLAVE": "c1", "MYSQL_USUARIO": "u2", "MYSQL_CLAVE": "c2"}
RUTA = "/test/recibos_service"


@pytest.fixture(autouse=True)
def _sin_reconfigurar_registro(monkeypatch: pytest.MonkeyPatch) -> None:
    """`configurar_registro` cambia los manejadores del registro raíz: en las pruebas se deja el de pytest."""
    monkeypatch.setattr(api, "configurar_registro", lambda: None)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "prueba")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "prueba")


def _cliente_ssm(parametros: dict[str, str], invalidos: list[str] | None = None) -> Any:
    cliente = boto3.client("ssm", region_name="us-east-1")
    stubber = Stubber(cliente)
    nombres = [f"{RUTA}/{n}" for n in ("oracle/username", "oracle/password", "mysql/username", "mysql/password")]
    respuesta: dict[str, Any] = {
        "Parameters": [{"Name": nombre, "Value": valor, "Type": "SecureString"} for nombre, valor in parametros.items()]
    }
    if invalidos:
        respuesta["InvalidParameters"] = invalidos
    stubber.add_response("get_parameters", respuesta, {"Names": nombres, "WithDecryption": True})
    stubber.activate()
    return cliente


def test_arranca_sin_conectar_a_las_bases() -> None:
    with registros("recibos_service.arranque") as eventos:
        app = api.create_app(entorno(ENV="dev", **LOCALES))
    respuesta = app.test_client().get("/health")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"status": "UP"}
    assert [e.getMessage() for e in eventos] == ["aplicacion_lista"]


def test_configuracion_invalida_no_arranca() -> None:
    with registros("recibos_service.arranque") as eventos, pytest.raises(ConfiguracionInvalida):
        api.create_app(entorno(ROL_AUTORIZADO=None, HILOS="99"))
    (evento,) = eventos
    assert evento.getMessage() == "configuracion_invalida"
    assert evento.datos == {"variables": [PREFIJO + "HILOS", PREFIJO + "ROL_AUTORIZADO"]}


def test_reglas_incompletas_no_arranca() -> None:
    reglas = {regla: espec for regla, espec in REGLAS.items() if regla != "evento_periodo"}
    reglas["regla_que_no_existe"] = REGLAS["evento_periodo"]
    reglas["dias_fecha_extraordinaria"] = {**REGLAS["dias_fecha_extraordinaria"], "formato": "lista"}
    with registros("recibos_service.arranque") as eventos, pytest.raises(ConfiguracionInvalida) as error:
        api.create_app(entorno(ENV="dev", PARAMETROS_REGLAS=json.dumps(reglas), **LOCALES))
    assert error.value.variables == [PREFIJO + "PARAMETROS_REGLAS"]
    problemas = next(e.datos["problemas"] for e in eventos if e.getMessage() == "reglas_mal_configuradas")
    assert problemas == ["falta evento_periodo", "sobra regla_que_no_existe", "formato de dias_fecha_extraordinaria"]


def test_secretos_de_ssm() -> None:
    conf = cargar_configuracion(entorno(SSM_RUTA=RUTA))
    valores = {
        f"{RUTA}/oracle/username": "lector",
        f"{RUTA}/oracle/password": "clave-oracle",
        f"{RUTA}/mysql/username": "recibos",
        f"{RUTA}/mysql/password": "clave-mysql",
    }
    secretos = api.leer_secretos(conf, _cliente_ssm(valores))
    assert secretos.oracle_usuario == "lector"
    assert secretos.mysql_clave.get_secret_value() == "clave-mysql"
    assert "clave-oracle" not in repr(secretos)


def test_secretos_con_formato_invalido() -> None:
    conf = cargar_configuracion(entorno(SSM_RUTA=RUTA))
    valores = {
        f"{RUTA}/oracle/username": "",
        f"{RUTA}/oracle/password": "x",
        f"{RUTA}/mysql/username": "y",
        f"{RUTA}/mysql/password": "z",
    }
    with pytest.raises(SecretosNoDisponibles, match="formato"):
        api.leer_secretos(conf, _cliente_ssm(valores))


def test_sin_secretos_no_arranca(monkeypatch: pytest.MonkeyPatch) -> None:
    cliente = _cliente_ssm({}, invalidos=[f"{RUTA}/oracle/password"])
    monkeypatch.setattr(api.boto3, "client", lambda *_args, **_kwargs: cliente)
    with registros("recibos_service.arranque") as eventos, pytest.raises(SecretosNoDisponibles):
        api.create_app(entorno(SSM_RUTA=RUTA))
    (evento,) = eventos
    assert evento.getMessage() == "secretos_no_disponibles"
    assert evento.datos == {"motivo": f"Faltan parámetros en SSM: {RUTA}/oracle/password"}


def test_construir_servicios_con_un_cliente_de_s3_propio() -> None:
    conf = cargar_configuracion(entorno(FESTIVOS_MOTOR="oracle", CORS_ORIGENES="https://a.udistrital.edu.co"))
    secretos = Secretos(oracle_usuario="u", oracle_clave=SecretStr("c"), mysql_usuario="u", mysql_clave=SecretStr("c"))
    servicios = api.construir_servicios(conf, secretos, cliente_s3=object())
    assert (servicios.max_archivo_bytes, servicios.max_nombre_archivo) == (2 * 1024 * 1024, 255)
    assert servicios.cors_origenes == ("https://a.udistrital.edu.co",)
    assert servicios.sentencias_sql() == []
