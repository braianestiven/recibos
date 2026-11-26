"""Configuración de recibos_service: variables `RECIBOS_SERVICE_*` (L33), validadas al arrancar.

Si falta una variable o un valor está fuera de su rango, el proceso no arranca y el error nombra las
variables, nunca sus valores (NFR-S11, SECURITY-09). Los límites del lote se pueden bajar, no subir
(nfr-design/logical-components.md §4). Las contraseñas de las bases salen de SSM; solo en `dev` se
pueden dar como variables, para trabajar en local.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, field_validator

PREFIJO = "RECIBOS_SERVICE_"
_IDENTIFICADOR = re.compile(r"[A-Za-z_][A-Za-z0-9_$]{0,63}")
_TABLA = re.compile(r"[A-Za-z_][A-Za-z0-9_$]{0,63}(\.[A-Za-z_][A-Za-z0-9_$]{0,63})?")
_MAX_ARCHIVO = 2 * 1024 * 1024

Campo = Literal["CodigoAbreviacion", "Nombre", "Descripcion", "NumeroOrden"]
Formato = Literal["entero", "texto", "lista", "lista_enteros", "json"]


class ConfiguracionInvalida(Exception):
    """Nombra las variables con problemas, sin mostrar sus valores."""

    def __init__(self, variables: list[str]) -> None:
        self.variables = sorted(set(variables))
        super().__init__("Configuración inválida o incompleta: " + ", ".join(self.variables))


class _Modelo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class EspecificacionRegla(_Modelo):
    """Dónde está el valor de una regla en "parametros" (AD-21, D6)."""

    id: Annotated[int, Field(gt=0)]
    campo: Campo
    formato: Formato


class ConfiguracionOracle(_Modelo):
    host: Annotated[str, Field(min_length=1)]
    puerto: Annotated[int, Field(ge=1, le=65535)] = 2484
    servicio: Annotated[str, Field(min_length=1)]
    ca: str | None = None  # ruta al certificado de la CA (D14); sin él se usan las CA del sistema


class ConfiguracionMysql(_Modelo):
    host: Annotated[str, Field(min_length=1)]
    puerto: Annotated[int, Field(ge=1, le=65535)] = 3306
    base: Annotated[str, Field(min_length=1)]
    ca: str | None = None
    prefijo: str = ""  # prefijo de las tablas (D4)
    llave_lote: str = "id"  # llave primaria de solicitudLote (D4, provisional)
    max_nombre_archivo: Annotated[int, Field(ge=10, le=1024)] = 255  # longitud de nombreOriginal (D4)

    @field_validator("base", "llave_lote")
    @classmethod
    def _identificador(cls, valor: str) -> str:
        if _IDENTIFICADOR.fullmatch(valor) is None:
            raise ValueError("no es un identificador de SQL")
        return valor

    @field_validator("prefijo")
    @classmethod
    def _prefijo(cls, valor: str) -> str:
        if valor and _IDENTIFICADOR.fullmatch(valor) is None:
            raise ValueError("no es un prefijo de tabla válido")
        return valor


class ConfiguracionFestivos(_Modelo):
    """Tabla de festivos de weboffice (D5): una columna de fecha, o día, mes y año."""

    motor: Literal["mysql", "oracle"]
    tabla: str
    columnas: tuple[str, ...]

    @field_validator("tabla")
    @classmethod
    def _tabla(cls, valor: str) -> str:
        if _TABLA.fullmatch(valor) is None:
            raise ValueError("no es un nombre de tabla válido")
        return valor

    @field_validator("columnas")
    @classmethod
    def _columnas(cls, valor: tuple[str, ...]) -> tuple[str, ...]:
        if len(valor) not in {1, 3} or any(_IDENTIFICADOR.fullmatch(c) is None for c in valor):
            raise ValueError("deben ser una columna de fecha o tres columnas (día, mes, año)")
        return valor


class Secretos(_Modelo):
    oracle_usuario: Annotated[str, Field(min_length=1)]
    oracle_clave: SecretStr
    mysql_usuario: Annotated[str, Field(min_length=1)]
    mysql_clave: SecretStr


class Configuracion(_Modelo):
    ambiente: Literal["dev", "test", "prod"]
    puerto: Annotated[int, Field(ge=1, le=65535)] = 8080
    rol_autorizado: Annotated[str, Field(min_length=1)]
    cors_origenes: tuple[str, ...] = ()
    proxies_confianza: Annotated[int, Field(ge=0, le=3)] = 0
    hilos: Annotated[int, Field(ge=2, le=8)] = 4
    limite_lote_s: Annotated[float, Field(ge=10, le=90)] = 90.0
    max_filas: Annotated[int, Field(ge=1, le=1000)] = 1000
    max_archivo_bytes: Annotated[int, Field(ge=1024, le=_MAX_ARCHIVO)] = _MAX_ARCHIVO
    corte_mysql: Annotated[int, Field(ge=1, le=20)] = 5
    userinfo_url: str
    parametros_url: str
    parametros_reglas: dict[str, EspecificacionRegla]
    s3_bucket: Annotated[str, Field(min_length=3, max_length=63)]
    ssm_ruta: str
    oracle: ConfiguracionOracle
    mysql: ConfiguracionMysql
    festivos: ConfiguracionFestivos
    secretos_locales: Secretos | None = None  # solo en dev

    @field_validator("userinfo_url", "parametros_url")
    @classmethod
    def _https(cls, valor: str) -> str:
        if not valor.startswith("https://"):
            raise ValueError("debe usar https")
        return valor.rstrip("/")

    @field_validator("cors_origenes")
    @classmethod
    def _origenes(cls, valor: tuple[str, ...]) -> tuple[str, ...]:
        for origen in valor:
            if origen == "*" or "*" in origen or not origen.startswith(("https://", "http://localhost")):
                raise ValueError("cada origen debe ser explícito, sin comodines (AD-14)")
        return valor

    @field_validator("ssm_ruta")
    @classmethod
    def _ruta(cls, valor: str) -> str:
        if not valor.startswith("/") or valor.endswith("/"):
            raise ValueError("debe empezar con / y no terminar con /")
        return valor


_VARIABLES = {
    "ambiente": "ENV",
    "puerto": "PORT",
    "rol_autorizado": "ROL_AUTORIZADO",
    "proxies_confianza": "PROXIES_CONFIANZA",
    "hilos": "HILOS",
    "limite_lote_s": "LIMITE_LOTE_S",
    "max_filas": "MAX_FILAS",
    "max_archivo_bytes": "MAX_ARCHIVO_BYTES",
    "corte_mysql": "CORTE_MYSQL",
    "userinfo_url": "USERINFO_URL",
    "parametros_url": "PARAMETROS_URL",
    "s3_bucket": "S3_BUCKET",
    "ssm_ruta": "SSM_RUTA",
}
_ANIDADAS = {
    "oracle": {"host": "ORACLE_HOST", "puerto": "ORACLE_PUERTO", "servicio": "ORACLE_SERVICIO", "ca": "ORACLE_CA"},
    "mysql": {
        "host": "MYSQL_HOST",
        "puerto": "MYSQL_PUERTO",
        "base": "MYSQL_BASE",
        "ca": "MYSQL_CA",
        "prefijo": "MYSQL_PREFIJO",
        "llave_lote": "MYSQL_LLAVE_LOTE",
        "max_nombre_archivo": "MYSQL_MAX_NOMBRE_ARCHIVO",
    },
    "festivos": {"motor": "FESTIVOS_MOTOR", "tabla": "FESTIVOS_TABLA", "columnas": "FESTIVOS_COLUMNAS"},
}
_SECRETOS_LOCALES = {
    "oracle_usuario": "ORACLE_USUARIO",
    "oracle_clave": "ORACLE_CLAVE",
    "mysql_usuario": "MYSQL_USUARIO",
    "mysql_clave": "MYSQL_CLAVE",
}


def _lista(texto: str) -> tuple[str, ...]:
    return tuple(parte.strip() for parte in texto.split(",") if parte.strip())


def nombre_variable(ubicacion: tuple[int | str, ...]) -> str:
    """Nombre de la variable de entorno que corresponde a un campo con error."""
    if not ubicacion:
        return PREFIJO + "?"
    raiz = str(ubicacion[0])
    if raiz in _VARIABLES:
        return PREFIJO + _VARIABLES[raiz]
    if raiz == "cors_origenes":
        return PREFIJO + "CORS_ORIGENES"
    if raiz == "parametros_reglas":
        return PREFIJO + "PARAMETROS_REGLAS"
    if raiz in _ANIDADAS and len(ubicacion) > 1 and str(ubicacion[1]) in _ANIDADAS[raiz]:
        return PREFIJO + _ANIDADAS[raiz][str(ubicacion[1])]
    if raiz == "secretos_locales" and len(ubicacion) > 1 and str(ubicacion[1]) in _SECRETOS_LOCALES:
        return PREFIJO + _SECRETOS_LOCALES[str(ubicacion[1])]
    return PREFIJO + raiz.upper()


def cargar_configuracion(entorno: Mapping[str, str]) -> Configuracion:
    """Lee las variables del entorno. Lanza `ConfiguracionInvalida` con los nombres de las que fallan."""

    def valor(nombre: str) -> str | None:
        texto = entorno.get(PREFIJO + nombre)
        return texto.strip() if texto is not None and texto.strip() else None

    datos: dict[str, object] = {campo: v for campo, nombre in _VARIABLES.items() if (v := valor(nombre)) is not None}
    if (origenes := valor("CORS_ORIGENES")) is not None:
        datos["cors_origenes"] = _lista(origenes)
    reglas = valor("PARAMETROS_REGLAS")
    if reglas is not None:
        try:
            datos["parametros_reglas"] = json.loads(reglas)
        except json.JSONDecodeError:
            raise ConfiguracionInvalida([PREFIJO + "PARAMETROS_REGLAS"]) from None
    for grupo, variables in _ANIDADAS.items():
        datos[grupo] = {campo: v for campo, nombre in variables.items() if (v := valor(nombre)) is not None}
    if isinstance(datos["festivos"], dict) and "columnas" in datos["festivos"]:
        datos["festivos"]["columnas"] = _lista(str(datos["festivos"]["columnas"]))
    if valor("ENV") == "dev" and any(valor(n) for n in _SECRETOS_LOCALES.values()):
        datos["secretos_locales"] = {c: v for c, n in _SECRETOS_LOCALES.items() if (v := valor(n)) is not None}
    try:
        return Configuracion.model_validate(datos)
    except ValidationError as error:
        raise ConfiguracionInvalida([nombre_variable(e["loc"]) for e in error.errors()]) from None
