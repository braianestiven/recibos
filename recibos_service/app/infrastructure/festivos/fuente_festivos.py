"""Festivos de la tabla de weboffice, en solo lectura y una vez por lote (BR-L13, BR-Q04, F9, F10; D5).

La tabla todavía no se conoce (D5): la base (MySQL u Oracle), la tabla y sus columnas son configuración,
validada como identificadores en `conf/conf.py`. Con una columna, es la fecha; con tres, son el día, el
mes y el año. Los sábados y domingos no se agregan: solo cuenta lo que está en la tabla (F10).
"""

# ruff: noqa: S608 - los nombres de la tabla y las columnas salen de la configuración validada

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Literal

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from app.application.errores import DependenciaNoDisponible
from app.application.presupuesto import Plazo
from app.infrastructure.db.motores import codigo_de_error
from app.infrastructure.oracle.repositorio_academico import limitar_llamada

registro = logging.getLogger(__name__)

Motor = Literal["mysql", "oracle"]
PEOR_CASO_MYSQL_S = 13.0  # 3 s para conectar y 10 s de lectura
TIEMPO_CONEXION_ORACLE_S = 5.0


def _nombre(identificador: str, motor: Motor) -> str:
    """En MySQL cada parte va entre comillas invertidas; en Oracle, sin comillas (sin distinguir mayúsculas)."""
    if motor == "oracle":
        return identificador
    return ".".join(f"`{parte}`" for parte in identificador.split("."))


def como_fecha(valor: object) -> date | None:
    if isinstance(valor, datetime):  # Oracle entrega DATE como datetime
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor.strip()[:10])
        except ValueError:
            return None
    return None


def fecha_de_partes(dia: object, mes: object, anio: object) -> date | None:
    try:
        return date(int(str(anio)), int(str(mes)), int(str(dia)))
    except (ValueError, OverflowError):
        return None


class FuenteFestivosWeboffice:
    def __init__(self, motor: Engine, tipo_motor: Motor, tabla: str, columnas: tuple[str, ...]) -> None:
        if len(columnas) not in {1, 3}:
            raise ValueError("Los festivos necesitan una columna de fecha o tres columnas (día, mes, año)")
        self._motor = motor
        self._tipo = tipo_motor
        nombre_tabla = _nombre(tabla, tipo_motor)
        nombres = [_nombre(c, tipo_motor) for c in columnas]
        if len(nombres) == 1:
            (fecha,) = nombres
            self._sql = text(f"SELECT {fecha} FROM {nombre_tabla} WHERE {fecha} >= :desde AND {fecha} < :hasta")
        else:
            dia, mes, anio = nombres
            self._sql = text(
                f"SELECT {dia}, {mes}, {anio} FROM {nombre_tabla} WHERE {anio} BETWEEN :anio_desde AND :anio_hasta"
            )
        self._una_columna = len(nombres) == 1

    def festivos(self, desde: date, hasta: date, plazo: Plazo) -> frozenset[date]:
        if self._una_columna:
            parametros: dict[str, object] = {"desde": desde, "hasta": hasta + timedelta(days=1)}
        else:
            parametros = {"anio_desde": desde.year, "anio_hasta": hasta.year}
        plazo.exigir(PEOR_CASO_MYSQL_S if self._tipo == "mysql" else TIEMPO_CONEXION_ORACLE_S)
        try:
            with self._motor.connect() as conexion:
                try:
                    if self._tipo == "oracle":
                        limitar_llamada(conexion, plazo)
                    filas = conexion.execute(self._sql, parametros).all()
                except DBAPIError:
                    conexion.invalidate()
                    raise
        except SQLAlchemyError as error:
            registro.warning(
                "festivos_no_disponibles",
                extra={"evento": "festivos_no_disponibles", "datos": {"codigo": codigo_de_error(error)}},
            )
            raise DependenciaNoDisponible("festivos") from None
        leidas = [como_fecha(fila[0]) if self._una_columna else fecha_de_partes(*fila[:3]) for fila in filas]
        ilegibles = sum(1 for fecha in leidas if fecha is None)
        if ilegibles:
            registro.warning(
                "festivos_ilegibles", extra={"evento": "festivos_ilegibles", "datos": {"filas": ilegibles}}
            )
        return frozenset(fecha for fecha in leidas if fecha is not None and desde <= fecha <= hasta)
