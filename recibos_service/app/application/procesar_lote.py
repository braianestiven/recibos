"""UC-01: procesar un lote en la misma petición (services.md; business-logic-model.md §4.1 y §4.9)."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

from app.application.errores import (
    ArchivoNoLegible,
    DependenciaNoDisponible,
    ErrorConexionBD,
    ErrorPersistencia,
    FormatoPlantillaInvalido,
    RespuestaInvalida,
)
from app.application.presupuesto import Plazo, PlazoVencido
from app.application.puertos import (
    AlmacenamientoArchivos,
    FuenteFestivos,
    FuenteReglas,
    LectorPlantilla,
    Reloj,
    RepositorioAcademico,
    RepositorioSolicitudes,
    SesionFilas,
)
from app.domain import fechas, generador_solicitud, mensajes, plantillas, validacion_estudiante, validacion_filas
from app.domain.errores import ExencionSinPorcentaje, FormatoInvalido, ReglaInvalida
from app.domain.modelos import (
    ContextoCarrera,
    Estudiante,
    FallaFila,
    FilaPlantilla,
    MotivoRechazo,
    NuevoLote,
    Procesado,
    Rechazo,
    ResumenLote,
    Solicitud,
    Usuario,
)
from app.domain.plantillas import EspecificacionPlantilla
from app.domain.reglas import ReglasLiquidacion

registro = logging.getLogger(__name__)


@dataclass(frozen=True)
class CargarLoteComando:
    contenido: bytes
    nombre_original: str
    usuario: Usuario
    ip: str  # de X-Forwarded-For con los proxies de confianza (AD-29)
    recibida_en: float  # Reloj.segundos() al llegar la petición; el plazo del lote cuenta desde aquí (AD-34)


@dataclass(frozen=True)
class ConfiguracionLote:
    limite_lote_s: float = 90.0  # BR-L16
    max_filas: int = 1000  # BR-L11
    corte_mysql: int = 5  # BR-T04
    presupuesto_previo_s: float = 30.0  # DN-03
    peor_caso_mysql_s: float = 13.0  # 3 s para conectar y 10 s de lectura
    peor_caso_s3_s: float = 15.0  # dos intentos de 7 s y la espera entre ellos
    tiempo_conexion_oracle_s: float = 5.0
    margen_festivos_dias: int = 30  # BR-L13


@dataclass(frozen=True)
class ResultadoLote:
    resumen: ResumenLote
    auditoria: dict[str, object] = field(default_factory=dict)  # `data` de la auditoría (BR-U02)


@dataclass(frozen=True)
class _ResultadoFila:
    resultado: Procesado | Rechazo
    falla_de_conexion: bool = False
    canceladas: tuple[int, ...] = ()
    creada: int | None = None


@dataclass
class _DatosAcademicos:
    estudiantes: Mapping[int, Estudiante]
    contextos: Mapping[int, ContextoCarrera]
    certificados: frozenset[int]
    festivos: frozenset[date]


class ProcesarLote:
    def __init__(
        self,
        *,
        fuente_reglas: FuenteReglas,
        repositorio: RepositorioSolicitudes,
        almacenamiento: AlmacenamientoArchivos,
        lector: LectorPlantilla,
        academico: RepositorioAcademico,
        fuente_festivos: FuenteFestivos,
        reloj: Reloj,
        configuracion: ConfiguracionLote,
        generar_id: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._reglas = fuente_reglas
        self._repositorio = repositorio
        self._almacenamiento = almacenamiento
        self._lector = lector
        self._academico = academico
        self._festivos = fuente_festivos
        self._reloj = reloj
        self._conf = configuracion
        self._generar_id = generar_id

    def ejecutar(self, comando: CargarLoteComando) -> ResultadoLote:
        plazo_lote = Plazo(comando.recibida_en + self._conf.limite_lote_s, self._reloj.segundos)  # BR-L16
        plazo_previo = Plazo(  # DN-03
            self._reloj.segundos() + self._conf.presupuesto_previo_s, self._reloj.segundos
        ).hasta(plazo_lote)
        try:
            reglas = self._leer_reglas(plazo_previo)
            id_lote = self._guardar_y_registrar(comando, plazo_previo)
        except PlazoVencido:
            raise DependenciaNoDisponible("presupuesto_previo") from None

        auditoria: dict[str, object] = {"id_lote": id_lote, "tamano_bytes": len(comando.contenido)}
        espec, filas = self._leer_plantilla(comando.contenido, id_lote, auditoria)
        auditoria["tipo_plantilla"] = espec.tipo.name

        resultados: dict[int, Procesado | Rechazo] = {}
        a_procesar = self._separar_codigos(filas, resultados)
        try:
            datos = self._leer_datos_academicos(a_procesar, espec, reglas, plazo_previo)
        except PlazoVencido:
            raise DependenciaNoDisponible("presupuesto_previo") from None

        creadas, canceladas, corte = self._procesar_filas(
            a_procesar, espec, reglas, datos, comando.usuario, plazo_lote, resultados
        )

        orden = [resultados[fila.numero] for fila in filas]
        resumen = ResumenLote(
            id_lote=id_lote,
            tipo=espec.tipo,
            procesados=tuple(r for r in orden if isinstance(r, Procesado)),
            rechazados=tuple(r for r in orden if isinstance(r, Rechazo)),
        )
        tiempo_agotado = sum(1 for r in resumen.rechazados if r.motivo is MotivoRechazo.TIEMPO_AGOTADO)
        auditoria.update(
            {
                "total_filas": resumen.total_filas,
                "procesados": len(resumen.procesados),
                "rechazados": len(resumen.rechazados),
                "solicitudes_creadas": creadas,
                "solicitudes_canceladas": {"estado_anterior": 0, "estado_nuevo": 2, "ids": canceladas},
            }
        )
        registro.info(
            "lote_terminado",
            extra={
                "evento": "lote_terminado",
                "datos": {
                    "id_lote": id_lote,
                    "tipo": espec.tipo.name,
                    "total_filas": resumen.total_filas,
                    "procesados": len(resumen.procesados),
                    "rechazados": len(resumen.rechazados),
                    "tiempo_agotado": tiempo_agotado,
                    "corte_mysql": corte,
                    "duracion_ms": round((self._reloj.segundos() - comando.recibida_en) * 1000),
                },
            },
        )
        return ResultadoLote(resumen=resumen, auditoria=auditoria)

    # --- fase previa ---------------------------------------------------------------------------

    def _leer_reglas(self, plazo: Plazo) -> ReglasLiquidacion:
        try:
            reglas = self._reglas.obtener(plazo)  # BR-L04
        except ReglaInvalida as error:
            raise RespuestaInvalida(error.mensaje) from None
        plazo.exigir(self._conf.peor_caso_mysql_s)
        requeridos = reglas.ids_de_los_mapas() | {reglas.id_exencion_votacion}
        try:
            porcentajes = self._repositorio.porcentajes_exencion(requeridos)
        except ErrorPersistencia:
            raise DependenciaNoDisponible("mysql") from None
        try:
            return reglas.con_porcentajes(porcentajes)  # BR-L05
        except ExencionSinPorcentaje as error:
            raise RespuestaInvalida(error.mensaje) from None

    def _guardar_y_registrar(self, comando: CargarLoteComando, plazo: Plazo) -> int:
        ahora = self._reloj.ahora()
        nombre_interno = f"lotes/{ahora:%Y}/{ahora:%m}/{self._generar_id()}.xls"  # nunca sale del nombre original
        plazo.exigir(self._conf.peor_caso_s3_s)
        self._almacenamiento.guardar(comando.contenido, nombre_interno)  # BR-L06
        plazo.exigir(self._conf.peor_caso_mysql_s)
        lote = NuevoLote(
            documento_usuario=comando.usuario.documento,
            nombre_original=comando.nombre_original,
            nombre_interno=nombre_interno,
            ip=comando.ip,
            fecha=ahora,
        )
        try:
            return self._repositorio.registrar_lote(lote)  # BR-L07
        except ErrorPersistencia:
            raise DependenciaNoDisponible("mysql") from None

    def _leer_plantilla(
        self, contenido: bytes, id_lote: int, auditoria: dict[str, object]
    ) -> tuple[EspecificacionPlantilla, list[FilaPlantilla]]:
        try:
            hoja = self._lector.leer(contenido)  # BR-L08
        except ArchivoNoLegible:
            raise FormatoPlantillaInvalido(id_lote, mensajes.PLANTILLA_ILEGIBLE, auditoria) from None
        try:
            espec = plantillas.identificar(hoja)  # BR-L09
            plantillas.validar_formato(hoja, espec)  # BR-L10
        except FormatoInvalido as error:
            raise FormatoPlantillaInvalido(id_lote, error.mensaje, auditoria) from None
        filas = plantillas.extraer_filas(hoja, espec)  # BR-L11
        auditoria_tipo = {**auditoria, "tipo_plantilla": espec.tipo.name}
        if not filas:
            raise FormatoPlantillaInvalido(id_lote, mensajes.PLANTILLA_SIN_FILAS, auditoria_tipo)
        if len(filas) > self._conf.max_filas:
            mensaje = mensajes.demasiadas_filas(len(filas), self._conf.max_filas)
            raise FormatoPlantillaInvalido(id_lote, mensaje, auditoria_tipo)
        return espec, filas

    @staticmethod
    def _separar_codigos(
        filas: Sequence[FilaPlantilla], resultados: dict[int, Procesado | Rechazo]
    ) -> list[tuple[FilaPlantilla, int]]:
        """Códigos inválidos (BR-F01) y repetidos (BR-F02) quedan resueltos; devuelve las filas a procesar."""
        primera_fila: dict[int, int] = {}
        a_procesar: list[tuple[FilaPlantilla, int]] = []
        for fila in filas:
            codigo = validacion_filas.validar_codigo(fila)
            if isinstance(codigo, Rechazo):
                resultados[fila.numero] = codigo
            elif codigo in primera_fila:
                resultados[fila.numero] = mensajes.rechazo_simple(
                    fila, MotivoRechazo.CODIGO_REPETIDO, mensajes.codigo_repetido(primera_fila[codigo])
                )
            else:
                primera_fila[codigo] = fila.numero
                a_procesar.append((fila, codigo))
        return a_procesar

    def _leer_datos_academicos(
        self,
        a_procesar: Sequence[tuple[FilaPlantilla, int]],
        espec: EspecificacionPlantilla,
        reglas: ReglasLiquidacion,
        plazo: Plazo,
    ) -> _DatosAcademicos:
        codigos = [codigo for _, codigo in a_procesar]
        if not codigos:
            return _DatosAcademicos({}, {}, frozenset(), frozenset())
        plazo.exigir(self._conf.tiempo_conexion_oracle_s)
        estudiantes = self._academico.estudiantes(codigos, plazo)  # BR-L12
        carreras = frozenset(e.codigo_carrera for e in estudiantes.values())
        plazo.exigir(self._conf.tiempo_conexion_oracle_s)
        contextos = self._academico.contextos_carrera(carreras, reglas.evento_periodo, reglas.evento_terminacion, plazo)
        plazo.exigir(self._conf.tiempo_conexion_oracle_s)
        certificados = self._academico.con_certificado_electoral(codigos, plazo)
        festivos = self._leer_festivos(a_procesar, espec, reglas, plazo)
        return _DatosAcademicos(estudiantes, contextos, certificados, festivos)

    def _leer_festivos(
        self,
        a_procesar: Sequence[tuple[FilaPlantilla, int]],
        espec: EspecificacionPlantilla,
        reglas: ReglasLiquidacion,
        plazo: Plazo,
    ) -> frozenset[date]:
        """Festivos de los años completos que necesita el lote; cada año revisado debe tener alguno (BR-L13)."""
        ordinarias = [d for fila, _ in a_procesar for d in validacion_filas.fechas_ordinarias_legibles(fila, espec)]
        rango = fechas.rango_de_festivos(ordinarias, reglas.dias_fecha_extraordinaria, self._conf.margen_festivos_dias)
        if rango is None:
            return frozenset()
        desde, hasta = date(rango[0].year, 1, 1), date(rango[1].year, 12, 31)
        conjunto = self._festivos.festivos(desde, hasta, plazo)
        anios_con_festivos = {d.year for d in conjunto}
        for anio in sorted(fechas.anios_a_revisar(ordinarias, reglas.dias_fecha_extraordinaria)):
            if anio not in anios_con_festivos:
                raise RespuestaInvalida(mensajes.anio_sin_festivos(anio))
        return conjunto

    # --- filas ---------------------------------------------------------------------------------

    def _procesar_filas(
        self,
        a_procesar: Sequence[tuple[FilaPlantilla, int]],
        espec: EspecificacionPlantilla,
        reglas: ReglasLiquidacion,
        datos: _DatosAcademicos,
        usuario: Usuario,
        plazo_lote: Plazo,
        resultados: dict[int, Procesado | Rechazo],
    ) -> tuple[list[int], list[int], bool]:
        creadas: list[int] = []
        canceladas: list[int] = []
        fallas_seguidas = 0
        hoy = self._reloj.ahora().date()
        if not a_procesar:
            return creadas, canceladas, False
        with self._repositorio.filas(plazo_lote) as sesion:
            for fila, codigo in a_procesar:
                if not plazo_lote.vigente():  # BR-L16: sin cancelar
                    resultados[fila.numero] = mensajes.rechazo_simple(
                        fila, MotivoRechazo.TIEMPO_AGOTADO, mensajes.TIEMPO_AGOTADO
                    )
                    continue
                if fallas_seguidas >= self._conf.corte_mysql:  # BR-T04: sin cancelar
                    resultados[fila.numero] = mensajes.rechazo_simple(
                        fila, MotivoRechazo.ERROR_GUARDADO, mensajes.ERROR_GUARDADO
                    )
                    continue
                estudiante = datos.estudiantes.get(codigo)
                if estudiante is None:  # BR-E01: sin cancelar
                    resultados[fila.numero] = mensajes.rechazo_simple(
                        fila, MotivoRechazo.ESTUDIANTE_NO_ENCONTRADO, mensajes.ESTUDIANTE_NO_ENCONTRADO
                    )
                    continue
                salida = self._evaluar(fila, espec, codigo, estudiante, reglas, datos, hoy)
                fila_resultado = self._guardar_fila(sesion, fila, codigo, salida, usuario)
                resultados[fila.numero] = fila_resultado.resultado
                canceladas.extend(fila_resultado.canceladas)
                if fila_resultado.creada is not None:
                    creadas.append(fila_resultado.creada)
                fallas_seguidas = fallas_seguidas + 1 if fila_resultado.falla_de_conexion else 0
        return creadas, canceladas, fallas_seguidas >= self._conf.corte_mysql

    @staticmethod
    def _evaluar(
        fila: FilaPlantilla,
        espec: EspecificacionPlantilla,
        codigo: int,
        estudiante: Estudiante,
        reglas: ReglasLiquidacion,
        datos: _DatosAcademicos,
        hoy: date,
    ) -> Solicitud | Rechazo:
        contexto = datos.contextos.get(estudiante.codigo_carrera)
        falla = validacion_estudiante.validar(estudiante, contexto, espec.tipo, reglas)  # BR-E02 a BR-E07
        if falla is not None:
            return mensajes.rechazo(fila, falla)
        assert contexto is not None  # noqa: S101 - validar exige el contexto (BR-E04)
        resultado = generador_solicitud.generar(
            fila, espec, codigo, estudiante, contexto, reglas, datos.festivos, hoy, codigo in datos.certificados
        )
        if isinstance(resultado, FallaFila):
            return mensajes.rechazo(fila, resultado)
        return resultado

    def _guardar_fila(
        self, sesion: SesionFilas, fila: FilaPlantilla, codigo: int, salida: Solicitud | Rechazo, usuario: Usuario
    ) -> _ResultadoFila:
        """Bloqueo, cancelación y guardado de una fila (business-logic-model.md §4.9)."""
        cancelo = False
        canceladas: tuple[int, ...] = ()
        try:
            with sesion.bloqueo_estudiante(codigo):  # BR-T05
                canceladas = sesion.cancelar_sin_imprimir(codigo)  # BR-T01
                cancelo = True
                if isinstance(salida, Rechazo):
                    return _ResultadoFila(salida, canceladas=canceladas)
                creada = sesion.guardar_solicitud(salida, usuario.documento, self._reloj.ahora())  # BR-T03
                return _ResultadoFila(Procesado(fila.numero, codigo), canceladas=canceladas, creada=creada)
        except PlazoVencido:  # BR-L16: no salió ninguna sentencia más
            if cancelo:
                rechazo = mensajes.rechazo_simple(fila, MotivoRechazo.ERROR_GUARDADO, mensajes.ERROR_GUARDADO)
            else:
                rechazo = mensajes.rechazo_simple(fila, MotivoRechazo.TIEMPO_AGOTADO, mensajes.TIEMPO_AGOTADO)
            return _ResultadoFila(rechazo, canceladas=canceladas)
        except ErrorPersistencia as error:  # BR-T02, BR-T03, BR-T05; solo ErrorConexionBD cuenta para el corte
            conexion = isinstance(error, ErrorConexionBD)
            registro.warning(
                "fila_sin_guardar", extra={"evento": "fila_sin_guardar", "datos": {"error": type(error).__name__}}
            )
            if not cancelo and isinstance(salida, Rechazo):
                return _ResultadoFila(mensajes.con_aviso_de_cancelacion(salida), falla_de_conexion=conexion)
            rechazo = mensajes.rechazo_simple(fila, MotivoRechazo.ERROR_GUARDADO, mensajes.ERROR_GUARDADO)
            return _ResultadoFila(rechazo, falla_de_conexion=conexion, canceladas=canceladas)
