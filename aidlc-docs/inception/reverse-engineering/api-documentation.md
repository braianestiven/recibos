# Documentación de interfaces (API)

- Etapa: INCEPTION → Reverse Engineering (2026-11-25)
- El sistema actual **no tiene API REST**. Esta sección documenta su interfaz HTTP real (formularios a `index.php`), sus interfaces internas y sus modelos de datos
- La API del sistema nuevo (`POST /v1/lotes`, `GET /v1/lotes`) ya está definida en `application-design/api-contract.md` y no se repite aquí

## Interfaz HTTP del sistema actual

Todas las peticiones van a `index.php`. El framework (no está en el repositorio) descifra los parámetros con `encriptar` y elige el bloque.

### Mostrar el formulario de carga
- **Método**: GET
- **Ruta**: `index.php?pagina=...` con los parámetros cifrados
- **Propósito**: `bloque.php` llama a `html()` → `nuevoRegistro` y dibuja el formulario
- **Petición**: sin campos propios
- **Respuesta**: HTML con un campo `archivo` y un campo oculto `formulario`

### Procesar un lote
- **Método**: POST, `multipart/form-data`
- **Ruta**: `index.php`
- **Propósito**: cargar la plantilla y generar las solicitudes (BT-03 a BT-08)
- **Petición**:
  - `archivo`: el `.xls`
  - `formulario`: texto cifrado con `pagina=registro_recibo_lote&procesar=true&nivel=<nivel>` (`funcion.class.php` 121–124). `action()` no usa el `nivel` que viene aquí: lo lee de la sesión
- **Respuesta**: HTML. Puede ser el resumen (procesados, rechazados con motivo y totales) o uno de estos mensajes de `mensajeErrorCarga`:

| Tipo | Encabezado | Cuándo |
|---|---|---|
| `noArchivo` | ERROR EN LA CARGA DEL ARCHIVO | No se pudo guardar el archivo o el usuario no tiene identificación |
| `sinLeer` | ERROR EN LA LECTURA DEL ARCHIVO | El lector no pudo abrir el `.xls` (el archivo ya quedó guardado y el lote registrado) |
| `inconsistencia` | EL ARCHIVO NO SE HA PODIDO CARGAR AL SISTEMA | Número de columnas distinto de 14 y 29, texto de A1 desconocido o usuario sin carreras |
| `parcial` | ARCHIVO PROCESADO PARCIALMENTE | Hubo al menos un estudiante rechazado; va antes del resumen |

En `inconsistencia`, `sinLeer` y `parcial` se muestra como "número de solicitud" el nombre interno del archivo sin la extensión.

### Interfaces fuera de alcance
- `admin_historicoPorEstudiante`: POST a `index.php` con `estudiante`, `action=admin_generados` y `opcion=generadoEstudiante`. Lo atiende `admin_generados`, que no está.
- `admin_consultasCoordinador`, el módulo de notas de Admisiones, Registro y Control (el nombre dice "coordinador" por error, RE-19): `opcion` = `verProyectos`, `controlNotas`, `registroAcuerdo`, `seleccionPeriodo` o `histNotas`, con `carrera`, `periodo`, `usuario`, `nivel`, `nomcra` y `tipoUser` tomados de `$_REQUEST` (R2, R3). Con `tipoUser=132` aplica las reglas de ARC: todos los proyectos activos y carga de novedades de notas sin la ventana del evento 89. `registroAcuerdo` llama a un método que no existe. Enlaza a `adminReportesExcelCoordinador` (Excel), `registro_notasDocente` (reporte de notas del curso) y `registro_cargarNovedadesNotasCurso` (novedades de notas), que no están en el repositorio.

### Contratos externos que usará el sistema nuevo
Ya están en los requisitos; se listan para tener el inventario completo:
- Servicio "parametros": `GET /v1/parametro/{id}`, sobre CRUD con `Status` como texto (RF-09 CA2, AD-20 a AD-22).
- WSO2 IS: `GET /oauth2/userinfo` con el token Bearer. En `utils_oas/auditoria` la respuesta se lee con los campos `documento`, `documento_compuesto`, `email`, `role` y `sub` (AD-09, A8).

## Interfaces internas

### `funciones_registroLoteRecibo` (`funcion.class.php`)

| Método | Parámetros | Devuelve | Qué hace |
|---|---|---|---|
| `__construct($configuracion, $sql)` | Configuración y catálogo SQL | — | Abre MySQL, lee la sesión, abre la cuenta de Oracle del nivel o termina con "NO TIENE PERMISOS" |
| `nuevoRegistro($configuracion, $acceso_db)` | — | — (escribe HTML) | Formulario de carga |
| `cargarArchivoLote($configuracion)` | — | Arreglo `nombreArchivo`, `nombreInterno`, `ip`, `id_usuario`, o `false` | Guarda el archivo y registra el lote |
| `leerArchivoLote($configuracion, $archivo)` | Nombre interno | Objeto del lector o `false` | Lee el `.xls` |
| `verificarLote($valor, $data, $tipo, $configuracion)` | Nombres del archivo, datos leídos, texto de A1 | `true` o `false` | Identifica la plantilla, recorre las filas y escribe el resumen. La llamada pasa un quinto argumento que no se declara (R13) |
| `verificarCodigo($configuracion, $carrera)` | Carreras permitidas | Fila del estudiante o `false` (motivo en `errorProceso`) | Existencia, matrícula, estado y carrera |
| `procesarRegistro($configuracion, $registro)` | Celdas de la fila | `true` o `false` | Cancela, revisa el evento 82 y las fechas de posgrado, y guarda todo |
| `verificarSolicitudCodigo($configuracion, $codigoPagador)` | Código del estudiante | Siempre `true` | Cancela las solicitudes sin imprimir |
| `guardarSolicitud($configuracion)` | — (usa `$this->solicitud`) | Id insertado o `false` | Inserta `solicitudRecibo` |
| `guardarCuotas($configuracion, $registro)` | Celdas de la fila | Siempre `true` | Decide las cuotas y llama a `guardarCuota` |
| `guardarCuota($configuracion, $registro = '')` | Celdas (solo pregrado) | Resultado del INSERT | Fechas de la facultad (pregrado) e inserción |
| `guardarExencion($configuracion, $exencion)` | Columnas marcadas | Texto concatenado (siempre verdadero) | Mapea columnas, filtra la votación, inserta y agrega la automática |
| `guardarConcepto($configuracion, $concepto)` | Columnas marcadas | `true` | Inserta 1, 19 (pregrado) y 2 a 4 |
| `conceptoPlantilla`, `exencionPlantilla`, `cuotaPlantilla` | Celdas y tipo | Arreglo, `false` o texto | Extraen columnas marcadas y el número de cuotas |
| `verificaCalendario($configuracion, $carrera, $evento)` | Carrera y evento | `'S'` o `'N'` (resultado de `fua_verifica_evento`) | Evento activo |
| `periodoActual($configuracion, $variable)` | Carrera | Filas `[año, periodo]` o `false` | Periodo con el evento 80 |
| `carrerasCoordinador`, `carrerasTotales` | Documento | Filas `[cra_cod]` o `false` | Carreras permitidas |
| `mensajeErrorCarga($configuracion, $tipo, $valor)` | Tipo de mensaje | — (escribe HTML) | Mensajes de error |

### `sql_registroLoteRecibo::cadena_sql($configuracion, $conexion, $opcion, $variable)`
- **Parámetros**: `$opcion` es el nombre de la sentencia; `$variable` es un valor o un arreglo. Antes de armar el texto se pasa por `$conexion->verificar_variables`, cuyo código no está.
- **Devuelve**: el texto SQL con los valores concatenados. Las 22 opciones están en `code-structure.md`.

### `funcionGeneral`

| Método | Devuelve | Qué hace |
|---|---|---|
| `ejecutarSQL($configuracion, $conexion, $cadena_sql, $tipo)` | Filas como arreglo indexado (`"busqueda"`) o el resultado de la sentencia | Ejecuta en la conexión dada |
| `rescatarValorSesion($configuracion, $conexion, $tipo)` | Valor o `false` | Lee `id_usuario`, `identificacion`, `nivelUsuario`, `usuario` |
| `conectarDB($configuracion, $nombre)` | Recurso de conexión | `""` = MySQL; `coordinador`, `asistente`, `secretario` = Oracle |
| `datosGenerales($configuracion, $conexion, $tipo, $variable)` | Valor | `anno` y `per` (se reemplazan por `periodoActual` en cada fila) |
| `revisarFormulario()` | — | `strip_tags` sobre `$_REQUEST`; este bloque no la llama |
| `cargarArchivoServidor($configuracion, $parametro, $tipoArchivo)` | Arreglo con nombres e IP, o `false` | Carga con `subir_archivo` |

### Clases del framework que no están (firmas deducidas del uso)

| Clase | Uso visto en el código |
|---|---|
| `dbConexion` | `recursodb($configuracion, $nombre)->conectar_db()`; la conexión expone `ejecutarAcceso`, `verificar_variables`, `ultimo_insertado`, `obtener_conteo_db`, `obtener_afectadas`, `obtener_enlace` |
| `sesiones` | `especificar_enlace`, `numero_sesion`, `rescatar_valor_sesion($configuracion, $tipo)` → `[[valor]]` |
| `datosSolicitud` | `rescatarDatoSolicitud($configuracion, "fechaPagoFacultad", [tipo, facultad], $conexion)` → `[[?, "dd/mm/aaaa", "dd/mm/aaaa"]]` (RE-08) |
| `calendario` | `buscar_festivo($dia, $mes, $anno, $configuracion)` → verdadero si es festivo (D5) |
| `subir_archivo` | Propiedades `directorio_carga`, `nombre_campo`, `tipos_permitidos`, `especial`, `unico`, `permisos`, `tamanno_maximo`; `cargar()`; `log["nombre_archivo"][0]`, `log["mi_archivo"][0]` |
| `Spreadsheet_Excel_Reader` | `read($ruta)`; `sheets[0]['numRows']`, `['numCols']`, `['cells'][fila][columna]` |
| `validarUsu` | `consultarProyectosAsistente($usuario, $nivel, $accesoOracle, $configuracion, $acceso_db)` → filas cuya posición 0 es la carrera |
| `encriptar` | `codificar_url($datos, $configuracion)` |
| `alerta` | `sin_registro($configuracion, $cadena, $encabezado)` |

### Contratos de `utils_oas` que reimplementa el sistema nuevo

| Paquete | Función | Firma |
|---|---|---|
| `apiStatusLib` | `Init` | `func Init()` |
| `auditoria` | `InitMiddleware`, `InitWithAuthEnforcer`, `LogRequest` | `func InitMiddleware()`; `func InitWithAuthEnforcer()`; `func LogRequest(ctx *beegoCtx.Context)` |
| `requestresponse` | `APIResponseDTO` | `func APIResponseDTO(success bool, statusCode int, data interface{}, customMessage ...interface{}) APIResponse` |
| `requestresponse` | `APIResponseMetadataDTO` | `func APIResponseMetadataDTO(success bool, statusCode int, data interface{}, metadata interface{}, customMessage ...interface{}) APIResponseMeta` |
| `security` | `SetSecurityHeaders` | `func SetSecurityHeaders()` |
| `ssm` | `GetValueFromParameterStore` | `func GetValueFromParameterStore(ctx context.Context, name string) (string, error)` |
| `database` | `BuildOracleConnectionString` | `func BuildOracleConnectionString() (string, error)` |
| `xray` | `Init`, `BeginSubsegment`, `CloseSubsegment` | `func Init()`; `func BeginSubsegment(ctx context.Context, req *http.Request) (context.Context, *xray.Segment)`; `func CloseSubsegment(subseg *xray.Segment, resp *http.Response, err error)` |
| `time_bogota` | `Tiempo_bogota` | `func Tiempo_bogota() time.Time` |
| `request` | `ExtractData` | `func ExtractData(respuesta map[string]interface{}, v interface{}, err2 error) error`. Hace `panic` si `Success` es falso; el sistema nuevo no copia ese comportamiento (`services.md`, errores) |

## Modelos de datos

### Tablas MySQL (columnas que usa el código; el DDL real es D4)

| Tabla | Columnas | Relaciones | Validación en el código |
|---|---|---|---|
| `solicitudLote` | `id_usuario`, `nombreOriginal`, `nombreInterno`, `ip`, `fecha` | Ninguna conocida | `fecha` = `time()`; ninguna otra |
| `solicitudRecibo` | `id_solicitud_recibo` (llave, leída en `datosSolicitud`), `id_usuario`, `codigo_est`, `estado`, `anno`, `periodo`, `fecha`, `cuota`, `id_carrera`, `tipoPlantilla`, `unidad` | 1 a N con cuotas, exenciones y conceptos | `estado` = `'0'` al insertar; `fecha` = `time()`; el resto sin validar |
| `solicitudCuota` | `id_solicitud`, `cuota`, `porcentaje`, `fecha_ordinaria`, `fecha_extra` | N a 1 con `solicitudRecibo` | Fechas en timestamp Unix; porcentaje sin validar en pregrado |
| `solicitudExencion` | `id_solicitud`, `id_exencion` | N a 1 con `solicitudRecibo`; `id_exencion` apunta a `exencion` | Solo se inserta si `exencion` tiene el porcentaje |
| `solicitudConcepto` | `id_solicitud`, `id_concepto` | N a 1 con `solicitudRecibo` | Ninguna |
| `exencion` | `id_exencion`, `nombre`, `porcentaje`, `etiqueta`, `tipo`, `soporte`, `EXE_COD` | Catálogo | Solo se lee `porcentaje` |
| `fechaPagoFacultad` | No se conocen (la consulta está en `datosSolicitud`) | Por facultad y tipo | El sistema nuevo no la usa: las fechas vienen de la plantilla (C3) |

Todas llevan el prefijo `$configuracion["prefijo"]` (AD-18).
### Lo que lee y escribe "Solicitados" (`admin_solicitudCoordinador`, RE-20)
| Objeto | Lee | Escribe |
|---|---|---|
| `solicitudRecibo` | Todas las columnas, solo con `estado=0` | `estado='1'`, `secuencia` y `observacion` al generar |
| `solicitudCuota` | `cuota`, `porcentaje`, `fecha_ordinaria`, `fecha_extra` (timestamp Unix) | — |
| `solicitudExencion` y `exencion` | `id_exencion`, `nombre`, `porcentaje`, `etiqueta`, `tipo`, `soporte`; solo las dos primeras filas cuentan (RE-24) | — |
| `solicitudConcepto` y `referenciaPago` | `id_concepto`, `etiqueta`, `valor`, `factor` y `base` (la consulta no dice de qué tabla sale cada una) | — |
| `consiga` (MySQL) | — | `id_secuencia`, `anno`, `cadena`, `id_usuario` |
| `ACEST`, `V_ACESTMATBRUTO`, `ACCRA` | Estudiante, valor de matrícula de pregrado y facultad | — |
| `ACVLRSCS` | Valores de seguro, carnet y sistematización | — |
| `acdeudores` | Deudas del estudiante; el resultado no se usa (TD-21) | — |
| `ACESTMAT`, `ACREFEST`, `acrefban` | Pagos ya registrados | Cuotas del recibo (`ACESTMAT`) y sus conceptos (`ACREFEST`); desactiva las cuotas sin pagar del periodo |

### Objetos de Oracle (solo lectura)

| Objeto | Columnas que usa el código | Para qué |
|---|---|---|
| `ACEST` | `est_cod`, `est_nro_iden`, `est_nombre`, `est_cra_cod`, `est_diferido`, `est_estado_est` | Estudiante, estado y carrera. `est_nro_iden` y `est_nombre` se leen pero no se usan |
| `V_ACESTMATBRUTO` | `emb_est_cod`, `emb_valor_matricula` | Que exista el valor de matrícula; el valor no se usa |
| `ACCRA` | `cra_cod`, `cra_abrev`, `cra_estado`, `cra_dep_cod`, `CRA_EMP_NRO_IDEN` | Carrera activa, facultad y coordinador |
| `ACASPERI` y `ACASPERIEVENTOS` | `ape_ano`, `ape_per`, `ape_estado`; `acn_estado`, `acn_cra_cod`, `acn_cod_evento` | Periodo vigente con el evento 80 |
| `ACCERELECTORAL` | `cer_est_cod`, `cer_fecha`, `cer_estado` | Certificado electoral activo |
| `fua_verifica_evento(carrera, evento)` | — | Evento 82 |
| `mntac.fua_verifica_diferido(est_cod)` | — | Diferido (se elimina) |

### Objetos de Oracle del módulo de notas de ARC (Fase 2)

| Objeto | Columnas que usa el código | Para qué |
|---|---|---|
| `ACASPERI` | `ape_ano`, `ape_per`, `ape_estado` | Periodos en estado 'A', 'X' o 'P', uno por estado (RE-18) |
| `ACCRA` | `cra_cod`, `cra_abrev`, `cra_estado`, `cra_emp_nro_iden`, `cra_dep_cod` | Proyectos activos; proyectos del coordinador o de la facultad |
| `GEDEP`, `PEEMP` | `dep_cod`, `dep_nombre`, `dep_emp_cod`; `emp_cod`, `emp_nro_iden`, `emp_nombre`, `emp_car_cod` (218 = decano), `emp_estado_e` | Facultad del decano |
| `ACDOCENTE` | Nombre, identificación, teléfono, celular, correos y estado del docente | Datos del docente en el control de notas |
| `V_ACINSNOTPAR`, `V_ACINSNOTPAR_ANTERIOR` | Asignatura, grupo, parciales 1 a 6, examen y definitiva | Notas parciales del periodo |
| `ACASI`, `ACCARGAS`, `ACCURSOS`, `ACHORARIOS` | Asignatura, carga del docente, curso, horario | Unir notas, cursos y docentes |
| `ACCALEVENTOS` | `ACE_ANIO`, `ACE_PERIODO`, `ACE_CRA_COD`, `ACE_COD_EVENTO`, `ACE_FEC_INI`, `ACE_FEC_FIN` | Evento 71 (cierre de semestre) y evento 89 (fechas de novedades de notas) |
| `ACEST`, `GEUSUCRA` | `est_cod`, `est_cra_cod`; `usucra_cra_cod`, `usucra_nro_iden` | Estudiante de las carreras del usuario; 999 = todas las carreras. Consulta sin uso |

### Plantillas

Las columnas de cada plantilla y su uso están en `templates-analysis.md`. Resumen de lo que lee el código:

| Tipo | A1 | Primera fila | Columnas |
|---|---|---|---|
| 1 Pregrado | `PLANTILLA GENERAL PREGRADOS` | 4 | 1 código; 2–4 conceptos (la 2 también se lee como cuota, RE-09); 5–14 exenciones (la 14 es Reingreso, se elimina). La plantilla nueva trae además las fechas de pago (C3, D1) |
| 2 Posgrado créditos | `PLANTILLA GENERAL POSTGRADOS CREDITOS` | 5 | 1 código; 2 unidad; 3 cuotas; 4–6 conceptos; 7–17 exenciones; 18–26 día, mes y año de las cuotas 1 a 3; 27–29 porcentajes |
| 3 Posgrado SMLV | `PLANTILLA GENERAL POSTGRADOS SALARIOS MINIMOS LEGALES` | 5 | Igual que el tipo 2 en el código; falta el archivo oficial (D2) |
