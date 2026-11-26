"""Capa HTTP con el cliente de pruebas de Flask: contrato, seguridad, CORS y auditoría (api-contract.md)."""

from __future__ import annotations

import io
import json
import logging
from typing import Any

import pytest

from app.application import contexto
from app.application.errores import (
    MENSAJE_DEPENDENCIA,
    DependenciaNoDisponible,
    ErrorPersistencia,
    FormatoPlantillaInvalido,
    NoAutenticado,
    RespuestaInvalida,
)
from app.application.procesar_lote import CargarLoteComando, ResultadoLote
from app.domain.modelos import Usuario
from app.infrastructure.registro import FormateadorJson
from app.interfaces.controllers.lotes_controller import (
    FALTA_ARCHIVO,
    LIMIT_INVALIDO,
    NOMBRE_INVALIDO,
    OFFSET_INVALIDO,
    TIPO_NO_PERMITIDO,
)
from app.interfaces.middlewares.cabeceras_seguridad import CABECERAS
from app.interfaces.middlewares.errores import MENSAJE_INESPERADO, mensaje_tamano
from app.interfaces.servicios import Servicios
from tests.interfaces import dobles
from tests.interfaces.dobles import (
    AUDITORIA,
    CODIGO_RECHAZADO,
    CONTENIDO_XLS,
    ORIGEN,
    TOKEN,
    USUARIO_ARC,
    archivo,
    autorizacion,
    cliente,
    registros,
    servicios,
)

RAIZ_TRAZA = "1-67891233-abcdef012345678912345678"
MENSAJE_REGLA = "No se pudo leer la regla evento_periodo del servicio de parámetros."
CAMPOS_AUDITORIA = {
    "app_name",
    "agent",
    "data",
    "date",
    "host",
    "ip_user",
    "method",
    "path",
    "query",
    "schema",
    "sql_statement",
    "status",
    "trace_id",
    "user",
}


def _sobre(respuesta: Any) -> dict[str, Any]:
    cuerpo: dict[str, Any] = respuesta.get_json()
    assert cuerpo["Status"] == respuesta.status_code
    assert cuerpo["Success"] is (respuesta.status_code < 400)
    assert isinstance(cuerpo["Message"], str)
    assert cuerpo["Message"]
    return cuerpo


def _cargar(servicios_app: Servicios | None = None, **kwargs: Any) -> Any:
    datos = kwargs.pop("data", archivo())
    cabeceras = kwargs.pop("headers", autorizacion())
    return cliente(servicios_app).post("/v1/lotes", data=datos, headers=cabeceras, content_type="multipart/form-data")


class TestHealthChecks:
    @pytest.mark.parametrize(("ruta", "cuerpo"), [("/", {"status": "ok"}), ("/health", {"status": "UP"})])
    def test_publicos_sin_auditoria(self, ruta: str, cuerpo: dict[str, str]) -> None:
        proveedor = dobles.ProveedorDePrueba()
        with registros("recibos_service.auditoria") as auditoria:
            respuesta = cliente(servicios(proveedor_identidad=proveedor)).get(ruta)
        assert respuesta.status_code == 200
        assert respuesta.get_json() == cuerpo
        assert auditoria == []  # AD-11
        assert proveedor.tokens == []  # no consulta a WSO2 (NFR-A05)
        assert "Cache-Control" not in respuesta.headers

    def test_ruta_desconocida_usa_el_sobre(self) -> None:
        respuesta = cliente().get("/no-existe")
        assert respuesta.status_code == 404
        assert _sobre(respuesta) == {"Success": False, "Status": 404, "Message": "Recurso no encontrado", "Data": None}


class TestAutenticacion:
    @pytest.mark.parametrize(
        "cabeceras",
        [
            {},
            {"Authorization": "Basic dXN1YXJpbzpjbGF2ZQ=="},
            {"Authorization": "Bearer"},
            {"Authorization": "Bearer token con espacios"},
            {"Authorization": "Bearer <script>"},
            {"Authorization": "Bearer " + "a" * 9000},
            {"Authorization": "Bearer token-desconocido"},
        ],
    )
    def test_sin_token_valido_es_401(self, cabeceras: dict[str, str]) -> None:
        respuesta = cliente().get("/v1/lotes", headers=cabeceras)
        assert respuesta.status_code == 401
        assert _sobre(respuesta) == {"Success": False, "Status": 401, "Message": "No autorizado", "Data": None}

    @pytest.mark.parametrize(
        "usuario",
        [
            Usuario("79123456", "otro@udistrital.edu.co", frozenset({"DOCENTE"})),
            Usuario("", "arc@udistrital.edu.co", frozenset({"ARC"})),
        ],
    )
    def test_sin_rol_o_sin_documento_es_403(self, usuario: Usuario) -> None:
        proveedor = dobles.ProveedorDePrueba({TOKEN: usuario})
        consultar = dobles.ConsultarLotesDePrueba()
        app_servicios = servicios(proveedor_identidad=proveedor, consultar_lotes=consultar)
        respuesta = cliente(app_servicios).get("/v1/lotes", headers=autorizacion())
        assert respuesta.status_code == 403
        assert _sobre(respuesta)["Message"] == "Prohibido"
        assert consultar.consultas == []

    def test_wso2_caido_es_503_y_falla_cerrada(self) -> None:
        proveedor = dobles.ProveedorDePrueba(error=DependenciaNoDisponible("wso2"))
        consultar = dobles.ConsultarLotesDePrueba()
        app_servicios = servicios(proveedor_identidad=proveedor, consultar_lotes=consultar)
        with registros("recibos_service.errores") as errores:
            respuesta = cliente(app_servicios).get("/v1/lotes", headers=autorizacion())
        assert respuesta.status_code == 503
        assert _sobre(respuesta)["Message"] == MENSAJE_DEPENDENCIA
        assert consultar.consultas == []
        eventos = [r.datos for r in errores if r.getMessage() == "dependencia_no_disponible"]
        assert eventos == [{"dependencia": "wso2"}]

    def test_el_esquema_bearer_no_distingue_mayusculas(self) -> None:
        respuesta = cliente().get("/v1/lotes", headers={"Authorization": f"bearer {TOKEN}"})
        assert respuesta.status_code == 200


class TestCargaDeLote:
    def test_lote_procesado_es_201_con_el_resumen(self) -> None:
        procesar = dobles.ProcesarLoteDePrueba()
        app_servicios = servicios(procesar_lote=procesar, segundos=lambda: 321.5)
        respuesta = _cargar(app_servicios, headers={**autorizacion(), "User-Agent": "pruebas"})
        assert respuesta.status_code == 201
        assert _sobre(respuesta) == {
            "Success": True,
            "Status": 201,
            "Message": "Recurso creado con éxito",
            "Data": {
                "id_lote": 1532,
                "tipo_plantilla": "PREGRADO",
                "total_filas": 3,
                "procesados": [{"fila": 4, "codigo": "20271020001"}, {"fila": 5, "codigo": "20271020017"}],
                "rechazados": [
                    {
                        "fila": 6,
                        "codigo": CODIGO_RECHAZADO,
                        "motivo": "ESTADO_NO_PERMITIDO",
                        "mensaje": "El estado del estudiante no permite",
                    }
                ],
            },
        }
        (comando,) = procesar.comandos
        assert comando == CargarLoteComando(
            contenido=CONTENIDO_XLS, nombre_original="lote.xls", usuario=USUARIO_ARC, ip="127.0.0.1", recibida_en=321.5
        )

    def test_el_token_llega_a_la_lectura_de_reglas_y_luego_se_olvida(self) -> None:
        procesar = dobles.ProcesarLoteDePrueba()
        _cargar(servicios(procesar_lote=procesar))
        assert procesar.tokens_vistos == [TOKEN]  # A11
        assert contexto.token_usuario.get() is None

    @pytest.mark.parametrize(
        ("datos", "status", "mensaje"),
        [
            ({}, 400, FALTA_ARCHIVO),
            ({"otro": (io.BytesIO(CONTENIDO_XLS), "lote.xls")}, 400, FALTA_ARCHIVO),
            (archivo(nombre=""), 400, FALTA_ARCHIVO),
            (archivo(nombre="lote\x07.xls"), 400, NOMBRE_INVALIDO),
            (archivo(nombre="a" * 252 + ".xls"), 400, NOMBRE_INVALIDO),
            (archivo(nombre="lote.xlsx"), 415, TIPO_NO_PERMITIDO),
            (archivo(contenido=b"PK\x03\x04" + b"\x00" * 100), 415, TIPO_NO_PERMITIDO),
            (archivo(contenido=b""), 415, TIPO_NO_PERMITIDO),
        ],
    )
    def test_archivo_no_permitido(self, datos: dict[str, object], status: int, mensaje: str) -> None:
        procesar = dobles.ProcesarLoteDePrueba()
        respuesta = _cargar(servicios(procesar_lote=procesar), data=datos)
        assert respuesta.status_code == status
        assert _sobre(respuesta)["Message"] == mensaje
        assert _sobre(respuesta)["Data"] is None
        assert procesar.comandos == []

    def test_textos_del_archivo_no_permitido(self) -> None:
        assert FALTA_ARCHIVO == "Falta el archivo de la plantilla."
        assert NOMBRE_INVALIDO == "El nombre del archivo no es válido."
        assert TIPO_NO_PERMITIDO == "Solo se aceptan plantillas .xls (Excel 97-2003)."

    def test_una_ruta_en_el_nombre_no_llega_al_caso_de_uso(self) -> None:
        procesar = dobles.ProcesarLoteDePrueba()
        respuesta = _cargar(servicios(procesar_lote=procesar), data=archivo(nombre="../../etc/passwd.xls"))
        if respuesta.status_code == 201:  # Werkzeug puede quitar las carpetas antes que el controller
            assert "/" not in procesar.comandos[0].nombre_original
        else:
            assert respuesta.status_code == 400
            assert procesar.comandos == []

    def test_archivo_mas_grande_que_el_maximo_es_413(self) -> None:
        app_servicios = servicios(max_archivo_bytes=1024)
        respuesta = _cargar(app_servicios, data=archivo(contenido=CONTENIDO_XLS + b"\x00" * 1024))
        assert respuesta.status_code == 413
        assert _sobre(respuesta)["Message"] == mensaje_tamano(1024)

    def test_cuerpo_mas_grande_que_el_limite_de_werkzeug_es_413(self) -> None:
        app_servicios = servicios(max_archivo_bytes=1024)
        grande = CONTENIDO_XLS + b"\x00" * (200 * 1024)
        respuesta = _cargar(app_servicios, data=archivo(contenido=grande))
        assert respuesta.status_code == 413
        assert _sobre(respuesta)["Message"] == "El archivo supera el tamaño máximo de 0.000976562 MB."

    def test_tamano_maximo_de_2_mb_en_el_mensaje(self) -> None:
        assert mensaje_tamano(2 * 1024 * 1024) == "El archivo supera el tamaño máximo de 2 MB."

    def test_formato_invalido_es_422_con_el_id_del_lote(self) -> None:
        error = FormatoPlantillaInvalido(1533, "La plantilla de pregrado no es la vigente", {"id_lote": 1533})
        with registros("recibos_service.auditoria") as auditoria:
            respuesta = _cargar(servicios(procesar_lote=dobles.ProcesarLoteDePrueba(error=error)))
        assert respuesta.status_code == 422
        assert _sobre(respuesta) == {
            "Success": False,
            "Status": 422,
            "Message": "La plantilla de pregrado no es la vigente",
            "Data": {"id_lote": 1533},
        }
        assert auditoria[0].auditoria["data"] == {"id_lote": 1533}

    @pytest.mark.parametrize(
        ("error", "status", "mensaje"),
        [
            (RespuestaInvalida(MENSAJE_REGLA), 502, MENSAJE_REGLA),
            (DependenciaNoDisponible("oracle"), 503, MENSAJE_DEPENDENCIA),
        ],
    )
    def test_dependencias(self, error: Exception, status: int, mensaje: str) -> None:
        respuesta = _cargar(servicios(procesar_lote=dobles.ProcesarLoteDePrueba(error=error)))
        assert respuesta.status_code == status
        assert _sobre(respuesta) == {"Success": False, "Status": status, "Message": mensaje, "Data": None}

    def test_error_inesperado_es_500_sin_detalles(self) -> None:
        secreto = "detalle interno 4815162342"
        procesar = dobles.ProcesarLoteDePrueba(error=RuntimeError(secreto))
        with registros("recibos_service.errores") as errores:
            respuesta = _cargar(servicios(procesar_lote=procesar))
        assert respuesta.status_code == 500
        assert _sobre(respuesta) == {"Success": False, "Status": 500, "Message": MENSAJE_INESPERADO, "Data": None}
        assert secreto not in respuesta.get_data(as_text=True)
        (registro,) = [r for r in errores if r.getMessage() == "error_inesperado"]
        assert registro.datos["tipo"] == "RuntimeError"
        assert secreto not in FormateadorJson().format(registro)

    def test_error_de_persistencia_que_escapa_es_500(self) -> None:
        respuesta = _cargar(servicios(procesar_lote=dobles.ProcesarLoteDePrueba(error=ErrorPersistencia())))
        assert respuesta.status_code == 500

    def test_metodo_no_permitido(self) -> None:
        respuesta = cliente().put("/v1/lotes", headers=autorizacion())
        assert respuesta.status_code == 405
        assert _sobre(respuesta)["Message"] == "Método no permitido"


class TestHistorial:
    def test_pagina_con_metadata(self) -> None:
        consultar = dobles.ConsultarLotesDePrueba(lotes=(dobles.lote(),), total=57)
        respuesta = cliente(servicios(consultar_lotes=consultar)).get("/v1/lotes", headers=autorizacion())
        assert respuesta.status_code == 200
        assert _sobre(respuesta) == {
            "Success": True,
            "Status": 200,
            "Message": "Solicitud exitosa",
            "Data": [
                {
                    "id": 1533,
                    "usuario": "79123456",
                    "fecha": "2026-12-01T10:15:00-05:00",
                    "nombre_archivo": "pregrado_2027_1.xls",
                    "ip": "10.20.30.40",
                }
            ],
            "Metadata": {"total": 57, "limit": 20, "offset": 0},
        }
        assert consultar.consultas == [(20, 0)]

    def test_sin_lotes(self) -> None:
        respuesta = cliente().get("/v1/lotes?limit=5&offset=10", headers=autorizacion())
        assert respuesta.status_code == 200
        assert respuesta.get_json()["Data"] == []
        assert respuesta.get_json()["Metadata"] == {"total": 0, "limit": 5, "offset": 10}

    @pytest.mark.parametrize(
        ("consulta", "mensaje"),
        [
            ("limit=0", LIMIT_INVALIDO),
            ("limit=101", LIMIT_INVALIDO),
            ("limit=abc", LIMIT_INVALIDO),
            ("limit=1.5", LIMIT_INVALIDO),
            ("limit=-1", LIMIT_INVALIDO),
            ("limit=123456789", LIMIT_INVALIDO),
            ("offset=-1", OFFSET_INVALIDO),
            ("offset=abc", OFFSET_INVALIDO),
            ("offset=99999999", OFFSET_INVALIDO),
        ],
    )
    def test_parametros_invalidos_son_400(self, consulta: str, mensaje: str) -> None:
        consultar = dobles.ConsultarLotesDePrueba()
        respuesta = cliente(servicios(consultar_lotes=consultar)).get(f"/v1/lotes?{consulta}", headers=autorizacion())
        assert respuesta.status_code == 400
        assert _sobre(respuesta)["Message"] == mensaje
        assert consultar.consultas == []

    def test_textos_de_los_parametros(self) -> None:
        assert LIMIT_INVALIDO == "El parámetro limit debe ser un entero de 1 a 100."
        assert OFFSET_INVALIDO == "El parámetro offset debe ser un entero de 0 o más."

    def test_mysql_caido_es_503(self) -> None:
        consultar = dobles.ConsultarLotesDePrueba(error=DependenciaNoDisponible("mysql"))
        respuesta = cliente(servicios(consultar_lotes=consultar)).get("/v1/lotes", headers=autorizacion())
        assert respuesta.status_code == 503


class TestCabeceras:
    @pytest.mark.parametrize(
        ("ruta", "cabeceras"),
        [
            ("/", {}),
            ("/health", {}),
            ("/v1/lotes", {}),
            ("/v1/lotes", autorizacion()),
            ("/v1/lotes?limit=0", autorizacion()),
            ("/no-existe", {}),
        ],
    )
    def test_cabeceras_de_seguridad_en_todas_las_respuestas(self, ruta: str, cabeceras: dict[str, str]) -> None:
        respuesta = cliente().get(ruta, headers=cabeceras)
        for nombre, valor in CABECERAS.items():
            assert respuesta.headers[nombre] == valor
        assert respuesta.headers["X-Request-Id"]
        if ruta.startswith("/v1/"):
            assert respuesta.headers["Cache-Control"] == "no-store"  # AD-36

    def test_las_nueve_cabeceras_del_contrato(self) -> None:
        # la décima, `Server` vacía, la pone gunicorn.conf.py (tests/test_gunicorn_conf.py)
        assert set(CABECERAS) == {
            "Content-Security-Policy",
            "Cross-Origin-Resource-Policy",
            "Permissions-Policy",
            "Referrer-Policy",
            "Strict-Transport-Security",
            "X-XSS-Protection",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-Permitted-Cross-Domain-Policies",
        }

    def test_request_id_desde_la_traza_del_balanceador(self) -> None:
        respuesta = cliente().get("/health", headers={"X-Amzn-Trace-Id": f"Self=1-1-1;Root={RAIZ_TRAZA};Sampled=0"})
        assert respuesta.headers["X-Request-Id"] == RAIZ_TRAZA

    @pytest.mark.parametrize("traza", ["", "Root=1-xyz", f"Root={RAIZ_TRAZA}" + "a" * 300])
    def test_request_id_generado_si_la_traza_no_sirve(self, traza: str) -> None:
        identificador = cliente().get("/health", headers={"X-Amzn-Trace-Id": traza}).headers["X-Request-Id"]
        assert len(identificador) == 32
        int(identificador, 16)

    def test_el_request_id_vuelve_al_valor_por_defecto(self) -> None:
        cliente().get("/health")
        assert contexto.request_id.get() == "-"


class TestCors:
    @staticmethod
    def _preflight(origen: str) -> Any:
        return cliente().options(
            "/v1/lotes",
            headers={
                "Origin": origen,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

    def test_origen_permitido_sin_token(self) -> None:
        respuesta = self._preflight(ORIGEN)
        assert respuesta.status_code == 200
        assert respuesta.headers["Access-Control-Allow-Origin"] == ORIGEN
        assert "POST" in respuesta.headers["Access-Control-Allow-Methods"]
        assert "Access-Control-Allow-Credentials" not in respuesta.headers

    @pytest.mark.parametrize("origen", ["https://evil.example.com", f"{ORIGEN}.evil.com", "null"])
    def test_origen_no_permitido(self, origen: str) -> None:
        assert "Access-Control-Allow-Origin" not in self._preflight(origen).headers

    def test_expone_el_request_id(self) -> None:
        respuesta = cliente().get("/v1/lotes", headers={**autorizacion(), "Origin": ORIGEN})
        assert respuesta.headers["Access-Control-Allow-Origin"] == ORIGEN
        assert "X-Request-Id" in respuesta.headers["Access-Control-Expose-Headers"]


class TestAuditoria:
    def test_una_linea_por_peticion_con_los_campos_de_utils_oas(self) -> None:
        sentencias = dobles.Sentencias()

        class ProcesarConSql(dobles.ProcesarLoteDePrueba):
            def ejecutar(self, comando: CargarLoteComando) -> ResultadoLote:
                sentencias.textos.extend(["INSERT INTO `solicitudLote` (...) VALUES (...)", "SELECT GET_LOCK(...)"])
                return super().ejecutar(comando)

        app_servicios = servicios(
            procesar_lote=ProcesarConSql(), iniciar_captura_sql=sentencias.iniciar, sentencias_sql=sentencias.sentencias
        )
        cabeceras = {**autorizacion(), "X-Amzn-Trace-Id": f"Root={RAIZ_TRAZA}"}
        with registros("recibos_service.auditoria") as auditoria:
            respuesta = _cargar(app_servicios, headers=cabeceras)
        assert respuesta.status_code == 201
        (registro,) = auditoria
        entrada = registro.auditoria
        assert set(entrada) == CAMPOS_AUDITORIA
        assert entrada["data"] == AUDITORIA
        assert (entrada["status"], entrada["method"], entrada["path"]) == (201, "POST", "/v1/lotes")
        assert (entrada["user"], entrada["trace_id"]) == (USUARIO_ARC.sub, RAIZ_TRAZA)
        assert entrada["app_name"] == "recibos_service"
        assert entrada["sql_statement"] == "INSERT INTO `solicitudLote` (...) VALUES (...); SELECT GET_LOCK(...)"
        linea = FormateadorJson().format(registro)
        assert json.loads(linea)["auditoria"]["status"] == 201
        assert TOKEN not in linea  # NFR-S08
        assert CODIGO_RECHAZADO not in linea  # sin códigos de estudiantes (BR-U02)
        assert sentencias.inicios == 1

    def test_las_peticiones_rechazadas_tambien_se_auditan(self) -> None:
        with registros("recibos_service.auditoria") as auditoria:
            respuesta = cliente().get("/v1/lotes?limit=5", headers={"Authorization": "Bearer otro-token"})
        assert respuesta.status_code == 401
        (registro,) = auditoria
        entrada = registro.auditoria
        assert (entrada["status"], entrada["user"], entrada["query"], entrada["data"]) == (401, "", "limit=5", {})
        assert "otro-token" not in FormateadorJson().format(registro)

    def test_registro_de_acceso_rechazado(self) -> None:
        with registros("recibos_service.errores") as errores:
            cliente().get("/v1/lotes")
        assert [r.datos for r in errores if r.getMessage() == "acceso_rechazado"] == [{"status": 401}]

    def test_los_health_checks_no_dejan_auditoria(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO)
        cliente().get("/health")
        assert not [r for r in caplog.records if r.name == "recibos_service.auditoria"]


def test_noautenticado_por_defecto() -> None:
    assert NoAutenticado().mensaje == "No autorizado"
