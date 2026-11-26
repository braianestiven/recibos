"""Dobles en memoria de los puertos de la aplicación."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from app.application.errores import (
    ArchivoNoLegible,
    BloqueoNoObtenido,
    DependenciaNoDisponible,
    ErrorConexionBD,
    ErrorPersistencia,
)
from app.application.presupuesto import Plazo
from app.domain.fechas import ZONA_BOGOTA
from app.domain.modelos import ContextoCarrera, Estudiante, HojaPlantilla, Lote, NuevoLote, Pagina, Solicitud
from app.domain.reglas import ReglasLiquidacion
from tests import fabricas


class RelojDePrueba:
    """`segundos()` avanza `paso` en cada llamada; `ahora()` es fijo."""

    def __init__(self, inicio: float = 1000.0, paso: float = 0.0, ahora: datetime | None = None) -> None:
        self.t = inicio
        self.paso = paso
        self._ahora = ahora or datetime(2027, 1, 4, 9, 30, tzinfo=ZONA_BOGOTA)

    def segundos(self) -> float:
        actual = self.t
        self.t += self.paso
        return actual

    def ahora(self) -> datetime:
        return self._ahora


class FuenteReglasEnMemoria:
    def __init__(self, reglas: ReglasLiquidacion | None = None, error: Exception | None = None) -> None:
        self.reglas = reglas or fabricas.reglas_actuales()
        self.error = error
        self.plazos: list[Plazo] = []

    def obtener(self, plazo: Plazo) -> ReglasLiquidacion:
        self.plazos.append(plazo)
        if self.error:
            raise self.error
        return self.reglas


class AlmacenamientoEnMemoria:
    def __init__(self, error: Exception | None = None) -> None:
        self.archivos: dict[str, bytes] = {}
        self.error = error

    def guardar(self, contenido: bytes, nombre_interno: str) -> None:
        if self.error:
            raise self.error
        self.archivos[nombre_interno] = contenido


class LectorEnMemoria:
    def __init__(self, hoja: HojaPlantilla | None = None) -> None:
        self.hoja = hoja

    def leer(self, contenido: bytes) -> HojaPlantilla:
        if self.hoja is None:
            raise ArchivoNoLegible("no se pudo leer")
        return self.hoja


class AcademicoEnMemoria:
    def __init__(
        self,
        estudiantes: Mapping[int, Estudiante] | None = None,
        contextos: Mapping[int, ContextoCarrera] | None = None,
        certificados: frozenset[int] = frozenset(),
        error: Exception | None = None,
    ) -> None:
        self._estudiantes = dict(estudiantes or {})
        self._contextos = dict(contextos or {})
        self._certificados = certificados
        self.error = error
        self.llamadas = 0

    def estudiantes(self, codigos: Sequence[int], plazo: Plazo) -> Mapping[int, Estudiante]:
        self.llamadas += 1
        plazo.para(20)
        if self.error:
            raise self.error
        return {c: self._estudiantes[c] for c in codigos if c in self._estudiantes}

    def contextos_carrera(
        self, codigos_carrera: frozenset[int], evento_periodo: int, evento_terminacion: int, plazo: Plazo
    ) -> Mapping[int, ContextoCarrera]:
        return {c: self._contextos[c] for c in codigos_carrera if c in self._contextos}

    def con_certificado_electoral(self, codigos: Sequence[int], plazo: Plazo) -> frozenset[int]:
        return frozenset(c for c in codigos if c in self._certificados)


class FestivosEnMemoria:
    def __init__(self, dias: frozenset[date] | None = None, error: Exception | None = None) -> None:
        self.dias = dias if dias is not None else frozenset({date(y, 1, 1) for y in range(2026, 2033)})
        self.error = error
        self.rangos: list[tuple[date, date]] = []

    def festivos(self, desde: date, hasta: date, plazo: Plazo) -> frozenset[date]:
        self.rangos.append((desde, hasta))
        if self.error:
            raise self.error
        return frozenset(d for d in self.dias if desde <= d <= hasta)


@dataclass
class SolicitudGuardada:
    id: int
    codigo_estudiante: int
    estado: int
    solicitud: Solicitud | None = None


@dataclass
class Fallas:
    """Fallas a pedido, por código de estudiante."""

    conexion_al_bloquear: set[int] = field(default_factory=set)
    bloqueo_no_llega: set[int] = field(default_factory=set)
    cancelacion: set[int] = field(default_factory=set)
    guardado: set[int] = field(default_factory=set)
    conexion_al_guardar: set[int] = field(default_factory=set)
    plazo_al_guardar: set[int] = field(default_factory=set)
    plazo_al_cancelar: set[int] = field(default_factory=set)


class SesionEnMemoria:
    def __init__(self, repositorio: RepositorioEnMemoria, plazo: Plazo) -> None:
        self._repo = repositorio
        self._plazo = plazo

    def _sentencia(self) -> None:
        self._plazo.exigir()
        self._repo.sentencias += 1
        if self._repo.reloj is not None:
            self._repo.reloj.t += self._repo.segundos_por_sentencia

    @contextmanager
    def bloqueo_estudiante(self, codigo_estudiante: int) -> Iterator[None]:
        fallas = self._repo.fallas
        self._sentencia()
        if codigo_estudiante in fallas.conexion_al_bloquear:
            raise ErrorConexionBD
        if codigo_estudiante in fallas.bloqueo_no_llega:
            raise BloqueoNoObtenido
        self._repo.bloqueados.add(codigo_estudiante)
        try:
            yield
        finally:
            self._repo.bloqueados.discard(codigo_estudiante)

    def cancelar_sin_imprimir(self, codigo_estudiante: int) -> tuple[int, ...]:
        if codigo_estudiante in self._repo.fallas.plazo_al_cancelar:
            self._plazo = Plazo(0.0, lambda: 1.0)
        self._sentencia()
        if codigo_estudiante in self._repo.fallas.cancelacion:
            raise ErrorPersistencia
        canceladas = []
        for guardada in self._repo.solicitudes.values():
            if guardada.codigo_estudiante == codigo_estudiante and guardada.estado == 0:
                guardada.estado = 2
                canceladas.append(guardada.id)
        return tuple(canceladas)

    def guardar_solicitud(self, solicitud: Solicitud, documento_usuario: str, creada_en: datetime) -> int:
        fallas = self._repo.fallas
        if solicitud.codigo_estudiante in fallas.plazo_al_guardar:
            self._plazo = Plazo(0.0, lambda: 1.0)
        self._sentencia()
        if solicitud.codigo_estudiante in fallas.conexion_al_guardar:
            raise ErrorConexionBD
        if solicitud.codigo_estudiante in fallas.guardado:
            raise ErrorPersistencia
        return self._repo.agregar(solicitud.codigo_estudiante, 0, solicitud)


class RepositorioEnMemoria:
    def __init__(self, porcentajes: Mapping[int, Decimal] | None = None) -> None:
        self.porcentajes = dict(porcentajes if porcentajes is not None else fabricas.PORCENTAJES_EXENCION)
        self.lotes: list[tuple[int, NuevoLote]] = []
        self.solicitudes: dict[int, SolicitudGuardada] = {}
        self.fallas = Fallas()
        self.bloqueados: set[int] = set()
        self.sentencias = 0
        self.sesiones = 0
        self.reloj: RelojDePrueba | None = None  # si se da, cada sentencia hace avanzar el reloj
        self.segundos_por_sentencia = 0.0
        self.error_porcentajes = False
        self.error_registro = False
        self.error_listado = False

    def agregar(self, codigo: int, estado: int, solicitud: Solicitud | None = None) -> int:
        nuevo_id = len(self.solicitudes) + 1
        self.solicitudes[nuevo_id] = SolicitudGuardada(nuevo_id, codigo, estado, solicitud)
        return nuevo_id

    def registrar_lote(self, lote: NuevoLote) -> int:
        if self.error_registro:
            raise ErrorPersistencia
        self.lotes.append((len(self.lotes) + 1, lote))
        return len(self.lotes)

    @contextmanager
    def filas(self, plazo: Plazo) -> Iterator[SesionEnMemoria]:
        self.sesiones += 1
        yield SesionEnMemoria(self, plazo)

    def listar_lotes(self, limite: int, desplazamiento: int) -> Pagina[Lote]:
        if self.error_listado:
            raise ErrorPersistencia
        lotes = [
            Lote(id=i, documento_usuario=n.documento_usuario, nombre_original=n.nombre_original, ip=n.ip, fecha=n.fecha)
            for i, n in reversed(self.lotes)
        ]
        return Pagina(tuple(lotes[desplazamiento : desplazamiento + limite]), len(lotes), limite, desplazamiento)

    def porcentajes_exencion(self, ids: frozenset[int]) -> Mapping[int, Decimal]:
        if self.error_porcentajes:
            raise ErrorPersistencia
        return {i: p for i, p in self.porcentajes.items() if i in ids}

    def estados_de(self, codigo: int) -> list[int]:
        return [s.estado for s in self.solicitudes.values() if s.codigo_estudiante == codigo]


def dependencia_caida(nombre: str = "x") -> DependenciaNoDisponible:
    return DependenciaNoDisponible(nombre)
