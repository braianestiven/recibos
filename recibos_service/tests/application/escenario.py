"""Arma un `ProcesarLote` con dobles en memoria y una plantilla de posgrado o de pregrado."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.application.procesar_lote import CargarLoteComando, ConfiguracionLote, ProcesarLote, ResultadoLote
from app.domain.modelos import ContextoCarrera, Estudiante, Usuario
from app.domain.plantillas import POSGRADO_CREDITOS, EspecificacionPlantilla
from tests import fabricas
from tests.application import dobles

USUARIO = Usuario(documento="79123456", sub="arc@udistrital.edu.co", roles=frozenset({"ARC"}))
CUOTA1, CUOTA2, _ = POSGRADO_CREDITOS.columnas_fecha


def celdas_posgrado_validas(codigo: str, **extra: str) -> dict[int, str]:
    """Fila de posgrado por créditos válida: 2 cuotas en febrero y marzo de 2027, sin porcentajes."""
    celdas = {1: codigo, 2: "12", 3: "2"}
    for terna, fecha in ((CUOTA1, date(2027, 2, 1)), (CUOTA2, date(2027, 3, 1))):
        celdas.update(dict(zip(terna, (str(fecha.day), str(fecha.month), str(fecha.year)), strict=True)))
    celdas.update({int(k[1:]): v for k, v in extra.items()})
    return celdas


@dataclass
class Escenario:
    espec: EspecificacionPlantilla = POSGRADO_CREDITOS
    filas: dict[int, dict[int, str]] = field(default_factory=dict)
    estudiantes: dict[int, Estudiante] = field(default_factory=dict)
    contextos: dict[int, ContextoCarrera] = field(default_factory=dict)
    certificados: frozenset[int] = frozenset()
    configuracion: ConfiguracionLote = field(default_factory=ConfiguracionLote)
    reloj: dobles.RelojDePrueba = field(default_factory=dobles.RelojDePrueba)
    reglas: dobles.FuenteReglasEnMemoria = field(default_factory=dobles.FuenteReglasEnMemoria)
    repositorio: dobles.RepositorioEnMemoria = field(default_factory=dobles.RepositorioEnMemoria)
    almacenamiento: dobles.AlmacenamientoEnMemoria = field(default_factory=dobles.AlmacenamientoEnMemoria)
    festivos: dobles.FestivosEnMemoria = field(default_factory=dobles.FestivosEnMemoria)
    hoja_ilegible: bool = False
    academico_error: Exception | None = None

    def agregar_estudiante(self, codigo: int, nivel: str = "POSGRADO", **kwargs: object) -> None:
        self.estudiantes[codigo] = fabricas.estudiante(codigo=codigo, **kwargs)  # type: ignore[arg-type]
        carrera = self.estudiantes[codigo].codigo_carrera
        self.contextos.setdefault(carrera, fabricas.contexto(codigo=carrera, nivel=nivel))

    def caso_de_uso(self) -> ProcesarLote:
        hoja = None if self.hoja_ilegible else fabricas.hoja_para(self.espec, filas=self.filas)
        return ProcesarLote(
            fuente_reglas=self.reglas,
            repositorio=self.repositorio,
            almacenamiento=self.almacenamiento,
            lector=dobles.LectorEnMemoria(hoja),
            academico=dobles.AcademicoEnMemoria(
                self.estudiantes, self.contextos, self.certificados, error=self.academico_error
            ),
            fuente_festivos=self.festivos,
            reloj=self.reloj,
            configuracion=self.configuracion,
            generar_id=lambda: "abc123",
        )

    def ejecutar(self, contenido: bytes = b"\xd0\xcf\x11\xe0") -> ResultadoLote:
        comando = CargarLoteComando(
            contenido=contenido,
            nombre_original="lote.xls",
            usuario=USUARIO,
            ip="10.0.0.1",
            recibida_en=self.reloj.t,
        )
        return self.caso_de_uso().ejecutar(comando)
