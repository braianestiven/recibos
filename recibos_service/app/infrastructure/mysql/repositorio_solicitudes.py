"""Tablas `solicitud*` y `exencion` de MySQL, las mismas que lee "Solicitados" (domain-entities.md §4).

- Nombres de tablas y columnas del PHP (`registro_lote_recibo/sql.class.php`), con el prefijo y la llave
  de `solicitudLote` de la configuración (D4). Esos nombres llegan validados como identificadores por
  `conf/conf.py`; los valores siempre van enlazados (SECURITY-05).
- `SesionFilasMySQL` usa una conexión para todas las filas de un lote (AD-35): bloqueo con nombre por
  estudiante (AD-32), cancelación y guardado, cada uno con su transacción (AD-30).
- Antes de cada sentencia, también del `COMMIT`, revisa el plazo del lote: si venció, no la envía y cierra
  la conexión, y MySQL revierte la transacción abierta y suelta el bloqueo (BR-L16).
- Los errores 2003, 2006, 2013 y 2055, la conexión que SQLAlchemy marca como perdida y la espera por una
  conexión del pool salen como `ErrorConexionBD`; los demás, como `ErrorPersistencia` (BR-T04).
- `codigo_est` se envía como texto, como el `INSERT` del PHP: así MySQL puede usar el índice tanto si la
  columna es numérica como si es de texto (N19).
"""

# ruff: noqa: S608 - los nombres de tablas y columnas salen de la configuración validada, nunca de la petición

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy import exc as sa_exc
from sqlalchemy.engine import Connection, CursorResult, Engine
from sqlalchemy.sql.elements import TextClause

from app.application.errores import BloqueoNoObtenido, ErrorConexionBD, ErrorPersistencia
from app.application.presupuesto import Plazo, PlazoVencido
from app.domain.fechas import ZONA_BOGOTA, timestamp, timestamp_medianoche
from app.domain.modelos import Lote, NuevoLote, Pagina, Solicitud
from app.infrastructure.db.motores import codigo_de_error

registro = logging.getLogger(__name__)

ERRORES_DE_CONEXION = frozenset({2003, 2006, 2013, 2055})
ESPERA_BLOQUEO_S = 5

Parametros = Mapping[str, Any] | Sequence[Mapping[str, Any]]


def nombre_bloqueo(codigo_estudiante: int) -> str:
    """`recibos_service:est:{código}`: 35 caracteres con un código de 15 dígitos; MySQL acepta 64."""
    return f"recibos_service:est:{codigo_estudiante}"


def es_falla_de_conexion(error: BaseException) -> bool:
    if isinstance(error, sa_exc.TimeoutError):  # no hubo una conexión libre en el pool
        return True
    if isinstance(error, sa_exc.DBAPIError):
        if error.connection_invalidated:
            return True
        argumentos: tuple[Any, ...] = getattr(error.orig, "args", ())
        return bool(argumentos) and argumentos[0] in ERRORES_DE_CONEXION
    return False


def traducir(error: sa_exc.SQLAlchemyError) -> ErrorPersistencia:
    perdida = es_falla_de_conexion(error)
    registro.warning(
        "mysql_error",
        extra={"evento": "mysql_error", "datos": {"codigo": codigo_de_error(error), "conexion": perdida}},
    )
    return ErrorConexionBD() if perdida else ErrorPersistencia()


def momento(valor: object) -> datetime:
    """`solicitudLote.fecha` es un timestamp Unix (`time()` del PHP); un valor dañado no tumba el historial."""
    try:
        return datetime.fromtimestamp(int(str(valor)), tz=ZONA_BOGOTA)
    except (ValueError, OverflowError, OSError):
        return datetime.fromtimestamp(0, tz=ZONA_BOGOTA)


def porcentaje(valor: object) -> Decimal | None:
    """Porcentaje de `exencion`; vacío o ilegible cuenta como faltante (BR-L05)."""
    if valor is None:
        return None
    try:
        leido = Decimal(str(valor))
    except InvalidOperation:
        return None
    return leido if leido.is_finite() else None


def _texto(valor: object) -> str:
    return "" if valor is None else str(valor)


class SentenciasMySQL:
    """Textos SQL con los nombres de la configuración."""

    def __init__(self, prefijo: str = "", llave_lote: str = "id") -> None:
        def tabla(nombre: str) -> str:
            return f"`{prefijo}{nombre}`"

        lote, recibo, llave = tabla("solicitudLote"), tabla("solicitudRecibo"), f"`{llave_lote}`"
        self.registrar_lote = text(
            f"INSERT INTO {lote} (`id_usuario`, `nombreOriginal`, `nombreInterno`, `ip`, `fecha`) "
            "VALUES (:id_usuario, :nombre_original, :nombre_interno, :ip, :fecha)"
        )
        self.listar_lotes = text(
            f"SELECT {llave}, `id_usuario`, `nombreOriginal`, `ip`, `fecha` FROM {lote} "
            f"ORDER BY {llave} DESC LIMIT :limite OFFSET :desplazamiento"
        )
        self.contar_lotes = text(f"SELECT COUNT(*) FROM {lote}")
        self.porcentajes = text(
            f"SELECT `id_exencion`, `porcentaje` FROM {tabla('exencion')} WHERE `id_exencion` IN :ids"
        ).bindparams(bindparam("ids", expanding=True))
        self.bloquear = text("SELECT GET_LOCK(:nombre, :espera)")
        self.soltar = text("SELECT RELEASE_LOCK(:nombre)")
        self.sin_imprimir = text(
            f"SELECT `id_solicitud_recibo` FROM {recibo} WHERE `codigo_est` = :codigo AND `estado` = 0 FOR UPDATE"
        )
        self.cancelar = text(
            f"UPDATE {recibo} SET `estado` = 2 WHERE `estado` = 0 AND `id_solicitud_recibo` IN :ids"
        ).bindparams(bindparam("ids", expanding=True))
        self.insertar_recibo = text(
            f"INSERT INTO {recibo} (`id_usuario`, `codigo_est`, `estado`, `anno`, `periodo`, `fecha`, `cuota`, "
            "`id_carrera`, `tipoPlantilla`, `unidad`) VALUES (:id_usuario, :codigo_est, 0, :anno, :periodo, "
            ":fecha, :cuota, :id_carrera, :tipo_plantilla, :unidad)"
        )
        self.insertar_cuota = text(
            f"INSERT INTO {tabla('solicitudCuota')} (`id_solicitud`, `cuota`, `porcentaje`, `fecha_ordinaria`, "
            "`fecha_extra`) VALUES (:id_solicitud, :cuota, :porcentaje, :fecha_ordinaria, :fecha_extra)"
        )
        self.insertar_exencion = text(
            f"INSERT INTO {tabla('solicitudExencion')} (`id_solicitud`, `id_exencion`) "
            "VALUES (:id_solicitud, :id_exencion)"
        )
        self.insertar_concepto = text(
            f"INSERT INTO {tabla('solicitudConcepto')} (`id_solicitud`, `id_concepto`) "
            "VALUES (:id_solicitud, :id_concepto)"
        )


class SesionFilasMySQL:
    """Implementa `SesionFilas`. Si la conexión se pierde, la fila siguiente toma otra del pool."""

    def __init__(self, motor: Engine, sql: SentenciasMySQL, plazo: Plazo) -> None:
        self._motor = motor
        self._sql = sql
        self._plazo = plazo
        self._conexion: Connection | None = None

    # --- puerto --------------------------------------------------------------------------------

    @contextmanager
    def bloqueo_estudiante(self, codigo_estudiante: int) -> Iterator[None]:
        nombre = nombre_bloqueo(codigo_estudiante)
        obtenido = self._ejecutar(self._sql.bloquear, {"nombre": nombre, "espera": ESPERA_BLOQUEO_S}).scalar()
        conexion_del_bloqueo = self._conexion
        try:
            self._confirmar()  # SQLAlchemy abrió una transacción con el SELECT; la cancelación abre la suya
            if obtenido != 1:  # 0: no llegó en 5 s; NULL: error de MySQL
                raise BloqueoNoObtenido
            yield
        finally:
            if obtenido == 1:
                self._soltar(nombre, conexion_del_bloqueo)

    def cancelar_sin_imprimir(self, codigo_estudiante: int) -> tuple[int, ...]:
        filas = self._ejecutar(self._sql.sin_imprimir, {"codigo": str(codigo_estudiante)})
        ids = tuple(int(i) for i in filas.scalars())
        if ids:
            self._ejecutar(self._sql.cancelar, {"ids": list(ids)})
        self._confirmar()
        return ids

    def guardar_solicitud(self, solicitud: Solicitud, documento_usuario: str, creada_en: datetime) -> int:
        recibo = self._ejecutar(
            self._sql.insertar_recibo,
            {
                "id_usuario": documento_usuario,
                "codigo_est": str(solicitud.codigo_estudiante),
                "anno": solicitud.periodo.anio,
                "periodo": solicitud.periodo.numero,
                "fecha": timestamp(creada_en),
                "cuota": solicitud.cuota,
                "id_carrera": solicitud.codigo_carrera,
                "tipo_plantilla": int(solicitud.tipo),
                "unidad": solicitud.unidad,
            },
        )
        id_solicitud = int(recibo.lastrowid)
        cuotas = [
            {
                "id_solicitud": id_solicitud,
                "cuota": cuota.numero,
                "porcentaje": cuota.porcentaje,
                "fecha_ordinaria": timestamp_medianoche(cuota.fechas.ordinaria),
                "fecha_extra": timestamp_medianoche(cuota.fechas.extraordinaria),
            }
            for cuota in solicitud.cuotas
        ]
        self._ejecutar(self._sql.insertar_cuota, cuotas)
        if solicitud.exenciones:
            exenciones = [{"id_solicitud": id_solicitud, "id_exencion": e} for e in solicitud.exenciones]
            self._ejecutar(self._sql.insertar_exencion, exenciones)
        if solicitud.conceptos:
            conceptos = [{"id_solicitud": id_solicitud, "id_concepto": c} for c in solicitud.conceptos]
            self._ejecutar(self._sql.insertar_concepto, conceptos)
        self._confirmar()
        return id_solicitud

    def cerrar(self) -> None:
        """Devuelve la conexión al pool, que revierte lo que haya quedado abierto; si falla, la descarta."""
        conexion, self._conexion = self._conexion, None
        if conexion is None:
            return
        try:
            conexion.close()
        except sa_exc.SQLAlchemyError:
            self._conexion = conexion
            self._descartar()

    # --- sentencias ----------------------------------------------------------------------------

    def _activa(self) -> Connection:
        if self._conexion is not None and (self._conexion.invalidated or self._conexion.closed):
            self._descartar()
        if self._conexion is None:
            self._conexion = self._motor.connect()
        return self._conexion

    def _exigir_plazo(self) -> None:
        try:
            self._plazo.exigir()
        except PlazoVencido:
            self._descartar()  # MySQL revierte la transacción abierta y suelta el bloqueo
            raise

    def _ejecutar(self, sentencia: TextClause, parametros: Parametros) -> CursorResult[Any]:
        self._exigir_plazo()
        try:
            return self._activa().execute(sentencia, parametros)
        except sa_exc.SQLAlchemyError as error:
            raise self._fallo(error) from None

    def _confirmar(self) -> None:
        self._exigir_plazo()
        try:
            self._activa().commit()
        except sa_exc.SQLAlchemyError as error:
            raise self._fallo(error) from None

    def _fallo(self, error: sa_exc.SQLAlchemyError) -> ErrorPersistencia:
        """Deja la sesión lista para la fila siguiente y traduce el error (AD-35)."""
        traducido = traducir(error)
        if isinstance(traducido, ErrorConexionBD):
            self._descartar()
        else:
            self._revertir()
        return traducido

    def _revertir(self) -> None:
        if self._conexion is None:
            return
        try:
            self._conexion.rollback()
        except sa_exc.SQLAlchemyError:
            self._descartar()

    def _descartar(self) -> None:
        """Cierra la conexión del driver: MySQL termina la sesión, revierte y suelta los bloqueos."""
        conexion, self._conexion = self._conexion, None
        if conexion is None:
            return
        try:
            conexion.invalidate()
            conexion.close()
        except sa_exc.SQLAlchemyError:
            registro.warning("mysql_conexion_no_cerrada", extra={"evento": "mysql_conexion_no_cerrada"})

    def _soltar(self, nombre: str, conexion_del_bloqueo: Connection | None) -> None:
        """Suelta el bloqueo sin lanzar errores. Si la conexión ya no es la del bloqueo, MySQL lo soltó."""
        conexion = self._conexion
        if conexion is None or conexion is not conexion_del_bloqueo:
            return
        if not self._plazo.vigente():  # después del plazo no sale ninguna sentencia
            self._descartar()
            return
        try:
            # Sin COMMIT: no cambia datos, y la transacción que abre SQLAlchemy la cierra el COMMIT siguiente
            # o el pool al recibir la conexión. Así no sale ninguna sentencia más después de revisar el plazo.
            conexion.execute(self._sql.soltar, {"nombre": nombre})
        except sa_exc.SQLAlchemyError:
            registro.warning("bloqueo_no_soltado", extra={"evento": "bloqueo_no_soltado"})
            self._descartar()


class RepositorioSolicitudesMySQL:
    def __init__(self, motor: Engine, sql: SentenciasMySQL) -> None:
        self._motor = motor
        self._sql = sql

    def registrar_lote(self, lote: NuevoLote) -> int:
        parametros = {
            "id_usuario": lote.documento_usuario,
            "nombre_original": lote.nombre_original,
            "nombre_interno": lote.nombre_interno,
            "ip": lote.ip,
            "fecha": timestamp(lote.fecha),
        }
        try:
            with self._motor.begin() as conexion:
                resultado = conexion.execute(self._sql.registrar_lote, parametros)
                return int(resultado.lastrowid)
        except sa_exc.SQLAlchemyError as error:
            raise traducir(error) from None

    @contextmanager
    def filas(self, plazo: Plazo) -> Iterator[SesionFilasMySQL]:
        sesion = SesionFilasMySQL(self._motor, self._sql, plazo)
        try:
            yield sesion
        finally:
            sesion.cerrar()

    def listar_lotes(self, limite: int, desplazamiento: int) -> Pagina[Lote]:
        try:
            with self._motor.connect() as conexion:
                total = int(conexion.execute(self._sql.contar_lotes).scalar_one())
                filas = conexion.execute(
                    self._sql.listar_lotes, {"limite": limite, "desplazamiento": desplazamiento}
                ).all()
        except sa_exc.SQLAlchemyError as error:
            raise traducir(error) from None
        lotes = tuple(
            Lote(
                id=int(llave),
                documento_usuario=_texto(usuario),
                nombre_original=_texto(nombre),
                ip=_texto(ip),
                fecha=momento(fecha),
            )
            for llave, usuario, nombre, ip, fecha in filas
        )
        return Pagina(elementos=lotes, total=total, limite=limite, desplazamiento=desplazamiento)

    def porcentajes_exencion(self, ids: frozenset[int]) -> Mapping[int, Decimal]:
        """Solo las exenciones con porcentaje legible; las demás faltan y el lote no empieza (BR-L05)."""
        if not ids:
            return {}
        try:
            with self._motor.connect() as conexion:
                filas = conexion.execute(self._sql.porcentajes, {"ids": sorted(ids)}).all()
        except sa_exc.SQLAlchemyError as error:
            raise traducir(error) from None
        leidos = {int(id_exencion): porcentaje(valor) for id_exencion, valor in filas}
        return {id_exencion: valor for id_exencion, valor in leidos.items() if valor is not None}
