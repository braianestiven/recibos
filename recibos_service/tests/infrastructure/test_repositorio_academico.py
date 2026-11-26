"""Oracle: lecturas en bloque, `call_timeout` según el plazo y errores (AD-06, AD-34; BR-L12)."""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from sqlalchemy.dialects.oracle import oracledb as dialecto_oracledb

from app.application.errores import DependenciaNoDisponible
from app.application.presupuesto import Plazo, PlazoVencido
from app.domain.modelos import ContextoCarrera, Estudiante, Periodo
from app.infrastructure.oracle.repositorio_academico import (
    SQL_CARRERAS,
    SQL_CERTIFICADOS,
    SQL_ESTUDIANTES,
    SQL_PERIODOS,
    RepositorioAcademicoOracle,
    bloques,
    unico,
)
from tests.infrastructure.bd_falsa import Motor, Resultado, error_oracle
from tests.interfaces.dobles import registros


def _repositorio(motor: Motor) -> RepositorioAcademicoOracle:
    return RepositorioAcademicoOracle(motor)  # type: ignore[arg-type]


def _plazo(motor: Motor, restante: float = 100.0) -> Plazo:
    return Plazo(motor.tiempo + restante, motor.reloj)


class TestEstudiantes:
    def test_en_bloques_de_1000_con_call_timeout(self) -> None:
        codigos = list(range(20271000000, 20271002500))

        def responder(_texto: str, parametros: Any) -> Resultado:
            return Resultado(filas=[(c, " A ", 20, 1 if c % 2 else 0) for c in parametros["codigos"][:2]])

        motor = Motor(responder)
        estudiantes = _repositorio(motor).estudiantes(codigos, _plazo(motor))
        assert [len(s.parametros["codigos"]) for s in motor.sentencias] == [1000, 1000, 500]
        assert [s.call_timeout for s in motor.sentencias] == [20_000, 20_000, 20_000]
        assert {s.conexion for s in motor.sentencias} == {1}
        assert estudiantes[20271000000] == Estudiante(20271000000, "A", 20, tiene_valor_matricula=False)
        assert estudiantes[20271000001] == Estudiante(20271000001, "A", 20, tiene_valor_matricula=True)
        assert len(estudiantes) == 6

    def test_call_timeout_con_lo_que_queda_del_plazo(self) -> None:
        motor = Motor()
        _repositorio(motor).estudiantes([1], _plazo(motor, restante=3.25))
        assert motor.sentencias[0].call_timeout == 3250

    def test_nunca_queda_sin_limite(self) -> None:
        motor = Motor()
        _repositorio(motor).estudiantes([1], _plazo(motor, restante=0.0004))
        assert motor.sentencias[0].call_timeout == 1  # 0 sería sin límite en python-oracledb

    def test_el_plazo_vence_entre_bloques(self) -> None:
        motor = Motor()
        motor.segundos_por_sentencia = 2.0
        with pytest.raises(PlazoVencido):
            _repositorio(motor).estudiantes(list(range(3000)), _plazo(motor, restante=3.0))
        assert len(motor.sentencias) == 2
        assert motor.eventos == ["connect 1", "close 1"]  # la conexión vuelve al pool: no salió nada más

    def test_sin_codigos_no_consulta(self) -> None:
        motor = Motor()
        assert _repositorio(motor).estudiantes([], _plazo(motor)) == {}
        assert motor.eventos == []

    def test_error_de_oracle(self) -> None:
        motor = Motor(lambda _t, _p: error_oracle("DPY-4024"))
        with registros("app.infrastructure.oracle.repositorio_academico") as eventos, pytest.raises(
            DependenciaNoDisponible
        ) as error:
            _repositorio(motor).estudiantes([1], _plazo(motor))
        assert error.value.dependencia == "oracle"
        assert "invalidate 1" in motor.eventos  # después de un call_timeout la conexión no sirve
        (evento,) = eventos
        assert evento.datos == {"codigo": "DPY-4024"}

    def test_oracle_no_acepta_conexiones(self) -> None:
        motor = Motor()
        motor.error_al_conectar = error_oracle("ORA-12541")
        with pytest.raises(DependenciaNoDisponible):
            _repositorio(motor).estudiantes([1], _plazo(motor))


class TestContextos:
    def test_proyectos_y_periodos(self) -> None:
        def responder(texto: str, _parametros: Any) -> Resultado:
            if texto.startswith("SELECT cra_cod"):
                return Resultado(
                    filas=[
                        (20, "A", " PREGRADO ", "N"),
                        (30, "I", None, "S"),
                        (40, "A", "MAESTRIA", None),
                        (50, "A", "POSGRADO", "s"),
                    ]
                )
            return Resultado(filas=[(20, 2027, 1), (30, 2027, 1), (30, 2027, 3), (40, 2027, 1), (40, 2027, 1)])

        motor = Motor(responder)
        contextos = _repositorio(motor).contextos_carrera(frozenset({50, 40, 30, 20}), 80, 82, _plazo(motor))
        assert contextos == {
            20: ContextoCarrera(20, activa=True, nivel="PREGRADO", periodo=Periodo(2027, 1), terminacion_activa=False),
            30: ContextoCarrera(30, activa=False, nivel="", periodo=None, terminacion_activa=True),
            40: ContextoCarrera(40, activa=True, nivel="MAESTRIA", periodo=Periodo(2027, 1), terminacion_activa=False),
            50: ContextoCarrera(50, activa=True, nivel="POSGRADO", periodo=None, terminacion_activa=True),
        }
        carreras, periodos = motor.sentencias
        assert carreras.parametros == {"carreras": [20, 30, 40, 50], "evento_terminacion": 82}
        assert periodos.parametros == {"carreras": [20, 30, 40, 50], "evento_periodo": 80}

    def test_sin_carreras_no_consulta(self) -> None:
        motor = Motor()
        assert _repositorio(motor).contextos_carrera(frozenset(), 80, 82, _plazo(motor)) == {}
        assert motor.eventos == []


def test_certificados_electorales() -> None:
    motor = Motor(lambda _t, _p: Resultado(filas=[(5,), (7,)]))
    assert _repositorio(motor).con_certificado_electoral([5, 6, 7], _plazo(motor)) == frozenset({5, 7})
    assert motor.sentencias[0].parametros == {"codigos": [5, 6, 7]}


@pytest.mark.parametrize(
    ("periodos", "esperado"),
    [
        ([], None),
        ([Periodo(2027, 1)], Periodo(2027, 1)),
        ([Periodo(2027, 1), Periodo(2027, 1)], Periodo(2027, 1)),
        ([Periodo(2027, 1), Periodo(2027, 3)], None),
    ],
)
def test_periodo_unico(periodos: list[Periodo], esperado: Periodo | None) -> None:
    assert unico(periodos) == esperado


@given(st.lists(st.integers(), max_size=3500), st.integers(1, 1500))
def test_los_bloques_reconstruyen_la_lista(valores: list[int], tamano: int) -> None:
    partes = list(bloques(valores, tamano))
    assert [v for parte in partes for v in parte] == valores
    assert all(1 <= len(parte) <= tamano for parte in partes)
    assert len(partes) == -(-len(valores) // tamano)


@pytest.mark.parametrize(
    ("sentencia", "parametro"),
    [(SQL_ESTUDIANTES, "codigos"), (SQL_CERTIFICADOS, "codigos"), (SQL_CARRERAS, "carreras"), (SQL_PERIODOS, "carreras")],
)
def test_los_codigos_van_enlazados(sentencia: Any, parametro: str) -> None:
    compilada = str(
        sentencia.bindparams(**{parametro: [101, 102]}).compile(
            dialect=dialecto_oracledb.dialect(), compile_kwargs={"render_postcompile": True}
        )
    )
    assert compilada.count(f":{parametro}_") == 2
    assert "101" not in compilada
