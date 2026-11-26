"""MySQL: SQL y parámetros enlazados, transacciones, bloqueo por estudiante, plazo por sentencia y errores.

Las pruebas usan un motor falso que registra cada sentencia (tests/infrastructure/bd_falsa.py). El SQL
real se compila con el dialecto de MySQL para revisar los parámetros de las listas.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from sqlalchemy import exc as sa_exc
from sqlalchemy.dialects.mysql import pymysql as dialecto_pymysql

from app.application.errores import BloqueoNoObtenido, ErrorConexionBD, ErrorPersistencia
from app.application.presupuesto import Plazo, PlazoVencido
from app.domain.fechas import ZONA_BOGOTA, timestamp_medianoche
from app.domain.modelos import Cuota, FechasPago, NuevoLote, Periodo, Solicitud, TipoPlantilla
from app.infrastructure.mysql.repositorio_solicitudes import (
    RepositorioSolicitudesMySQL,
    SentenciasMySQL,
    SesionFilasMySQL,
    es_falla_de_conexion,
    momento,
    nombre_bloqueo,
    porcentaje,
    traducir,
)
from app.infrastructure.registro import FormateadorJson
from tests.infrastructure.bd_falsa import Motor, Resultado, error_mysql
from tests.interfaces.dobles import registros

MODULO = "app.infrastructure.mysql.repositorio_solicitudes"
CODIGO = 20271020001
DOCUMENTO = "79123456"
CREADA = datetime(2027, 1, 4, 9, 30, tzinfo=ZONA_BOGOTA)
SOLICITUD = Solicitud(
    codigo_estudiante=CODIGO,
    codigo_carrera=20,
    periodo=Periodo(2027, 1),
    tipo=TipoPlantilla.POSGRADO_CREDITOS,
    unidad="12",
    cuotas=(
        Cuota(1, 60, FechasPago(date(2027, 2, 1), date(2027, 2, 9))),
        Cuota(2, 40, FechasPago(date(2027, 3, 1), date(2027, 3, 9))),
    ),
    exenciones=(1, 16),
    conceptos=(1, 2),
)
FILA_COMPLETA = [
    "SELECT GET_LOCK(:nombre, :espera)",
    "COMMIT",
    "SELECT `id_solicitud_recibo` FROM `solicitudRecibo`",
    "UPDATE `solicitudRecibo` SET `estado` = 2",
    "COMMIT",
    "INSERT INTO `solicitudRecibo`",
    "INSERT INTO `solicitudCuota`",
    "INSERT INTO `solicitudExencion`",
    "INSERT INTO `solicitudConcepto`",
    "COMMIT",
    "SELECT RELEASE_LOCK(:nombre)",
]


def responder(
    sin_imprimir: tuple[int, ...] = (77, 78), bloqueo: object = 1, fallas: dict[str, BaseException] | None = None
) -> Any:
    """Respuestas de MySQL; `fallas` lanza una excepción en la primera sentencia que empieza con la clave."""
    pendientes = dict(fallas or {})

    def responder_(texto: str, _parametros: Any) -> Resultado | BaseException:
        for inicio in list(pendientes):
            if texto.startswith(inicio):
                return pendientes.pop(inicio)
        if texto.startswith("SELECT GET_LOCK"):
            return Resultado(escalar=bloqueo)
        if "FOR UPDATE" in texto:
            return Resultado(filas=[(i,) for i in sin_imprimir])
        if texto.startswith("INSERT INTO `solicitudRecibo`"):
            return Resultado(lastrowid=901)
        return Resultado()

    return responder_


def sesion(motor: Motor, vence_en: float = 1000.0) -> SesionFilasMySQL:
    return SesionFilasMySQL(motor, SentenciasMySQL(), Plazo(vence_en, motor.reloj))


def procesar_fila(sesion_filas: SesionFilasMySQL, valida: bool = True) -> tuple[tuple[int, ...], int | None]:
    """Lo mismo que hace `ProcesarLote._guardar_fila` con una fila."""
    with sesion_filas.bloqueo_estudiante(CODIGO):
        canceladas = sesion_filas.cancelar_sin_imprimir(CODIGO)
        creada = sesion_filas.guardar_solicitud(SOLICITUD, DOCUMENTO, CREADA) if valida else None
    return canceladas, creada


def _inicios(motor: Motor) -> list[str]:
    return [s.texto.split(" (")[0].split(" WHERE")[0] for s in motor.sentencias]


class TestSesionFilas:
    def test_fila_valida_completa(self) -> None:
        motor = Motor(responder())
        filas = sesion(motor)
        assert procesar_fila(filas) == ((77, 78), 901)
        filas.cerrar()
        assert _inicios(motor) == FILA_COMPLETA
        parametros = [s.parametros for s in motor.sentencias]
        assert parametros[0] == {"nombre": "recibos_service:est:20271020001", "espera": 5}
        assert parametros[2] == {"codigo": "20271020001"}  # texto, como el INSERT del PHP (N19)
        assert parametros[3] == {"ids": [77, 78]}
        assert parametros[5] == {
            "id_usuario": DOCUMENTO,
            "codigo_est": "20271020001",
            "anno": 2027,
            "periodo": 1,
            "fecha": int(CREADA.timestamp()),
            "cuota": 2,
            "id_carrera": 20,
            "tipo_plantilla": 2,
            "unidad": "12",
        }
        assert parametros[6] == [
            {
                "id_solicitud": 901,
                "cuota": numero,
                "porcentaje": por,
                "fecha_ordinaria": timestamp_medianoche(ordinaria),
                "fecha_extra": timestamp_medianoche(extra),
            }
            for numero, por, ordinaria, extra in (
                (1, 60, date(2027, 2, 1), date(2027, 2, 9)),
                (2, 40, date(2027, 3, 1), date(2027, 3, 9)),
            )
        ]
        assert parametros[7] == [{"id_solicitud": 901, "id_exencion": 1}, {"id_solicitud": 901, "id_exencion": 16}]
        assert parametros[8] == [{"id_solicitud": 901, "id_concepto": 1}, {"id_solicitud": 901, "id_concepto": 2}]
        assert {s.conexion for s in motor.sentencias} == {1}  # una conexión para todo el lote (AD-35)
        assert motor.eventos == ["connect 1", "close 1"]

    def test_sin_solicitudes_previas_no_hay_update(self) -> None:
        motor = Motor(responder(sin_imprimir=()))
        assert procesar_fila(sesion(motor), valida=False) == ((), None)
        assert not [t for t in motor.textos() if t.startswith("UPDATE")]

    def test_solicitud_sin_exenciones_ni_conceptos(self) -> None:
        motor = Motor(responder())
        sesion(motor).guardar_solicitud(replace(SOLICITUD, exenciones=(), conceptos=()), DOCUMENTO, CREADA)
        assert not [t for t in motor.textos() if "solicitudExencion" in t or "solicitudConcepto" in t]

    @pytest.mark.parametrize("resultado", [0, None])
    def test_bloqueo_que_no_llega(self, resultado: object) -> None:
        motor = Motor(responder(bloqueo=resultado))
        with pytest.raises(BloqueoNoObtenido):
            procesar_fila(sesion(motor))
        assert not [t for t in motor.textos() if "RELEASE_LOCK" in t or "FOR UPDATE" in t]

    def test_conexion_perdida_en_la_cancelacion(self) -> None:
        motor = Motor(responder(fallas={"SELECT `id_solicitud_recibo`": error_mysql(2013)}))
        filas = sesion(motor)
        with pytest.raises(ErrorConexionBD):
            procesar_fila(filas)
        assert "invalidate 1" in motor.eventos
        assert not [t for t in motor.textos() if "RELEASE_LOCK" in t]  # MySQL lo soltó al cerrar la sesión
        assert procesar_fila(filas) == ((77, 78), 901)  # la fila siguiente toma otra conexión del pool
        assert motor.sentencias[-1].conexion == 2

    def test_espera_por_bloqueos_de_filas_revierte_y_suelta_el_bloqueo(self) -> None:
        motor = Motor(responder(fallas={"INSERT INTO `solicitudCuota`": error_mysql(1205)}))
        with pytest.raises(ErrorPersistencia) as error:
            procesar_fila(sesion(motor))
        assert not isinstance(error.value, ErrorConexionBD)
        assert "rollback 1" in motor.eventos
        assert "invalidate 1" not in motor.eventos
        assert motor.textos()[-1] == "SELECT RELEASE_LOCK(:nombre)"

    def test_conexion_perdida_al_confirmar(self) -> None:
        motor = Motor(responder(fallas={"COMMIT": error_mysql(2006)}))
        with pytest.raises(ErrorConexionBD):
            procesar_fila(sesion(motor))
        assert "invalidate 1" in motor.eventos

    def test_rollback_que_falla_descarta_la_conexion(self) -> None:
        motor = Motor(responder(fallas={"UPDATE": error_mysql(1213)}))
        motor.error_al_revertir = error_mysql(2013)
        with pytest.raises(ErrorPersistencia):
            procesar_fila(sesion(motor))
        assert motor.eventos == ["connect 1", "rollback 1", "invalidate 1", "close 1"]

    def test_el_plazo_vence_antes_de_una_sentencia(self) -> None:
        motor = Motor(responder())
        motor.segundos_por_sentencia = 1.0
        filas = sesion(motor, vence_en=3.5)  # alcanzan GET_LOCK, COMMIT, SELECT ... FOR UPDATE y UPDATE
        with pytest.raises(PlazoVencido):
            procesar_fila(filas)
        assert _inicios(motor) == FILA_COMPLETA[:4]
        assert "invalidate 1" in motor.eventos  # MySQL revierte la cancelación sin confirmar

    def test_el_plazo_vence_antes_de_soltar_el_bloqueo(self) -> None:
        motor = Motor(responder())
        motor.segundos_por_sentencia = 1.0
        filas = sesion(motor, vence_en=9.5)  # alcanzan las 10 sentencias de la fila, no RELEASE_LOCK
        assert procesar_fila(filas) == ((77, 78), 901)
        assert _inicios(motor) == FILA_COMPLETA[:10]
        assert "invalidate 1" in motor.eventos

    def test_soltar_el_bloqueo_que_falla_no_lanza_errores(self) -> None:
        motor = Motor(responder(fallas={"SELECT RELEASE_LOCK": error_mysql(2013)}))
        with registros(MODULO) as eventos:
            assert procesar_fila(sesion(motor)) == ((77, 78), 901)
        assert "invalidate 1" in motor.eventos
        assert "bloqueo_no_soltado" in [e.getMessage() for e in eventos]

    def test_sin_conexiones_libres_en_el_pool(self) -> None:
        motor = Motor(responder())
        motor.error_al_conectar = sa_exc.TimeoutError("QueuePool limit")
        with pytest.raises(ErrorConexionBD):
            procesar_fila(sesion(motor))

    def test_mysql_no_acepta_conexiones(self) -> None:
        motor = Motor(responder())
        motor.error_al_conectar = error_mysql(2003)
        with pytest.raises(ErrorConexionBD):
            procesar_fila(sesion(motor))

    def test_cerrar_sin_conexion_y_con_error(self) -> None:
        motor = Motor(responder())
        filas = sesion(motor)
        filas.cerrar()
        assert motor.eventos == []
        procesar_fila(filas)
        motor.error_al_cerrar = sa_exc.InvalidRequestError("x")
        with registros(MODULO) as eventos:
            filas.cerrar()
        assert motor.conexiones[0].invalidated
        assert [e.getMessage() for e in eventos] == ["mysql_conexion_no_cerrada"]

    def test_una_conexion_invalidada_se_reemplaza(self) -> None:
        motor = Motor(responder())
        filas = sesion(motor)
        procesar_fila(filas)
        motor.conexiones[0].invalidated = True
        procesar_fila(filas)
        assert motor.sentencias[-1].conexion == 2


@given(st.integers(0, 14), st.booleans())
def test_ninguna_sentencia_sale_despues_del_plazo(permitidas: int, valida: bool) -> None:
    motor = Motor(responder())
    motor.segundos_por_sentencia = 1.0
    filas = sesion(motor, vence_en=permitidas + 0.5)
    vencio = False
    try:
        procesar_fila(filas, valida=valida)
    except PlazoVencido:
        vencio = True
    finally:
        filas.cerrar()
    assert all(s.momento < permitidas + 0.5 for s in motor.sentencias)  # BR-L16
    if vencio:
        assert any(e.startswith("invalidate") for e in motor.eventos)
    for conexion in motor.conexiones:  # ninguna conexión vuelve al pool con un bloqueo tomado
        if not conexion.invalidated:
            propias = [s.texto for s in motor.sentencias if s.conexion == conexion.numero]
            assert sum("GET_LOCK" in t for t in propias) == sum("RELEASE_LOCK" in t for t in propias)


def _repositorio(motor: Motor, prefijo: str = "", llave: str = "id") -> RepositorioSolicitudesMySQL:
    return RepositorioSolicitudesMySQL(motor, SentenciasMySQL(prefijo, llave))  # type: ignore[arg-type]


class TestRepositorio:
    def test_registrar_lote(self) -> None:
        motor = Motor(lambda texto, _p: Resultado(lastrowid=1532) if texto.startswith("INSERT") else Resultado())
        lote = NuevoLote(DOCUMENTO, "pregrado.xls", "lotes/2027/01/abc.xls", "10.0.0.1", CREADA)
        assert _repositorio(motor).registrar_lote(lote) == 1532
        insercion, confirmacion = motor.sentencias
        assert insercion.texto.startswith("INSERT INTO `solicitudLote`")
        assert insercion.parametros == {
            "id_usuario": DOCUMENTO,
            "nombre_original": "pregrado.xls",
            "nombre_interno": "lotes/2027/01/abc.xls",
            "ip": "10.0.0.1",
            "fecha": int(CREADA.timestamp()),
        }
        assert confirmacion.texto == "COMMIT"

    @pytest.mark.parametrize(("codigo", "esperado"), [(1062, ErrorPersistencia), (2013, ErrorConexionBD)])
    def test_registrar_lote_con_error(self, codigo: int, esperado: type[Exception]) -> None:
        motor = Motor(lambda _t, _p: error_mysql(codigo))
        lote = NuevoLote(DOCUMENTO, "a.xls", "lotes/x.xls", "10.0.0.1", CREADA)
        with pytest.raises(esperado):
            _repositorio(motor).registrar_lote(lote)

    def test_listar_lotes(self) -> None:
        filas = [(9, 79123456, "b.xls", "10.0.0.2", "1767225600"), (8, None, None, None, "dañado")]

        def responder_(texto: str, _p: Any) -> Resultado:
            return Resultado(escalar=57) if "COUNT" in texto else Resultado(filas=filas)

        motor = Motor(responder_)
        pagina = _repositorio(motor, "wo_", "id_lote").listar_lotes(2, 4)
        assert (pagina.total, pagina.limite, pagina.desplazamiento) == (57, 2, 4)
        primero, segundo = pagina.elementos
        assert (primero.id, primero.documento_usuario, primero.nombre_original) == (9, "79123456", "b.xls")
        assert (primero.ip, primero.fecha) == ("10.0.0.2", datetime(2025, 12, 31, 19, tzinfo=ZONA_BOGOTA))
        assert (segundo.documento_usuario, segundo.nombre_original, segundo.ip) == ("", "", "")
        assert segundo.fecha == datetime.fromtimestamp(0, tz=ZONA_BOGOTA)
        conteo, consulta = motor.sentencias
        assert conteo.texto == "SELECT COUNT(*) FROM `wo_solicitudLote`"
        assert consulta.texto.endswith("ORDER BY `id_lote` DESC LIMIT :limite OFFSET :desplazamiento")
        assert consulta.parametros == {"limite": 2, "desplazamiento": 4}

    def test_listar_lotes_con_error(self) -> None:
        with pytest.raises(ErrorConexionBD):
            _repositorio(Motor(lambda _t, _p: error_mysql(2006))).listar_lotes(20, 0)

    def test_porcentajes_de_exencion(self) -> None:
        filas = [(1, 10), (2, "50.5"), (3, None), (4, "abc"), (5, "NaN"), (6, Decimal("7.25"))]
        motor = Motor(lambda _t, _p: Resultado(filas=filas))
        porcentajes = _repositorio(motor).porcentajes_exencion(frozenset({6, 1, 2, 3}))
        assert porcentajes == {1: Decimal(10), 2: Decimal("50.5"), 6: Decimal("7.25")}
        assert motor.sentencias[0].parametros == {"ids": [1, 2, 3, 6]}

    def test_porcentajes_sin_ids_no_consulta(self) -> None:
        motor = Motor()
        assert _repositorio(motor).porcentajes_exencion(frozenset()) == {}
        assert motor.eventos == []

    def test_porcentajes_con_error(self) -> None:
        with pytest.raises(ErrorPersistencia):
            _repositorio(Motor(lambda _t, _p: error_mysql(1146))).porcentajes_exencion(frozenset({1}))

    def test_filas_cierra_la_sesion(self) -> None:
        motor = Motor(responder())
        with _repositorio(motor).filas(Plazo(100.0, motor.reloj)) as filas:
            procesar_fila(filas)
        assert motor.eventos[-1] == "close 1"


class TestSql:
    def test_prefijo_y_llave_de_la_configuracion(self) -> None:
        sql = SentenciasMySQL("wo_", "id_lote")
        for sentencia in (sql.registrar_lote, sql.contar_lotes, sql.listar_lotes):
            assert "`wo_solicitudLote`" in str(sentencia)
        assert "`wo_exencion`" in str(sql.porcentajes)
        assert "`wo_solicitudCuota`" in str(sql.insertar_cuota)
        assert "`wo_solicitudRecibo`" in str(sql.cancelar)

    @pytest.mark.parametrize("nombre", ["porcentajes", "cancelar"])
    def test_las_listas_van_enlazadas(self, nombre: str) -> None:
        sentencia = getattr(SentenciasMySQL(), nombre).bindparams(ids=[11, 12, 13])
        compilada = str(
            sentencia.compile(dialect=dialecto_pymysql.dialect(), compile_kwargs={"render_postcompile": True})
        )
        assert compilada.endswith("IN (%s, %s, %s)")  # un parámetro por valor; PyMySQL los escapa
        assert "11" not in compilada

    def test_nombre_del_bloqueo(self) -> None:
        assert nombre_bloqueo(999_999_999_999_999) == "recibos_service:est:999999999999999"
        assert len(nombre_bloqueo(999_999_999_999_999)) <= 64


class TestErrores:
    @pytest.mark.parametrize("codigo", [2003, 2006, 2013, 2055])
    def test_fallas_de_conexion(self, codigo: int) -> None:
        assert es_falla_de_conexion(error_mysql(codigo))

    @pytest.mark.parametrize("codigo", [1205, 1213, 1062, 1146])
    def test_la_base_responde(self, codigo: int) -> None:
        assert not es_falla_de_conexion(error_mysql(codigo))

    def test_otros_casos(self) -> None:
        assert es_falla_de_conexion(error_mysql(1205, invalidada=True))
        assert es_falla_de_conexion(sa_exc.TimeoutError("pool"))
        assert not es_falla_de_conexion(sa_exc.InvalidRequestError("x"))
        assert not es_falla_de_conexion(sa_exc.OperationalError("SQL", {}, Exception()))

    def test_el_registro_trae_el_codigo_y_no_el_mensaje(self) -> None:
        with registros(MODULO) as eventos:
            assert isinstance(traducir(error_mysql(2013)), ErrorConexionBD)
        (evento,) = eventos
        assert evento.datos == {"codigo": "2013", "conexion": True}
        assert "20271020001" not in FormateadorJson().format(evento)


def test_conversion_de_valores_guardados() -> None:
    assert momento(1767225600) == datetime(2025, 12, 31, 19, tzinfo=ZONA_BOGOTA)
    assert momento(None) == datetime.fromtimestamp(0, tz=ZONA_BOGOTA)
    assert momento(10**20) == datetime.fromtimestamp(0, tz=ZONA_BOGOTA)
    assert porcentaje("12.5") == Decimal("12.5")
    assert porcentaje("Infinity") is None
