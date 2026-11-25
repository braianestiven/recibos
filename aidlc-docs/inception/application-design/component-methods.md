# Métodos de los componentes

Firmas de diseño en Python (la última versión estable con soporte, C4; se fija en U1 NFR Requirements). Code Generation puede cambiar nombres internos, pero no las responsabilidades ni los tipos de entrada y salida. Las reglas detalladas de cada función se cierran en U1 Functional Design.

## 1. Dominio (`app/domain/`)

### 1.1 Modelos (dataclasses inmutables)

| Tipo | Campos |
|---|---|
| `TipoPlantilla` (Enum) | `PREGRADO = 1`, `POSGRADO_CREDITOS = 2`, `POSGRADO_SMLV = 3` (valor = `tipoPlantilla` en MySQL) |
| `HojaPlantilla` | `celdas: Mapping[tuple[int, int], str]` (fila, columna → texto; solo celdas con contenido), `num_columnas: int`; método `valor(fila, columna) -> str \| None` |
| `FilaPlantilla` | `numero: int`, `celdas: Mapping[int, str]`; métodos `marcada(columna) -> bool` (celda con cualquier contenido), `texto(columna) -> str \| None` |
| `Usuario` | `documento: str`, `sub: str`, `roles: frozenset[str]` |
| `Estudiante` | `codigo: int`, `estado: str`, `codigo_carrera: int`, `tiene_valor_matricula: bool` |
| `Periodo` | `anio: int`, `numero: int` |
| `ContextoCarrera` | `codigo: int`, `activa: bool`, `nivel: str` (`ACTIPCRA.tra_nivel`, F5), `periodo: Periodo \| None` (ninguno o más de uno: `None`, A13), `terminacion_activa: bool` |
| `FechasPago` | `ordinaria: date`, `extraordinaria: date` |
| `Cuota` | `numero: int`, `porcentaje: int` (0–100), `fechas: FechasPago` |
| `DatosPosgrado` | `numero_cuotas: int`, `unidad: str`, `fechas_ordinarias: tuple[date, ...]`, `porcentajes: tuple[int \| None, ...]` |
| `Solicitud` | `codigo_estudiante: int`, `codigo_carrera: int`, `periodo: Periodo`, `tipo: TipoPlantilla`, `unidad: str` (créditos o SMLV en posgrado; `"0"` en pregrado, RE-07), `cuotas: tuple[Cuota, ...]`, `exenciones: tuple[int, ...]`, `conceptos: tuple[int, ...]` |
| `MotivoRechazo` (Enum) | `CODIGO_INVALIDO`, `CODIGO_REPETIDO`, `ESTUDIANTE_NO_ENCONTRADO`, `SIN_VALOR_MATRICULA`, `ESTADO_NO_PERMITIDO`, `CARRERA_INACTIVA`, `NO_TERMINACION_MATERIAS`, `SIN_PERIODO_VIGENTE`, `NIVEL_NO_CORRESPONDE`, `CUOTAS_INVALIDAS`, `UNIDAD_INVALIDA`, `FECHA_INVALIDA`, `PORCENTAJE_INVALIDO`, `PORCENTAJES_NO_SUMAN_100`, `DESCUENTOS_NO_ACUMULABLES`, `ERROR_GUARDADO` |
| `Rechazo` | `fila: int`, `codigo: str \| None`, `motivo: MotivoRechazo`, `detalle: str \| None` |
| `Procesado` | `fila: int`, `codigo: int` |
| `ResumenLote` | `id_lote: int`, `tipo: TipoPlantilla`, `total_filas: int`, `procesados: tuple[Procesado, ...]`, `rechazados: tuple[Rechazo, ...]` (RF-11 CA3) |
| `NuevoLote` | `documento_usuario: str`, `nombre_original: str`, `nombre_interno: str`, `ip: str`, `fecha: datetime` |
| `Lote` | `id: int`, `documento_usuario: str`, `nombre_original: str`, `ip: str`, `fecha: datetime` |
| `Pagina[T]` | `elementos: tuple[T, ...]`, `total: int`, `limite: int`, `desplazamiento: int` |

### 1.2 Reglas (`reglas.py`)

`ReglasLiquidacion` es una instantánea de las reglas, leída una vez por lote.

| Campo | Valor actual (código PHP) |
|---|---|
| `estados_permitidos: frozenset[str]` | V, J, T, A, Q, B |
| `estados_terminacion: frozenset[str]` | T, H |
| `evento_periodo: int` | 80 |
| `evento_terminacion: int` | 82 |
| `concepto_matricula: int` | 1 |
| `concepto_exclusivo_pregrado: int` | 19 |
| `conceptos_por_columna: Mapping[TipoPlantilla, Mapping[int, int]]` | pregrado 2→2, 3→3, 4→4; posgrado 4→2, 5→3, 6→4 |
| `exenciones_por_columna: Mapping[TipoPlantilla, Mapping[int, int]]` | según `templates-analysis.md` |
| `id_exencion_votacion: int` | 1 |
| `porcentaje_por_exencion: Mapping[int, Decimal]` | de la tabla MySQL `exencion`, en solo lectura, como hoy (F11); no viene de "parametros" |
| `id_exencion_secretaria: int` | 16: la Secretaría de Educación no cuenta como descuento para C2 (F12) |
| `nivel_pregrado: str` | PREGRADO (valor de `ACTIPCRA.tra_nivel`, F5) |
| `porcentajes_por_defecto: Mapping[int, tuple[int, ...]]` | 1: (100); 2: (60, 40); 3: (40, 30, 30) |
| `dias_fecha_extraordinaria: int` | 8 |

Ya no hay umbral de la votación automática (90): lo reemplaza el tope de 100% de `exenciones`, que es una constante del dominio y no una regla de "parametros" (C7, 2026-11-25).

```python
class ReglasLiquidacion:
    def exencion_de_columna(self, tipo: TipoPlantilla, columna: int) -> int | None: ...
    def concepto_de_columna(self, tipo: TipoPlantilla, columna: int) -> int | None: ...
    def porcentaje_exencion(self, id_exencion: int) -> Decimal: ...
    def porcentaje_por_defecto(self, numero_cuotas: int, posicion: int) -> int: ...
```

### 1.3 Plantillas (`plantillas.py`)

```python
@dataclass(frozen=True)
class EspecificacionPlantilla:
    tipo: TipoPlantilla
    texto_a1: str
    fila_inicial: int
    num_columnas: int                  # pregrado 13, posgrado 29
    encabezados: tuple[str, ...]       # textos oficiales; D1 (pregrado) y D2 (SMLV)
    columnas_concepto: range           # pregrado 2–4; posgrado 4–6
    columnas_exencion: range           # pregrado 5–13; posgrado 7–17
    columna_votacion: int              # pregrado 5; posgrado 7
    columna_unidad: int | None         # posgrado 2
    columna_cuotas: int | None         # posgrado 3
    columnas_fecha: tuple[tuple[int, int, int], ...]  # posgrado (18,19,20), (21,22,23), (24,25,26); pregrado una terna de la fecha ordinaria, según D1 (C3, F8)
    trae_fecha_extraordinaria: bool    # no, en las dos plantillas: se calcula (F8)
    columnas_porcentaje: tuple[int, ...]              # posgrado 27, 28, 29

def identificar(hoja: HojaPlantilla) -> EspecificacionPlantilla: ...
    # FormatoInvalido("Plantilla no reconocida") si A1 no coincide con ninguna plantilla
def validar_formato(hoja: HojaPlantilla, espec: EspecificacionPlantilla) -> None: ...
    # FormatoInvalido: número de columnas, encabezados; mensaje propio para la plantilla de 14 columnas
def extraer_filas(hoja: HojaPlantilla, espec: EspecificacionPlantilla) -> list[FilaPlantilla]: ...
    # desde fila_inicial; omite las filas vacías (una celda con solo espacios cuenta como vacía, F4);
    # una fila con datos y sin código se devuelve para que validar_codigo la rechace (F3)
```

### 1.4 Validaciones

```python
# validacion_filas.py
def validar_codigo(fila: FilaPlantilla) -> int | Rechazo: ...
    # sin código: CODIGO_INVALIDO "Falta el código del estudiante" (F3); los repetidos los marca el caso de uso (F2)
def validar_posgrado(fila: FilaPlantilla, espec: EspecificacionPlantilla) -> DatosPosgrado | Rechazo: ...
    # cuotas obligatorias, de 1 a 3 (vacío o fuera de rango: CUOTAS_INVALIDAS, RE-03 y RE-04)
    # cada cuota con fecha existente y año de 4 dígitos (si falta: FECHA_INVALIDA, RE-06); porcentajes enteros 0–100 o vacíos
    # ninguna fecha ordinaria anterior al día de la carga y cada cuota después de la anterior (FECHA_INVALIDA, F7)
    # columna 2 obligatoria y > 0: entero en créditos, hasta dos decimales en SMLV (UNIDAD_INVALIDA, F6)

# validacion_estudiante.py
def validar(fila: FilaPlantilla, codigo: int, estudiante: Estudiante | None,
            contexto: ContextoCarrera | None, tipo: TipoPlantilla, reglas: ReglasLiquidacion) -> Rechazo | None: ...
    # en el orden actual: existencia → valor de matrícula → estado → proyecto activo → terminación de materias;
    # después las nuevas: periodo vigente (SIN_PERIODO_VIGENTE, RE-05, A13) → nivel frente a la plantilla (NIVEL_NO_CORRESPONDE, F5)
```

### 1.5 Cálculo

```python
# fechas.py
def fecha_extraordinaria(ordinaria: date, dias: int, festivos: AbstractSet[date]) -> date: ...
    # suma días calendario; si cae en festivo, avanza un día a la vez hasta el primero que no lo sea

# cuotas.py
def cuotas_pregrado(fechas: FechasPago) -> tuple[Cuota]: ...
    # la fecha ordinaria viene de la fila de la plantilla (C3); la extraordinaria se calcula como en posgrado (F8)
def cuotas_posgrado(datos: DatosPosgrado, reglas: ReglasLiquidacion,
                    festivos: AbstractSet[date]) -> tuple[Cuota, ...] | Rechazo: ...
    # completa los porcentajes vacíos por posición; rechaza si la suma no es 100

# exenciones.py
def seleccionar(fila: FilaPlantilla, espec: EspecificacionPlantilla, reglas: ReglasLiquidacion,
                tiene_certificado: bool) -> tuple[int, ...] | Rechazo: ...
    # 1. descuentos marcados = columnas de exención marcadas, sin la de votación ni la de la Secretaría de Educación (F12)
    # 2. más de un descuento marcado: Rechazo DESCUENTOS_NO_ACUMULABLES; la fila no se sube (C2)
    # 3. votación marcada: se registra, sola o con el descuento, en las dos plantillas (C2)
    # 4. sin votación marcada: se agrega la automática si hay certificado y hay un descuento marcado (C1, C6, A14)
    # 5. si el descuento más la votación pasa de TOPE_EXENCIONES (100), se quita la votación y queda solo el descuento (C7)
    # 6. la votación aparece una sola vez
    # 7. orden: votación, descuento y al final la Secretaría (RE-24). F14 y F15 fijan cómo entra la Secretaría en 4 y 5

# conceptos.py
def seleccionar(fila: FilaPlantilla, espec: EspecificacionPlantilla,
                reglas: ReglasLiquidacion) -> tuple[int, ...]: ...
    # matrícula + exclusivo de pregrado (solo pregrado) + conceptos de las columnas marcadas

# generador_solicitud.py
def generar(fila: FilaPlantilla, espec: EspecificacionPlantilla, codigo: int,
            estudiante: Estudiante, contexto: ContextoCarrera, reglas: ReglasLiquidacion,
            festivos: AbstractSet[date], tiene_certificado: bool) -> Solicitud | Rechazo: ...
    # FECHA_INVALIDA si faltan fechas en la plantilla (RE-06); el periodo ya lo validó validacion_estudiante
```

## 2. Aplicación (`app/application/`)

### 2.1 Puertos (`typing.Protocol`)

```python
class LectorPlantilla(Protocol):
    def leer(self, contenido: bytes) -> HojaPlantilla: ...            # ArchivoNoLegible

class AlmacenamientoArchivos(Protocol):
    def guardar(self, contenido: bytes, nombre_interno: str) -> None: ...

class RepositorioAcademico(Protocol):
    def estudiantes(self, codigos: Sequence[int]) -> Mapping[int, Estudiante]: ...
    def contextos_carrera(self, codigos_carrera: AbstractSet[int], evento_periodo: int,
                          evento_terminacion: int) -> Mapping[int, ContextoCarrera]: ...
    def con_certificado_electoral(self, codigos: Sequence[int]) -> frozenset[int]: ...

class RepositorioSolicitudes(Protocol):
    def registrar_lote(self, lote: NuevoLote) -> int: ...
    def cancelar_sin_imprimir(self, codigo_estudiante: int) -> tuple[int, ...]: ...
        # transacción propia: estado 0 → 2 de las sin imprimir del estudiante, de cualquier periodo, como hoy (C8); devuelve los ids (AD-25, AD-30); ErrorPersistencia
    def guardar_solicitud(self, solicitud: Solicitud, documento_usuario: str,
                          creada_en: datetime) -> int: ...
        # una transacción: recibo, cuotas, exenciones y conceptos; devuelve el id; ErrorPersistencia. No revierte la cancelación (RE-02)
    def listar_lotes(self, limite: int, desplazamiento: int) -> Pagina[Lote]: ...
    def porcentajes_exencion(self, ids: AbstractSet[int]) -> Mapping[int, Decimal]: ...
        # solo lectura de la tabla `exencion` (F11); si falta un id: ReglaFaltante, y el lote no se procesa (AD-22)

class FuenteReglas(Protocol):
    def obtener(self) -> ReglasLiquidacion: ...                       # DependenciaNoDisponible, RespuestaInvalida

class FuenteFestivos(Protocol):
    def festivos(self, desde: date, hasta: date) -> frozenset[date]: ...

class ProveedorIdentidad(Protocol):
    def usuario(self, token: str) -> Usuario: ...                     # NoAutenticado

class Reloj(Protocol):
    def ahora(self) -> datetime: ...                                  # America/Bogota
```

### 2.2 Casos de uso

```python
@dataclass(frozen=True)
class CargarLoteComando:
    contenido: bytes
    nombre_original: str
    usuario: Usuario
    ip: str                               # de X-Forwarded-For con los proxies de confianza (AD-29)

class ProcesarLote:                       # UC-01
    def ejecutar(self, comando: CargarLoteComando) -> ResumenLote: ...
        # FormatoPlantillaInvalido(id_lote, motivo), DependenciaNoDisponible, RespuestaInvalida

class ConsultarLotes:                     # UC-02
    def ejecutar(self, limite: int, desplazamiento: int) -> Pagina[Lote]: ...

class AutorizarUsuario:                   # UC-03
    def ejecutar(self, usuario: Usuario) -> None: ...                 # AccesoDenegado
```

## 3. Infraestructura (`app/infrastructure/`)

| Clase | Constructor | Métodos |
|---|---|---|
| `RepositorioAcademicoOracle` | `engine` (`oracle+oracledb`) | Los del puerto. Consultas en bloques de hasta 1000 códigos (límite de `IN` en Oracle) |
| `RepositorioSolicitudesMySQL` | `engine` (`mysql+pymysql`), `prefijo_tablas` | Los del puerto. `cancelar_sin_imprimir` y `guardar_solicitud` usan cada uno su propio `engine.begin()` (AD-30) |
| `AlmacenamientoS3` | cliente boto3, `bucket` | `guardar`: `put_object` con cifrado del lado del servidor |
| `LectorXlrd` | — | `leer`: `xlrd.open_workbook(file_contents=...)`, primera hoja, solo celdas con contenido |
| `ProveedorIdentidadWso2` | `url_userinfo`, cliente httpx | `usuario`: llama a `/oauth2/userinfo` en cada petición, sin caché (AD-09) |
| `ClienteParametros` | `url_base`, `reglas: Mapping[str, EspecificacionParametro]`, cliente httpx | `obtener`: `GET /v1/parametro/{id}` por regla y arma `ReglasLiquidacion`. `_leer(id) -> ParametroDTO` valida el sobre (`Success`, `Status` 2xx como texto o entero, `Data.Id`, `Data.Activo`). `_convertir(parametro, espec) -> Any` toma el campo y aplica el formato (AD-21) |
| `FuenteFestivosWeboffice` | `engine` de la base donde está la tabla de festivos de weboffice (D5) | `festivos`: lee esa tabla en solo lectura (F9); los sábados y domingos no se agregan (F10) |
| `LectorSsm` | cliente boto3 | `secreto(ruta) -> str` (`WithDecryption=True`) |
| `CapturaSql` | `ContextVar[list[str]]` | `registrar(engine)`; `iniciar()`; `sentencias() -> list[str]` |
| `RelojBogota` | — | `ahora` con `zoneinfo.ZoneInfo("America/Bogota")` |

Respuesta de "parametros" (según el ejemplo del usuario) y mapeo de reglas (AD-21):

```python
# infrastructure/parametros/modelos.py
class ReferenciaId(BaseModel):
    Id: int

class ParametroDTO(BaseModel):            # Data de GET /v1/parametro/{id}
    Id: int
    Nombre: str = ""
    Descripcion: str = ""
    CodigoAbreviacion: str = ""
    Activo: bool
    NumeroOrden: int = 0
    TipoParametroId: ReferenciaId | None = None
    ParametroPadreId: ReferenciaId | None = None
    # FechaCreacion y FechaModificacion no se usan

class RespuestaParametros(BaseModel):     # sobre CRUD
    Success: bool
    Status: str | int                     # el servicio envía "200"
    Message: str | None = None
    Data: ParametroDTO | None = None

@dataclass(frozen=True)
class EspecificacionParametro:            # una por regla, desde configuración
    regla: str                            # p. ej. "evento_terminacion"
    id: int                               # id del parámetro en ese ambiente
    campo: Literal["CodigoAbreviacion", "Nombre", "Descripcion", "NumeroOrden"]
    formato: Literal["entero", "decimal", "texto", "lista", "fecha", "json"]
```

## 4. Interfaces (`app/interfaces/`)

```python
# controllers/lotes_controller.py
def crear_lote() -> Response: ...        # POST /v1/lotes
def listar_lotes() -> Response: ...      # GET /v1/lotes

# controllers/estado_controller.py
def raiz() -> Response: ...              # GET /       → {"status": "ok"}
def salud() -> Response: ...             # GET /health → {"status": "UP"}

# schemas/respuesta.py
def exito(status: int, data: Any, metadata: Any | None = None, mensaje: str | None = None) -> Response: ...
def error(status: int, mensaje: str | None = None, data: Any | None = None) -> Response: ...

# middlewares
def registrar_cors(app: Flask, origenes: list[str]) -> None: ...
def autenticar() -> None: ...                     # before_request en /v1/*: 401 / 403
def iniciar_auditoria() -> None: ...              # before_request: limpia la captura de SQL
def registrar_auditoria(resp: Response) -> Response: ...  # after_request en /v1/*: log JSON
def agregar_cabeceras(resp: Response) -> Response: ...    # after_request en todas las rutas
def registrar_trazas(app: Flask) -> None: ...     # X-Ray
def registrar_manejadores_error(app: Flask) -> None: ...  # excepción → sobre institucional
```
