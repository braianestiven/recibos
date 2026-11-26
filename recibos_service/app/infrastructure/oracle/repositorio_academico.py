"""Datos académicos de Oracle, en solo lectura y en bloque (AD-06; BR-L12; component-dependency.md §4).

Tres lecturas por lote: estudiantes, contexto de los proyectos curriculares y certificados electorales.
Los códigos van en bloques de hasta 1000 (límite de `IN` en Oracle) y enlazados, nunca en el texto.
Cada lectura usa una conexión del pool, y antes de cada sentencia se fija `call_timeout` con lo que
quede del plazo, hasta 20 s (AD-34).
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.sql.elements import TextClause

from app.application.errores import DependenciaNoDisponible
from app.application.presupuesto import Plazo
from app.domain.modelos import ContextoCarrera, Estudiante, Periodo
from app.infrastructure.db.motores import codigo_de_error

registro = logging.getLogger(__name__)

TAMANO_BLOQUE = 1000
LLAMADA_MAXIMA_S = 20.0

SQL_ESTUDIANTES = text(
    "SELECT est_cod, est_estado_est, est_cra_cod, "
    "CASE WHEN EXISTS (SELECT 1 FROM v_acestmatbruto WHERE emb_est_cod = est_cod) THEN 1 ELSE 0 END "
    "FROM acest WHERE est_cod IN :codigos"
).bindparams(bindparam("codigos", expanding=True))

SQL_CARRERAS = text(
    "SELECT cra_cod, cra_estado, tra_nivel, fua_verifica_evento(cra_cod, :evento_terminacion) "
    "FROM accra LEFT JOIN actipcra ON tra_cod = cra_tip_cra WHERE cra_cod IN :carreras"
).bindparams(bindparam("carreras", expanding=True))

SQL_PERIODOS = text(
    "SELECT acn_cra_cod, ape_ano, ape_per FROM acasperi "
    "INNER JOIN acasperieventos ON acn_estado = ape_estado "
    "WHERE acn_cra_cod IN :carreras AND acn_cod_evento = :evento_periodo"
).bindparams(bindparam("carreras", expanding=True))

SQL_CERTIFICADOS = text(
    "SELECT DISTINCT cer_est_cod FROM accerelectoral WHERE cer_est_cod IN :codigos AND cer_estado = 'A'"
).bindparams(bindparam("codigos", expanding=True))

Consulta = tuple[TextClause, dict[str, Any]]
Filas = Sequence[Sequence[Any]]


def bloques[T](valores: Sequence[T], tamano: int = TAMANO_BLOQUE) -> Iterator[list[T]]:
    for inicio in range(0, len(valores), tamano):
        yield list(valores[inicio : inicio + tamano])


def _texto(valor: object) -> str:
    return "" if valor is None else str(valor).strip()


def unico(periodos: Sequence[Periodo]) -> Periodo | None:
    """Exactamente un periodo vigente; con ninguno o con más de uno, ninguno (A13, BR-E06).

    Dos filas iguales son el mismo periodo: no hay ambigüedad sobre cuál usar.
    """
    distintos = set(periodos)
    return distintos.pop() if len(distintos) == 1 else None


def limitar_llamada(conexion: Connection, plazo: Plazo) -> None:
    """`call_timeout` en milisegundos: lo que quede del plazo, hasta 20 s; nunca 0, que sería sin límite."""
    segundos = plazo.para(LLAMADA_MAXIMA_S)  # PlazoVencido si no queda tiempo: la sentencia no sale
    crudo: Any = conexion.connection.driver_connection
    crudo.call_timeout = max(1, int(segundos * 1000))


class RepositorioAcademicoOracle:
    def __init__(self, motor: Engine) -> None:
        self._motor = motor

    def estudiantes(self, codigos: Sequence[int], plazo: Plazo) -> Mapping[int, Estudiante]:
        consultas = [(SQL_ESTUDIANTES, {"codigos": bloque}) for bloque in bloques(codigos)]
        return {
            int(codigo): Estudiante(
                codigo=int(codigo),
                estado=_texto(estado),
                codigo_carrera=int(carrera),
                tiene_valor_matricula=bool(matricula),
            )
            for resultado in self._leer(consultas, plazo)
            for codigo, estado, carrera, matricula in resultado
        }

    def contextos_carrera(
        self, codigos_carrera: frozenset[int], evento_periodo: int, evento_terminacion: int, plazo: Plazo
    ) -> Mapping[int, ContextoCarrera]:
        grupos = list(bloques(sorted(codigos_carrera)))
        consultas: list[Consulta] = [
            *((SQL_CARRERAS, {"carreras": b, "evento_terminacion": evento_terminacion}) for b in grupos),
            *((SQL_PERIODOS, {"carreras": b, "evento_periodo": evento_periodo}) for b in grupos),
        ]
        resultados = self._leer(consultas, plazo)
        periodos: dict[int, list[Periodo]] = {}
        for resultado in resultados[len(grupos) :]:
            for carrera, anio, numero in resultado:
                periodos.setdefault(int(carrera), []).append(Periodo(int(anio), int(numero)))
        return {
            int(codigo): ContextoCarrera(
                codigo=int(codigo),
                activa=_texto(estado) == "A",
                nivel=_texto(nivel),
                periodo=unico(periodos.get(int(codigo), [])),
                terminacion_activa=_texto(terminacion).upper() == "S",
            )
            for resultado in resultados[: len(grupos)]
            for codigo, estado, nivel, terminacion in resultado
        }

    def con_certificado_electoral(self, codigos: Sequence[int], plazo: Plazo) -> frozenset[int]:
        consultas = [(SQL_CERTIFICADOS, {"codigos": bloque}) for bloque in bloques(codigos)]
        return frozenset(int(codigo) for resultado in self._leer(consultas, plazo) for (codigo,) in resultado)

    def _leer(self, consultas: Sequence[Consulta], plazo: Plazo) -> list[Filas]:
        """Las filas de cada consulta, en una sola conexión. `DependenciaNoDisponible` si Oracle falla."""
        if not consultas:
            return []
        resultados: list[Filas] = []
        try:
            with self._motor.connect() as conexion:
                try:
                    for sentencia, parametros in consultas:
                        limitar_llamada(conexion, plazo)
                        resultados.append(conexion.execute(sentencia, parametros).all())
                except DBAPIError:
                    conexion.invalidate()  # después de un call_timeout la conexión no sirve
                    raise
        except SQLAlchemyError as error:
            registro.warning(
                "oracle_no_disponible",
                extra={"evento": "oracle_no_disponible", "datos": {"codigo": codigo_de_error(error)}},
            )
            raise DependenciaNoDisponible("oracle") from None
        return resultados
