"""Pruebas de ejemplo de los modelos, los errores, los mensajes y las reglas de liquidación."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.domain import mensajes
from app.domain.errores import ExencionSinPorcentaje, FormatoInvalido, ReglaInvalida
from app.domain.modelos import (
    Cuota,
    FallaFila,
    FechasPago,
    MotivoRechazo,
    Periodo,
    Procesado,
    Rechazo,
    ResumenLote,
    Solicitud,
    TipoPlantilla,
    crear_hoja,
)
from tests import fabricas


def test_tipo_de_plantilla_sabe_si_es_de_posgrado() -> None:
    assert not TipoPlantilla.PREGRADO.es_posgrado
    assert TipoPlantilla.POSGRADO_CREDITOS.es_posgrado
    assert TipoPlantilla.POSGRADO_SMLV.es_posgrado
    assert int(TipoPlantilla.POSGRADO_SMLV) == 3


def test_crear_hoja_descarta_celdas_vacias_y_con_solo_espacios() -> None:
    hoja = crear_hoja({(1, 1): "A", (2, 1): "   ", (2, 2): "", (3, 4): " x "})
    assert hoja.celdas == {(1, 1): "A", (3, 4): " x "}
    assert hoja.valor(3, 4) == " x "
    assert hoja.valor(2, 1) is None
    assert hoja.ultima_fila() == 3
    assert hoja.ultima_columna() == 4
    assert hoja.ultima_columna(hasta_fila=3) == 1


def test_hoja_vacia() -> None:
    hoja = crear_hoja({})
    assert hoja.ultima_fila() == 0
    assert hoja.ultima_columna() == 0


def test_fila_marcada_y_texto() -> None:
    fila = fabricas.fila(numero=7, c1="123", c5="x")
    assert fila.marcada(5)
    assert not fila.marcada(6)
    assert fila.texto(1) == "123"
    assert fila.texto(2) is None


def test_solicitud_y_resumen() -> None:
    fechas = FechasPago(date(2027, 2, 1), date(2027, 2, 9))
    solicitud = Solicitud(
        codigo_estudiante=1,
        codigo_carrera=20,
        periodo=Periodo(2027, 1),
        tipo=TipoPlantilla.POSGRADO_CREDITOS,
        unidad="12",
        cuotas=(Cuota(1, 60, fechas), Cuota(2, 40, fechas)),
        exenciones=(),
        conceptos=(1,),
    )
    assert solicitud.cuota == 2
    resumen = ResumenLote(
        id_lote=9,
        tipo=TipoPlantilla.PREGRADO,
        procesados=(Procesado(5, 1),),
        rechazados=(Rechazo(6, "x", MotivoRechazo.CODIGO_INVALIDO, "m"),),
    )
    assert resumen.total_filas == 2


def test_errores_del_dominio_guardan_su_mensaje() -> None:
    assert FormatoInvalido("m").mensaje == "m"
    error = ReglaInvalida("evento_periodo", "texto")
    assert (error.regla, error.mensaje) == ("evento_periodo", "texto")
    sin = ExencionSinPorcentaje(7, "texto")
    assert sin.id_exencion == 7


def test_mensajes_con_datos_de_la_fila() -> None:
    assert mensajes.codigo_repetido(4) == "El código ya está en la fila 4; solo se procesa la primera vez que aparece."
    assert mensajes.estado_no_permitido("E") == "El estado del estudiante (E) no permite generar el recibo."
    assert mensajes.nivel_no_corresponde("MAESTRIA", TipoPlantilla.PREGRADO) == (
        "El proyecto curricular del estudiante es de MAESTRIA y la plantilla es de pregrado."
    )
    assert "un nivel desconocido" in mensajes.nivel_no_corresponde(" ", TipoPlantilla.POSGRADO_SMLV)
    assert "plantilla es de posgrado" in mensajes.nivel_no_corresponde("PREGRADO", TipoPlantilla.POSGRADO_CREDITOS)
    assert mensajes.fecha_faltante(None) == "Falta la fecha de pago."
    assert mensajes.fecha_faltante(2) == "Cuota 2: falta la fecha de pago."
    assert mensajes.fecha_inexistente(None) == "La fecha de pago no existe o no tiene el año completo."
    assert mensajes.fecha_anterior_a_hoy(1) == "Cuota 1: la fecha de pago es anterior al día de la carga."
    assert mensajes.fecha_fuera_de_orden(3) == "Cuota 3: vence el mismo día o antes que la cuota 2."
    assert mensajes.porcentaje_invalido(2) == "Cuota 2: el porcentaje debe ser un número entero de 0 a 100."
    assert mensajes.porcentajes_no_suman_100(90) == "Los porcentajes de las cuotas deben sumar 100; suman 90."
    assert mensajes.columnas_distintas(TipoPlantilla.POSGRADO_SMLV, "faltan 2") == (
        "La plantilla de posgrado por SMLV no tiene las columnas esperadas: faltan 2."
    )
    assert mensajes.demasiadas_filas(1200, 1000) == (
        "El lote tiene 1200 filas con datos y el máximo es 1000. Divida el archivo."
    )
    assert "regla evento_periodo" in mensajes.regla_invalida("evento_periodo")
    assert "exención 16" in mensajes.exencion_sin_porcentaje(16)
    assert "año 2028" in mensajes.anio_sin_festivos(2028)


def test_codigo_para_reporte_se_recorta_y_puede_faltar() -> None:
    assert mensajes.codigo_para_reporte(fabricas.fila(c2="x")) is None
    assert mensajes.codigo_para_reporte(fabricas.fila(c1="  " + "9" * 40 + " ")) == "9" * 30


def test_rechazo_y_aviso_de_cancelacion() -> None:
    fila = fabricas.fila(numero=8, c1=" 77 ")
    rechazo = mensajes.rechazo(fila, FallaFila(MotivoRechazo.CARRERA_INACTIVA, mensajes.CARRERA_INACTIVA))
    assert rechazo == Rechazo(8, "77", MotivoRechazo.CARRERA_INACTIVA, mensajes.CARRERA_INACTIVA)
    con_aviso = mensajes.con_aviso_de_cancelacion(rechazo)
    assert con_aviso.mensaje == mensajes.CARRERA_INACTIVA + mensajes.AVISO_CANCELACION
    assert con_aviso.motivo is MotivoRechazo.CARRERA_INACTIVA


class TestReglasLiquidacion:
    def test_mapas_por_tipo_de_plantilla(self) -> None:
        reglas = fabricas.reglas_actuales()
        assert reglas.exencion_de_columna(TipoPlantilla.PREGRADO, 6) == 2
        assert reglas.exencion_de_columna(TipoPlantilla.POSGRADO_SMLV, 16) == 16
        assert reglas.exencion_de_columna(TipoPlantilla.PREGRADO, 30) is None
        assert reglas.concepto_de_columna(TipoPlantilla.PREGRADO, 2) == 2
        assert reglas.concepto_de_columna(TipoPlantilla.POSGRADO_CREDITOS, 6) == 4
        assert reglas.ids_de_los_mapas() == frozenset(range(1, 18))
        assert reglas.porcentaje_por_defecto(3, 2) == 30
        assert reglas.porcentaje_exencion(1) == Decimal(10)

    def test_falta_el_porcentaje_de_una_exencion_de_los_mapas(self) -> None:
        reglas = fabricas.reglas_actuales()
        incompletos = {k: v for k, v in fabricas.PORCENTAJES_EXENCION.items() if k != 13}
        with pytest.raises(ExencionSinPorcentaje) as error:
            reglas.con_porcentajes(incompletos)
        assert error.value.id_exencion == 13

    def test_porcentaje_de_una_exencion_desconocida(self) -> None:
        with pytest.raises(ExencionSinPorcentaje):
            fabricas.reglas_actuales().porcentaje_exencion(99)

    @pytest.mark.parametrize(
        ("cambio", "regla"),
        [
            ({"porcentajes_por_defecto": {1: (100,), 2: (60, 30), 3: (40, 30, 30)}}, "porcentajes_por_defecto"),
            ({"porcentajes_por_defecto": {1: (100,), 2: (60, 40)}}, "porcentajes_por_defecto"),
            ({"porcentajes_por_defecto": {1: (100,), 2: (60, 40), 3: (50, 50)}}, "porcentajes_por_defecto"),
            ({"porcentajes_por_defecto": {1: (100,), 2: (110, -10), 3: (40, 30, 30)}}, "porcentajes_por_defecto"),
            ({"dias_fecha_extraordinaria": -1}, "dias_fecha_extraordinaria"),
            ({"estados_permitidos": frozenset()}, "estados_permitidos"),
        ],
    )
    def test_reglas_que_no_sirven(self, cambio: dict[str, object], regla: str) -> None:
        with pytest.raises(ReglaInvalida) as error:
            fabricas.reglas_actuales(**cambio)
        assert error.value.regla == regla
