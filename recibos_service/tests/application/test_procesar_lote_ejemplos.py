"""Pruebas de ejemplo de UC-01 (US-02, US-06, US-09, US-10, US-12, US-15; business-logic-model.md §5)."""

from __future__ import annotations

from datetime import date

import pytest

from app.application.errores import DependenciaNoDisponible, FormatoPlantillaInvalido, RespuestaInvalida
from app.application.presupuesto import PlazoVencido
from app.application.procesar_lote import CargarLoteComando, ConfiguracionLote
from app.domain import mensajes
from app.domain.errores import ReglaInvalida
from app.domain.modelos import MotivoRechazo, Procesado, Rechazo, crear_hoja
from app.domain.plantillas import PREGRADO
from tests.application import dobles
from tests.application.escenario import USUARIO, Escenario, celdas_posgrado_validas

A, B, C = 20271020001, 20271020002, 20271020003


def _escenario_basico() -> Escenario:
    escenario = Escenario()
    escenario.filas = {
        5: celdas_posgrado_validas(str(A)),
        6: {1: "12x", 4: "x"},  # código inválido
        7: celdas_posgrado_validas(str(B), c15="x", c9="x"),  # dos descuentos
        8: celdas_posgrado_validas(str(A)),  # repetido
        9: celdas_posgrado_validas(str(C)),  # no está en Oracle
    }
    escenario.agregar_estudiante(A)
    escenario.agregar_estudiante(B)
    escenario.repositorio.agregar(A, 0)  # sin imprimir: se cancela
    escenario.repositorio.agregar(A, 1)  # ya impreso: no se toca
    escenario.repositorio.agregar(B, 0)
    escenario.repositorio.agregar(C, 0)
    return escenario


def test_lote_con_filas_validas_y_rechazadas() -> None:
    escenario = _escenario_basico()
    resultado = escenario.ejecutar()
    resumen = resultado.resumen
    assert resumen.id_lote == 1
    assert resumen.procesados == (Procesado(5, A),)
    motivos = [(r.fila, r.motivo) for r in resumen.rechazados]
    assert motivos == [
        (6, MotivoRechazo.CODIGO_INVALIDO),
        (7, MotivoRechazo.DESCUENTOS_NO_ACUMULABLES),
        (8, MotivoRechazo.CODIGO_REPETIDO),
        (9, MotivoRechazo.ESTUDIANTE_NO_ENCONTRADO),
    ]
    assert resumen.rechazados[2].mensaje == mensajes.codigo_repetido(5)
    assert resumen.total_filas == 5
    # US-09: se cancelan las sin imprimir de los conocidos, también del rechazado; nunca las de C
    assert escenario.repositorio.estados_de(A) == [2, 1, 0]
    assert escenario.repositorio.estados_de(B) == [2]
    assert escenario.repositorio.estados_de(C) == [0]
    assert escenario.almacenamiento.archivos == {"lotes/2027/01/abc123.xls": b"\xd0\xcf\x11\xe0"}
    lote = escenario.repositorio.lotes[0][1]
    assert (lote.documento_usuario, lote.nombre_original, lote.ip) == ("79123456", "lote.xls", "10.0.0.1")
    assert resultado.auditoria["solicitudes_creadas"] == [5]
    assert resultado.auditoria["solicitudes_canceladas"] == {"estado_anterior": 0, "estado_nuevo": 2, "ids": [1, 3]}
    assert resultado.auditoria["tipo_plantilla"] == "POSGRADO_CREDITOS"
    assert resultado.auditoria["tamano_bytes"] == 4


def test_lote_de_pregrado() -> None:
    escenario = Escenario(espec=PREGRADO)
    escenario.filas = {4: {1: str(A), 2: "x", 14: "1", 15: "2", 16: "2027"}}
    escenario.agregar_estudiante(A, nivel="PREGRADO")
    resumen = escenario.ejecutar().resumen
    assert resumen.procesados == (Procesado(4, A),)
    guardada = escenario.repositorio.solicitudes[1].solicitud
    assert guardada is not None
    assert guardada.conceptos == (1, 19, 2)
    assert guardada.unidad == "0"


@pytest.mark.parametrize(
    ("preparar", "mensaje"),
    [
        (lambda e: setattr(e, "hoja_ilegible", True), mensajes.PLANTILLA_ILEGIBLE),
        (lambda e: e.filas.clear(), mensajes.PLANTILLA_SIN_FILAS),
    ],
)
def test_formato_invalido_deja_el_lote_registrado(preparar: object, mensaje: str) -> None:
    escenario = _escenario_basico()
    preparar(escenario)  # type: ignore[operator]
    with pytest.raises(FormatoPlantillaInvalido) as error:
        escenario.ejecutar()
    assert (error.value.id_lote, error.value.mensaje) == (1, mensaje)
    assert error.value.auditoria["id_lote"] == 1
    assert escenario.repositorio.estados_de(A) == [0, 1]  # nada cancelado


def test_mas_filas_que_el_maximo() -> None:
    escenario = _escenario_basico()
    escenario.configuracion = ConfiguracionLote(max_filas=3)
    with pytest.raises(FormatoPlantillaInvalido) as error:
        escenario.ejecutar()
    assert error.value.mensaje == mensajes.demasiadas_filas(5, 3)


def test_plantilla_no_reconocida() -> None:
    escenario = _escenario_basico()
    caso = escenario.caso_de_uso()
    caso._lector = dobles.LectorEnMemoria(crear_hoja({(1, 1): "OTRA"}))
    with pytest.raises(FormatoPlantillaInvalido) as error:
        caso.ejecutar(CargarLoteComando(b"x", "a.xls", USUARIO, "1.1.1.1", escenario.reloj.t))
    assert error.value.mensaje == mensajes.PLANTILLA_NO_RECONOCIDA


class TestDependencias:
    def test_regla_invalida_es_502_y_no_registra_nada(self) -> None:
        escenario = _escenario_basico()
        escenario.reglas.error = ReglaInvalida("evento_periodo", mensajes.regla_invalida("evento_periodo"))
        with pytest.raises(RespuestaInvalida) as error:
            escenario.ejecutar()
        assert "evento_periodo" in error.value.mensaje
        assert not escenario.repositorio.lotes
        assert not escenario.almacenamiento.archivos

    def test_parametros_no_responde_es_503(self) -> None:
        escenario = _escenario_basico()
        escenario.reglas.error = dobles.dependencia_caida("parametros")
        with pytest.raises(DependenciaNoDisponible):
            escenario.ejecutar()

    def test_falta_el_porcentaje_de_una_exencion(self) -> None:
        escenario = _escenario_basico()
        del escenario.repositorio.porcentajes[13]
        with pytest.raises(RespuestaInvalida) as error:
            escenario.ejecutar()
        assert error.value.mensaje == mensajes.exencion_sin_porcentaje(13)

    def test_mysql_no_responde_al_leer_porcentajes_o_registrar(self) -> None:
        escenario = _escenario_basico()
        escenario.repositorio.error_porcentajes = True
        with pytest.raises(DependenciaNoDisponible):
            escenario.ejecutar()
        escenario = _escenario_basico()
        escenario.repositorio.error_registro = True
        with pytest.raises(DependenciaNoDisponible):
            escenario.ejecutar()
        assert escenario.almacenamiento.archivos  # el archivo queda en S3 y lo borra la retención

    def test_s3_no_responde(self) -> None:
        escenario = _escenario_basico()
        escenario.almacenamiento.error = dobles.dependencia_caida("s3")
        with pytest.raises(DependenciaNoDisponible):
            escenario.ejecutar()
        assert not escenario.repositorio.lotes

    def test_oracle_no_responde_deja_el_lote_sin_solicitudes(self) -> None:
        escenario = _escenario_basico()
        escenario.academico_error = dobles.dependencia_caida("oracle")
        with pytest.raises(DependenciaNoDisponible):
            escenario.ejecutar()
        assert escenario.repositorio.lotes
        assert escenario.repositorio.estados_de(A) == [0, 1]

    def test_anio_sin_festivos_es_502(self) -> None:
        escenario = _escenario_basico()
        escenario.festivos.dias = frozenset({date(2026, 1, 1)})
        with pytest.raises(RespuestaInvalida) as error:
            escenario.ejecutar()
        assert error.value.mensaje == mensajes.anio_sin_festivos(2027)
        assert escenario.festivos.rangos == [(date(2027, 1, 1), date(2027, 12, 31))]

    def test_se_acaba_el_presupuesto_durante_las_lecturas_de_oracle(self) -> None:
        escenario = _escenario_basico()
        escenario.academico_error = PlazoVencido()
        with pytest.raises(DependenciaNoDisponible) as error:
            escenario.ejecutar()
        assert error.value.dependencia == "presupuesto_previo"

    def test_sin_fechas_legibles_no_se_consultan_festivos(self) -> None:
        escenario = Escenario()
        escenario.filas = {5: {1: str(A), 2: "12", 3: "1", 18: "x", 19: "2", 20: "2027"}}
        escenario.agregar_estudiante(A)
        resumen = escenario.ejecutar().resumen
        assert resumen.rechazados[0].motivo is MotivoRechazo.FECHA_INVALIDA
        assert escenario.festivos.rangos == []

    def test_se_acaba_el_presupuesto_de_la_fase_previa(self) -> None:
        escenario = _escenario_basico()
        escenario.reloj.paso = 20.0  # cada lectura del reloj suma 20 s
        with pytest.raises(DependenciaNoDisponible) as error:
            escenario.ejecutar()
        assert error.value.dependencia == "presupuesto_previo"
        assert not escenario.almacenamiento.archivos


class TestFilas:
    def test_plazo_del_lote_mas_corto_que_la_fase_previa(self) -> None:
        escenario = _escenario_basico()
        escenario.configuracion = ConfiguracionLote(limite_lote_s=0.0001)
        with pytest.raises(DependenciaNoDisponible):
            escenario.ejecutar()

    def test_tiempo_agotado_en_las_filas(self) -> None:
        escenario = Escenario()
        escenario.filas = {5: celdas_posgrado_validas(str(A)), 6: celdas_posgrado_validas(str(B))}
        escenario.agregar_estudiante(A)
        escenario.agregar_estudiante(B)
        escenario.repositorio.agregar(B, 0)
        # cada sentencia de MySQL tarda 30 s: la fila 5 usa los 90 s y la fila 6 ya no empieza
        escenario.repositorio.reloj = escenario.reloj
        escenario.repositorio.segundos_por_sentencia = 30.0
        resumen = escenario.ejecutar().resumen
        assert resumen.procesados == (Procesado(5, A),)
        assert resumen.rechazados == (
            Rechazo(6, str(B), MotivoRechazo.TIEMPO_AGOTADO, mensajes.TIEMPO_AGOTADO),
        )
        assert escenario.repositorio.estados_de(B) == [0]  # no se canceló nada

    def test_plazo_vence_a_mitad_de_la_fila(self) -> None:
        escenario = _escenario_basico()
        escenario.repositorio.fallas.plazo_al_guardar.add(A)
        escenario.repositorio.fallas.plazo_al_cancelar.add(B)
        resumen = escenario.ejecutar().resumen
        por_fila = {r.fila: r for r in resumen.rechazados}
        assert por_fila[5].motivo is MotivoRechazo.ERROR_GUARDADO  # ya había cancelado
        assert escenario.repositorio.estados_de(A) == [2, 1]
        assert por_fila[7].motivo is MotivoRechazo.TIEMPO_AGOTADO  # no alcanzó a cancelar
        assert escenario.repositorio.estados_de(B) == [0]

    def test_bloqueo_que_no_llega(self) -> None:
        escenario = _escenario_basico()
        escenario.repositorio.fallas.bloqueo_no_llega.update({A, B})
        resumen = escenario.ejecutar().resumen
        por_fila = {r.fila: r for r in resumen.rechazados}
        assert por_fila[5].motivo is MotivoRechazo.ERROR_GUARDADO
        assert por_fila[7].motivo is MotivoRechazo.DESCUENTOS_NO_ACUMULABLES
        assert por_fila[7].mensaje.endswith(mensajes.AVISO_CANCELACION)
        assert escenario.repositorio.estados_de(A) == [0, 1]

    def test_falla_al_guardar_mantiene_la_cancelacion(self) -> None:
        escenario = _escenario_basico()
        escenario.repositorio.fallas.guardado.add(A)
        resultado = escenario.ejecutar()
        esperado = Rechazo(5, str(A), MotivoRechazo.ERROR_GUARDADO, mensajes.ERROR_GUARDADO)
        assert resultado.resumen.rechazados[0] == esperado
        assert escenario.repositorio.estados_de(A) == [2, 1]
        assert resultado.auditoria["solicitudes_creadas"] == []

    def test_falla_de_la_cancelacion_en_una_fila_valida(self) -> None:
        escenario = _escenario_basico()
        escenario.repositorio.fallas.cancelacion.add(A)
        resumen = escenario.ejecutar().resumen
        assert resumen.rechazados[0].motivo is MotivoRechazo.ERROR_GUARDADO
        assert escenario.repositorio.estados_de(A) == [0, 1]

    def test_corte_despues_de_cinco_fallas_de_conexion_seguidas(self) -> None:
        escenario = Escenario()
        codigos = [20271020100 + i for i in range(8)]
        escenario.filas = {5 + i: celdas_posgrado_validas(str(c)) for i, c in enumerate(codigos)}
        for codigo in codigos:
            escenario.agregar_estudiante(codigo)
        escenario.repositorio.fallas.conexion_al_bloquear.update(codigos[:6])
        resultado = escenario.ejecutar()
        motivos = [r.motivo for r in resultado.resumen.rechazados]
        assert motivos == [MotivoRechazo.ERROR_GUARDADO] * 8
        # las 5 primeras intentaron; las 3 siguientes no tocaron MySQL
        assert escenario.repositorio.sentencias == 5

    def test_una_falla_que_no_es_de_conexion_reinicia_la_cuenta(self) -> None:
        escenario = Escenario()
        codigos = [20271020100 + i for i in range(7)]
        escenario.filas = {5 + i: celdas_posgrado_validas(str(c)) for i, c in enumerate(codigos)}
        for codigo in codigos:
            escenario.agregar_estudiante(codigo)
        escenario.repositorio.fallas.conexion_al_bloquear.update(codigos[:4] + codigos[5:])
        escenario.repositorio.fallas.bloqueo_no_llega.add(codigos[4])
        escenario.ejecutar()
        assert escenario.repositorio.sentencias == 7  # nunca hubo 5 fallas de conexión seguidas

    def test_conexion_perdida_al_guardar_cuenta_para_el_corte(self) -> None:
        escenario = Escenario()
        escenario.filas = {5: celdas_posgrado_validas(str(A))}
        escenario.agregar_estudiante(A)
        escenario.repositorio.fallas.conexion_al_guardar.add(A)
        resumen = escenario.ejecutar().resumen
        assert resumen.rechazados[0].motivo is MotivoRechazo.ERROR_GUARDADO

    def test_sin_filas_a_procesar_no_abre_la_sesion_de_mysql(self) -> None:
        escenario = Escenario()
        escenario.filas = {5: {1: "abc"}, 6: {1: "", 2: "12"}}
        resumen = escenario.ejecutar().resumen
        assert [r.motivo for r in resumen.rechazados] == [MotivoRechazo.CODIGO_INVALIDO] * 2
        assert escenario.repositorio.sesiones == 0
