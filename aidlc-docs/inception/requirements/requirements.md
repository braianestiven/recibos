# Requisitos — Migración del módulo de recibos por lote (weboffice)

- Fase: INCEPTION → Requirements Analysis
- Profundidad: Comprehensive
- Tipo de proyecto: Brownfield (migración / modernización)
- Fecha: 2026-11-24
- Inputs: `Product-Definition/vision-document.md`, `Product-Definition/technical-environment.md`, `Product-Definition/open-questions.md`
- Soporte: `Product-Definition/interview/technical/existing-system-analysis.md`, `.../templates-analysis.md`
- Estado: **aprobado 2026-11-24**. Actualizado el mismo día con las decisiones de User Stories (P-3, P-5, P-7, P-11) y con evidencia del código PHP actual (ver §12)

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

- **Admisiones, Registro y Control (ARC)** — rol operativo único; absorbe coordinador/asistente/secretario. Carga lotes de cualquier proyecto curricular.
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
- CA2: se rechaza el archivo que supere el tamaño máximo (OQ-T-10 → §5, por defecto 10 MB).
- CA3: el archivo original no queda en disco local del contenedor ni con permisos abiertos.
- Origen: IN-1; deny de `documento/solicitudes/` local y `0777`; allow S3 privado.

### RF-02 — Identificación y validación de formato de plantilla
El sistema identifica el tipo por el texto de la celda A1 y valida el número de columnas y los
encabezados antes de procesar filas.
- CA1: pregrado = **tipo 1**, A1 `PLANTILLA GENERAL PREGRADOS`, datos desde fila 4, **exactamente 13 columnas** (sin "Reingreso"). El formato de 14 columnas **se rechaza** (C-3).
- CA2: posgrado créditos = **tipo 2**, A1 `PLANTILLA GENERAL POSTGRADOS CREDITOS`, datos desde fila 5, **29 columnas**.
- CA3: posgrado SMLV = **tipo 3**, A1 `PLANTILLA GENERAL POSTGRADOS SALARIOS MINIMOS LEGALES`, datos desde fila 5; estructura por confirmar (OQ-B-2, dependencia bloqueante).
- CA4: si A1 no coincide o el número/orden de columnas no corresponde, se rechaza todo el lote con un motivo claro (no se procesa parcialmente el formato).
- Origen: IN-1; templates-analysis.md; C-3.

### RF-03 — Validación académica del estudiante (Oracle, solo lectura)
Por cada código de estudiante del lote, el sistema valida contra Oracle académico.
- CA1: el estado del estudiante debe estar entre los **estados permitidos** (hoy `V,J,T,A,Q,B`; parametrizado vía "parametros", RF-09).
- CA2: el proyecto curricular del estudiante debe estar activo (`cra_estado = 'A'`, código distinto de 0 y 999). Es el comportamiento actual del perfil con acceso a todas las carreras (nivel 132, consulta `carrerasTotales`), que corresponde al rol único ARC.
- CA3: si el evento de **terminación de materias** (hoy 82) está activo para el proyecto curricular del estudiante (`fua_verifica_evento`), solo se aceptan los estados `T` o `H`. Como `H` no está en la lista de estados permitidos, hoy se rechaza antes por CA1; se conserva ese orden.
- CA4: Oracle se usa **solo lectura**; no se modifica estructura ni datos.
- CA5: si el estudiante existe pero no tiene valor de matrícula en `V_ACESTMATBRUTO`, se rechaza con el motivo "Sin información de matrícula".
- CA6: las validaciones se aplican en el orden del sistema actual (existencia, información de matrícula, estado, proyecto curricular, terminación de materias); el motivo de rechazo es el de la primera que falla.
- Origen: IN-2; existing-system-analysis.md §3; `funcion.class.php` (`verificarCodigo`, `procesarRegistro`); deny de escritura en Oracle.

### RF-04 — Generación de solicitud de recibo
Por cada estudiante válido, el sistema crea una solicitud con sus cuotas, exenciones y
conceptos, equivalente al sistema actual salvo las reglas acordadas (§4.A).
- CA1: la solicitud se escribe en `solicitudRecibo` con los formatos que lee "Solicitados" (fechas = timestamp Unix, porcentajes 0–100, `estado` existente).
- CA2: equivalencia 100% en cuotas, exenciones y conceptos frente al actual sobre los lotes de prueba (métrica de éxito; herramienta de comparación en etapa posterior, C-4).
- Origen: IN-3; métricas de éxito.

### RF-05 — Reglas de cuotas (con cambios acordados)
- CA1: **Pregrado** — una sola cuota al **100%**. La fecha ordinaria y la extraordinaria salen de las fechas de pago de la facultad del proyecto curricular: tipo normal, o tipo "terminación de materias" (hoy 3) si su columna está marcada, aunque por P-12 se registre otro descuento de mayor porcentaje. **Se elimina** el diferido (3 cuotas al 0% "COVID"). **No** se lee "Seguro Estudiantil" como número de cuota.
- CA2: **Posgrado (créditos y SMLV)** — 1 a 3 cuotas según la plantilla; cada cuota debe traer una fecha válida. Un porcentaje vacío toma el valor por defecto de su posición (**100 / 60-40 / 40-30-30**), como hoy. La suma de los porcentajes debe ser **100**; si no, se rechaza el estudiante (decisión P-5, cambio frente al sistema actual).
- CA3: **Posgrado** — fecha extraordinaria = fecha ordinaria **+ 8 días calendario**; si ese día es festivo, se avanza un día a la vez hasta el primero que no lo sea (código actual, `guardarCuotas`). Origen de los festivos: D5.
- Origen: IN-3; "Reglas acordadas"; "Reglas de cálculo vigentes".

### RF-06 — Exenciones
- CA1: se aplica el mapa **columna → id_exención** por tipo de plantilla (parametrizado, RF-09; hoy fijo en código).
- CA2: pregrado **excluye "Reingreso"** (C-045558, `id_exencion 18`); la columna no existe en la plantilla de 13.
- CA3: **Votación** (10%, `id_exencion 1`): es la única exención acumulable y se registra **una sola vez**, venga de la columna de la plantilla, de `ACCERELECTORAL` (certificado activo) o de ambas (decisión P-3). Se conserva la regla actual (decisión P-13): (a) la votación marcada se registra, salvo en pregrado cuando además hay marcado un descuento de las columnas 8 a 13; (b) si la votación no quedó registrada, se consulta `ACCERELECTORAL` solo cuando el descuento registrado es ≤ 90% o no hay descuento; (c) en posgrado la votación marcada se registra siempre, aunque el total pase de 100%, como hoy.
- CA4: **Los descuentos no son acumulables** (decisión P-3): una solicitud lleva como máximo un descuento además de la votación. Si la fila trae varios descuentos marcados, se registra solo el de **mayor porcentaje** (decisión P-12); en empate, el de la columna que aparece primero (supuesto A9). Es un cambio frente al sistema actual, que registra todas las exenciones marcadas.
- CA5: una columna de concepto o de exención está **marcada** si su celda tiene cualquier contenido, como hoy (`isset` en `conceptoPlantilla` y `exencionPlantilla`).
- Origen: IN-3; templates-analysis.md; "Reglas acordadas".

### RF-07 — Conceptos
- CA1: siempre se graba el concepto 1 (matrícula); el 19 solo en pregrado; los conceptos 2, 3, 4 según las columnas de la plantilla.
- CA2: los IDs de concepto son **parámetros** (RF-09), no literales en el código.
- Origen: IN-3; existing-system-analysis.md §3.

### RF-08 — Cancelación de solicitudes previas sin imprimir
Antes de insertar la nueva solicitud de un estudiante, se cancelan sus solicitudes anteriores
**sin imprimir** (estado `0 → 2`).
- CA1: solo afecta solicitudes del mismo estudiante en estado "sin imprimir".
- CA2: la cancelación y la inserción nueva ocurren dentro de la **misma transacción** que RF-10.
- CA3: las pruebas en paralelo se ejecutan contra una **base de datos de pruebas dedicada** (copia con datos de periodos anteriores), de modo que la cancelación de solicitudes previas **nunca sobrescribe ni cancela** solicitudes creadas por el sistema PHP en producción (OQ-B-5 resuelta).
- CA4: solo se cancelan las solicitudes sin imprimir del **periodo vigente**, es decir, el año y periodo de la nueva solicitud (decisión P-7). Es un cambio frente al sistema actual, cuya consulta `cancelarSolicitud` cancela las de todos los periodos.
- Origen: IN-4.

### RF-09 — Reglas parametrizadas vía servicio externo "parametros"
Las reglas que hoy están fijas en el código se **consultan** (solo lectura, decisión P-11) en el servicio externo
REST síncrono "parametros": conceptos, exenciones, fechas de pago por facultad, porcentajes por
defecto, estados permitidos, eventos de calendario, plazo de la fecha extraordinaria y mapa
columna → exención.
- CA1: **ningún** ID de concepto/exención/evento/estado ni porcentaje queda fijo en el código (deny: reglas activadas comentando código).
- CA2: el acceso se modela como un **puerto** en `app/application/` con un **adaptador** en `app/infrastructure/`. Contrato conocido (usuario, 2026-11-24): cada parámetro se consulta por su id con `GET /v1/parametro/{id}` (por ejemplo `/v1/parametro/9`). La respuesta usa el sobre CRUD (`Status` como texto, `"200"`) y `Data` es un objeto `Parametro` (`Id`, `Nombre`, `Descripcion`, `CodigoAbreviacion`, `Activo`, `NumeroOrden`, `TipoParametroId`, `ParametroPadreId`) sin un campo de valor. Falta definir en qué campo va el valor de cada regla, el id de cada regla por ambiente, la URL y la autenticación (D6, acotada).
- CA3: Meta de negocio: **cero cambios de código por periodo**.
- CA4: `recibos_service` **no** crea, modifica ni borra reglas en "parametros"; las actualiza el responsable de ese servicio, fuera de este sistema (P-11).
- Origen: IN-5; C-1; OQ-T-11.

### RF-10 — Atomicidad por solicitud
Cada solicitud se guarda **completa o no se guarda**: inserción de `solicitudRecibo`,
`solicitudCuota`, `solicitudExencion`, `solicitudConcepto` y la cancelación previa (RF-08)
dentro de una transacción.
- CA1: ante un fallo a mitad de camino, no quedan solicitudes sin cuotas ni sin conceptos (métrica objetivo: 0 incompletas).
- CA2: el fallo de un estudiante no aborta todo el lote: ese estudiante se marca como rechazado con motivo (RF-11) y el resto continúa.
- Origen: IN-6; deny de escrituras relacionadas sin transacción; métrica de éxito.

### RF-11 — Resumen del lote
Al terminar, el sistema devuelve en la misma respuesta (síncrono) el resumen: procesados y
rechazados con el **motivo** de cada rechazo.
- CA1: cada rechazo indica el código del estudiante y la causa (estado inválido, no encontrado, formato de fila, etc.).
- CA2: el resumen es consistente con lo efectivamente escrito en MySQL.
- Origen: IN-7.

### RF-12 — Historial de lotes
Se conserva el registro de cada lote cargado (quién, cuándo, nombre del archivo, IP, resultado).
- CA1: se usa `solicitudLote` existente sin cambiar su estructura: `id_usuario`, `nombreOriginal`, `nombreInterno`, `ip`, `fecha`.
- CA2: el lote se registra al cargarse el archivo, antes de validar el formato, como hoy; los lotes rechazados por formato también quedan en el historial. Los archivos rechazados por tipo o tamaño no se guardan ni se registran (la petición queda en la auditoría, RF-13).
- CA3: la tabla no guarda totales ni motivos de rechazo. El historial muestra usuario, fecha, archivo e IP, que es el alcance de IN-8; el resumen completo se ve al terminar la carga (RF-11).
- Origen: IN-8.

### RF-13 — Auditoría por petición
Cada petición genera un log JSON de auditoría con los campos del contrato `utils_oas/auditoria`:
`app_name, agent, data, date, host, ip_user, method, path, query, schema, sql_statement, status,
trace_id, user`.
- CA1: `sql_statement` capturado **por petición**; `data` **sin datos personales** (Ley 1581).
- CA2: logs **siempre habilitados**; destino CloudWatch Logs (OQ-T-5, §5).
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
- CA4: `id_usuario` guarda el documento de identidad del usuario, como hoy (supuesto A8). Queda pendiente en D3 el valor de `solicitudRecibo.cuota` en pregrado (hoy depende, por el defecto, de la columna "Seguro Estudiantil") y la lista de los demás estados.
- Origen: IN-10; "Lo que NO debe cambiar".

### 4.A — Reglas de cálculo (referencia de equivalencia)
Resumen consolidado (fuente de verdad para las pruebas unitarias de `app/domain/`, cobertura 100%):
1. Pregrado: 1 cuota 100%; fecha ordinaria y extraordinaria de la tabla de la facultad (tipo normal, o terminación de materias si esa exención está marcada); sin diferido; sin "Seguro" como cuota; sin "Reingreso".
2. Posgrado: 1–3 cuotas, cada una con fecha válida; un % vacío toma el valor por defecto de su posición (100 / 60-40 / 40-30-30); la suma debe ser 100.
3. Posgrado: extraordinaria = ordinaria + 8 días calendario; si cae en festivo, se avanza al siguiente día no festivo (origen de los festivos: D5). *Corrige la primera versión de este documento, que decía "8 días hábiles".*
4. Exenciones: un solo descuento (no acumulables; si hay varios marcados, el de mayor porcentaje, P-12) más la votación, que se registra una sola vez con la regla actual (P-13): en pregrado no se registra la marcada si hay un descuento de las columnas 8 a 13; la automática solo si el descuento es ≤ 90%; en posgrado la marcada se registra siempre. Una columna está marcada si su celda tiene contenido.
5. Conceptos: 1 siempre; 19 solo pregrado; 2/3/4 según plantilla.
6. Periodo de la solicitud: año y periodo vigentes del proyecto curricular (evento 80); la cancelación de solicitudes previas se limita a ese periodo (P-7).
7. Todos los IDs/porcentajes/eventos/estados provienen de "parametros" (RF-09), en solo lectura.

---

## 5. Requisitos no funcionales

Prioridad declarada en la Visión: (1) tiempo de respuesta, (2) seguridad y protección de datos, (3) costos bajos.

### RNF-1 — Rendimiento (síncrono, 1000 estudiantes/lote)
Un lote de hasta 1000 estudiantes se procesa en una sola petición. Los timeouts de gunicorn,
balanceador y WSO2 AM deben permitirlo. (El valor objetivo de latencia se fija en NFR Requirements
de Construction; aquí se fija la restricción estructural.)

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
Clean Architecture en `recibos_service` (domain → application → infrastructure → interfaces, dependencias hacia adentro); Flask + Blueprints; API REST con OpenAPI/Swagger (flasgger); sobre `{Success, Status, Message, Data}`; versión en ruta `/v1`; recursos en español, plural, kebab-case, sin tildes ni ñ, sin verbos CRUD. Dos repos: `recibos_service`, `recibos_mf`.

### RNF-5 — Observabilidad
Auditoría JSON por petición (RF-13); trazas X-Ray; destino de logs CloudWatch Logs (OQ-T-5).

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

---

## 6. Fuera de alcance (deny / OUT — explícito)

No se construyen en esta versión, por ser OUT en la Visión o deny en el Entorno técnico:
- Pantalla de administración de parámetros (Fase 2).
- Consulta histórica por estudiante `admin_historicoPorEstudiante` / `admin_generados` (Fase 2).
- Generar/imprimir el recibo (sigue "Solicitados"; Fase 2+).
- Migrar solicitudes históricas (OQ-B-6 → no aplica).
- Código muerto: `action.php`, `html.php`, "PLANTILLA SIMPLE".
- Consultas de notas del coordinador `admin_consultasCoordinador`.
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

**OQ-B-4 — Contrato detallado con "Solicitados"** · *Requiere insumo externo* 🔺
Requisito: RF-16 mantiene estructura/estados/formatos. Conocido: estados `0`/`2`. **Dependencia**:
obtener código o documentación de "Solicitados" y el esquema MySQL real (DBA) para confirmar los
campos y estados exactos que lee de `solicitudRecibo/Cuota/Exencion/Concepto`.
**Actualización (2026-11-24):** las columnas que se escriben se conocen por el código actual (RF-16 CA3). Si el sistema nuevo escribe lo mismo que el PHP, "Solicitados" lee lo mismo. Queda pendiente el valor de `solicitudRecibo.cuota` en pregrado y la lista de los demás estados.

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
Backend fijo: Python 3.12 (Flask). Frontend: tomar las versiones de la rama
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
| D1 | Plantilla oficial pregrado 13 columnas (OQ-B-3) | ARC | Validación formato tipo 1 |
| D2 | Plantilla oficial posgrado SMLV (OQ-B-2) | ARC | Validación formato tipo 3 |
| D3 | Valor de `solicitudRecibo.cuota` en pregrado y demás estados que lee "Solicitados" (OQ-B-4, acotada) | DBA / dueño de "Solicitados" | Adaptador MySQL de escritura (RF-16) |
| D4 | DDL real `solicitud*`/`exencion`/`fechaPagoFacultad` + modelo aprobado (OQ-T-9) | DBA | Adaptadores MySQL |
| D5 | Origen de los festivos y si sábados y domingos cuentan (OQ-T-8, acotada) | DBA / OATI | RF-05 CA3 |
| D6 | Campo y formato del valor de cada regla dentro del objeto `Parametro`, id de cada regla por ambiente, URL y autenticación (OQ-T-11, acotada; el formato del sobre ya se conoce) | Usuario / OATI | Adaptador "parametros" (RF-09) |
| D7 | Rutas SSM finales y `{parameterStore}` (OQ-T-7), destino/retención logs (OQ-T-5), límites/retención S3 (OQ-T-10) | Infraestructura / Seguridad | Infraestructura y config |
| D10 | Crear en "parametros" (dev y test) los parámetros de las reglas, que hoy están en el código PHP y en las tablas `exencion` y `fechaPagoFacultad` | OATI / ARC | Procesar lotes en test |
| D11 | Origen (URL) desde el que el root institucional carga `recibos_mf` en cada ambiente, para la lista de CORS | Arquitectura / infraestructura | U1 Infrastructure Design |
| D12 | Política de limitación de tráfico (throttling) de la API en WSO2 AM | Arquitectura | U1 Infrastructure Design |

---

## 9. Supuestos (anulables por el usuario) 🔸

- A1: tamaño máximo de archivo 10 MB (OQ-T-10).
- A2: logs a CloudWatch Logs, con retención de al menos 90 días (SECURITY-14). El valor final se confirma con infraestructura (OQ-T-5).
- A3: convención SSM MySQL `/{parameterStore}/recibos_service/mysql/...` (OQ-T-7).
- A4: Node LTS vigente + versiones de `oas_cliente` para Angular/TS (OQ-T-1).
- A5: ~~pruebas en paralelo contra copia de la base~~ → **confirmado por el usuario (2026-11-24)**: base de pruebas dedicada; la cancelación no sobrescribe producción (OQ-B-5).
- A6: posgrado SMLV = 29 columnas como créditos (OQ-B-2), hasta confirmar el archivo.
- A7: reemplazo definitivo de PHP fuera de esta versión (OQ-B-1).
- A8: `id_usuario` (en `solicitudRecibo` y `solicitudLote`) = claim `documento` de `/oauth2/userinfo` de WSO2, que corresponde a la identificación que guarda hoy el sistema PHP.
- A9: si dos descuentos marcados tienen el mismo porcentaje, se registra el de la columna que aparece primero en la plantilla (P-12). El valor a pagar es el mismo; solo cambia la exención que queda registrada.
- A10: las fechas de las cuotas se guardan como timestamp Unix de la medianoche en America/Bogota, como hoy (AD-15).
- A11: la llamada a "parametros" reenvía el token del usuario, como `utils_oas/request` (AD-20).

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
| P-7 | La cancelación de solicitudes sin imprimir aplica solo al periodo vigente | RF-08 CA4 |
| P-11 | `recibos_service` solo consulta el servicio "parametros" | RF-09, CA4 |
| P-12 | Si hay varios descuentos marcados, se registra solo el de mayor porcentaje | RF-06 CA4 |
| P-13 | Para la votación se conserva exactamente la regla actual, incluida la diferencia entre pregrado y posgrado | RF-06 CA3 |
| P-15 | Todas las reglas se leen de "parametros", incluidos los porcentajes de las exenciones y las fechas por facultad | RF-09 |

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
| Hoy se registran todas las exenciones marcadas y la cancelación no filtra por periodo | `funcion.class.php` → `guardarExencion`; `sql.class.php` → `cancelarSolicitud` | P-3, P-7 |

### 12.3 Cambios acordados frente al sistema actual

La métrica de coincidencia del 100% (C-4) se mide **excluyendo** estos cambios intencionales:

1. Sin exención "Reingreso"; plantilla de pregrado de 13 columnas (Visión).
2. Sin pago diferido ni cuotas al 0% en pregrado (Visión).
3. "Seguro Estudiantil" no se lee como número de cuotas (Visión).
4. Descuentos no acumulables: un solo descuento, el de mayor porcentaje, más la votación (P-3, P-12). La regla de la votación no cambia (P-13).
5. Los porcentajes de las cuotas de posgrado deben sumar 100 (P-5).
6. La cancelación de solicitudes sin imprimir se limita al periodo vigente (P-7).
7. Validación estricta del archivo y de las filas: tipo real del archivo, fechas existentes con año completo, porcentajes 0–100 (Entorno técnico, "Validación de entradas").

### 12.4 Preguntas nuevas

- **P-12:** resuelta (2026-11-24): se registra el descuento de mayor porcentaje; en empate, el de la columna que aparece primero (A9).
- **P-13:** resuelta (2026-11-24): se conserva la regla actual de la votación, incluida la diferencia entre pregrado y posgrado.
- **P-14:** pendiente para U1 Functional Design: ¿el resumen del lote debe avisar cuando se descartó un descuento por no ser acumulable? Propuesta: no en el MVP (IN-7 pide procesados y rechazados con motivo).
- **P-15:** resuelta (2026-11-24): todas las reglas, incluidos los porcentajes de las exenciones y las fechas por facultad, se leen de "parametros". Consecuencia: si un porcentaje cambia, hay que cambiarlo en "parametros" y en la tabla `exencion`, que probablemente usa "Solicitados" para calcular el valor.

### 12.5 Extensiones de AI-DLC (decididas el 2026-11-24, en Units Generation)

| Extensión | Decisión | Efecto en los requisitos |
|---|---|---|
| Seguridad | Activa; las 15 reglas son bloqueantes | RF-14 CA2: el token se valida en cada petición, sin caché (SECURITY-08). CORS con lista explícita de orígenes en todos los ambientes (D11). Throttling en WSO2 AM (D12). Registros con nivel y `request_id`; retención de al menos 90 días (A2). Auditoría de cambios con el estado antes y después (`application-design.md` AD-23 a AD-28) |
| Pruebas basadas en propiedades | Parcial: bloqueantes PBT-02, 03, 07, 08 y 09 | RNF-6: las pruebas unitarias del dominio incluyen pruebas basadas en propiedades con Hypothesis (por ejemplo: los porcentajes suman 100, la fecha extraordinaria no cae en festivo, se registra un solo descuento). Siguen siendo pruebas unitarias automatizadas |
| Resiliencia | No activa | Sin cambios; se puede activar antes del paso a producción |

Estas decisiones complementan `technical-environment.md`. Donde el entorno técnico describía el contrato de `utils_oas` (caché de 60 minutos, CORS `*` en dev), manda la extensión de seguridad, igual que con las mejoras que ese documento ya pedía para `sql_statement` y `data`.
