"""Validación de las variables `RECIBOS_SERVICE_*` al arrancar (conf/conf.py; NFR-S11, SECURITY-09)."""

from __future__ import annotations

import json

import pytest

from app.infrastructure.parametros.modelos import FORMAS
from conf.conf import PREFIJO, ConfiguracionInvalida, cargar_configuracion, nombre_variable

FORMATO_POR_FORMA = {
    "entero": "entero",
    "texto": "texto",
    "conjunto_textos": "lista",
    "conjunto_enteros": "lista_enteros",
    "mapa_columnas": "json",
    "porcentajes": "json",
}
REGLAS = {
    regla: {"id": i, "campo": "CodigoAbreviacion", "formato": FORMATO_POR_FORMA[forma]}
    for i, (regla, forma) in enumerate(FORMAS.items(), start=1)
}
CLAVE_LOCAL = "clave-local-que-no-debe-salir"


def entorno(**cambios: str | None) -> dict[str, str]:
    """Entorno válido de test; un valor `None` quita la variable."""
    base = {
        "ENV": "test",
        "ROL_AUTORIZADO": "ARC",
        "USERINFO_URL": "https://autenticacion.portaloas.udistrital.edu.co/oauth2/userinfo",
        "PARAMETROS_URL": "https://parametros.portaloas.udistrital.edu.co/",
        "PARAMETROS_REGLAS": json.dumps(REGLAS),
        "S3_BUCKET": "recibos-service-test",
        "SSM_RUTA": "/test/recibos_service",
        "ORACLE_HOST": "oracle.udistrital.edu.co",
        "ORACLE_SERVICIO": "ACADEMICA",
        "MYSQL_HOST": "mysql.udistrital.edu.co",
        "MYSQL_BASE": "weboffice",
        "FESTIVOS_MOTOR": "mysql",
        "FESTIVOS_TABLA": "festivos",
        "FESTIVOS_COLUMNAS": "fecha",
    }
    for nombre, valor in cambios.items():
        if valor is None:
            base.pop(nombre, None)
        else:
            base[nombre] = valor
    return {PREFIJO + nombre: valor for nombre, valor in base.items()}


def _variables_con_error(**cambios: str | None) -> list[str]:
    with pytest.raises(ConfiguracionInvalida) as error:
        cargar_configuracion(entorno(**cambios))
    return error.value.variables


def test_valores_por_defecto() -> None:
    conf = cargar_configuracion(entorno())
    assert (conf.puerto, conf.hilos, conf.proxies_confianza, conf.cors_origenes) == (8080, 4, 0, ())
    assert (conf.limite_lote_s, conf.max_filas, conf.max_archivo_bytes, conf.corte_mysql) == (90.0, 1000, 2097152, 5)
    assert (conf.oracle.puerto, conf.oracle.ca, conf.mysql.puerto, conf.mysql.ca) == (2484, None, 3306, None)
    assert (conf.mysql.prefijo, conf.mysql.llave_lote, conf.mysql.max_nombre_archivo) == ("", "id", 255)
    assert conf.parametros_url == "https://parametros.portaloas.udistrital.edu.co"
    assert conf.festivos.columnas == ("fecha",)
    assert conf.secretos_locales is None
    assert set(conf.parametros_reglas) == set(FORMAS)


def test_listas_y_valores_propios() -> None:
    conf = cargar_configuracion(
        entorno(
            CORS_ORIGENES="https://a.udistrital.edu.co, https://b.udistrital.edu.co,",
            FESTIVOS_COLUMNAS="dia, mes, anio",
            FESTIVOS_TABLA="weboffice.festivos",
            MYSQL_PREFIJO="wo_",
            LIMITE_LOTE_S="60",
            HILOS="8",
        )
    )
    assert conf.cors_origenes == ("https://a.udistrital.edu.co", "https://b.udistrital.edu.co")
    assert conf.festivos.columnas == ("dia", "mes", "anio")
    assert (conf.festivos.tabla, conf.mysql.prefijo) == ("weboffice.festivos", "wo_")
    assert (conf.limite_lote_s, conf.hilos) == (60, 8)


def test_faltan_variables() -> None:
    variables = _variables_con_error(ROL_AUTORIZADO=None, MYSQL_HOST=None, PARAMETROS_REGLAS=None)
    assert variables == [PREFIJO + "MYSQL_HOST", PREFIJO + "PARAMETROS_REGLAS", PREFIJO + "ROL_AUTORIZADO"]


def test_un_valor_en_blanco_cuenta_como_faltante() -> None:
    assert _variables_con_error(ROL_AUTORIZADO="   ") == [PREFIJO + "ROL_AUTORIZADO"]


@pytest.mark.parametrize(
    ("variable", "valor"),
    [
        ("ENV", "produccion"),
        ("PORT", "0"),
        ("HILOS", "1"),
        ("HILOS", "9"),
        ("PROXIES_CONFIANZA", "4"),
        ("LIMITE_LOTE_S", "91"),
        ("LIMITE_LOTE_S", "9"),
        ("MAX_FILAS", "1001"),
        ("MAX_ARCHIVO_BYTES", "3000000"),
        ("CORTE_MYSQL", "0"),
        ("CORTE_MYSQL", "21"),
        ("USERINFO_URL", "http://autenticacion.portaloas.udistrital.edu.co/oauth2/userinfo"),
        ("PARAMETROS_URL", "ftp://parametros"),
        ("CORS_ORIGENES", "*"),
        ("CORS_ORIGENES", "https://*.udistrital.edu.co"),
        ("CORS_ORIGENES", "http://recibos.udistrital.edu.co"),
        ("S3_BUCKET", "ab"),
        ("SSM_RUTA", "test/recibos_service"),
        ("SSM_RUTA", "/test/recibos_service/"),
        ("ORACLE_PUERTO", "70000"),
        ("MYSQL_BASE", "web office"),
        ("MYSQL_PREFIJO", "wo-"),
        ("MYSQL_LLAVE_LOTE", "id; DROP TABLE x"),
        ("MYSQL_MAX_NOMBRE_ARCHIVO", "5"),
        ("FESTIVOS_MOTOR", "postgres"),
        ("FESTIVOS_TABLA", "festivos; DROP TABLE x"),
        ("FESTIVOS_TABLA", "a.b.c"),
        ("FESTIVOS_COLUMNAS", "dia,mes"),
        ("FESTIVOS_COLUMNAS", "fecha`"),
        ("PARAMETROS_REGLAS", "{no es json"),
        ("PARAMETROS_REGLAS", json.dumps({"evento_periodo": {"id": 0, "campo": "Nombre", "formato": "entero"}})),
        ("PARAMETROS_REGLAS", json.dumps({"evento_periodo": {"id": 1, "campo": "Valor", "formato": "entero"}})),
        ("PARAMETROS_REGLAS", json.dumps({"evento_periodo": {"id": 1, "campo": "Nombre", "formato": "fecha"}})),
    ],
)
def test_valor_fuera_de_rango_o_invalido(variable: str, valor: str) -> None:
    assert _variables_con_error(**{variable: valor}) == [PREFIJO + variable]


def test_el_error_no_muestra_valores() -> None:
    with pytest.raises(ConfiguracionInvalida) as error:
        cargar_configuracion(entorno(ENV="dev", ORACLE_CLAVE=CLAVE_LOCAL, LIMITE_LOTE_S="999999"))
    assert CLAVE_LOCAL not in str(error.value)
    assert "999999" not in str(error.value)
    assert PREFIJO + "LIMITE_LOTE_S" in str(error.value)


def test_credenciales_locales_solo_en_dev() -> None:
    locales = {"ORACLE_USUARIO": "u1", "ORACLE_CLAVE": CLAVE_LOCAL, "MYSQL_USUARIO": "u2", "MYSQL_CLAVE": "c2"}
    conf = cargar_configuracion(entorno(ENV="dev", **locales))
    assert conf.secretos_locales is not None
    assert conf.secretos_locales.oracle_clave.get_secret_value() == CLAVE_LOCAL
    assert CLAVE_LOCAL not in repr(conf)
    assert cargar_configuracion(entorno(ENV="prod", **locales)).secretos_locales is None


def test_credenciales_locales_incompletas() -> None:
    variables = _variables_con_error(ENV="dev", ORACLE_USUARIO="u1", ORACLE_CLAVE=CLAVE_LOCAL)
    assert variables == [PREFIJO + "MYSQL_CLAVE", PREFIJO + "MYSQL_USUARIO"]


@pytest.mark.parametrize(
    ("ubicacion", "nombre"),
    [
        ((), PREFIJO + "?"),
        (("hilos",), PREFIJO + "HILOS"),
        (("oracle", "host"), PREFIJO + "ORACLE_HOST"),
        (("oracle",), PREFIJO + "ORACLE"),
        (("secretos_locales", "mysql_clave"), PREFIJO + "MYSQL_CLAVE"),
        (("parametros_reglas", "evento_periodo", "id"), PREFIJO + "PARAMETROS_REGLAS"),
    ],
)
def test_nombre_de_la_variable(ubicacion: tuple[int | str, ...], nombre: str) -> None:
    assert nombre_variable(ubicacion) == nombre
