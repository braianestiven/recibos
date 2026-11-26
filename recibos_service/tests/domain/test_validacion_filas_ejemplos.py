"""Pruebas de ejemplo de la lectura de celdas y de los datos de la fila (US-06, US-08; BR-F01, BR-D01 a BR-D04)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.domain import mensajes, validacion_filas
from app.domain.modelos import DatosPosgrado, FallaFila, MotivoRechazo, Rechazo, TipoPlantilla
from app.domain.plantillas import POSGRADO_CREDITOS, POSGRADO_SMLV, PREGRADO
from tests import fabricas
from tests.fabricas import HOY, celdas_fecha

CUOTA1, CUOTA2, CUOTA3 = POSGRADO_CREDITOS.columnas_fecha


@pytest.mark.parametrize(("texto", "esperado"), [(None, None), (" 12 ", 12), ("1.0", None), ("-3", None), ("", None)])
def test_leer_entero(texto: str | None, esperado: int | None) -> None:
    assert validacion_filas.leer_entero(texto) == esperado


class TestCodigo:
    def test_valido_sin_espacios(self) -> None:
        assert validacion_filas.validar_codigo(fabricas.fila(c1=" 20271020001 ")) == 20271020001

    def test_falta_el_codigo(self) -> None:
        resultado = validacion_filas.validar_codigo(fabricas.fila(numero=9, c5="x"))
        assert resultado == Rechazo(9, None, MotivoRechazo.CODIGO_INVALIDO, mensajes.FALTA_CODIGO)

    @pytest.mark.parametrize("texto", ["12a", "1234567890123456", "12 34", "+1"])
    def test_invalido(self, texto: str) -> None:
        resultado = validacion_filas.validar_codigo(fabricas.fila(c1=texto))
        assert isinstance(resultado, Rechazo)
        assert resultado.motivo is MotivoRechazo.CODIGO_INVALIDO
        assert resultado.mensaje == mensajes.CODIGO_INVALIDO
        assert resultado.codigo == texto.strip()


class TestUnidad:
    @pytest.mark.parametrize(("texto", "esperado"), [("12", "12"), ("007", "7"), (" 3 ", "3")])
    def test_creditos_validos(self, texto: str, esperado: str) -> None:
        assert validacion_filas.leer_unidad(texto, TipoPlantilla.POSGRADO_CREDITOS) == esperado

    @pytest.mark.parametrize("texto", [None, "0", "1000", "4,5", "x"])
    def test_creditos_invalidos(self, texto: str | None) -> None:
        assert validacion_filas.leer_unidad(texto, TipoPlantilla.POSGRADO_CREDITOS) is None

    @pytest.mark.parametrize(
        ("texto", "esperado"), [("4,50", "4.5"), ("7.00", "7"), ("0,5", "0.5"), ("999.99", "999.99"), ("12", "12")]
    )
    def test_smlv_validos(self, texto: str, esperado: str) -> None:
        assert validacion_filas.leer_unidad(texto, TipoPlantilla.POSGRADO_SMLV) == esperado

    @pytest.mark.parametrize("texto", ["0", "0,00", "4.123", "1000", "-1", "1."])
    def test_smlv_invalidos(self, texto: str) -> None:
        assert validacion_filas.leer_unidad(texto, TipoPlantilla.POSGRADO_SMLV) is None

    def test_formatear_unidad(self) -> None:
        assert validacion_filas.formatear_unidad(Decimal("100")) == "100"
        assert validacion_filas.formatear_unidad(Decimal("4.50")) == "4.5"


class TestFechaOrdinaria:
    terna = (14, 15, 16)

    def test_valida(self) -> None:
        fila = fabricas.fila(c14="15", c15="1", c16="2027")
        assert validacion_filas.leer_fecha_ordinaria(fila, self.terna, None, HOY) == date(2027, 1, 15)

    def test_el_mismo_dia_de_la_carga_vale(self) -> None:
        fila = fabricas.fila(**celdas_fecha(self.terna, HOY))
        assert validacion_filas.leer_fecha_ordinaria(fila, self.terna, None, HOY) == HOY

    def test_falta(self) -> None:
        falla = validacion_filas.leer_fecha_ordinaria(fabricas.fila(c1="1"), self.terna, None, HOY)
        assert falla == FallaFila(MotivoRechazo.FECHA_INVALIDA, mensajes.fecha_faltante(None))

    @pytest.mark.parametrize(
        "celdas",
        [
            {"c14": "31", "c15": "4", "c16": "2027"},
            {"c14": "1", "c15": "2", "c16": "27"},
            {"c14": "1", "c16": "2027"},
            {"c14": "x", "c15": "2", "c16": "2027"},
            {"c14": "29", "c15": "2", "c16": "2027"},
        ],
    )
    def test_no_existe_o_sin_anio_completo(self, celdas: dict[str, str]) -> None:
        falla = validacion_filas.leer_fecha_ordinaria(fabricas.fila(**celdas), self.terna, 2, HOY)
        assert falla == FallaFila(MotivoRechazo.FECHA_INVALIDA, mensajes.fecha_inexistente(2))

    def test_anterior_a_hoy(self) -> None:
        fila = fabricas.fila(c14="3", c15="1", c16="2027")
        falla = validacion_filas.leer_fecha_ordinaria(fila, self.terna, None, HOY)
        assert falla == FallaFila(MotivoRechazo.FECHA_INVALIDA, mensajes.fecha_anterior_a_hoy(None))


def test_fechas_legibles_para_el_rango_de_festivos() -> None:
    pregrado = fabricas.fila(c14="10", c15="2", c16="2027")
    assert validacion_filas.fechas_ordinarias_legibles(pregrado, PREGRADO) == [date(2027, 2, 10)]
    celdas = {**celdas_fecha(CUOTA1, date(2027, 2, 1)), **celdas_fecha(CUOTA2, date(2027, 3, 1))}
    celdas.update({"c24": "31", "c25": "4", "c26": "2027"})
    con_dos_cuotas = fabricas.fila(c3="2", **celdas)
    assert validacion_filas.fechas_ordinarias_legibles(con_dos_cuotas, POSGRADO_CREDITOS) == [
        date(2027, 2, 1),
        date(2027, 3, 1),
    ]
    sin_cuotas_validas = fabricas.fila(c3="x", **celdas)
    assert len(validacion_filas.fechas_ordinarias_legibles(sin_cuotas_validas, POSGRADO_CREDITOS)) == 2


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [(None, (True, None)), ("40", (True, 40)), ("0", (True, 0)), ("101", (False, None)), ("0,6", (False, None))],
)
def test_porcentaje_valido(texto: str | None, esperado: tuple[bool, int | None]) -> None:
    assert validacion_filas.porcentaje_valido(texto) == esperado


class TestPosgrado:
    def _fila(self, **cambios: str) -> dict[str, str]:
        celdas = {"c1": "20271020001", "c2": "12", "c3": "2"}
        celdas.update(celdas_fecha(CUOTA1, date(2027, 2, 1)))
        celdas.update(celdas_fecha(CUOTA2, date(2027, 3, 1)))
        celdas.update(cambios)
        return celdas

    def test_datos_validos(self) -> None:
        datos = validacion_filas.validar_posgrado(fabricas.fila(**self._fila(c27="70")), POSGRADO_CREDITOS, HOY)
        assert datos == DatosPosgrado(2, "12", (date(2027, 2, 1), date(2027, 3, 1)), (70, None))

    def test_cuotas_de_mas_no_se_miran(self) -> None:
        celdas = self._fila(c24="x", c29="500")
        datos = validacion_filas.validar_posgrado(fabricas.fila(**celdas), POSGRADO_CREDITOS, HOY)
        assert isinstance(datos, DatosPosgrado)

    @pytest.mark.parametrize("cuotas", [None, "0", "4", "dos"])
    def test_cuotas_invalidas(self, cuotas: str | None) -> None:
        celdas = self._fila()
        if cuotas is None:
            del celdas["c3"]
        else:
            celdas["c3"] = cuotas
        falla = validacion_filas.validar_posgrado(fabricas.fila(**celdas), POSGRADO_CREDITOS, HOY)
        assert falla == FallaFila(MotivoRechazo.CUOTAS_INVALIDAS, mensajes.CUOTAS_INVALIDAS)

    def test_unidad_invalida_en_creditos_y_en_smlv(self) -> None:
        celdas = self._fila(c2="0")
        assert validacion_filas.validar_posgrado(fabricas.fila(**celdas), POSGRADO_CREDITOS, HOY) == FallaFila(
            MotivoRechazo.UNIDAD_INVALIDA, mensajes.UNIDAD_INVALIDA_CREDITOS
        )
        assert validacion_filas.validar_posgrado(fabricas.fila(**celdas), POSGRADO_SMLV, HOY) == FallaFila(
            MotivoRechazo.UNIDAD_INVALIDA, mensajes.UNIDAD_INVALIDA_SMLV
        )

    def test_fecha_de_la_segunda_cuota_falta(self) -> None:
        celdas = self._fila()
        for clave in ("c21", "c22", "c23"):
            del celdas[clave]
        falla = validacion_filas.validar_posgrado(fabricas.fila(**celdas), POSGRADO_CREDITOS, HOY)
        assert falla == FallaFila(MotivoRechazo.FECHA_INVALIDA, mensajes.fecha_faltante(2))

    def test_cuota_que_vence_antes_que_la_anterior(self) -> None:
        celdas = self._fila(**celdas_fecha(CUOTA2, date(2027, 2, 1)))
        falla = validacion_filas.validar_posgrado(fabricas.fila(**celdas), POSGRADO_CREDITOS, HOY)
        assert falla == FallaFila(MotivoRechazo.FECHA_INVALIDA, mensajes.fecha_fuera_de_orden(2))

    def test_porcentaje_invalido(self) -> None:
        falla = validacion_filas.validar_posgrado(fabricas.fila(**self._fila(c28="0,4")), POSGRADO_CREDITOS, HOY)
        assert falla == FallaFila(MotivoRechazo.PORCENTAJE_INVALIDO, mensajes.porcentaje_invalido(2))

    def test_no_aplica_a_pregrado(self) -> None:
        with pytest.raises(ValueError, match="posgrado"):
            validacion_filas.validar_posgrado(fabricas.fila(c1="1"), PREGRADO, HOY)
