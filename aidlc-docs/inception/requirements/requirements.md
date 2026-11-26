# Requisitos — Migración del módulo de recibos por lote (weboffice)

- Fase: INCEPTION → Requirements Analysis
- Profundidad: Comprehensive
- Tipo de proyecto: Brownfield (migración / modernización)
- Fecha: 2026-11-24
- Inputs: `Product-Definition/vision-document.md`, `Product-Definition/technical-environment.md`, `Product-Definition/open-questions.md`
- Soporte: `Product-Definition/interview/technical/existing-system-analysis.md`, `.../templates-analysis.md`
- Estado: **aprobado 2026-11-24**. Actualizado el mismo día con las decisiones de User Stories (P-3, P-5, P-7, P-11) y con evidencia del código PHP actual (ver §12). Actualizado el 2026-11-25 con las decisiones de Reverse Engineering (§12.6 y §12.7) y con el análisis de "Solicitados" (D3 resuelta, A15; C6 = b, C7 = a y C8 = a, respondidas el mismo día), y con las respuestas F1 a F13 del diseño funcional de U1 (§12.8), y con las decisiones de NFR Requirements de U1 (§12.9)

> Límite de alcance (regla dura): solo la lista **"Funcionalidades IN"** de la Visión. Las
> listas allow/deny del Entorno técnico son **restricciones**, no sugerencias. Nada fuera de
> "IN" entra en esta versión aunque sea técnicamente fácil (ver §6, Fuera de alcance).

---

## 1. Análisis de intención

Modernizar el módulo `registro_lote_recibo` de weboffice (PHP 5 + framework propio) a un
nuevo stack (frontend Angular `recibos_mf`, backend Python/Flask `recibos_service`) siguiendo
la arquitectura OAS, **sin cambiar** las bases de datos existentes (Oracle académico de solo
lectura, MySQL `solicitud*`) ni el módulo de impresión "Solicitados". El sistema nuevo debe
producir solicitudes de recibo **equivalentes** a las del sistema actual (métrica: 100% de
coincidencia en cuotas, exenciones y conceptos sobre lotes de prueba) salvo tres reglas de
negocio acordadas, y debe estar desplegado en el ambiente de **pruebas (test)** el
**15/12/2026**, listo para la revisión de Seguridad.

Clase de cambio: reescritura de plataforma con equivalencia funcional (no es rediseño de
negocio). El valor está en retirar PHP 5, cerrar vulnerabilidades (SQLi, XSS, permisos
manipulables), garantizar integridad transaccional y externalizar las reglas que hoy viven
en el código.

---

## 2. Alcance (traza a "Funcionalidades IN")

Cada capacidad del MVP se traza a requisitos funcionales (§4). El ID de la izquierda es la
funcionalidad IN de la Visión.

| IN | Capacidad | RF |
|----|-----------|----|
| IN-1 | Carga de 3 plantillas vigentes con validación de formato | RF-01, RF-02 |
| IN-2 | Validación del estudiante en Oracle académico (estado, carrera, terminación de materias) | RF-03 |
| IN-3 | Generación de solicitudes (cuotas, exenciones, conceptos) equivalente al actual, con las 3 reglas acordadas | RF-04, RF-05, RF-06, RF-07 |
| IN-4 | Cancelación automática de solicitudes previas sin imprimir del mismo estudiante | RF-08 |
| IN-5 | Reglas parametrizadas vía servicio externo "parametros" (sin pantalla propia) | RF-09 |
| IN-6 | Cada solicitud se guarda completa o no se guarda (atomicidad) | RF-10 |
| IN-7 | Resumen del lote: procesados y rechazados con motivo | RF-11 |
| IN-8 | Historial de lotes y auditoría (quién, cuándo, qué archivo, IP) | RF-12, RF-13 |
| IN-9 | Inicio de sesión y rol único con WSO2 + `configuracion_cliente` | RF-14, RF-15 |
| IN-10 | Escritura en `solicitudrecibo` (MySQL) para que "Solicitados" siga funcionando | RF-16 |

Procesamiento **síncrono** (C-2): un lote de hasta **1000 estudiantes** se carga, procesa y
responde en la misma petición. Sin colas ni workers.

---

## 3. Actores

- **Admisiones, Registro y Control (ARC)** — rol operativo único; absorbe coordinador/asistente/secretario. Carga lotes de cualquier proyecto curricular. Hoy es el nivel 132 de weboffice, que el código llama "ORC" (RE-19, 2026-11-25).
- **Estudiante** — usuario indirecto; recibe el recibo (lo produce "Solicitados", no este sistema).
- **Seguridad** — consume logs de auditoría; ejecuta la revisión en test. Fuera del ciclo de desarrollo.
- **Sistemas externos**: Oracle académico (solo lectura), MySQL `solicitud*` (lectura/escritura), S3 (archivo cargado), WSO2 IS/AM (auth), servicio "parametros" (reglas), "Solicitados" (consumidor aguas abajo).

---

## 4. Requisitos funcionales

Cada RF: descripción, criterios de aceptación (CA) y origen. Las reglas de cálculo detalladas
("igual que el sistema actual") están en §4.A para no repetirlas.

### RF-01 — Carga del archivo de lote
El usuario ARC sube un archivo de plantilla; el sistema lo almacena en S3 (privado, cifrado,
nombre interno generado por el sistema) y registra el lote en `solicitudLote` (usuario, nombre
original, IP, fecha).
- CA1: solo se acepta `.xls` (BIFF binario), verificando el tipo real, no solo la extensión.
- CA2: se rechaza el archivo que supere el tamaño máximo de 2 MB (N7, 2026-11-25; antes el supuesto A1 decía 10 MB).
- CA3: el archivo original no queda en disco local del contenedor ni con permisos abiertos.
- Origen: IN-1; deny de `documento/solicitudes/` local y `0777`; allow S3 privado.

### RF-02 — Identificación y validación de formato de plantilla
El sistema identifica el tipo por el texto de la celda A1 y valida el número de columnas y los
encabezados antes de procesar filas.
- CA1: pregrado = **tipo 1**, A1 `PLANTILLA GENERAL PREGRADOS`, datos desde fila 4, sin "Reingreso" y **con las columnas de fecha de pago** (C3, 2026-11-25). El número final de columnas, sus encabezados y la posición de las fechas salen de la plantilla oficial (D1). La plantilla anterior, con "Reingreso", **se rechaza** (C-3); se reconoce por sus encabezados, porque la nueva también puede tener 14 columnas o más.
- CA2: posgrado créditos = **tipo 2**, A1 `PLANTILLA GENERAL POSTGRADOS CREDITOS`, datos desde fila 5, **29 columnas**.
- CA3: posgrado SMLV = **tipo 3**, A1 `PLANTILLA GENERAL POSTGRADOS SALARIOS MINIMOS LEGALES`, datos desde fila 5; estructura por confirmar (OQ-B-2, dependencia bloqueante).
- CA4: si A1 no coincide o el número/orden de columnas no corresponde, se rechaza todo el lote con un motivo claro (no se procesa parcialmente el formato).
- CA5: un lote con más de **1000 filas con datos** se rechaza completo, sin procesar ninguna fila (422); el mensaje dice el máximo y cuántas filas trae, y el lote queda registrado (RF-12 CA2). Decisión F1 (P-1, 2026-11-25); hoy no hay máximo.
- CA6: una fila con datos y sin código aparece como no subida con `CODIGO_INVALIDO` ("Falta el código del estudiante"); las filas vacías se omiten, y una celda con solo espacios cuenta como vacía (decisiones F3 y F4, 2026-11-25). Hoy toda fila sin código se omite sin aviso.
- Origen: IN-1; templates-analysis.md; C-3.

### RF-03 — Validación académica del estudiante (Oracle, solo lectura)
Por cada código de estudiante del lote, el sistema valida contra Oracle académico.
- CA1: el estado del estudiante debe estar entre los **estados permitidos** (hoy `V,J,T,A,Q,B`; parametrizado vía "parametros", RF-09).
- CA2: el proyecto curricular del estudiante debe estar activo (`cra_estado = 'A'`, código distinto de 0 y 999). Es el comportamiento actual del perfil con acceso a todas las carreras (nivel 132, consulta `carrerasTotales`), que corresponde al rol único ARC. Confirmado el 2026-11-25: el nivel 132 es Admisiones, Registro y Control ("ORC" en `admin_consultasCoordinador`, RE-19). Ese módulo de notas lista los proyectos activos sin excluir 0 ni 999; para recibos se conserva la regla de `registro_lote_recibo`.
- CA3: si el evento de **terminación de materias** (hoy 82) está activo para el proyecto curricular del estudiante (`fua_verifica_evento`), solo se aceptan los estados `T` o `H`. Como `H` no está en la lista de estados permitidos, hoy se rechaza antes por CA1; se conserva ese orden.
- CA4: Oracle se usa **solo lectura**; no se modifica estructura ni datos.
- CA5: si el estudiante existe pero no tiene valor de matrícula en `V_ACESTMATBRUTO`, se rechaza con el motivo "Sin información de matrícula".
- CA6: las validaciones se aplican en el orden del sistema actual (existencia, información de matrícula, estado, proyecto curricular, terminación de materias); el motivo de rechazo es el de la primera que falla. Las validaciones nuevas van después, en este orden: periodo vigente (RE-05) y nivel del estudiante frente a la plantilla (CA7).
- CA7: el nivel del proyecto curricular del estudiante debe corresponder a la plantilla: la de pregrado solo acepta proyectos de nivel pregrado, y las de posgrado solo los demás niveles. El nivel sale de Oracle (`ACCRA.cra_tip_cra` → `ACTIPCRA.tra_nivel`), la misma relación que usa "Solicitados". Si no corresponde, la fila no se sube con `NIVEL_NO_CORRESPONDE` (decisión F5, 2026-11-25). Hoy no se revisa, y "Solicitados" calcula un valor que no corresponde, o 0 (RE-22).
- CA8: si un código aparece más de una vez en el lote, solo se procesa su primera aparición. Las siguientes no se procesan y aparecen como no subidas con `CODIGO_REPETIDO` ("El código ya está en la fila N"). Como no se procesan, no cancelan solicitudes: si cancelaran, borrarían la que acaba de crear la primera aparición (decisión F2, P-2, 2026-11-25). Hoy queda la solicitud de la última aparición.
- Origen: IN-2; existing-system-analysis.md §3; `funcion.class.php` (`verificarCodigo`, `procesarRegistro`); deny de escritura en Oracle.

### RF-04 — Generación de solicitud de recibo
Por cada estudiante válido, el sistema crea una solicitud con sus cuotas, exenciones y
conceptos, equivalente al sistema actual salvo las reglas acordadas (§4.A).
- CA1: la solicitud se escribe en `solicitudRecibo` con los formatos que lee "Solicitados" (fechas = timestamp Unix, porcentajes 0–100, `estado` existente).
- CA2: equivalencia 100% en cuotas, exenciones y conceptos frente al actual sobre los lotes de prueba (métrica de éxito; herramienta de comparación en etapa posterior, C-4).
- Origen: IN-3; métricas de éxito.

### RF-05 — Reglas de cuotas (con cambios acordados)
- CA1: **Pregrado** — una sola cuota al **100%**. Las fechas de pago vienen de la plantilla, como en posgrado (C3, 2026-11-25); ya no salen de las fechas de la facultad. La plantilla trae solo la **fecha ordinaria**, en tres columnas (día, mes y año), y la extraordinaria se calcula como en posgrado (CA3) (decisión F8, 2026-11-25); la posición de las columnas sale del archivo oficial (D1). La columna de terminación de materias ya no cambia las fechas: solo registra su exención. Si faltan las fechas o son inválidas, la fila no se sube y aparece en el resumen con el motivo (RE-06). **Se elimina** el diferido (3 cuotas al 0% "COVID"). **No** se lee "Seguro Estudiantil" como número de cuota.
- CA2: **Posgrado (créditos y SMLV)** — el número de cuotas es obligatorio y va de 1 a 3. Si la celda está vacía o tiene otro valor, la fila no se sube y aparece en el resumen con el motivo (RE-03 y RE-04; hoy la celda vacía genera 1 cuota y un 0 o un texto guardan la solicitud sin cuotas). Cada cuota debe traer una fecha válida en la plantilla; si falta, la fila no se sube (RE-06). Un porcentaje vacío toma el valor por defecto de su posición (**100 / 60-40 / 40-30-30**), como hoy. La suma de los porcentajes debe ser **100**; si no, se rechaza el estudiante (decisión P-5, cambio frente al sistema actual).
- CA3: **Pregrado y posgrado** — fecha extraordinaria = fecha ordinaria **+ 8 días calendario**; si ese día es festivo, se avanza un día a la vez hasta el primero que no lo sea (código actual, `guardarCuotas`; en pregrado desde F8). Los festivos son los de la tabla que usa hoy weboffice (decisión F9, 2026-11-25; el DBA la identifica, D5). Solo mueven la fecha los días que están en esa tabla: un sábado o un domingo que no esté en ella es una fecha válida (decisión F10).
- CA4: **Fechas** (decisión F7, 2026-11-25): ninguna fecha ordinaria puede ser anterior al día de la carga (America/Bogota), y en posgrado cada cuota debe vencer después de la anterior. Si no se cumple, la fila no se sube con `FECHA_INVALIDA`, y el detalle dice la cuota. Hoy no se revisa.
- CA5: **Créditos o SMLV** (columna 2 de posgrado; decisión F6, P-6): obligatorio y mayor que 0; en créditos, un número entero; en SMLV, un número con hasta dos decimales. Si no cumple, la fila no se sube con `UNIDAD_INVALIDA`. Si el DDL (D4) muestra que `unidad` solo guarda enteros, SMLV también se limita a enteros. Hoy no se valida, y con 0 o vacío "Solicitados" genera el recibo en 0 (RE-22).
- CA6: los porcentajes de las cuotas de posgrado son números enteros de 0 a 100; un decimal se rechaza con `PORCENTAJE_INVALIDO` (decisión de diseño de U1 Functional Design, 2026-11-25). Hoy se acepta cualquier número de hasta 100.
- Origen: IN-3; "Reglas acordadas"; "Reglas de cálculo vigentes".

### RF-06 — Exenciones
- CA1: se aplica el mapa **columna → id_exención** por tipo de plantilla (parametrizado, RF-09; hoy fijo en código).
- CA2: pregrado **excluye "Reingreso"** (C-045558, `id_exencion 18`); la columna no existe en la plantilla de 13.
- CA3: **Votación** (10%, `id_exencion 1`): es la única exención acumulable y se registra **una sola vez**, venga de la columna de la plantilla, de `ACCERELECTORAL` (certificado activo) o de ambas (decisión P-3). Reglas desde el 2026-11-25 (C1, C2, C6, C7, F14 y F15; cambian P-13): (a) la votación marcada se registra sola o con un descuento, en las dos plantillas; (b) si la votación no está marcada y la fila tiene marcado un descuento o, en posgrado, la Secretaría de Educación, se registra la votación cuando el estudiante tiene certificado activo en `ACCERELECTORAL` (respuesta del usuario sobre A14; C6; F15 = a, como hoy); una fila sin ninguna exención marcada no recibe la votación automática, como hoy (C1); (c) **el descuento y la votación juntos no pasan de 100%**: si pasarían, se registra solo el descuento, en las dos plantillas y para la votación marcada o la automática (C7 = a), porque "Solicitados" dejaría la matrícula negativa (RE-23). La Secretaría no entra en esa suma, porque "Solicitados" la aplica sobre el valor que queda (F14 = a). Con la votación en 10%, la regla (c) da para la votación automática el mismo resultado que el tope actual de 90%, salvo con la Secretaría y un descuento de más de 20%: hoy no se agrega y ahora sí (F14). Para la votación marcada cambian dos casos frente a hoy: en pregrado, con un descuento de las columnas 8 a 13, hoy se quita siempre y ahora solo si la suma pasa de 100%; en posgrado hoy se registra siempre y ahora se quita si la suma pasa de 100%. Reglas detalladas: BR-X01 a BR-X07 en `aidlc-docs/construction/recibos_service/functional-design/business-rules.md`.
- CA4: **Los descuentos no son acumulables** (decisión P-3): una solicitud lleva como máximo dos exenciones, la votación y un descuento (C2, 2026-11-25). Si la fila trae más de un descuento marcado, sin contar la votación, la fila **no se sube** y aparece en el resumen con el motivo `DESCUENTOS_NO_ACUMULABLES`. Reemplaza a P-12 (registrar el de mayor porcentaje) y al supuesto A9. Es un cambio frente al sistema actual, que registra todas las exenciones marcadas. **La Secretaría de Educación** (posgrado, columna 16, `id_exencion 16`) no cuenta como descuento para esta regla: una fila puede llevar la votación, un descuento y la Secretaría, como lo calcula hoy "Solicitados", que la aplica aparte, sobre el valor que queda (decisión F12, 2026-11-25). Las exenciones se guardan en este orden: votación, descuento y al final la Secretaría, porque "Solicitados" solo cuenta las dos primeras filas para la votación y el descuento (RE-24). No entra en la suma de C7 (F14 = a) y, como cualquier exención marcada, permite la votación automática (F15 = a).
- CA5: una columna de concepto o de exención está **marcada** si su celda tiene contenido distinto de espacios. Una celda con solo espacios no cuenta (decisión F4, 2026-11-25); hoy cuenta cualquier contenido (`isset` en `conceptoPlantilla` y `exencionPlantilla`).
- CA6: el porcentaje de cada exención se lee de la tabla MySQL `exencion`, en solo lectura: son los mismos con los que cobra "Solicitados" (decisión F11, 2026-11-25). Revierte P-15 en este punto, y es como lo hace hoy el lote PHP. Si una exención del mapa no tiene porcentaje en la tabla, el lote no se procesa y el mensaje la nombra, como con una regla que falta (AD-22); hoy se omite sin aviso (RE-12).
- Origen: IN-3; templates-analysis.md; "Reglas acordadas".

### RF-07 — Conceptos
- CA1: siempre se graba el concepto 1 (matrícula); el 19 solo en pregrado; los conceptos 2, 3, 4 según las columnas de la plantilla.
- CA2: los IDs de concepto son **parámetros** (RF-09), no literales en el código.
- Origen: IN-3; existing-system-analysis.md §3.

### RF-08 — Cancelación de solicitudes previas sin imprimir
Por cada estudiante del lote, **procesado o rechazado**, se cancelan sus solicitudes anteriores
**sin imprimir** (estado `0 → 2`) de cualquier periodo, como hoy (C8). Si el estudiante es válido, la cancelación va
antes de insertar la solicitud nueva.
- CA1: solo afecta solicitudes del mismo estudiante en estado "sin imprimir".
- CA2: la cancelación va en su **propia transacción**. Si después falla el guardado de la solicitud nueva (RF-10), la cancelación se mantiene. Si la cancelación falla, no se inserta la solicitud nueva y la fila queda rechazada por error al guardar. *Cambiado el 2026-11-25 (RE-02): antes, la cancelación y la inserción iban en la misma transacción.*
- CA3: las pruebas en paralelo se ejecutan contra una **base de datos de pruebas dedicada** (copia con datos de periodos anteriores), de modo que la cancelación de solicitudes previas **nunca sobrescribe ni cancela** solicitudes creadas por el sistema PHP en producción (OQ-B-5 resuelta).
- CA4: se cancelan las solicitudes sin imprimir del estudiante **de todos los periodos**, como hace hoy la consulta `cancelarSolicitud` (C8 = a, 2026-11-25). *Antes (P-7, 2026-11-24): solo las del periodo vigente. Se revirtió porque la búsqueda por estudiante de "Solicitados" muestra las solicitudes sin imprimir de cualquier periodo y las genera en el periodo vigente (RE-26).*
- CA5: un estudiante **rechazado por cualquier motivo** también pierde sus solicitudes sin imprimir, de cualquier periodo (decisión del usuario, RE-02; C8). Hoy el PHP ya lo hace con los rechazados por terminación de materias, por fechas de posgrado o por error al guardar, pero no con los rechazados por estado, valor de matrícula o proyecto curricular.
- CA6: la cancelación necesita saber quién es el estudiante: su código es válido y está en Oracle. Por eso no aplica cuando la fila se rechaza por código inválido o estudiante no encontrado, ni cuando se rechaza el lote completo (formato, reglas de "parametros", máximo de filas) (supuesto A12). Desde C8 (2026-11-25) sí aplica al estudiante cuyo proyecto curricular no tiene periodo vigente, porque la cancelación ya no necesita el periodo.
- Origen: IN-4.

### RF-09 — Reglas parametrizadas vía servicio externo "parametros"
Las reglas que hoy están fijas en el código se **consultan** (solo lectura, decisión P-11) en el servicio externo
REST síncrono "parametros": conceptos, exenciones, porcentajes por defecto, estados permitidos,
eventos de calendario, plazo de la fecha extraordinaria y mapa columna → exención. Las fechas de
pago por facultad ya no se usan: desde el 2026-11-25 las fechas vienen de la plantilla (C3). Tampoco salen de
"parametros" los porcentajes de las exenciones, que se leen de la tabla `exencion` (RF-06 CA6, F11), ni los festivos, que se leen de la tabla de weboffice (RF-05 CA3, F9).
- CA1: **ningún** ID de concepto/exención/evento/estado ni porcentaje queda fijo en el código (deny: reglas activadas comentando código).
- CA2: el acceso se modela como un **puerto** en `app/application/` con un **adaptador** en `app/infrastructure/`. Contrato conocido (usuario, 2026-11-24): cada parámetro se consulta por su id con `GET /v1/parametro/{id}` (por ejemplo `/v1/parametro/9`). La respuesta usa el sobre CRUD (`Status` como texto, `"200"`) y `Data` es un objeto `Parametro` (`Id`, `Nombre`, `Descripcion`, `CodigoAbreviacion`, `Activo`, `NumeroOrden`, `TipoParametroId`, `ParametroPadreId`) sin un campo de valor. Falta definir en qué campo va el valor de cada regla, el id de cada regla por ambiente, la URL y la autenticación (D6, acotada).
- CA3: Meta de negocio: **cero cambios de código por periodo**.
- CA4: `recibos_service` **no** crea, modifica ni borra reglas en "parametros"; las actualiza el responsable de ese servicio, fuera de este sistema (P-11).
- Origen: IN-5; C-1; OQ-T-11.

### RF-10 — Atomicidad por solicitud
Cada solicitud se guarda **completa o no se guarda**: inserción de `solicitudRecibo`,
`solicitudCuota`, `solicitudExencion` y `solicitudConcepto` dentro de una transacción. La
cancelación previa (RF-08) va en su propia transacción y no se revierte si la solicitud nueva
falla (RE-02, 2026-11-25).
- CA1: ante un fallo a mitad de camino, no quedan solicitudes sin cuotas ni sin conceptos (métrica objetivo: 0 incompletas).
- CA2: el fallo de un estudiante no aborta todo el lote: ese estudiante se marca como rechazado con motivo (RF-11) y el resto continúa.
- Origen: IN-6; deny de escrituras relacionadas sin transacción; métrica de éxito.

### RF-11 — Resumen del lote
Al terminar, el sistema devuelve en la misma respuesta (síncrono) el resumen: procesados y
rechazados con el **motivo** de cada rechazo.
- CA1: cada rechazo indica el código del estudiante y la causa (estado inválido, no encontrado, formato de fila, etc.).
- CA2: el resumen es consistente con lo efectivamente escrito en MySQL.
- CA3: el resumen lista los estudiantes que se subieron (fila y código) y los que no se subieron (fila, código y motivo), como pidió el usuario el 2026-11-25 ("los que no se subieron y el porqué y los que sí se subieron"). El PHP actual también lista los códigos procesados.
- CA4: la lista no se exporta en el MVP; el resumen se ve en pantalla (decisión F13, P-10, 2026-11-25).
- Origen: IN-7.

### RF-12 — Historial de lotes
Se conserva el registro de cada lote cargado (quién, cuándo, nombre del archivo, IP, resultado).
- CA1: se usa `solicitudLote` existente sin cambiar su estructura: `id_usuario`, `nombreOriginal`, `nombreInterno`, `ip`, `fecha`.
- CA2: el lote se registra al cargarse el archivo, antes de validar el formato, como hoy; los lotes rechazados por formato también quedan en el historial. Los archivos rechazados por tipo o tamaño no se guardan ni se registran (la petición queda en la auditoría, RF-13).
- CA3: la tabla no guarda totales ni motivos de rechazo. El historial muestra usuario, fecha, archivo e IP, que es el alcance de IN-8; el resumen completo se ve al terminar la carga (RF-11).
- CA4: la IP se toma de la cabecera `X-Forwarded-For` (decisión del usuario, RE-13). Se usa la dirección que agrega el último proxy de confianza delante del servicio (WSO2 AM y el balanceador), no la primera de la lista, que el cliente puede escribir. El número de proxies de confianza es D13. La misma IP va en `ip_user` de la auditoría (RF-13).
- Origen: IN-8.

### RF-13 — Auditoría por petición
Cada petición genera un log JSON de auditoría con los campos del contrato `utils_oas/auditoria`:
`app_name, agent, data, date, host, ip_user, method, path, query, schema, sql_statement, status,
trace_id, user`.
- CA1: `sql_statement` capturado **por petición**; `data` **sin datos personales** (Ley 1581).
- CA2: logs **siempre habilitados**; destino CloudWatch Logs (OQ-T-5, §5), con retención de 365 días (N8).
- CA3: `trace_id` lleva el identificador de la petición (`request_id`), el mismo de los registros de la aplicación. En el MVP no hay trazas de X-Ray (N14 = c, 2026-11-25).
- Origen: IN-8; restricción de seguridad; contrato auditoría.

### RF-14 — Autenticación con WSO2
- CA1: `recibos_mf` inicia sesión por el microcliente core y envía el token Bearer en cada llamada.
- CA2: `recibos_service` valida el token contra `/oauth2/userinfo` en **cada petición, sin caché**, y responde **401** si falta o es inválido. *Cambiado el 2026-11-24 por la extensión de seguridad (SECURITY-08): el contrato de `utils_oas` guardaba la validación 60 minutos.*
- CA3: nunca se usan `localStorage`/cookies sin protección para token o datos personales (deny).
- Origen: IN-9; seguridad.

### RF-15 — Autorización por rol único
- CA1: rol único **Admisiones, Registro y Control**, registrado en `configuracion_cliente`, verificado **en el backend** en cada petición.
- CA2: **nunca** se confía en permisos enviados por el cliente (deny: `$_REQUEST['tipoUser']`).
- Origen: IN-9; R3 del análisis existente.

### RF-16 — Contrato de escritura con "Solicitados"
Las solicitudes se escriben en las tablas MySQL `solicitud*` manteniendo estructura, estados y
formatos que **"Solicitados" lee sin cambios**.
- CA1: estados conocidos: `0` = sin imprimir, `2` = cancelada; demás estados y campos exactos por confirmar (OQ-B-4, dependencia bloqueante).
- CA2: no se modifica la estructura de `solicitud*`, `exencion` ni `fechaPagoFacultad`.
- CA3: se escriben las mismas columnas que escribe hoy el sistema PHP (`sql.class.php`): `solicitudRecibo` (`id_usuario`, `codigo_est`, `estado`, `anno`, `periodo`, `fecha`, `cuota`, `id_carrera`, `tipoPlantilla`, `unidad`), `solicitudCuota` (`id_solicitud`, `cuota`, `porcentaje`, `fecha_ordinaria`, `fecha_extra`), `solicitudExencion` (`id_solicitud`, `id_exencion`) y `solicitudConcepto` (`id_solicitud`, `id_concepto`).
- CA4: `id_usuario` guarda el documento de identidad del usuario, como hoy (supuesto A8). `unidad` vale `0` en pregrado, como hoy (RE-07, confirmado por el usuario el 2026-11-25). `solicitudRecibo.cuota` vale 1 en pregrado y el número de cuotas en posgrado (supuesto A15). Estados: 0 = sin imprimir, el único que lee "Solicitados"; 1 = recibo generado, lo escribe "Solicitados"; 2 = cancelada por el lote. D3 quedó resuelta el 2026-11-25 con el código de "Solicitados" (RE-21).
- Origen: IN-10; "Lo que NO debe cambiar".

### 4.A — Reglas de cálculo (referencia de equivalencia)
Resumen consolidado (fuente de verdad para las pruebas unitarias de `app/domain/`, cobertura 100%):
1. Pregrado: 1 cuota 100%; la fecha ordinaria viene de la plantilla (C3, F8; posición de las columnas en D1) y la extraordinaria se calcula como en el punto 3; si faltan o son inválidas, la fila no se sube (RE-06); sin diferido; sin "Seguro" como cuota (`solicitudRecibo.cuota` = 1, A15); sin "Reingreso".
2. Posgrado: número de cuotas obligatorio, de 1 a 3 (RE-03, RE-04), cada una con fecha válida en la plantilla (si falta, la fila no se sube, RE-06); un % vacío toma el valor por defecto de su posición (100 / 60-40 / 40-30-30); los porcentajes son enteros y la suma debe ser 100; la columna 2 (créditos o SMLV) es obligatoria y mayor que 0 (F6); ninguna fecha ordinaria es anterior al día de la carga y cada cuota vence después de la anterior (F7).
3. Pregrado y posgrado: extraordinaria = ordinaria + 8 días calendario; si cae en festivo, se avanza al siguiente día no festivo. Festivos: los de la tabla que usa hoy weboffice (F9; el DBA la identifica, D5); un sábado o un domingo que no esté en ella no mueve la fecha (F10). *Corrige la primera versión de este documento, que decía "8 días hábiles".*
4. Exenciones: como máximo un descuento más la votación; la fila con más de un descuento marcado no se sube (C2). La votación se registra una sola vez: la marcada, sola o con un descuento; la automática (`ACCERELECTORAL`), solo si la fila tiene un descuento marcado (C1, C6, A14). El descuento y la votación juntos no pasan de 100%: si pasarían, se registra solo el descuento (C7). Una columna está marcada si su celda tiene contenido distinto de espacios (F4). La Secretaría de Educación no cuenta como descuento para C2 (F12); no entra en la suma de C7 (F14) y permite la votación automática, como hoy (F15). Los porcentajes de las exenciones salen de la tabla `exencion` (F11).
5. Conceptos: 1 siempre; 19 solo pregrado; 2/3/4 según plantilla.
6. Periodo de la solicitud: año y periodo vigentes del proyecto curricular (evento 80). Si el proyecto no tiene periodo vigente, o la consulta devuelve más de uno (A13), la fila no se sube y el mensaje pide reportarlo al área de sistemas (RE-05). La cancelación de las solicitudes previas sin imprimir abarca todos los periodos, como hoy (C8, que revierte P-7), y aplica también a los estudiantes rechazados (RE-02).
7. Los IDs, eventos, estados, mapas y porcentajes por defecto de las cuotas provienen de "parametros" (RF-09), en solo lectura. Los porcentajes de las exenciones salen de la tabla `exencion` (F11) y los festivos, de la tabla de weboffice (F9).
8. Validaciones nuevas del diseño funcional de U1: un lote de más de 1000 filas con datos se rechaza completo (F1); una fila con datos y sin código es `CODIGO_INVALIDO` (F3); un código repetido se procesa solo en su primera aparición, y las demás son `CODIGO_REPETIDO`, sin cancelar nada (F2); un estudiante de un nivel distinto al de la plantilla es `NIVEL_NO_CORRESPONDE` (F5).

---

## 5. Requisitos no funcionales

Prioridad declarada en la Visión: (1) tiempo de respuesta, (2) seguridad y protección de datos, (3) costos bajos.

### RNF-1 — Rendimiento (síncrono, 1000 estudiantes/lote)
Un lote de hasta 1000 estudiantes se procesa en una sola petición. Los timeouts de gunicorn,
balanceador y WSO2 AM deben permitirlo. (El valor objetivo de latencia se fija en NFR Requirements
de Construction; aquí se fija la restricción estructural.)
**Valores (U1 NFR Requirements, 2026-11-25, N2 y N3):** 1000 estudiantes en 60 s o menos en 95 de cada 100 lotes; hasta 10 estudiantes en 5 s o menos; límite propio de 90 s, después del cual las filas que faltan salen con `TIEMPO_AGOTADO` y no cancelan nada; los tiempos de espera de gunicorn, el balanceador y WSO2 AM, de 120 s o más (`construction/recibos_service/nfr-requirements/nfr-requirements.md`, NFR-P01 a NFR-P05).

### RNF-2 — Seguridad y cumplimiento
- Ley 1581 de 2012; checklist de seguridad OAS; referencia OWASP Top 10 / ASVS / API Security Top 10.
- 0 vulnerabilidades críticas/altas (SQLi, XSS, permisos manipulables) — métrica de éxito.
- SQL solo con **parámetros enlazados** (SQLAlchemy/driver); prohibido concatenar o f-strings.
- Cabeceras de seguridad HTTP obligatorias en todas las respuestas (CSP, HSTS, X-Frame-Options DENY, etc.).
- Secretos solo en SSM Parameter Store (`SecureString`); nada en el repo; `.env` local fuera del repo.
- CORS restringido a `*.udistrital.edu.co` fuera de dev.
- `DEBUG=False` y gunicorn fuera de local; sin endpoint que devuelva variables de entorno/credenciales.
- Health check `GET /` → `{"status":"ok"}` y `/health`.

### RNF-3 — Integridad de datos
Transacciones por solicitud (RF-10). Cero solicitudes incompletas (métrica de éxito).

### RNF-4 — Mantenibilidad / arquitectura
Clean Architecture en `recibos_service` (domain → application → infrastructure → interfaces, dependencias hacia adentro); Flask + Blueprints; API REST documentada en Swagger 2.0 (`swagger/swagger.yml`, publicado en WSO2 AM; sin flasgger desde N12, 2026-11-25); sobre `{Success, Status, Message, Data}`; versión en ruta `/v1`; recursos en español, plural, kebab-case, sin tildes ni ñ, sin verbos CRUD. Dos repos: `recibos_service`, `recibos_mf`.

### RNF-5 — Observabilidad
Auditoría JSON por petición (RF-13); destino de logs CloudWatch Logs, con retención de 365 días (N8). *Cambiado el 2026-11-25 (N14 = c): sin trazas distribuidas en el MVP. Se agregan después con OpenTelemetry, porque el SDK y el daemon de X-Ray pierden el soporte el 2027-02-25.*

### RNF-6 — Pruebas / calidad
Solo pruebas **unitarias automatizadas** en el ciclo de desarrollo (reglas de cuotas, exenciones,
conceptos, fecha extraordinaria con festivos, validación de plantillas). Cobertura ≥80% en
`recibos_service`, **100%** en `app/domain/`. Gate SonarQube: 0 bugs, 0 vulnerabilidades, ≤50%
duplicación. Pruebas de carga/usuario/equivalencia/seguridad las hacen otros grupos, **fuera**
del ciclo; AI-DLC **no** las planea ni genera.

### RNF-7 — Costos
Reutilizar infraestructura existente (modelo aprobado, bases actuales, WSO2). No se crean bases
nuevas; sin Lambda/serverless; contenedores en ECS.

### RNF-8 — Plazo
Desplegado en **test** el **15/12/2026**, listo para la revisión de Seguridad.
### RNF-9 — Disponibilidad
Producción 24/7 con 99,9% de disponibilidad al mes, medida sobre el propio servicio: no cuentan las caídas de Oracle, MySQL, WSO2, "parametros" ni S3. Dos tareas o más en zonas distintas, despliegues sin interrupción y alarmas que atiende el grupo de infraestructura de la OAS (U1 NFR Requirements, 2026-11-25: N6 = c, N15 = a, N16 = a; NFR-A01 a NFR-A08). La extensión de resiliencia sigue desactivada (N17 = b).

---

## 6. Fuera de alcance (deny / OUT — explícito)

No se construyen en esta versión, por ser OUT en la Visión o deny en el Entorno técnico:
- Pantalla de administración de parámetros (Fase 2).
- Consulta histórica por estudiante `admin_historicoPorEstudiante` / `admin_generados` (Fase 2).
- Generar/imprimir el recibo (sigue "Solicitados"; Fase 2+).
- Migrar solicitudes históricas (OQ-B-6 → no aplica).
- Código muerto: `action.php`, `html.php`, "PLANTILLA SIMPLE".
- Consultas de notas de Admisiones, Registro y Control (`admin_consultasCoordinador`; el nombre dice "coordinador" por error, corrección del usuario del 2026-11-25): proyectos, control de notas parciales, histórico de notas y carga de novedades de notas. No son de recibos. Quedan para la **Fase 2** (C5 = b, 2026-11-25).
- Exención de "Reingreso" (C-045558).
- Procesamiento asíncrono / colas / workers (C-2).
- Volver a ver el resumen (procesados y rechazados) de lotes anteriores: `solicitudLote` no lo guarda e IN-8 solo pide quién, cuándo, qué archivo e IP.
- Escritura en el servicio "parametros" (P-11).
- Migrar bases a PostgreSQL o renombrar tablas (lineamientos OAS aplican al **código**, no a las BD).
- Nuevas bases (RDS/DynamoDB), S3 público, Lambda, PHP, `cx_Oracle`, pandas para leer plantillas,
  SQL concatenado, `localStorage` para tokens/datos personales.

---

## 7. Resolución de las 15 preguntas abiertas

Convención de estado:
- **Decidida** — resuelta por decisión aquí; no bloquea.
- **Decidida (supuesto)** — valor por defecto razonable; el usuario puede anularlo (marcado 🔸).
- **Resuelta a nivel de requisito; requiere insumo externo** — el requisito está definido, pero
  la **construcción** depende de un artefacto que hoy no está en el workspace (plantilla, DDL o
  código de "Solicitados"). Marcado 🔺 **dependencia bloqueante para Construction**, no para User
  Stories / Application Design.

### Negocio

**OQ-B-1 — Fecha de reemplazo definitivo de PHP** · *Decidida (supuesto)* 🔸
Fuera del alcance de esta versión. En 2027-1 ambos sistemas corren en paralelo **solo para
pruebas**; el reemplazo en producción se agenda con ARC y OATI **después** de la revisión de
Seguridad en test, idealmente antes de generar los recibos definitivos de 2027-1. No bloquea el MVP.

**OQ-B-2 — Plantilla oficial de posgrado SMLV** · *Requiere insumo externo* 🔺
Requisito: RF-02 CA3 soporta el tipo 3. Supuesto de trabajo: misma estructura de 29 columnas que
créditos, con "SMLV" en la columna 2. **Dependencia**: ARC entrega el `.xls` oficial a
`documentacion/plantillas-recibos/` para confirmar columnas/encabezados antes de cerrar la
validación de formato del tipo 3.

**OQ-B-3 — Nueva plantilla de pregrado (13 columnas, sin Reingreso)** · *Requiere insumo externo* 🔺
Requisito: RF-02 CA1 fija 13 columnas y rechaza 14 (C-3). **Dependencia**: ARC entrega la versión
final (y confirma si cambia el texto de A1 o la fila inicial) antes de construir la validación.
**Actualización (2026-11-25):** la plantilla nueva también trae las fechas de pago (C3), así que ya no tendrá 13 columnas. D1 incluye ahora el número de columnas, la posición y el formato de las fechas, y si trae la fecha extraordinaria.

**OQ-B-4 — Contrato detallado con "Solicitados"** · *Requiere insumo externo* 🔺
Requisito: RF-16 mantiene estructura/estados/formatos. Conocido: estados `0`/`2`. **Dependencia**:
obtener código o documentación de "Solicitados" y el esquema MySQL real (DBA) para confirmar los
campos y estados exactos que lee de `solicitudRecibo/Cuota/Exencion/Concepto`.
**Actualización (2026-11-24):** las columnas que se escriben se conocen por el código actual (RF-16 CA3). Si el sistema nuevo escribe lo mismo que el PHP, "Solicitados" lee lo mismo. Queda pendiente el valor de `solicitudRecibo.cuota` en pregrado y la lista de los demás estados.
**Actualización (2026-11-25):** resuelta con el código de "Solicitados" (`admin_solicitudCoordinador`, RE-20 a RE-26): lee solo el estado 0, pasa la solicitud a 1 al generar y no lee `cuota` en pregrado (A15). Falta solo el DDL (D4).

**OQ-B-5 — Base de datos para pruebas en paralelo** · *Decidida (usuario, 2026-11-24)*
Riesgo: la regla "cancelar solicitudes previas sin imprimir" (RF-08) podría cancelar solicitudes
creadas por el otro sistema si ambos escriben en el mismo `solicitudrecibo`. **Decisión del
usuario**: las pruebas se ejecutan contra una **base de datos de pruebas dedicada** (copia con
datos de periodos anteriores), por lo que la cancelación **no sobrescribe** solicitudes de
producción del sistema PHP. Reflejado en RF-08 CA3. Coherente con "pruebas evaluadas de forma
independiente" (C-3). Queda pendiente solo la provisión operativa de esa copia con el DBA (no
bloquea el diseño).

**OQ-B-6 — Migración de solicitudes históricas** · *Decidida*
**No aplica.** La base MySQL se mantiene (no se migra ni renombra), así que no hay que migrar ni
reprocesar históricos. La versión trabaja solo con solicitudes nuevas. Cerrada.

### Técnicas

**OQ-T-1 — Versiones de Angular y Node** · *Decidida (supuesto)* 🔸
Backend fijo: Python 3.12 (Flask); *actualizado el 2026-11-25 (C4 = a): se usa la última versión estable con soporte de Python, Node y Angular en todo el proyecto (máquina, imagen Docker y CI); las versiones exactas y la compatibilidad de las librerías se fijan en NFR Requirements de cada unidad.* **U1: Python 3.15 (N1, 2026-11-25).** Frontend: tomar las versiones de la rama
`feature/clientes_nuevos` de `oas_cliente` como fuente de verdad; fijar una **Node LTS con soporte
vigente** (no Node 16, que ya no tiene soporte) compatible con esa versión de Angular y con
`single-spa-angular`, y la versión de TypeScript que exija ese Angular. Los valores exactos se
confirman al clonar `oas_cliente` en Construction.

**OQ-T-2 — ¿Existe `utils_oas` en Python?** · *Decidida*
Supuesto: **no** existe librería Python oficial; `utils_oas` es Go/Beego y **no se importa**. Se
**reimplementan sus contratos** dentro de `recibos_service` (errores/respuestas, auditoría/token,
cabeceras, credenciales SSM, health check) según `utils-oas-analysis.md`. Si Arquitectura confirma
que existe una equivalente, se revisa; no bloquea.

**OQ-T-4 — Ejemplo de prueba Python** · *Decidida*
No hay referencia OAS de pruebas Python (los lineamientos cubren Go/Beego). Se define en
Construction un **patrón base de pytest** (`tests/test_*.py`, fixtures, `pytest-cov`) y se usa como
referencia del proyecto. No bloquea.

**OQ-T-5 — Destino y retención de logs de auditoría** · *Decidida (supuesto)* 🔸
Destino por defecto: **CloudWatch Logs** (lista allow). Retención concreta a confirmar con
infraestructura; por defecto alinear con la política de retención institucional/Ley 1581. No
bloquea el diseño; se parametriza en Infraestructura.

**OQ-T-7 — Convención SSM para credenciales de MySQL** · *Decidida (supuesto)* 🔸
Reusar la convención de `utils_oas/database`:
`/{parameterStore}/recibos_service/db/username|password` para Oracle y una ruta análoga para
MySQL, p. ej. `/{parameterStore}/recibos_service/mysql/username|password`. El valor de
`{parameterStore}` y la ruta final se confirman con infraestructura y se documentan en el README de
`recibos_service`.

**OQ-T-8 — Núcleo del framework y fuentes de datos implícitas** · *Requiere insumo externo* 🔺
Faltan en el repo clases con lógica necesaria para la equivalencia: origen de **festivos**
(`calendario.class.php`), **fechas de pago por facultad** (`datosSolicitud` → `fechaPagoFacultad`),
**año y periodo** (`datosGenerales.class.php`) y validación de usuario WO. **Decisión**: estos
datos se consumen vía el servicio "parametros" (festivos, plazo extraordinario, fechas por
facultad; RF-09) y/o Oracle (periodo/eventos, RF-03). **Dependencia**: obtener con DBA/OATI la
definición exacta de esas consultas y el origen de los festivos antes de cerrar RF-05 CA3.
**Actualización (2026-11-24):** el código del módulo resuelve casi todo. El periodo sale de Oracle (consulta `periodoActual`: `ACASPERI` + `ACASPERIEVENTOS`, evento 80, por proyecto curricular) y reemplaza al valor de `datosGenerales`. Las fechas de pregrado salen de `fechaPagoFacultad` por facultad (`ACCRA.cra_dep_cod`) y tipo (normal o terminación de materias). La fecha extraordinaria de posgrado es +8 días calendario y luego salta festivos. Solo falta el origen de los festivos (`calendario.class.php`, `buscar_festivo`) y saber si sábados y domingos cuentan como festivos.

**OQ-T-9 — Modelo de datos aprobado y DDL real** · *Requiere insumo externo* 🔺
Requisito: RF-16 no cambia la estructura. **Dependencia**: incorporar a `documentacion/` el modelo
aprobado por el comité y el DDL real de `solicitud*`, `exencion`, `fechaPagoFacultad` (DBA) para
que la construcción de los adaptadores MySQL sea exacta.

**OQ-T-10 — Límite del archivo y retención en S3** · *Decidida (supuesto)* 🔸
Por defecto: tamaño máximo **10 MB** por archivo (holgado para 1000 filas `.xls`) y retención de
las plantillas cargadas en S3 **alineada a Ley 1581** (valor concreto a fijar con Seguridad/ARC).
Bucket privado, cifrado, sin acceso público. Ajustable sin impacto de diseño.
**Actualización (2026-11-25, N7 y N8):** tamaño máximo de 2 MB y retención de 365 días.

**OQ-T-11 — Contrato del servicio "parametros"** · *Decidida (estrategia)* 🔺
El contrato real (endpoints, autenticación, formato, reglas de actualización) lo entrega el usuario
**después**. **Estrategia**: modelar el acceso como **puerto** en `app/application/` + **adaptador**
en `app/infrastructure/`, aplicando el contrato de cliente de `utils_oas/request` (extraer `Data`
del sobre institucional). Esto desbloquea User Stories y Application Design; el adaptador concreto
se implementa en Construction cuando llegue la sintaxis (dependencia bloqueante solo para esa parte
de Construction).

**Actualización OQ-T-11 (2026-11-24):** el usuario definió la consulta: `GET /v1/parametro/{id}`, un id por parámetro. El adaptador lee cada regla por su id al inicio de cada lote; los ids van en configuración, no en el código (AD-20). El usuario también dio un ejemplo de respuesta: sobre CRUD con `Status` como texto y un objeto `Parametro` sin campo de valor. El servicio es `parametros_crud` (citado en `lineamientos_oas/generacion_de_apis/endpoint_validacions.md`). Quedan pendientes el campo donde va el valor de cada regla, el id de cada regla por ambiente, la URL y la autenticación.

### Cerradas en consolidación (contexto)
OQ-T-3 (asíncrono) → cerrada: **síncrono** (C-2). OQ-T-6 (nombres de repo) → cerrada:
`recibos_service`/`recibos_mf` aceptados (C-5).

---

## 8. Dependencias bloqueantes para Construction (no para User Stories/Design)

Estas resoluciones dejan el **requisito** definido pero necesitan un artefacto externo antes de
**codificar** la parte correspondiente. No bloquean User Stories ni Application Design.

| # | Artefacto requerido | Responsable | Bloquea |
|---|---------------------|-------------|---------|
| D1 | Archivo oficial de la plantilla de pregrado sin "Reingreso" y con la fecha de pago (OQ-B-3, C3): texto de A1, encabezados y posición de las tres columnas de la fecha ordinaria; F8 fijó que la extraordinaria se calcula | ARC | Validación del formato tipo 1 y fechas de pregrado (US-03, US-07) |
| D2 | Plantilla oficial posgrado SMLV (OQ-B-2) | ARC | Validación formato tipo 3 |
| D3 | ~~Valor de `solicitudRecibo.cuota` en pregrado y demás estados que lee "Solicitados"~~ **Resuelta el 2026-11-25** con el código de "Solicitados" (RE-21, A15) | — | Ya no bloquea |
| D4 | DDL real `solicitud*`/`exencion` + modelo aprobado (OQ-T-9); `fechaPagoFacultad` ya no se usa (C3) | DBA | Adaptadores MySQL |
| D5 | Tabla de festivos que usa hoy weboffice: base, nombre y columnas (F9). Los sábados y domingos no mueven la fecha (F10) | DBA | Adaptador de festivos (RF-05 CA3). Dependencia técnica: ya no bloquea historias |
| D6 | Campo y formato del valor de cada regla dentro del objeto `Parametro`, id de cada regla por ambiente, URL y autenticación (OQ-T-11, acotada; el formato del sobre ya se conoce) | Usuario / OATI | Adaptador "parametros" (RF-09) |
| D7 | Rutas SSM finales y `{parameterStore}` (OQ-T-7), destino de los logs (OQ-T-5). El tamaño máximo (2 MB) y la retención (365 días) se decidieron el 2026-11-25 (N7, N8) | Infraestructura / Seguridad | Infraestructura y config |
| D10 | Crear en "parametros" (dev y test) los parámetros de las reglas que hoy están en el código PHP. Los porcentajes de las exenciones siguen en la tabla `exencion` (F11) y las fechas por facultad ya no se usan (C3). La lista está en `aidlc-docs/construction/recibos_service/functional-design/business-rules.md` §11 | OATI / ARC | Procesar lotes en test |
| D11 | Origen (URL) desde el que el root institucional carga `recibos_mf` en cada ambiente, para la lista de CORS | Arquitectura / infraestructura | U1 Infrastructure Design |
| D12 | Política de limitación de tráfico (throttling) de la API en WSO2 AM | Arquitectura | U1 Infrastructure Design |
| D13 | Número de proxies de confianza delante de `recibos_service` que agregan `X-Forwarded-For` (WSO2 AM, balanceador u otros), para tomar la IP correcta (RF-12 CA4, RE-13) | Infraestructura / Arquitectura | U1 Infrastructure Design |
| D14 | Servicio TCPS y puerto de Oracle, y el certificado de la CA de Oracle y de MySQL, para verificar el servidor (N9) | DBA | U1 Infrastructure Design |
| D15 | Canal y turnos con los que el grupo de infraestructura atiende las alarmas 24/7 (N6, N16) | Infraestructura | U1 Infrastructure Design |
| D16 | Cuántas conexiones puede abrir el servicio: hasta 24 a MySQL y 16 a Oracle en producción, y el doble durante un despliegue (U1 NFR Design) | DBA | U1 Infrastructure Design |
| D17 | Con el DDL (D4): que las tablas `solicitud*` sean InnoDB, la versión de MySQL y si `solicitudRecibo` tiene un índice que empiece por (`codigo_est`, `estado`); si no lo tiene, crearlo antes de producción (N19) | DBA | U1 Code Generation del repositorio de MySQL |

---

## 9. Supuestos (anulables por el usuario) 🔸

- A1: ~~tamaño máximo de archivo 10 MB (OQ-T-10)~~ **Decidido el 2026-11-25 (N7): 2 MB.**
- A2: logs a CloudWatch Logs, con retención de al menos 90 días (SECURITY-14). El valor final se confirma con infraestructura (OQ-T-5). **Decidido el 2026-11-25 (N8): 365 días.**
- A3: convención SSM MySQL `/{parameterStore}/recibos_service/mysql/...` (OQ-T-7).
- A4: Node LTS vigente + versiones de `oas_cliente` para Angular/TS (OQ-T-1).
- A5: ~~pruebas en paralelo contra copia de la base~~ → **confirmado por el usuario (2026-11-24)**: base de pruebas dedicada; la cancelación no sobrescribe producción (OQ-B-5).
- A6: posgrado SMLV = 29 columnas como créditos (OQ-B-2), hasta confirmar el archivo.
- A7: reemplazo definitivo de PHP fuera de esta versión (OQ-B-1).
- A8: `id_usuario` (en `solicitudRecibo` y `solicitudLote`) = claim `documento` de `/oauth2/userinfo` de WSO2, que corresponde a la identificación que guarda hoy el sistema PHP.
- A9: **ya no aplica** (C2, 2026-11-25): una fila con más de un descuento ya no se procesa, así que no hay empate que resolver. Antes: si dos descuentos marcados tenían el mismo porcentaje, se registraba el de la columna que aparece primero (P-12).
- A10: las fechas de las cuotas se guardan como timestamp Unix de la medianoche en America/Bogota, como hoy (AD-15).
- A11: la llamada a "parametros" reenvía el token del usuario, como `utils_oas/request` (AD-20).
- A12: la cancelación de las solicitudes de un estudiante rechazado (RE-02) solo es posible si se sabe quién es: su código es válido y está en Oracle. No se cancela nada cuando la fila se rechaza por código inválido o estudiante no encontrado, ni cuando se rechaza el lote completo. *Cambiado el 2026-11-25 por C8: antes también hacía falta el periodo vigente, porque P-7 limitaba la cancelación a ese periodo; ahora el estudiante cuyo proyecto no tiene periodo vigente también cancela.*
- A13: si la consulta del periodo vigente devuelve más de un periodo para el proyecto curricular, la fila no se sube con `SIN_PERIODO_VIGENTE`, como en RE-05. El módulo de notas de ARC muestra que hay un periodo por estado ('A', 'X', 'P'), así que más de uno indica una base inconsistente (RE-18).
- A14: **resuelto el 2026-11-25** con la respuesta del usuario ("si no esta marcado en el archivo y si lo encuentras en la tabla ACCERELECTORAL aplica el descuento"), C6 = b y C7 = a: si la votación no está marcada y la fila tiene un descuento marcado, se registra la votación cuando el estudiante tiene certificado activo en `ACCERELECTORAL`, siempre que el descuento y la votación juntos no pasen de 100%. Con la votación en 10% equivale al tope actual de 90%, así que la votación automática da el mismo resultado que hoy. *Antes: la votación automática conservaba el tope de 90% (P-13).*
- A15: `solicitudRecibo.cuota` vale 1 en pregrado (la única cuota) y el número de cuotas de la plantilla en posgrado. "Solicitados" solo muestra ese campo en posgrado y genera un recibo por cada fila de `solicitudCuota` (RE-21). Si el DBA sabe de otro módulo que lo lea (por ejemplo `admin_generados` o `borrar_registro`, que no están en el workspace), se revisa.

---

## 10. Trazabilidad (resumen)

- IN-1..IN-10 → RF-01..RF-16 (§2).
- Prioridades NFR de la Visión → RNF-1 (tiempo), RNF-2 (seguridad), RNF-7 (costos).
- Allow/deny del Entorno técnico → §5 (allow) y §6 (deny), más restricciones embebidas en los CA.
- 15 preguntas abiertas → §7 (todas con estado), §8 (dependencias) y §9 (supuestos).

---

## 11. Próximo paso

Pendiente de **aprobación explícita**. Tras aprobar:
- **User Stories** (condicional, recomendado: hay funcionalidad de usuario y múltiples escenarios).
- **Application Design** (condicional, recomendado: nuevos componentes `recibos_service`/`recibos_mf`).

No se avanza a User Stories ni Application Design sin aprobación (regla del workflow y de la
convención de aprobación).

---

## 12. Cambios posteriores a la aprobación (2026-11-24)

Origen: respuestas del usuario a los puntos por confirmar de User Stories y lectura del código PHP
(`codigo-fuente/weboffice/bloque/registro_lote_recibo/funcion.class.php` y `sql.class.php`).

### 12.1 Decisiones del usuario

| ID | Decisión | Afecta |
|---|---|---|
| P-3 | Los descuentos no son acumulables; la votación es la única exención acumulable y se registra una sola vez | RF-06 CA3, CA4 |
| P-5 | Los porcentajes de las cuotas de posgrado deben sumar 100 | RF-05 CA2 |
| P-7 | La cancelación de solicitudes sin imprimir aplica solo al periodo vigente. *Revertida el 2026-11-25 por C8: abarca todos los periodos, como hoy* | RF-08 CA4 |
| P-11 | `recibos_service` solo consulta el servicio "parametros" | RF-09, CA4 |
| P-12 | Si hay varios descuentos marcados, se registra solo el de mayor porcentaje. *Reemplazada el 2026-11-25 por C2: la fila con más de un descuento no se sube* | RF-06 CA4 |
| P-13 | Para la votación se conserva exactamente la regla actual, incluida la diferencia entre pregrado y posgrado. *Cambiada el 2026-11-25 por C1, C2, C6 y C7: la votación marcada se registra con cualquier descuento, la automática solo con un descuento marcado, y el descuento más la votación no pasa de 100%* | RF-06 CA3 |
| P-15 | Todas las reglas se leen de "parametros", incluidos los porcentajes de las exenciones y las fechas por facultad. *Desde el 2026-11-25 las fechas vienen de la plantilla (C3); las fechas por facultad ya no se usan. Cambiada el mismo día por F11: los porcentajes de las exenciones se leen de la tabla `exencion`* | RF-09 |

Interpretación aplicada a P-5: se conserva lo que hace hoy el PHP con un porcentaje vacío (toma el
valor por defecto de su posición) y se agrega la validación de que la suma sea 100.

### 12.2 Lo que mostró el código actual

| Hallazgo | Fuente | Afecta |
|---|---|---|
| El periodo sale de Oracle por proyecto curricular (evento 80) | `sql.class.php` → `periodoActual` | RF-05, RF-08, OQ-T-8 |
| Pregrado: fecha ordinaria y extraordinaria salen de `fechaPagoFacultad` por facultad y tipo (normal o terminación de materias) | `funcion.class.php` → `guardarCuota` | RF-05 CA1 |
| Posgrado: extraordinaria = +8 días **calendario** y luego salta festivos (no 8 días hábiles, como decía por error la primera versión de §4.A) | `funcion.class.php` → `guardarCuotas` | RF-05 CA3, §4.A |
| Validación del proyecto curricular activo y del valor de matrícula; orden de las validaciones; el estado H se rechaza por la lista de permitidos | `funcion.class.php` → `verificarCodigo`, `procesarRegistro`; `sql.class.php` → `carrerasTotales` | RF-03 |
| Columnas que se escriben en `solicitud*` y `solicitudLote` | `sql.class.php` → `insertar*` | RF-12, RF-16 |
| El lote se registra al cargarse, antes de validar el formato; `solicitudLote` no tiene columnas para totales | `funcion.class.php` (carga), `sql.class.php` → `insertarLote` | RF-12 |
| Hoy se registran todas las exenciones marcadas y la cancelación no filtra por periodo | `funcion.class.php` → `guardarExencion`; `sql.class.php` → `cancelarSolicitud` | P-3, P-7 (revertida por C8: la cancelación sigue en todos los periodos) |

### 12.3 Cambios acordados frente al sistema actual

La métrica de coincidencia del 100% (C-4) se mide **excluyendo** estos cambios intencionales:

1. Sin exención "Reingreso"; plantilla de pregrado nueva, sin "Reingreso" y con las fechas de pago (Visión, C3).
2. Sin pago diferido ni cuotas al 0% en pregrado (Visión).
3. "Seguro Estudiantil" no se lee como número de cuotas (Visión).
4. Descuentos no acumulables: como máximo un descuento más la votación; la fila con más de un descuento marcado no se sube (P-3, C2). La votación marcada se registra con cualquier descuento mientras la suma no pase de 100%; si pasa, se registra solo el descuento (C2, C7). Frente a hoy cambian dos casos: en pregrado, la votación marcada con un descuento de las columnas 8 a 13 se registra si la suma no pasa de 100% (hoy se quita siempre); en posgrado, la votación marcada se quita si la suma pasa de 100% (hoy se registra siempre). La votación automática da el mismo resultado que hoy (C1, C6, C7, A14). La Secretaría de Educación de posgrado no cuenta como descuento: puede ir con la votación y un descuento, como hoy (F12). Con la Secretaría y un descuento de más de 20% (y hasta 90%), la votación automática ahora se agrega; hoy no (F14). Las exenciones se guardan en el orden votación, descuento y Secretaría (RE-24); hoy van en el orden de las columnas, con la votación automática al final.
5. Los porcentajes de las cuotas de posgrado deben sumar 100 (P-5).
6. ~~La cancelación de solicitudes sin imprimir se limita al periodo vigente (P-7).~~ *Ya no es un cambio: con C8 (2026-11-25) la cancelación sigue abarcando todos los periodos, como hoy. El número se conserva porque otros documentos lo citan.*
7. Validación estricta del archivo y de las filas: tipo real del archivo, fechas existentes con año completo, porcentajes 0–100 (Entorno técnico, "Validación de entradas").
8. Posgrado: el número de cuotas es obligatorio y va de 1 a 3. Hoy la celda vacía genera 1 cuota, un 0 o un texto guardan la solicitud sin cuotas, y 4 o más dan un resultado imprevisible (RE-03, RE-04).
9. Los estudiantes rechazados por estado, valor de matrícula o proyecto curricular también pierden sus solicitudes sin imprimir, de todos los periodos (C8); una falla al guardar la solicitud nueva no revierte la cancelación (RE-02). Hoy esos rechazados no cancelan nada.
10. Si el proyecto curricular no tiene periodo vigente, la fila no se sube y el mensaje pide reportarlo al área de sistemas (RE-05). Hoy se guarda la solicitud sin año ni periodo.
11. Si faltan las fechas de pago en la plantilla o son inválidas, la fila no se sube (RE-06). Hoy, en pregrado, la cuota se guarda sin fechas cuando la facultad no las tiene, y en posgrado se guardan fechas vacías o erradas.
12. Las fechas de pago de pregrado vienen de la plantilla y no de la tabla de fechas de cada facultad (C3). La columna de terminación de materias ya no cambia las fechas. Solo viene la ordinaria; la extraordinaria se calcula como en posgrado (F8).
13. Un lote con más de 1000 filas con datos se rechaza completo (F1). Hoy no hay máximo.
14. Si un código se repite en el lote, solo se procesa su primera aparición; las siguientes no se suben (`CODIGO_REPETIDO`) y no cancelan nada (F2). Hoy queda la solicitud de la última aparición.
15. Una fila con datos y sin código aparece como no subida (`CODIGO_INVALIDO`) (F3). Hoy se omite sin aviso.
16. Una celda con solo espacios no cuenta como marcada (F4). Hoy cuenta.
17. El nivel del proyecto curricular del estudiante debe corresponder a la plantilla (`NIVEL_NO_CORRESPONDE`) (F5). Hoy no se revisa.
18. Posgrado: la columna 2 (créditos o SMLV) es obligatoria y mayor que 0 (`UNIDAD_INVALIDA`) (F6), y los porcentajes de las cuotas son enteros (decisión de diseño). Hoy no se validan.
19. Ninguna fecha ordinaria puede ser anterior al día de la carga, y en posgrado cada cuota vence después de la anterior (F7). Hoy no se revisa.
20. Si un lote llega a su límite propio de 90 s, las filas que faltan no se suben (`TIEMPO_AGOTADO`) y no cancelan nada (N3). Hoy no hay límite.
21. El archivo pesa como máximo 2 MB (N7). Hoy no hay límite (TD-11).

### 12.4 Preguntas nuevas

- **P-12:** resuelta (2026-11-24): se registra el descuento de mayor porcentaje; en empate, el de la columna que aparece primero (A9). *Reemplazada por C2 (2026-11-25): la fila con más de un descuento no se sube.*
- **P-13:** resuelta (2026-11-24): se conserva la regla actual de la votación, incluida la diferencia entre pregrado y posgrado. *Cambiada por C2 y C1 (2026-11-25): ver RF-06 CA3.*
- **P-14:** ya no aplica (2026-11-25): con C2 ningún descuento se descarta; la fila con más de un descuento no se sube y el resumen da el motivo.
- **P-15:** resuelta (2026-11-24): todas las reglas, incluidos los porcentajes de las exenciones y las fechas por facultad, se leen de "parametros". Consecuencia: si un porcentaje cambia, hay que cambiarlo en "parametros" y en la tabla `exencion`, que "Solicitados" usa para calcular el valor (confirmado con su código el 2026-11-25, RE-22). *Cambiada en parte el 2026-11-25 por F11: los porcentajes de las exenciones se leen de la tabla `exencion`, así que ya no hay que cambiarlos en dos lugares.* *Desde el 2026-11-25 las fechas por facultad ya no se usan: vienen de la plantilla (C3).*

### 12.5 Extensiones de AI-DLC (decididas el 2026-11-24, en Units Generation)

| Extensión | Decisión | Efecto en los requisitos |
|---|---|---|
| Seguridad | Activa; las 15 reglas son bloqueantes | RF-14 CA2: el token se valida en cada petición, sin caché (SECURITY-08). CORS con lista explícita de orígenes en todos los ambientes (D11). Throttling en WSO2 AM (D12). Registros con nivel y `request_id`; retención de 365 días (A2, N8). Auditoría de cambios con el estado antes y después (`application-design.md` AD-23 a AD-28) |
| Pruebas basadas en propiedades | Parcial: bloqueantes PBT-02, 03, 07, 08 y 09 | RNF-6: las pruebas unitarias del dominio incluyen pruebas basadas en propiedades con Hypothesis (por ejemplo: los porcentajes suman 100, la fecha extraordinaria no cae en festivo, se registra un solo descuento, el descuento más la votación no pasa de 100%). Siguen siendo pruebas unitarias automatizadas |
| Resiliencia | No activa | Sin cambios; se puede activar antes del paso a producción |

Estas decisiones complementan `technical-environment.md`. Donde el entorno técnico describía el contrato de `utils_oas` (caché de 60 minutos, CORS `*` en dev), manda la extensión de seguridad, igual que con las mejoras que ese documento ya pedía para `sql_statement` y `data`.

### 12.6 Decisiones de Reverse Engineering (2026-11-25)

Origen: respuestas del usuario a los hallazgos de `reverse-engineering/story-code-traceability.md`.

| Hallazgo | Decisión del usuario | Afecta |
|---|---|---|
| RE-01 | "Solo se puede marcar máximo dos descuentos, solo el de votación con cualquier otro; los demás descuentos entre sí no se pueden sumar". Resuelta con C1 = a (sin votación automática en filas sin exenciones marcadas) y C2 = b (más de un descuento: la fila no se sube; la votación marcada va con cualquier descuento). El tope de 90% de la automática se conserva (A14) | RF-06 CA3, CA4; §4.A punto 4; cambio acordado 4 |
| RE-02 | Si el estudiante se rechaza por cualquier motivo, se cancelan sus solicitudes sin imprimir | RF-08 CA2, CA5, CA6; RF-10; A12; cambio acordado 9 |
| RE-03 | Si no tiene número de cuotas, la fila no se sube y aparece en el reporte con el motivo | RF-05 CA2; cambio acordado 8 |
| RE-04 | Las cuotas van de 1 a 3 | RF-05 CA2; cambio acordado 8 |
| RE-05 | El año y el periodo son obligatorios y vienen de la base de datos; si no hay periodo vigente, el mensaje lo dice para que se reporte al área de sistemas | §4.A punto 6; cambio acordado 10 |
| RE-06 | Si faltan las fechas de pago, la fila no se sube y aparece en el reporte. Con C3 = b, también en pregrado las fechas vienen de la plantilla | RF-05 CA1, CA2; cambios acordados 11 y 12 |
| RE-07 | `unidad` se guarda como `0` en pregrado, como hoy | RF-16 CA4 |
| RE-13 | La IP se toma de `X-Forwarded-For` | RF-12 CA4; D13 |
| RE-21 | Sin decisión del usuario: el código de "Solicitados" resuelve D3; `cuota` = 1 en pregrado | RF-16 CA4; D3; A15 |
| A14, C6, C7 | Sobre A14: "si no esta marcado en el archivo y si lo encuentras en la tabla ACCERELECTORAL aplica el descuento". C6 = b: la votación automática solo en filas con un descuento marcado (se mantiene C1). C7 = a, "porque no supera el 100%": si el descuento y la votación pasan de 100%, se registra solo el descuento | RF-06 CA3; §4.A punto 4; cambio acordado 4; A14 |
| RE-26, C8 | C8 = a: se cancelan las solicitudes sin imprimir de todos los periodos, como hoy; revierte P-7 | RF-08 CA4, CA5, CA6; §4.A punto 6; A12; cambios acordados 6 y 9 |
| Reporte | El resumen muestra los que se subieron y los que no, con el motivo | RF-11 CA3 |
| Máquina de desarrollo | Usar las versiones actualizadas de los lenguajes y herramientas. C4 = a: la última versión estable con soporte en todo el proyecto (máquina, imagen y CI); las versiones exactas se fijan en NFR Requirements | `technical-environment.md`; OQ-T-1; AD-27 |
| RE-18 | Sin decisión propia; se aplica el supuesto A13 (más de un periodo = sin periodo vigente) | §4.A punto 6; §9 A13 |
| RE-19 | `admin_consultasCoordinador` es la lógica del usuario de Registro y Control; el nombre está mal. C5 = b: queda fuera de la primera versión y se migra en la Fase 2 | §3; RF-03 CA2; §6 |

Las aclaraciones C1 a C5 se respondieron el 2026-11-25 (`reverse-engineering/reverse-engineering-clarification-questions.md`): C1 a, C2 b (con la precisión "solo la votación y otro"), C3 b, C4 a y C5 b.

### 12.7 Funcionalidades nuevas (sin equivalente en el sistema actual)

El PHP no tiene estas funcionalidades. El usuario confirmó el 2026-11-25 que se incluyen en el MVP. La comparación de equivalencia (C-4) no las busca en el sistema actual.

| Funcionalidad | Historia | Caso de uso | IN |
|---|---|---|---|
| Consultar el historial de lotes | US-13 | UC-02 | IN-8 |
| Auditoría de cada petición | US-14 | Transversal (`services.md`) | IN-8 |

### 12.8 Decisiones de U1 Functional Design (2026-11-25)
Respuestas del usuario a las preguntas F1 a F13 de `aidlc-docs/construction/plans/recibos_service-functional-design-plan.md`: "f1 a, f2 b, f3 a, f4 a, f5 a, f6 a, f7 b, f8 a, f9 c, f10  a, f11 a, f12 b, f13 a".
| Pregunta | Decisión | Afecta |
|---|---|---|
| F1 (P-1) | Un lote con más de 1000 filas con datos se rechaza completo (422) y queda registrado | RF-02 CA5; cambio acordado 13 |
| F2 (P-2) | Código repetido: solo se procesa la primera aparición; las siguientes son `CODIGO_REPETIDO` y no cancelan nada | RF-03 CA8; cambio acordado 14 |
| F3 | Fila con datos y sin código: `CODIGO_INVALIDO` ("Falta el código del estudiante") | RF-02 CA6; cambio acordado 15 |
| F4 | Una celda con solo espacios no cuenta como marcada | RF-06 CA5; cambio acordado 16 |
| F5 | El nivel del proyecto debe corresponder a la plantilla: `NIVEL_NO_CORRESPONDE` | RF-03 CA6, CA7; cambio acordado 17 |
| F6 (P-6) | Créditos o SMLV obligatorios y mayores que 0; entero en créditos, hasta dos decimales en SMLV: `UNIDAD_INVALIDA` | RF-05 CA5; cambio acordado 18 |
| F7 | Ninguna fecha ordinaria anterior al día de la carga; en posgrado, cada cuota vence después de la anterior | RF-05 CA4; cambio acordado 19 |
| F8 (D1) | La plantilla de pregrado trae solo la fecha ordinaria (día, mes y año); la extraordinaria se calcula como en posgrado | RF-05 CA1, CA3; D1; cambio acordado 12 |
| F9 (D5) | Los festivos son los de la tabla que usa hoy weboffice; el DBA la identifica | RF-05 CA3; D5 |
| F10 (D5) | Solo los festivos de la tabla mueven la fecha; los sábados y domingos no | RF-05 CA3; D5 |
| F11 (P-15) | Los porcentajes de las exenciones se leen de la tabla `exencion`, en solo lectura; "parametros" conserva los ids y los mapas | RF-06 CA6; RF-09; P-15; D10 |
| F12 | La Secretaría de Educación no cuenta como descuento para C2: puede ir con la votación y un descuento | RF-06 CA4; cambio acordado 4 |
| F13 (P-10) | No se exporta la lista de no subidos en el MVP | RF-11 CA4 |
| F14 | La Secretaría de Educación no entra en la suma de C7 (descuento + votación ≤ 100%) | RF-06 CA3; cambio acordado 4 |
| F15 | Una fila con solo la Secretaría marcada recibe la votación automática, como hoy | RF-06 CA3 |

F14 y F15 salieron de F12 y se respondieron el mismo día ("f14 a, f15 a"). El diseño funcional de U1 está en `aidlc-docs/construction/recibos_service/functional-design/`; las reglas que hay que crear en "parametros" (D10) están en `business-rules.md` §11.

### 12.9 Decisiones de U1 NFR Requirements (2026-11-25)
Respuestas del usuario a N1 a N13 ("N1 a, N2 a, N3 a, N4 a, N5 a, N6 C, N7 a, N8 a, N9 a, N10 b, N11 a, N12 b, N13 a") y a las aclaraciones N14 a N17 ("n14 c, n15 a, n16 a, n17 b"). El detalle está en `aidlc-docs/construction/recibos_service/nfr-requirements/`.
| Pregunta | Decisión | Afecta |
|---|---|---|
| N1 | Python 3.15; 3.14 de respaldo si una dependencia no se instala | OQ-T-1; AD-27 |
| N2 | 1000 estudiantes en 60 s o menos; hasta 10 en 5 s o menos | RNF-1 |
| N3 | Límite propio de 90 s; las filas que faltan salen con `TIEMPO_AGOTADO` y no cancelan nada | RNF-1; cambio acordado 20; AD-31 |
| N4 | Hasta 3 lotes a la vez | NFR-C01 |
| N5 | Bloqueo por estudiante en MySQL entre la cancelación y el guardado | AD-32; BR-T05 |
| N6, N15, N16 | 24/7 con 99,9%, medido sobre el propio servicio; alarmas para el grupo de infraestructura | RNF-9; D15 |
| N7 | Archivo de 2 MB como máximo | RF-01 CA2; A1; cambio acordado 21 |
| N8 | 365 días para archivos y registros | A2; D7 |
| N9 | TLS hacia Oracle (TCPS) y MySQL, con modo thin | D14 |
| N10, N14 | Sin trazas en el MVP: el SDK de X-Ray pierde el soporte el 2027-02-25 | RNF-5; RF-13 CA3; AD-24; AD-33 |
| N11 | requests en lugar de httpx | AD-08 |
| N12 | Sin flasgger; Swagger 2.0 publicado en WSO2 AM y Swagger UI en un contenedor, en local | RNF-4; AD-13 |
| N13 | ruff y mypy, además de SonarQube | NFR-M02 |
| N17 | La extensión de resiliencia sigue desactivada | §12.5 |

### 12.10 Decisiones de U1 NFR Design (2026-11-25)
Respuestas del usuario a N18 a N20 ("n18 a, los dbas no cambian la claves, n19 a, n20 a"). El detalle está en `aidlc-docs/construction/recibos_service/nfr-design/`.

| Pregunta | Decisión | Afecta |
|---|---|---|
| N18 | Un cambio de contraseña de las bases se toma con un despliegue nuevo, sin cortar el servicio. El usuario aclara que hoy los DBA no cambian las claves | NFR-S11 |
| N19 | Si `solicitudRecibo` no tiene un índice por (`codigo_est`, `estado`), el DBA crea uno no único | RNF-1; D17 |
| N20 | Si MySQL falla por la conexión en 5 filas seguidas, el lote deja de intentar y las filas que faltan salen con `ERROR_GUARDADO` | RF-10; BR-T04; AD-35 |
