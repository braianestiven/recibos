# Historias y casos de uso frente al código actual

- Etapa: INCEPTION → Reverse Engineering (2026-11-25)
- Compara: `user-stories/stories.md` (US-01 a US-15), `application-design/services.md` (UC-01 a UC-03) y `requirements/requirements.md` contra `codigo-fuente/weboffice/`
- Los números entre paréntesis son líneas de `bloque/registro_lote_recibo/funcion.class.php`, salvo que se indique otro archivo
- Las decisiones del usuario del 2026-11-25 ya se aplicaron a los requisitos, las historias y el diseño (sección 4). Las aclaraciones C1 a C5 se respondieron y aplicaron el 2026-11-25 (`reverse-engineering-clarification-questions.md`). RE-18 y RE-19 se agregaron el 2026-11-25, al leer completo `admin_consultasCoordinador` RE-20 a RE-26 salen de `admin_solicitudCoordinador` ("Solicitados"), que se agregó al workspace y se analizó el 2026-11-25 a pedido del usuario; sus preguntas abiertas son C7 y C8, y C6 sale de la respuesta del usuario a A14.

Valores de la columna "Resultado":
- **Igual**: el sistema nuevo hace lo mismo que el código.
- **Cambio acordado**: difiere a propósito y está en `requirements.md` §12.3 o en una decisión P-n.
- **Nueva**: no tiene equivalente en el código.
- **RE-n**: hay un hallazgo (sección 3).

## 1. Historias

| Historia | Código actual | Resultado | Nota |
|---|---|---|---|
| US-01 Acceso con el rol ARC | `__construct` (28–60): sesión del framework; nivel 4/132, 110 o 114 abre una cuenta de Oracle distinta; otro nivel se rechaza | Cambio acordado (IN-9) | En este bloque el nivel sale de la sesión, no de `$_REQUEST`. El permiso manipulable (R3) está en `admin_consultasCoordinador` |
| US-02 Cargar el archivo | `cargarArchivoLote` (157–180) y `funcionGeneral::cargarArchivoServidor` (100–168): solo revisa la extensión `xls`, sin límite de tamaño (línea 115 comentada), permisos `0777`, nombre interno único, lote registrado antes de leer el archivo | Cambio acordado (RF-01; punto 7 de §12.3) | El orden "registrar y luego validar el formato" es igual (P-9). Si el usuario no tiene identificación, hoy el archivo queda en el disco sin lote (166–173); el sistema nuevo responde 403 (UC-03). La IP es RE-13 |
| US-03 Formato de pregrado | `bloque.php` (64) acepta 14 o 29 columnas; A1 `PLANTILLA GENERAL PREGRADOS`; fila 4 | Cambio acordado (13 columnas, punto 1) | Bloqueada por D1 |
| US-04 Formato de créditos | A1 `PLANTILLA GENERAL POSTGRADOS CREDITOS`; fila 5; 29 columnas | Igual, más validación de encabezados | Hoy un archivo de créditos con 14 columnas también pasa el control de columnas |
| US-05 Formato SMLV | A1 `...SALARIOS MINIMOS LEGALES`; fila 5; misma lógica que créditos | Igual | Bloqueada por D2 |
| US-06 Validar al estudiante | `verificarCodigo` (506–545) y evento 82 en `procesarRegistro` (417–427) | Igual en reglas y orden | RE-14 (motivo vacío) y RE-16 (código no numérico). Hoy el motivo del escenario 6 es "La carrera del estudiante no se puede asociar a la del usuario" |
| US-07 Solicitudes de pregrado | `guardarCuotas` (909–964), `guardarCuota` (823–892), `guardarExencion` (552–650), `guardarConcepto` (672–721) | Cambio acordado (puntos 2, 3 y 4) | **RE-01** (escenario 8), RE-06, RE-08 y RE-10. Escenario 10 igual: la columna 8 cambia las fechas aunque se registre otro descuento (838) |
| US-08 Solicitudes de posgrado | `procesarRegistro` (436–451) y `guardarCuotas` (969–1024) | Cambio acordado (puntos 4, 5 y 7) | **RE-01** (escenario 10), RE-03, RE-04 y RE-17. Escenario 9 igual (RE-10) |
| US-09 Cancelar las anteriores | `verificarSolicitudCodigo` (391–402): estado 0 → 2 en todos los periodos | Cambio acordado (P-7, punto 6) | RE-02 (escenario 3) |
| US-10 Guardar completa o no guardar | Sin transacción; los fallos de cuotas, exenciones y conceptos no se detectan porque los resultados se concatenan con `.=` (630, 681, 711) | Cambio acordado (RF-10, IN-6) | — |
| US-11 Entregar a "Solicitados" | Columnas de `sql.class.php` `insertarSolicitud`, `insertarCuota`, `insertarExencion`, `insertarConcepto` | Igual en columnas | RE-07 (`unidad` en pregrado), RE-09 y RE-21 (`cuota` en pregrado: D3 resuelta, A15), RE-05 y RE-06 (valores vacíos), RE-20 a RE-26 (lo que lee "Solicitados") |
| US-12 Resumen del lote | HTML con códigos procesados, rechazados y motivo (310–379) | Igual en contenido | Hoy el "número de solicitud" que se muestra es el nombre interno del archivo sin extensión (`mensajeErrorCarga`); el sistema nuevo usa `id_lote` |
| US-13 Historial de lotes | No hay | Nueva | RE-15 |
| US-14 Auditoría | No hay; solo un `error_log` de la consulta `porcentajeExencion` (`sql.class.php` 227) | Nueva | — |
| US-15 Reglas en "parametros" | Reglas fijas en el código y en las tablas MySQL `exencion` y `fechaPagoFacultad` | Cambio acordado (C-1, P-15) | RE-12 |

## 2. Casos de uso

### UC-01 Procesar lote

| Paso | Diseño | Código actual | Resultado |
|---|---|---|---|
| 1 | Token y rol | Sesión y nivel en el constructor | Cambio acordado |
| 2 | Campo, nombre, tamaño, tipo real | Solo extensión; nombre saneado por `subir_archivo` (`funcionGeneral` 117) | Cambio acordado (punto 7) |
| 3 | Leer reglas de "parametros" | Reglas fijas | Cambio acordado (C-1) |
| 4 | Guardar en S3 | Disco local, `0777` | Cambio acordado (RF-01) |
| 5 | Registrar en `solicitudLote` | `insertarLote`, en el mismo punto del flujo | Igual |
| 6 | Formato | `bloque.php` (64) y `verificarLote` (216–239) | Cambio acordado (RF-02) |
| 7 | Extraer filas; omitir las que no tienen código | Igual (276) | Igual |
| 8 | Máximo de filas | Sin límite; `set_time_limit(0)` (`funcionGeneral` 102) | Nueva (P-1) |
| 9 | Código numérico | No se valida | RE-16 |
| 10 | Oracle en bloque | Unas 5 consultas por estudiante: `datosEstudiante`, `periodoActual`, `verificaCalendario`, `facultadCarrera` (una por cuota) y `certificadoElectoral`, más `datosBasicosEstudiante` con el evento 82 | Igual en resultado (AD-06) |
| 11 | Festivos | `calendario::buscar_festivo` por cada día (989); la clase no está (D5) | Igual en regla |
| 12 | Dominio fila por fila | `verificarCodigo`, `procesarRegistro`, `guardar*` | RE-02 (orden) |
| 13 | Una transacción por estudiante | Cancelación primero (414) y escrituras sueltas | Cambio acordado (RF-10); RE-02 |
| 14 | Respuesta con el resumen | HTML | Igual en contenido |

Reglas de la orquestación: las filas se procesan en el orden de la plantilla y un código repetido cancela la solicitud que creó la fila anterior. Es igual al código (P-2 sigue pendiente).

### UC-02 Consultar lotes
No tiene equivalente en el código (RE-15).

### UC-03 Autorizar usuario
Hoy la autorización es el nivel de la sesión y, para el nivel 132, todas las carreras activas. El rol único ARC toma ese alcance (RF-03 CA2). El sistema nuevo nunca lee permisos de la petición, igual que este bloque; la diferencia está en `admin_consultasCoordinador`, el módulo de notas de ARC, que lee `tipoUser` de `$_REQUEST` y con el valor 132 entrega los permisos de ARC (RE-19, fuera de alcance).

## 3. Hallazgos

La columna "Qué hacer" es la propuesta inicial; el estado actual de cada hallazgo está en la sección 4.

| ID | Tipo | Qué hacer |
|---|---|---|
| RE-01 | Decisión, alta | Pregunta 1 |
| RE-02, RE-04, RE-05, RE-06 | Registrar como cambio acordado | Pregunta 4 |
| RE-03 | Decisión, media | Pregunta 2 |
| RE-07 | Decisión, baja | Pregunta 3 |
| RE-08, RE-09, RE-13 | Insumo para una etapa siguiente | Se usan en U1 Functional Design, D3 y U1 NFR Design |
| RE-10, RE-11, RE-12, RE-14, RE-15, RE-16, RE-17 | Confirmación | Sin cambios en los artefactos |
| RE-18 | Supuesto nuevo (A13) | Se aplica; el usuario puede anularlo |
| RE-19 | Corrección del nombre del módulo y pregunta de alcance | Aclaración C5 |
| RE-20, RE-22, RE-24 | Confirmación del contrato con "Solicitados" | Sin cambios en las reglas; insumo para U1 Functional Design (P-6, P-15) |
| RE-21 | Insumo que cierra D3 | Supuesto A15 |
| RE-23 | Decisión, alta: recibos con valor negativo en Oracle | Aclaración C7 |
| RE-25 | Insumo para D1 | La fecha extraordinaria de pregrado tiene que existir |
| RE-26 | Decisión, media | Aclaración C8 |

### RE-01 — La votación automática solo se evalúa si la fila tiene alguna exención marcada
- **Código**: `procesarRegistro` llama a `guardarExencion` solo si `exencionPlantilla` devuelve un arreglo (477). `exencionPlantilla` devuelve `false` cuando ninguna columna de exención tiene contenido (760–784). La consulta a `ACCERELECTORAL` está dentro de `guardarExencion` (638–646). Por eso, si la fila no tiene ninguna columna de exención marcada, hoy no se registra la votación aunque el estudiante tenga certificado activo.
- **Artefactos aprobados**: RF-06 CA3 (b) y §4.A punto 4 ("o no hay descuento"), US-07 escenario 8, US-08 escenario 10 y `component-methods.md` (`exenciones.seleccionar`, paso 4) la aplican también a esas filas. La decisión P-13 pidió conservar la regla actual.
- **Efecto**: en las filas sin columnas de exención marcadas, los dos sistemas darían un recibo distinto a los estudiantes con certificado. Rompe la comparación de equivalencia y cambia el valor que se cobra.
- **No verificable aquí**: si "Solicitados" agrega la votación por su cuenta cuando genera el recibo (lee Oracle). Su código no está en el repositorio.

### RE-02 — Hoy la cancelación ocurre antes de las últimas validaciones
- **Código**: `procesarRegistro` cancela las solicitudes sin imprimir (414) antes de revisar el evento 82 (417–427), las fechas de posgrado (436–451) y de guardar la solicitud (463). Un estudiante rechazado en esos pasos, o cuya solicitud no se pudo guardar, pierde hoy sus solicitudes sin imprimir.
- **Artefactos aprobados**: US-09 escenario 3 y UC-01 paso 13 ponen la cancelación en la misma transacción que la inserción, así que un rechazado no pierde nada.
- **Falta**: no está en la lista de cambios acordados (§12.3).

### RE-03 — Posgrado con la columna de cuotas vacía
- **Código**: `cuotaPlantilla` devuelve 1 si la columna 3 está vacía (805–810). La solicitud se genera con una cuota.
- **Artefactos aprobados**: US-08 escenario 6 y `validacion_filas.validar_posgrado` piden cuotas entre 1 y 3, pero no dicen qué pasa con la celda vacía.

### RE-04 — Posgrado con cuotas 0, texto o mayores que 3
- **Código**: con 0 o texto no se validan las fechas (437) y el ciclo de cuotas (971) no se ejecuta, así que se guarda una solicitud sin cuotas. Con 4 o más, la cuarta fecha se lee de las columnas 27 a 29, que son los porcentajes: según su contenido, la fila se rechaza por "fecha errónea" o se guarda una cuarta cuota con fecha inválida y el porcentaje de la cuota anterior.
- **Artefactos aprobados**: US-08 escenario 6 y el motivo `CUOTAS_INVALIDAS` rechazan la fila. El punto 7 de §12.3 no nombra las cuotas.

### RE-05 — Proyecto curricular sin periodo vigente
- **Código**: si la consulta `periodoActual` (1071–1083) no devuelve filas, `anno` y `periodo` quedan vacíos (293–294) y la solicitud se guarda así. La consulta une `ACASPERI` y `ACASPERIEVENTOS` por estado (`sql.class.php` 27–38) y puede devolver más de una fila; el código toma la primera.
- **Artefactos aprobados**: el motivo `SIN_PERIODO_VIGENTE` (`component-methods.md`, `api-contract.md`) rechaza la fila. No está en §12.3.
- **Para U1 Functional Design**: definir qué hacer si la consulta devuelve más de un periodo.

### RE-06 — Facultad sin fechas de pago (pregrado)
- **Código**: `guardarCuota` no revisa el resultado de `fechaPagoFacultad` (858). Si no hay fila, guarda la cuota con fechas vacías.
- **Artefactos aprobados**: el motivo `SIN_FECHAS_FACULTAD` rechaza la fila. No está en §12.3.

### RE-07 — `unidad` en pregrado vale 0, no vacío
- **Código**: `unidad` se pone en 0 una vez por lote (255) y solo cambia en posgrado (284). En pregrado se escribe `'0'`. En posgrado con la columna 2 vacía se escribe vacío.
- **Artefactos aprobados**: US-11 (Reglas) dice "vacía en pregrado, como hoy"; `component-methods.md` define `Solicitud.unidad: str | None`. El caso de posgrado queda en P-6.

### RE-08 — Cómo se leen hoy las fechas de la facultad
- `fechaPagoFacultad` se consulta con dos valores: el tipo y la facultad (`ACCRA.cra_dep_cod`). El tipo es 0 para la cuota única normal (número de cuota menos 1, 853–856) y 3 con terminación de materias (838–851). El tipo 1 solo lo usaba la segunda cuota del diferido.
- La respuesta trae la fecha ordinaria en la posición 1 y la extraordinaria en la 2, como texto `dd/mm/aaaa`, que se convierte con `strtotime` (860–877). Las dos ramas del `if` de 866 son iguales.
- Uso: definir los parámetros de las fechas en "parametros" (D10) y verificar A10. Los nombres reales de las columnas siguen pendientes (D4), porque `datosSolicitud.class.php` no está.

### RE-09 — Valor de `solicitudRecibo.cuota` hoy
- Pregrado: el valor de la celda "Seguro Estudiantil" si es 0, 1 o 2; 0 si está vacía, no es numérica (por ejemplo "X") o es otro número (453–461).
- Posgrado: el número de cuotas de la columna 3.
- Uso: completa D3. Cerrada con RE-21 (supuesto A15): "Solicitados" no lee `cuota` en pregrado.

### RE-10 — La votación marcada en pregrado depende de la última columna marcada
- `guardarExencion` quita la votación marcada si la última columna marcada es mayor o igual que 8 y distinta de 14 (611–614). Con la plantilla de 13 columnas equivale a "hay un descuento marcado en las columnas 8 a 13" (RF-06 CA3 (a), US-07 escenario 7).
- En posgrado la condición nunca se cumple, porque la columna 5 no está en su rango de exenciones (7–17). La votación marcada siempre se registra (RF-06 CA3 (c), US-08 escenario 9).
- Sin cambios.

### RE-11 — El tope del 90% se compara hoy con la suma de las exenciones
- `porcentajeExencion` suma todas las exenciones registradas (628) y el tope se compara con esa suma (638). Con un solo descuento (P-3, P-12) se compara con ese descuento. Ya está cubierto por el punto 4 de §12.3.

### RE-12 — Exención sin fila en la tabla `exencion`
- Si una columna marcada apunta a una exención sin fila en la tabla MySQL `exencion`, hoy se omite sin aviso (626–632). En el sistema nuevo, una regla que falta en "parametros" detiene el lote (AD-22). Es coherente con el diseño. Para la comparación de equivalencia, los dos sistemas deben usar los mismos porcentajes.

### RE-13 — La IP del lote se puede falsear
- `cargarArchivoServidor` toma la IP de `X-Forwarded-For` y de otras cabeceras que el cliente puede enviar antes que de `REMOTE_ADDR` (`funcionGeneral.class.php` 141–162). Un usuario puede poner cualquier IP en `solicitudLote`.
- El diseño aprobado no dice de dónde sale la IP. El contrato de auditoría de `utils_oas` tampoco lo resuelve: llena `ip_user` con `ctx.Input.IP()` de Beego (`auditoria.go` 156), que toma la primera entrada de `X-Forwarded-For` cuando existe (comportamiento de Beego 1.x; su código no está en el workspace).
- Propuesta para U1 NFR Design: tomar la IP de la cadena de proxies conocida (WSO2 AM y balanceador), no de la primera entrada de `X-Forwarded-For`. Se relaciona con SECURITY-03 y SECURITY-13 (registros confiables).

### RE-14 — Motivo de rechazo vacío o heredado
- Si el estudiante existe y tiene valor de matrícula, pero su carrera no está en `ACCRA`, `verificarCodigo` devuelve `false` sin motivo (530–541). Como `errorProceso` solo se limpia en `procesarRegistro` (413), el resumen muestra el motivo de la fila anterior o ninguno.
- En el sistema nuevo el caso cae en `CARRERA_INACTIVA`. Sin cambios.

### RE-15 — Nadie lee `solicitudLote` en el repositorio
- El historial de lotes (US-13, UC-02) es una consulta nueva dentro de IN-8. No se sabe si otro módulo de weboffice lee esa tabla.

### RE-16 — Código de estudiante no numérico
- Hoy el código se concatena en el SQL (`sql.class.php` 103); la consulta falla y el motivo es "El código no está registrado". El sistema nuevo lo rechaza antes con `CODIGO_INVALIDO` (US-06 escenario 2). Solo cambia el motivo; las cuotas, exenciones y conceptos no cambian.

### RE-17 — Validación débil de fechas y porcentajes de posgrado
- Solo se revisa día ≤ 31 y mes ≤ 12, y solo si el número de cuotas es numérico (436–451). `strtotime` corre las fechas inexistentes (el 31 de febrero pasa al 3 de marzo) y acepta años de dos dígitos. Los porcentajes negativos se aceptan y los mayores que 100 toman el valor por defecto sin aviso (999–1020).
- Cubierto por el punto 7 de §12.3 y por P-5.

### RE-18 — Un periodo por estado: más de un periodo indica una base inconsistente
- **Código** (`admin_consultasCoordinador`): `seleccionarPeriodo` arma la lista de periodos de `ACASPERI` con `ape_estado` 'A', 'X' o 'P' y usa el estado como valor de cada opción (`funcion.class.php` 449–464). Después, `anioper` busca el periodo por ese estado y toma la primera fila (`sql.class.php` 29–36; `funcion.class.php` 232 y 522). El módulo supone un solo periodo por estado. El encabezado del módulo (27/12/2018) dice que los periodos activos se manejan "con base en el registro de la tabla de estados de periodo para cada proyecto".
- **Relación con recibos**: `periodoActual` usa la misma relación. Une `ACASPERI` con `ACASPERIEVENTOS` por estado, y el estado lo da el evento 80 de cada proyecto (`registro_lote_recibo/sql.class.php` 27–38). Con datos consistentes devuelve una sola fila; si devuelve varias, la base está desactualizada o inconsistente, que es el caso que el usuario pidió reportar en RE-05.
- **Aplicado como supuesto A13**: si la consulta devuelve más de un periodo para el proyecto, la fila no se sube con `SIN_PERIODO_VIGENTE` y el mensaje pide reportarlo al área de sistemas. Cierra la pregunta que estaba pendiente para U1 Functional Design. El significado de 'X' y 'P' no está en el código.

### RE-19 — `admin_consultasCoordinador` es el módulo de notas de ARC
- **Dato del usuario** (2026-11-25): es la lógica del usuario de Admisiones, Registro y Control; el nombre dice "coordinador" por error.
- **Lo que muestra el código**: el nivel 132 se llama "ORC" (`listaProyectosORC`, `novedadesORC`), lo que confirma que el nivel 132 de weboffice es Registro y Control. Discovery lo tenía como "¿ORC / admisiones?". El módulo conserva ramas para coordinador (proyectos por `cra_emp_nro_iden`) y decano (cargo 218), pero el usuario indica que lo usa ARC.
- **Qué hace para ARC**: lista todos los proyectos curriculares activos (`listaProyectosORC`, sin excluir 0 ni 999); deja escoger el periodo ('A', 'X' o 'P'); muestra el control de notas parciales (parciales 1 a 6, examen y definitiva, con los datos de contacto del docente) con exportación a Excel; muestra el histórico de notas con enlace al reporte de cada curso; y deja cargar novedades de notas en cuanto existe el cierre de semestre (evento 71), sin la ventana de fechas del evento 89 que se exige a los demás usuarios (`funcion.class.php` 543–549, 610, 653). La opción `registroAcuerdo` llama a un método que no existe (189).
- **Seguridad**: el nivel llega en la petición (`tipoUser`, líneas 44, 148 y 531) y el usuario también, cuando la sesión no lo trae (`$_REQUEST['usuario']`, líneas 62, 217, 399 y 513). Cualquier usuario de weboffice que envíe `tipoUser=132` obtiene los permisos de ARC en este módulo (R3). Sigue en producción mientras el PHP corra.
- **Relación con recibos**: ninguna funcional; las reglas del MVP no cambian. La lista de proyectos de ARC en recibos sigue siendo la de `registro_lote_recibo` (`carrerasTotales`, activos y sin 0 ni 999, RF-03 CA2). El código 999 también aparece en `GEUSUCRA` como "todas las carreras" (`sql.class.php` 185–193), lo que confirma que es un código especial.
- **Aplicado**: el nombre se corrigió en Discovery y en Inception. **Abierto**: C5, si el módulo sigue fuera del proyecto.

### RE-20 — "Solicitados" es `admin_solicitudCoordinador`: qué lee y qué escribe
- **Origen**: la carpeta se agregó al workspace el 2026-11-25 y el usuario pidió analizarla. Su encabezado dice "caso de uso: CONSULTAR SOLICITUD DE RECIBO DE PAGO" (`bloque.php` 15–18). Es la página `admin_recibo`, opción `solicitado`, y la usan ARC (nivel 132), coordinadores (4) y asistentes o secretarios (110 y 114). Los números de línea de RE-20 a RE-26 son de `admin_solicitudCoordinador/funcion.class.php`, salvo que se indique otro archivo.
- **Lista**: por proyecto curricular, las solicitudes con `estado=0` del año y periodo vigentes del proyecto. El periodo sale de `periodoActual` (evento 80), la misma consulta del lote (`sql.class.php` 30–84). ARC ve todos los proyectos activos (`carrerasTotales`) y puede generar aunque el calendario no lo permita (693, 1025).
- **Genera** (`generarRecibo`, 165–557): por cada fila de `solicitudCuota` inserta una cuota en `ACESTMAT` y sus conceptos en `ACREFEST` (Oracle), guarda una cadena en la tabla MySQL `consiga` y pasa la solicitud a `estado='1'` con `secuencia` y `observacion` (`sql.class.php` 302–311). Antes desactiva las cuotas sin pagar del mismo periodo (`actualizaracestmat`). Si el estudiante ya pagó esa cuota en el periodo, no la genera (`verificapagoCuota`).
- **Lee**: `solicitudRecibo` (`codigo_est`, `id_carrera`, `cuota`, `tipoPlantilla`, `unidad`), `solicitudCuota` (`cuota`, `porcentaje`, `fecha_ordinaria`, `fecha_extra`), `solicitudExencion` unida al catálogo `exencion` (`porcentaje`, `etiqueta`) y `solicitudConcepto` unida a `referenciaPago`. Las fechas se leen como timestamp Unix con `date("Ymd", …)` (339–365).
- **Confirma**: RF-16 CA1 y CA3, el periodo del evento 80 (§4.A punto 6), A10 y la validación de `V_ACESTMATBRUTO` (RF-03 CA5): sin esa fila, "Solicitados" no muestra la solicitud (`datosEstudiante`, `sql.class.php` 173–200).
- **Defectos**: TD-20 a TD-25 (`code-quality-assessment.md`). "Solicitados" sigue en PHP, así que se reportan a su dueño y a Seguridad; no cambian el sistema nuevo.
### RE-21 — `solicitudRecibo.cuota` y los estados (D3)
- **`cuota`**: solo se muestra en posgrado, como "Pagar en N cuota(s)" (887, 963, 1175). En pregrado ese número sale de Oracle: 2 si el estudiante tiene diferido y 1 si no (874, 950, 1162). La generación no lee `cuota`: crea un recibo por cada fila de `solicitudCuota` (201–203).
- **Estados**: lee solo el 0 y pone el 1 al generar. El 2 lo escribe la cancelación del lote y ningún código del workspace lo lee. El botón "Borrar el registro" lleva a `borrar_registro`, que no está.
- **Aplicado (supuesto A15)**: `cuota` vale 1 en pregrado, el número real de cuotas (cambio acordado 1), y en posgrado el número de cuotas de la plantilla, como hoy. D3 queda resuelta y US-11 queda bloqueada solo por D4.
- **Efecto visible para ARC**: a un estudiante con diferido en Oracle, "Solicitados" le seguirá mostrando "Pagar en 2 cuota(s)", aunque el sistema nuevo crea una sola cuota (cambio acordado 2). Se genera un solo recibo; solo cambia el texto de la pantalla.
### RE-22 — "Solicitados" recalcula todos los valores
- **Valor bruto** (`registroPagoBruto`, 1260–1322): en pregrado, `emb_valor_matricula` de `V_ACESTMATBRUTO`; en posgrado por créditos, un factor por facultad y nivel × el salario mínimo del nivel (Acuerdo 007 de 2026) × `unidad`; en posgrado SMLV, el salario mínimo × `unidad`.
- **Exenciones** (`porcentajeExencion`, 1324–1377): toma el porcentaje de la tabla MySQL `exencion`, no el de "parametros". Neto = bruto × (1 − (descuento + votación) / 100) (196). La exención de la Secretaría de Educación (`id 16`) se aplica después, multiplicando (236–238).
- **Cuotas**: en pregrado, neto × porcentaje de la cuota, y el valor extraordinario es igual al ordinario (207–228). En posgrado, interés de 1,6368% por cada cuota después de la primera y recargo extraordinario de 20% (245–260).
- **Conceptos** (`conceptosPago`, 1379–1443): seguro, carnet y sistematización salen de Oracle (`MNTAC.ACVLRSCS`) y la matrícula es la cuota calculada. Del lado del lote solo importan los ids.
- **No consulta `ACCERELECTORAL`**: la votación automática solo existe si el lote la escribe.
- **Consecuencias**: el sistema nuevo no escribe valores, como dice RF-16 CA3. La consecuencia de P-15 queda confirmada: un cambio de porcentaje se hace en "parametros" y en la tabla `exencion`. Para U1 Functional Design: evaluar leer esos porcentajes de la tabla `exencion` en solo lectura, para que el lote decida con los mismos números que cobra "Solicitados". Para P-6: en posgrado, con `unidad` vacía o en 0 el recibo sale en 0.
### RE-23 — Si descuento y votación suman más de 100%, el recibo queda negativo
- **Código**: el neto no tiene tope (196, 851, 1141). La cuota 1 con valor 0 o negativo se genera igual (270–294): se inserta en `ACESTMAT`, y su concepto de matrícula en `ACREFEST`, con ese valor (`insertarCuota`, `insertarConcepto`).
- **Hoy**: en pregrado el lote quita la votación marcada si la última columna marcada es de la 8 a la 13, que el comentario del código describe como exenciones de 100% (`registro_lote_recibo/funcion.class.php` 610–614), y solo agrega la automática si la suma es de 90% o menos (638). En posgrado no hay esa protección: la votación marcada se registra aunque el descuento sea de 100% (US-08 escenario 9).
- **Con lo decidido**: C2 (la votación marcada va con cualquier descuento) y la respuesta del usuario a A14 (2026-11-25: la automática se aplica siempre que el estudiante esté en `ACCERELECTORAL`) quitan esas protecciones. Un descuento de 100% más la votación deja la matrícula en −10% del valor bruto.
- **Abierto**: aclaración C7.
### RE-24 — Solo se leen las dos primeras exenciones
- `porcentajeExencion` recorre como máximo las dos primeras filas de `solicitudExencion` (1344), y la consulta no tiene `ORDER BY` (`sql.class.php` 155–171). Con dos descuentos, solo cuenta el último que lee. La exención de la Secretaría de Educación (`id 16`) se busca aparte en todas las filas, pero también ocupa uno de esos dos lugares.
- Con C2 una solicitud lleva como máximo dos exenciones, así que "Solicitados" las lee todas. Confirma C2 y P-3. Si algún día se permiten tres, importará el orden en que se insertan.
### RE-25 — Pregrado: con una sola cuota, el recibo usa la fecha extraordinaria
- Con una cuota, la fecha de `solicitudCuota.fecha_extra` va al recibo (346–349). Como el sistema nuevo crea siempre una cuota en pregrado, esa fecha tiene que existir: la plantilla la trae o el sistema la calcula (D1).
- La observación de los recibos de pregrado es "TERMINACION DE MATERIAS" con esa exención, "REINGRESO - DTO. MAT. CERO 100%" con la 18, y "EXONERACION 100% MATRICULA CERO" en los demás casos, aunque el estudiante pague (384–394). Es un resto de 2020 en "Solicitados" y no cambia con la migración.
### RE-26 — La búsqueda por estudiante no filtra el periodo
- `reciboEstudiante` trae todas las solicitudes del estudiante con `estado=0`, de cualquier periodo (`sql.class.php` 520–540), y la generación usa el periodo vigente del proyecto, no el de la solicitud (276, 298, 322). Una solicitud sin imprimir de un periodo anterior se puede generar como recibo del periodo actual, con sus exenciones y fechas viejas.
- Hoy el lote cancela las solicitudes sin imprimir de todos los periodos (`cancelarSolicitud`), así que un estudiante que se vuelve a cargar no conserva solicitudes viejas. Con P-7 (solo el periodo vigente), la solicitud vieja sigue en estado 0 y aparece en esa búsqueda junto a la nueva.
- **Abierto**: aclaración C8.
## 4. Decisiones del usuario (2026-11-25)

| Hallazgo | Decisión | Estado | Artefactos actualizados |
|---|---|---|---|
| RE-01 | Máximo dos exenciones por solicitud: la votación y un descuento; los descuentos no se suman entre sí | Resuelto: C1 = a (sin votación automática en filas sin exenciones marcadas) y C2 = b (más de un descuento: la fila no se sube; la votación marcada va con cualquier descuento). La automática conserva el tope de 90% (A14) | RF-06 CA3 y CA4, §4.A punto 4, cambio acordado 4; US-07 y US-08; `component-methods.md` (`exenciones.seleccionar`), `api-contract.md` (`DESCUENTOS_NO_ACUMULABLES`) |
| RE-02 | Un estudiante rechazado por cualquier motivo pierde sus solicitudes sin imprimir del periodo vigente | Resuelto: cambio acordado 9; supuesto A12 para las filas sin periodo conocido | RF-08, RF-10, US-06, US-09, US-10, UC-01 pasos 13 y 14, AD-05, AD-30, `component-methods.md`, `component-dependency.md` |
| RE-03 | Sin número de cuotas, la fila no se sube y aparece en el reporte | Resuelto: cambio acordado 8 | RF-05 CA2, §4.A, US-08 escenario 6, `api-contract.md`, `component-methods.md` |
| RE-04 | Cuotas de 1 a 3 | Resuelto: cambio acordado 8 | Los mismos de RE-03 |
| RE-05 | Año y periodo obligatorios; sin periodo vigente, un mensaje pide reportarlo al área de sistemas | Resuelto: cambio acordado 10. Queda para U1 Functional Design qué hacer si la consulta devuelve más de un periodo | §4.A punto 6, US-06 escenario 8, `api-contract.md` |
| RE-06 | Sin fechas de pago, la fila no se sube y aparece en el reporte | Resuelto: cambio acordado 11. Con C3 = b, en pregrado las fechas también vienen de la plantilla (cambio acordado 12); las columnas quedan en D1 | RF-05, §4.A, US-07 escenario 11, US-08, `api-contract.md` |
| RE-07 | `unidad` se guarda como `0` en pregrado | Resuelto: igual que hoy | RF-16 CA4, US-11, `component-methods.md` |
| RE-13 | La IP se toma de `X-Forwarded-For` | Resuelto con la entrada que agrega el último proxy de confianza; falta D13 | RF-12 CA4, US-02, AD-29, `services.md` paso 5 |
| RE-15 | El historial de lotes y la auditoría son funcionalidades nuevas del MVP | Resuelto | `requirements.md` §12.7, US-13, US-14 |
| Reporte | El resumen lista los estudiantes que se subieron y los que no, con el motivo | Resuelto | RF-11 CA3, US-12, `api-contract.md`, `component-methods.md`, `components.md` |
| Versiones | Usar en la máquina de desarrollo las versiones actualizadas | Resuelto: C4 = a, la última versión estable con soporte en todo el proyecto | `technical-environment.md`, OQ-T-1, AD-27, `unit-of-work.md`, `execution-plan.md`, `technology-stack.md` |
| RE-08, RE-09 | RE-08 ya no aplica al sistema nuevo: las fechas de pregrado vienen de la plantilla (C3). RE-09 cierra D3 junto con RE-21 (A15) | Sin cambio | — |
| RE-10, RE-11, RE-12, RE-14, RE-16, RE-17 | Confirmaciones | Sin cambio | — |
| RE-18 | Sin decisión del usuario: supuesto A13, derivado de su respuesta a RE-05 | Aplicado: más de un periodo para el proyecto = `SIN_PERIODO_VIGENTE`; cierra la pregunta pendiente de U1 Functional Design | `requirements.md` §4.A punto 6 y §9 A13; US-06 escenario 8 |
| RE-19 | `admin_consultasCoordinador` es la lógica del usuario de Registro y Control; el nombre está mal | Resuelto: corregido en Discovery y en Inception; C5 = b, el módulo queda para la Fase 2 | `vision-document.md`, `existing-system-analysis.md`, `requirements.md` §3, §6 y RF-03, `personas.md` y los artefactos de Reverse Engineering |
| A14 (pregunta sobre el tope) | "si no esta marcado en el archivo y si lo encuentras en la tabla ACCERELECTORAL aplica el descuento" | Pendiente: C6 (filas sin descuento; cambia C1) y C7 (suma mayor que 100%, RE-23). Se aplica cuando se respondan | `requirements.md` A14 registra la respuesta |
| RE-20 a RE-26 | El usuario pidió analizar `admin_solicitudCoordinador`: "ya lo habias leido pero analizalo de nuevo si lo necesitas" | D3 resuelta (A15). Abiertas C7 y C8. Las demás son confirmaciones e insumos para U1 Functional Design | RF-16 CA4, OQ-B-4, D3, A15; US-11; los artefactos de Reverse Engineering; `existing-system-analysis.md` |

