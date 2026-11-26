"""Propiedades de UC-01 y de `Plazo` (business-logic-model.md §9; PBT-03 y PBT-06 orientativa)."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from app.application.presupuesto import Plazo, PlazoVencido
from app.application.procesar_lote import ConfiguracionLote
from app.domain.modelos import MotivoRechazo, Rechazo
from app.domain.plantillas import POSGRADO_CREDITOS
from tests.application import dobles
from tests.application.escenario import Escenario, celdas_posgrado_validas

CODIGOS = st.sampled_from([20271020100 + i for i in range(6)])
SIN_ESTUDIANTE = {MotivoRechazo.CODIGO_INVALIDO, MotivoRechazo.CODIGO_REPETIDO, MotivoRechazo.ESTUDIANTE_NO_ENCONTRADO}
ANTES_DEL_RECORRIDO = {MotivoRechazo.CODIGO_INVALIDO, MotivoRechazo.CODIGO_REPETIDO}


@st.composite
def escenarios(draw: st.DrawFn) -> Escenario:
    """Lote de posgrado con códigos repetidos, inválidos y desconocidos, y solicitudes previas al azar."""
    escenario = Escenario()
    textos = st.one_of(CODIGOS.map(str), st.sampled_from(["x1", "99999999999"]))
    filas = draw(st.lists(textos, min_size=1, max_size=12))
    for i, codigo in enumerate(filas):
        extra = draw(st.sampled_from([{}, {"c15": "x"}, {"c15": "x", "c9": "x"}, {"c3": "7"}]))
        escenario.filas[POSGRADO_CREDITOS.fila_inicial + i] = celdas_posgrado_validas(codigo, **extra)
    for codigo in draw(st.sets(CODIGOS)):
        escenario.agregar_estudiante(codigo, estado=draw(st.sampled_from(["A", "E"])))
    for codigo in draw(st.lists(CODIGOS, max_size=8)):
        escenario.repositorio.agregar(codigo, draw(st.sampled_from([0, 1])))
    return escenario


@given(escenarios())
def test_cada_fila_aparece_una_vez_y_solo_se_cancela_a_los_estudiantes_conocidos(escenario: Escenario) -> None:
    antes = {s.id: (s.codigo_estudiante, s.estado) for s in escenario.repositorio.solicitudes.values()}
    resumen = escenario.ejecutar().resumen
    filas = sorted(escenario.filas)
    assert sorted([p.fila for p in resumen.procesados] + [r.fila for r in resumen.rechazados]) == filas
    assert resumen.total_filas == len(filas)
    conocidos = {p.codigo for p in resumen.procesados} | {
        int(r.codigo) for r in resumen.rechazados if r.codigo and r.motivo not in SIN_ESTUDIANTE
    }
    for id_solicitud, (codigo, estado) in antes.items():
        despues = escenario.repositorio.solicitudes[id_solicitud].estado
        if estado == 1:
            assert despues == 1  # una solicitud impresa nunca cambia
        else:
            assert despues == (2 if codigo in conocidos else 0)
    for codigo in conocidos:  # cada estudiante procesado queda con una sin imprimir como máximo: la nueva
        assert escenario.repositorio.estados_de(codigo).count(0) <= 1
    creadas = {s.codigo_estudiante for s in escenario.repositorio.solicitudes.values() if s.id not in antes}
    assert creadas == {p.codigo for p in resumen.procesados}  # una fila rechazada nunca guarda solicitud


@given(escenarios(), st.integers(1, 12))
def test_desde_que_vence_el_plazo_las_filas_salen_con_tiempo_agotado(escenario: Escenario, sentencias: int) -> None:
    escenario.repositorio.reloj = escenario.reloj
    escenario.repositorio.segundos_por_sentencia = 90.0 / sentencias + 0.001
    resumen = escenario.ejecutar().resumen
    orden = sorted([*resumen.procesados, *resumen.rechazados], key=lambda r: r.fila)
    assert len(orden) == len(escenario.filas)
    vencidas = [r for r in orden if isinstance(r, Rechazo) and r.motivo is MotivoRechazo.TIEMPO_AGOTADO]
    if vencidas:
        posteriores = [r for r in orden if r.fila > vencidas[0].fila]
        assert all(
            isinstance(r, Rechazo) and r.motivo in {MotivoRechazo.TIEMPO_AGOTADO} | ANTES_DEL_RECORRIDO
            for r in posteriores
        )


@given(escenarios(), st.integers(1, 5))
def test_despues_del_corte_ninguna_fila_llega_a_mysql(escenario: Escenario, corte: int) -> None:
    escenario.configuracion = ConfiguracionLote(corte_mysql=corte)
    escenario.repositorio.fallas.conexion_al_bloquear.update(escenario.estudiantes)
    resultado = escenario.ejecutar()
    assert escenario.repositorio.sentencias <= corte
    assert resultado.resumen.procesados == ()
    assert resultado.resumen.total_filas == len(escenario.filas)


@given(st.floats(0, 1000), st.floats(0, 1000), st.floats(0.001, 200))
def test_el_tiempo_para_una_llamada_nunca_es_negativo_ni_mayor_que_lo_que_queda(
    ahora: float, vence: float, maximo: float
) -> None:
    plazo = Plazo(vence, dobles.RelojDePrueba(inicio=ahora).segundos)
    try:
        tiempo = plazo.para(maximo)
    except PlazoVencido:
        assert vence - ahora <= 0
        return
    assert 0 < tiempo <= maximo
    assert tiempo <= vence - ahora


class LotesSucesivos(RuleBasedStateMachine):
    """Lotes uno tras otro sobre las mismas tablas, con "Solicitados" imprimiendo entre ellos (PBT-06).

    Después de cada paso, cada estudiante tiene como máximo una solicitud sin imprimir: la del último lote
    que lo guardó, mientras nadie la imprima (BR-T01, BR-T05, NFR-R02). El bloqueo real de MySQL se prueba
    con la sesión de filas de la infraestructura; aquí se prueba el orden de cancelación y guardado.
    """

    def __init__(self) -> None:
        super().__init__()
        self.repositorio = dobles.RepositorioEnMemoria()
        self.esperadas: dict[int, int] = {}  # código → id de la solicitud sin imprimir que debe quedar

    @rule(codigos=st.lists(CODIGOS, min_size=1, max_size=6), validos=st.sets(CODIGOS))
    def cargar_lote(self, codigos: list[int], validos: set[int]) -> None:
        escenario = Escenario(repositorio=self.repositorio)
        for i, codigo in enumerate(codigos):
            escenario.filas[POSGRADO_CREDITOS.fila_inicial + i] = celdas_posgrado_validas(str(codigo))
        for codigo in set(codigos):
            escenario.agregar_estudiante(codigo, estado="A" if codigo in validos else "E")
        antes = set(self.repositorio.solicitudes)
        resumen = escenario.ejecutar().resumen
        nuevas = {s.codigo_estudiante: s.id for s in self.repositorio.solicitudes.values() if s.id not in antes}
        assert set(nuevas) == {p.codigo for p in resumen.procesados}
        for codigo in set(codigos):  # estudiante conocido: sus anteriores sin imprimir quedaron canceladas
            self.esperadas.pop(codigo, None)
        self.esperadas.update(nuevas)

    @rule(codigo=CODIGOS)
    def solicitados_imprime(self, codigo: int) -> None:
        for guardada in self.repositorio.solicitudes.values():
            if guardada.codigo_estudiante == codigo and guardada.estado == 0:
                guardada.estado = 1
        self.esperadas.pop(codigo, None)

    @invariant()
    def una_sin_imprimir_por_estudiante(self) -> None:
        sin_imprimir: dict[int, int] = {}
        for guardada in self.repositorio.solicitudes.values():
            if guardada.estado == 0:
                assert guardada.codigo_estudiante not in sin_imprimir
                sin_imprimir[guardada.codigo_estudiante] = guardada.id
        assert sin_imprimir == self.esperadas


LotesSucesivos.TestCase.settings = settings(stateful_step_count=8)
TestLotesSucesivos = LotesSucesivos.TestCase
