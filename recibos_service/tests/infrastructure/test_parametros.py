"""Reglas desde "parametros": sobre, conversión del valor (AD-21, AD-22), paralelismo, plazo y token (A11)."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from dataclasses import replace
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.application import contexto
from app.application.errores import DependenciaNoDisponible, RespuestaInvalida
from app.application.presupuesto import Plazo, PlazoVencido
from app.domain import mensajes
from app.domain.errores import ReglaInvalida
from app.infrastructure.http import RespuestaHttp
from app.infrastructure.parametros.fuente_reglas import FuenteReglasParametros, ReglasMalConfiguradas
from app.infrastructure.parametros.modelos import (
    FORMAS,
    FORMATOS_POR_FORMA,
    EspecificacionParametro,
    RespuestaParametros,
    convertir,
    dar_forma,
    problemas_de_configuracion,
)
from tests import fabricas
from tests.interfaces.dobles import registros
from tests.test_conf import FORMATO_POR_FORMA

URL = "https://parametros.portaloas.udistrital.edu.co"
ESPECIFICACIONES = {
    regla: EspecificacionParametro(i, "CodigoAbreviacion", FORMATO_POR_FORMA[forma])  # type: ignore[arg-type]
    for i, (regla, forma) in enumerate(FORMAS.items(), start=101)
}
VALORES = {
    "estados_permitidos": "V, J, T, A, Q, B",
    "estados_terminacion": "T,H,",
    "evento_periodo": "80",
    "evento_terminacion": " 82 ",
    "proyectos_excluidos": "0, 999",
    "nivel_pregrado": "PREGRADO",
    "niveles_posgrado": "POSGRADO, ESPECIALIZACION, MAESTRIA, DOCTORADO",
    "concepto_matricula": "1",
    "concepto_exclusivo_pregrado": "19",
    "conceptos_columna_pregrado": '{"2": 2, "3": 3, "4": 4}',
    "conceptos_columna_posgrado": '{"4": 2, "5": 3, "6": 4}',
    "exenciones_columna_pregrado": json.dumps({str(c): e for c, e in fabricas.EXENCIONES_PREGRADO.items()}),
    "exenciones_columna_posgrado": json.dumps({str(c): e for c, e in fabricas.EXENCIONES_POSGRADO.items()}),
    "id_exencion_votacion": "1",
    "id_exencion_secretaria": "16",
    "porcentajes_por_defecto": '{"1": [100], "2": [60, 40], "3": [40, 30, 30]}',
    "dias_fecha_extraordinaria": "8",
}
ESPERADAS = replace(fabricas.reglas_actuales(), porcentaje_por_exencion={})


def sobre(id_parametro: int, valor: object, **cambios: object) -> RespuestaHttp:
    """Respuesta de `GET /v1/parametro/{id}` como la del ejemplo del usuario (sobre CRUD)."""
    datos: dict[str, Any] = {
        "Id": id_parametro,
        "Nombre": "regla",
        "Descripcion": "",
        "CodigoAbreviacion": valor,
        "Activo": True,
        "NumeroOrden": 0,
        "FechaCreacion": "2020-12-15 14:52:59.75962 +0000 +0000",
        "FechaModificacion": "2020-12-15 14:52:59.759703 +0000 +0000",
        "TipoParametroId": {"Id": 3},
        "ParametroPadreId": None,
    }
    datos.update(cambios.pop("datos", {}))  # type: ignore[call-overload]
    cuerpo = {"Success": True, "Status": "200", "Message": "Request successful", "Data": datos, **cambios}
    return RespuestaHttp(200, json.dumps(cuerpo).encode())


class ClienteParametros:
    def __init__(self, respuestas: dict[int, RespuestaHttp | Exception] | None = None, demora: float = 0.0) -> None:
        self.respuestas: dict[int, RespuestaHttp | Exception] = {
            espec.id: sobre(espec.id, VALORES[regla]) for regla, espec in ESPECIFICACIONES.items()
        }
        self.respuestas.update(respuestas or {})
        self.demora = demora
        self.llamadas: list[tuple[str, dict[str, str], float, float, str]] = []
        self._candado = threading.Lock()

    def obtener(
        self, url: str, cabeceras: dict[str, str], conectar: float, responder: float, dependencia: str
    ) -> RespuestaHttp:
        with self._candado:
            self.llamadas.append((url, dict(cabeceras), conectar, responder, dependencia))
        if self.demora:
            time.sleep(self.demora)
        respuesta = self.respuestas[int(url.rsplit("/", 1)[1])]
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


@pytest.fixture
def fuentes() -> Iterator[list[FuenteReglasParametros]]:
    creadas: list[FuenteReglasParametros] = []
    yield creadas
    for fuente in creadas:
        if fuente._grupo is not None:
            fuente._grupo.shutdown(wait=False, cancel_futures=True)


def _fuente(fuentes: list[FuenteReglasParametros], cliente: ClienteParametros) -> FuenteReglasParametros:
    fuente = FuenteReglasParametros(URL + "/", ESPECIFICACIONES, cliente)  # type: ignore[arg-type]
    fuentes.append(fuente)
    return fuente


def _plazo(segundos: float = 30.0) -> Plazo:
    return Plazo(time.monotonic() + segundos, time.monotonic)


def _id(regla: str) -> int:
    return ESPECIFICACIONES[regla].id


class TestFuenteReglas:
    def test_las_17_reglas_con_el_token_del_usuario(self, fuentes: list[FuenteReglasParametros]) -> None:
        cliente = ClienteParametros()
        marca = contexto.token_usuario.set("token-del-usuario")
        try:
            reglas = _fuente(fuentes, cliente).obtener(_plazo())
        finally:
            contexto.token_usuario.reset(marca)
        assert reglas == ESPERADAS
        assert sorted(url for url, *_ in cliente.llamadas) == sorted(
            f"{URL}/v1/parametro/{espec.id}" for espec in ESPECIFICACIONES.values()
        )
        for _url, cabeceras, conectar, responder, dependencia in cliente.llamadas:
            assert cabeceras == {"Accept": "application/json", "Authorization": "Bearer token-del-usuario"}
            assert 0 < conectar <= 2.0
            assert 0 < responder <= 3.0
            assert dependencia == "parametros"

    def test_sin_token_no_envia_authorization(self, fuentes: list[FuenteReglasParametros]) -> None:
        cliente = ClienteParametros()
        _fuente(fuentes, cliente).obtener(_plazo())
        assert all("Authorization" not in cabeceras for _u, cabeceras, *_ in cliente.llamadas)

    @pytest.mark.parametrize(
        ("regla", "respuesta"),
        [
            ("evento_periodo", sobre(_id("evento_periodo"), "80", datos={"Activo": False})),
            ("evento_periodo", sobre(999, "80")),
            ("evento_periodo", sobre(_id("evento_periodo"), "80", Success=False)),
            ("evento_periodo", sobre(_id("evento_periodo"), "80", Status="500")),
            ("evento_periodo", sobre(_id("evento_periodo"), "80", Data=None)),
            ("evento_periodo", sobre(_id("evento_periodo"), "ochenta")),
            ("nivel_pregrado", sobre(_id("nivel_pregrado"), "   ")),
            ("porcentajes_por_defecto", sobre(_id("porcentajes_por_defecto"), "{no es json")),
            ("conceptos_columna_pregrado", sobre(_id("conceptos_columna_pregrado"), '{"x": 2}')),
            ("evento_periodo", RespuestaHttp(404, b"")),
            ("evento_periodo", RespuestaHttp(200, b"<html></html>")),
            ("evento_periodo", RespuestaHttp(401, b"{}")),
        ],
    )
    def test_regla_que_no_sirve_es_502_y_la_nombra(
        self, fuentes: list[FuenteReglasParametros], regla: str, respuesta: RespuestaHttp
    ) -> None:
        cliente = ClienteParametros({_id(regla): respuesta})
        with registros("app.infrastructure.parametros.fuente_reglas") as eventos, pytest.raises(
            RespuestaInvalida
        ) as error:
            _fuente(fuentes, cliente).obtener(_plazo())
        assert error.value.mensaje == mensajes.regla_invalida(regla)
        assert [e.datos for e in eventos] == [{"regla": regla, "status": respuesta.status}]

    def test_el_error_nombra_la_primera_regla_en_orden(self, fuentes: list[FuenteReglasParametros]) -> None:
        cliente = ClienteParametros(
            {_id("dias_fecha_extraordinaria"): RespuestaHttp(404, b""), _id("estados_terminacion"): RespuestaHttp(404, b"")}
        )
        with pytest.raises(RespuestaInvalida) as error:
            _fuente(fuentes, cliente).obtener(_plazo())
        assert error.value.mensaje == mensajes.regla_invalida("estados_terminacion")

    @pytest.mark.parametrize(
        "respuesta", [RespuestaHttp(503, b""), RespuestaHttp(500, b"{}"), DependenciaNoDisponible("parametros")]
    )
    def test_parametros_no_responde_es_503(
        self, fuentes: list[FuenteReglasParametros], respuesta: RespuestaHttp | Exception
    ) -> None:
        cliente = ClienteParametros({_id("evento_periodo"): respuesta})
        with pytest.raises(DependenciaNoDisponible) as error:
            _fuente(fuentes, cliente).obtener(_plazo())
        assert error.value.dependencia == "parametros"

    def test_valor_que_no_cumple_las_reglas_del_dominio(self, fuentes: list[FuenteReglasParametros]) -> None:
        porcentajes = '{"1": [100], "2": [50, 40], "3": [40, 30, 30]}'
        cliente = ClienteParametros({_id("porcentajes_por_defecto"): sobre(_id("porcentajes_por_defecto"), porcentajes)})
        with pytest.raises(ReglaInvalida) as error:
            _fuente(fuentes, cliente).obtener(_plazo())
        assert error.value.regla == "porcentajes_por_defecto"

    def test_las_reglas_juntas_no_pasan_del_plazo(self, fuentes: list[FuenteReglasParametros]) -> None:
        cliente = ClienteParametros(demora=0.6)
        inicio = time.monotonic()
        with pytest.raises(DependenciaNoDisponible) as error:
            _fuente(fuentes, cliente).obtener(_plazo(0.2))
        assert error.value.dependencia == "parametros"
        assert time.monotonic() - inicio < 0.5

    def test_sin_tiempo_no_llama(self, fuentes: list[FuenteReglasParametros]) -> None:
        cliente = ClienteParametros()
        with pytest.raises(PlazoVencido):
            _fuente(fuentes, cliente).obtener(_plazo(-1.0))
        assert cliente.llamadas == []

    def test_plazo_vencido_al_empezar_una_llamada(self, fuentes: list[FuenteReglasParametros]) -> None:
        cliente = ClienteParametros()
        fuente = _fuente(fuentes, cliente)
        especificacion = ESPECIFICACIONES["evento_periodo"]
        with pytest.raises(DependenciaNoDisponible):
            fuente._leer("evento_periodo", especificacion, {}, Plazo(0.0, lambda: 1.0))
        assert cliente.llamadas == []

    def test_un_grupo_de_hilos_por_proceso(self, fuentes: list[FuenteReglasParametros]) -> None:
        fuente = _fuente(fuentes, ClienteParametros())
        assert fuente._grupo is None  # se crea la primera vez que se usa
        fuente.obtener(_plazo())
        grupo = fuente._grupo
        fuente.obtener(_plazo())
        assert fuente._grupo is grupo
        assert grupo is not None
        assert grupo._max_workers == 8

    def test_configuracion_incompleta(self) -> None:
        especificaciones = {r: e for r, e in ESPECIFICACIONES.items() if r != "evento_periodo"}
        with pytest.raises(ReglasMalConfiguradas) as error:
            FuenteReglasParametros(URL, especificaciones, ClienteParametros())  # type: ignore[arg-type]
        assert error.value.problemas == ["falta evento_periodo"]


class TestConfiguracionDeReglas:
    def test_configuracion_completa(self) -> None:
        assert problemas_de_configuracion(ESPECIFICACIONES) == []

    def test_problemas(self) -> None:
        especificaciones = dict(ESPECIFICACIONES)
        del especificaciones["evento_periodo"]
        especificaciones["sobrante"] = EspecificacionParametro(1, "Nombre", "texto")
        especificaciones["nivel_pregrado"] = EspecificacionParametro(2, "NumeroOrden", "texto")
        especificaciones["porcentajes_por_defecto"] = EspecificacionParametro(3, "Descripcion", "lista")
        especificaciones["dias_fecha_extraordinaria"] = EspecificacionParametro(4, "NumeroOrden", "entero")
        assert problemas_de_configuracion(especificaciones) == [
            "falta evento_periodo",
            "sobra sobrante",
            "campo de nivel_pregrado",
            "formato de porcentajes_por_defecto",
        ]


class TestConversion:
    @pytest.mark.parametrize(
        ("crudo", "formato", "forma", "esperado"),
        [
            (" 80 ", "entero", "entero", 80),
            (82, "entero", "entero", 82),
            (82.0, "entero", "entero", 82),
            ("8", "json", "entero", 8),
            ("PREGRADO", "texto", "texto", "PREGRADO"),
            ('"PREGRADO "', "json", "texto", "PREGRADO"),
            ("V, J,,T,", "lista", "conjunto_textos", frozenset({"V", "J", "T"})),
            ('["T", "H"]', "json", "conjunto_textos", frozenset({"T", "H"})),
            ("0, 999", "lista_enteros", "conjunto_enteros", frozenset({0, 999})),
            ("[]", "json", "conjunto_enteros", frozenset()),
            ('{"2": 2, "13": 9}', "json", "mapa_columnas", {2: 2, 13: 9}),
            ('{"1": [100], "2": [60, 40]}', "json", "porcentajes", {1: (100,), 2: (60, 40)}),
        ],
    )
    def test_valores_validos(self, crudo: Any, formato: Any, forma: Any, esperado: object) -> None:
        assert dar_forma(convertir(crudo, formato), forma) == esperado

    @pytest.mark.parametrize(
        ("crudo", "formato", "forma"),
        [
            ("", "texto", "texto"),
            ("x" * 9000, "texto", "texto"),
            ("8.0", "entero", "entero"),
            ("-1", "entero", "entero"),
            ("1e3", "entero", "entero"),
            (82.5, "entero", "entero"),
            (True, "entero", "entero"),
            (82, "texto", "texto"),
            ("-3", "json", "entero"),
            ("true", "json", "entero"),
            ("[1]", "json", "texto"),
            (",,", "lista", "conjunto_textos"),
            ("[]", "json", "conjunto_textos"),
            ('["T", 3]', "json", "conjunto_textos"),
            ('"T"', "json", "conjunto_textos"),
            ("0,x", "lista_enteros", "conjunto_enteros"),
            ("{}", "json", "mapa_columnas"),
            ('{"0": 1}', "json", "mapa_columnas"),
            ('{"257": 1}', "json", "mapa_columnas"),
            ('{"a": 1}', "json", "mapa_columnas"),
            ('{"2": -1}', "json", "mapa_columnas"),
            ('{"2": "2"}', "json", "mapa_columnas"),
            ("[[2, 2]]", "json", "mapa_columnas"),
            ('{"1": 100}', "json", "porcentajes"),
            ("{no es json", "json", "porcentajes"),
        ],
    )
    def test_valores_que_no_sirven(self, crudo: Any, formato: Any, forma: Any) -> None:
        with pytest.raises(ValueError):  # noqa: PT011 - cualquier ValueError se convierte en un 502 que nombra la regla
            dar_forma(convertir(crudo, formato), forma)

    @pytest.mark.parametrize(
        ("status", "exito", "esperado"),
        [("200", True, True), (201, True, True), (" 204 ", True, True), ("500", True, False), ("abc", True, False)],
    )
    def test_sobre_exitoso(self, status: object, exito: bool, esperado: bool) -> None:
        sobre_crud = RespuestaParametros.model_validate({"Success": exito, "Status": status, "Data": None})
        assert sobre_crud.exitosa() is esperado
        assert RespuestaParametros.model_validate({"Success": False, "Status": "200"}).exitosa() is False


SIN_SEPARADORES = st.characters(blacklist_categories=("Z", "C"), blacklist_characters=",")
VALORES_POR_FORMA: dict[str, st.SearchStrategy[Any]] = {
    "entero": st.integers(0, 10**18 - 1),
    "texto": st.text(min_size=1, max_size=50).map(str.strip).filter(bool),
    "conjunto_textos": st.frozensets(st.text(SIN_SEPARADORES, min_size=1, max_size=10), min_size=1, max_size=8),
    "conjunto_enteros": st.frozensets(st.integers(0, 10**9), min_size=1, max_size=8),
    "mapa_columnas": st.dictionaries(st.integers(1, 256), st.integers(0, 10**6), min_size=1, max_size=20),
    "porcentajes": st.dictionaries(
        st.integers(1, 256), st.lists(st.integers(0, 100), max_size=3).map(tuple), min_size=1, max_size=5
    ),
}


def codificar(valor: Any, forma: str, formato: str) -> str:
    """Cómo se escribiría el valor en el campo del parámetro, en cada formato que admite su tipo."""
    if formato == "entero":
        return str(valor)
    if formato == "texto":
        return valor  # type: ignore[no-any-return]
    if formato in {"lista", "lista_enteros"}:
        return ",".join(str(v) for v in sorted(valor))
    if forma in {"conjunto_textos", "conjunto_enteros"}:
        return json.dumps(sorted(valor))
    if forma in {"mapa_columnas", "porcentajes"}:
        return json.dumps({str(k): list(v) if isinstance(v, tuple) else v for k, v in valor.items()})
    return json.dumps(valor)


@given(st.data())
def test_ida_y_vuelta_de_cada_tipo_en_cada_formato(datos: st.DataObject) -> None:
    forma = datos.draw(st.sampled_from(sorted(FORMATOS_POR_FORMA)))
    valor = datos.draw(VALORES_POR_FORMA[forma])
    for formato in sorted(FORMATOS_POR_FORMA[forma]):  # type: ignore[index]
        assert dar_forma(convertir(codificar(valor, forma, formato), formato), forma) == valor  # type: ignore[arg-type]
