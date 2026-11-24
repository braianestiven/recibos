# Entrevista Técnica — Historial de respuestas

Registro de solo anexado: aquí se agrega cada pregunta con su respuesta confirmada. Nunca se reescribe ni se borra.

---

## Sección T1 — Resumen técnico · T1–T4
**Registrado**: 2026-11-23T23:15:00Z
Respuesta del usuario (verbatim): "t1 a, t2 a, t3 b, t4  6 personas en diversos roles en el que 3 son devs, 1 infra, 1 bd, y 1 seguridad"

### T1: ¿En qué entorno se ejecutará el sistema?
[Answer]: a — Solo nube.
Por confirmar: ubicación de Oracle académico y MySQL (QB2 dice que se mantienen las bases actuales). Si siguen en servidores propios, el entorno sería híbrido.

### T2: ¿Qué proveedor de nube?
[Answer]: a — AWS.

### T3: ¿Cuál es el modelo de despliegue?
[Answer]: b — Contenedores (Docker en AWS ECS según lineamientos OAS).

### T4: Equipo
[Answer]: 6 personas en diversos roles: 3 desarrolladores, 1 infraestructura, 1 base de datos, 1 seguridad.
Experiencia por tecnología: no especificada.

---

## Sección T1 — Aclaración T1 y cierre
**Registrado**: 2026-11-23T23:18:00Z
Respuesta del usuario (verbatim): "a"

### T1 (aclaración): ¿Dónde están Oracle académico y MySQL?
[Answer]: a — También en AWS. "Solo nube" se confirma: aplicaciones y bases de datos en AWS.
T4: experiencia por tecnología no especificada.

## ✅ Sección T1 completa — aprobada
Aprobación: el usuario respondió la aclaración indicada como condición de cierre de la sección.

---

## Sección T2 — Lenguajes · T5–T7
**Registrado**: 2026-11-23T23:22:00Z
Respuesta del usuario (verbatim): "t5 ok, t6 sin otros, t7 php"

### T5: Lenguajes obligatorios
[Answer]: ok

| Lenguaje | Versión | Propósito | Justificación |
|---|---|---|---|
| Python | 3.12 | Backend | Decisión de negocio (Q6); lineamiento Flask (L5); 3.8 sin soporte (L9) |
| TypeScript | 5.x (la que exija Angular) | Frontend Angular / microcliente single-spa | Decisión de negocio (Q6); lineamientos de clientes (L14) |
| SQL | Oracle y MySQL | Oracle académico (solo lectura) y `solicitudrecibo` | Bases actuales se mantienen (QB2) |

Pendiente (pregunta abierta técnica): versiones de Angular y Node (lineamiento cita Node 16, sin soporte).

### T6: Lenguajes permitidos
[Answer]: b — Ninguno además de los obligatorios ("sin otros").
Nota: los archivos de soporte que exige la plataforma (Dockerfile, `.drone.yml`, `entrypoint.sh` si aplica) no se consideran lenguaje de aplicación.

### T7: Lenguajes prohibidos
[Answer]: a

| Lenguaje | Motivo |
|---|---|
| PHP | Es lo que se reemplaza; objetivo de retirar PHP 5 (Q5) |

---

## ✅ Sección T2 completa — aprobada
**Registrado**: 2026-11-23T23:25:00Z
Aprobación del usuario: "aprobar"

---

## Sección T3 — Frameworks y librerías · T8–T10
**Registrado**: 2026-11-23T23:28:00Z
Respuesta del usuario (verbatim): "t8 ok, t9, t10 ok"
Interpretación: T8, T9 y T10 aceptadas tal como se sugirieron.

### T8: Frameworks obligatorios
[Answer]: ok

| Framework | Dominio | Justificación |
|---|---|---|
| Flask (con Blueprints) | API backend | Único lineamiento Python OAS (L5) |
| gunicorn | Servidor de aplicación en el contenedor | Lineamiento Flask (L6) |
| flasgger (Swagger/OpenAPI) | Documentación de la API | Swagger exigido para desplegar (L6, L41) |
| Angular + single-spa-angular | Frontend (microcliente) | Arquitectura de microclientes (L2); plantilla `oas_cliente` (L14) |
| Angular Material | Componentes de interfaz | Tema institucional (L17) |

### T9: Librerías preferidas
[Answer]: ok

| Librería | Uso / condiciones |
|---|---|
| python-oracledb (modo thin) | Oracle académico, solo lectura |
| PyMySQL o mysqlclient | MySQL (`solicitudrecibo`); elección final en diseño |
| SQLAlchemy 2.x (Core) | Consultas parametrizadas y transacciones |
| xlrd 2.x | Lectura de plantillas `.xls` |
| pydantic | Validación de filas de plantilla y entradas de la API |
| python-dotenv | Variables de entorno en local (L7) |
| pytest | Pruebas del backend (L10) |

### T10: Librerías y prácticas prohibidas
[Answer]: ok

| Prohibido | Motivo | Usar en su lugar |
|---|---|---|
| `cx_Oracle` | Reemplazado por su sucesor | `python-oracledb` |
| SQL concatenado o con f-strings | Inyección SQL; bloqueante en Seguridad (R1, L38) | Parámetros enlazados (SQLAlchemy / driver) |
| Servidor de desarrollo de Flask o `DEBUG=True` fuera de local | Expone información (L8) | gunicorn con `DEBUG=False` |
| Devolver variables de entorno o credenciales en un endpoint | Bloqueante (L8, L38) | `/health` que solo devuelve estado |
| `localStorage` / cookies sin protección para tokens o datos personales | Robo de sesión; Ley 1581 (L18) | Sesión manejada por el microcliente core con WSO2 |
| pandas para leer plantillas | Dependencia pesada innecesaria | xlrd |

---

## Sección T3 — Cambio aprobado · T9 (librerías por `utils_oas`)
**Registrado**: 2026-11-23T23:45:00Z
Respuesta del usuario (verbatim): "aprobar"

### T9 (adición)
[Answer]: se agregan a las librerías preferidas (ver `interview/technical/utils-oas-analysis.md`):

| Librería | Uso | Equivale a (`utils_oas`, Go) |
|---|---|---|
| boto3 | Credenciales en AWS SSM Parameter Store | `ssm`, `database` |
| aws-xray-sdk | Trazas X-Ray | `xray` |
| httpx o requests | Validar token en `/oauth2/userinfo` | `auditoria` |
| cachetools | Caché de 60 min del usuario por token | `auditoria` |

Decisión asociada: `utils_oas` es Go/Beego y no se importa; sus contratos (sobre `{Success, Status, Message, Data}`, 10 cabeceras de `security`, log JSON y validación de token de `auditoria`, `GET /` de `apiStatusLib`, rutas SSM, `America/Bogota`) se reimplementan en un módulo Python del proyecto.
Pendiente (pregunta abierta técnica): ¿existe o se planea una versión Python de `utils_oas`? (sin respuesta)

## ✅ Sección T3 completa — aprobada
**Registrado**: 2026-11-23T23:45:00Z

---

## Sección T4 — Servicios en la nube · T11–T12
**Registrado**: 2026-11-23T23:48:00Z
Respuesta del usuario (verbatim): "ok"

### T11: Servicios AWS permitidos
[Answer]: ok

| Servicio | Condiciones / notas |
|---|---|
| ECS (clusters `test` y `oas`) | Contenedores del backend y del microcliente (L43) |
| ECR | Imágenes publicadas por Drone (L43) |
| SSM Parameter Store | Credenciales de BD y parámetros, cifrados (`utils_oas/ssm`) |
| X-Ray | Trazas (`utils_oas/xray`) |
| CloudWatch Logs | Logs de auditoría JSON (por confirmar con infraestructura) |
| S3 | Plantillas cargadas: bucket privado, cifrado, sin acceso público, retención definida (Ley 1581); reemplaza `documento/solicitudes/` con 0777 |
| Oracle y MySQL existentes en AWS | Solo los existentes (QB2); Oracle solo lectura |
| WSO2 IS/AM institucional | Autenticación y publicación de la API (L19) |

### T12: Servicios / usos prohibidos
[Answer]: ok (a)

| Servicio / uso | Motivo |
|---|---|
| Buckets S3 públicos o URLs públicas permanentes | Datos personales (Ley 1581) |
| Bases de datos nuevas (RDS, DynamoDB u otras) | Se mantienen las bases actuales (QB2) |
| Lambda / serverless | Se eligió contenedores en ECS (T3) |
| Credenciales en texto plano en variables de la tarea ECS | Deben venir de SSM; bloqueante si se exponen (L38) |

---

## ✅ Sección T4 completa — aprobada
**Registrado**: 2026-11-23T23:50:00Z
Aprobación del usuario: "aprobar"

---

## Sección T5 — Arquitectura y patrones · T13–T16
**Registrado**: 2026-11-23T23:55:00Z
Respuesta del usuario (verbatim): "t13 a, t14 a usando las bds existentes, 15 d, t16 debe llamarse recibos_service y recibos_mf para el front"

### T13: Estilo de API
[Answer]: a — REST documentada con OpenAPI/Swagger; `/v1`; recursos en español, plural, kebab-case, sin verbos CRUD (L30–L34); sobre `{Success, Status, Message, Data}` (`utils_oas/requestresponse`).

### T14: Patrones de datos
[Answer]: a — Relacional, usando las bases existentes: Oracle académico (solo lectura) y MySQL (`solicitudrecibo` y relacionadas, con transacciones). Plantillas cargadas en S3 (T11).

### T15: Comunicación entre componentes
[Answer]: d — Mezcla. (Por aclarar: qué partes son síncronas y cuáles asíncronas.)
Tamaño máximo de lote: sin respuesta.

### T16: Estructura del código
[Answer]: Repositorios:
- `recibos_service` — backend (API Flask).
- `recibos_mf` — frontend (microfrontend Angular / single-spa).
Nota: los nombres difieren del lineamiento `<negocio>_cliente|mid|crud` (L3, `repositorios_institucionales/nombre_repos.md`); se registra como decisión del proyecto. No se crea repositorio CRUD separado.

---

## Sección T5 — Aclaración T15
**Registrado**: 2026-11-23T23:58:00Z
Respuesta del usuario (verbatim): "t15 asumes correctamente"

### T15: Comunicación entre componentes
[Answer]: d — Mezcla, según la propuesta:

| Interacción | Tipo |
|---|---|
| Iniciar sesión, consultar y ver el resultado de un lote | Síncrona |
| Cargar el archivo a S3 y registrar el lote (devuelve número de lote) | Síncrona |
| Procesar las filas del lote (validar en Oracle, escribir en MySQL) | Asíncrona; el microfrontend consulta el estado del lote |

Pendientes (preguntas abiertas técnicas): mecanismo del procesamiento en segundo plano (SQS + worker en ECS, hilo en el mismo contenedor u otro) y tamaño máximo de un lote.

---

## Sección T5 — Aclaración tamaño de lote
**Registrado**: 2026-11-24T00:00:00Z
Respuesta del usuario (verbatim): "en promedio puede procesar maximo 1000 estudiantes"

[Answer]: Un lote puede tener hasta **1000 estudiantes** (máximo de referencia para dimensionar procesamiento asíncrono y pruebas de carga).
Nota: las plantillas vacías de `documentacion/plantillas-recibos/` tienen ~50 filas preparadas; el sistema nuevo no debe limitarse a ese número.
Sigue pendiente: mecanismo del procesamiento en segundo plano.

---

## ✅ Sección T5 completa — aprobada
**Registrado**: 2026-11-24T00:02:00Z
Aprobación del usuario: "aprobar"

---

## Sección T6 — Seguridad · T17–T21
**Registrado**: 2026-11-24T00:06:00Z
Respuesta del usuario (verbatim): "t17 ok, t18 ok confirmamos cifrado, t19 ok, t20 ok, t21 ok"

### T17: Autenticación
[Answer]: a — OAuth2/OIDC con WSO2 IS (`autenticacion.portaloas.udistrital.edu.co`).
- `recibos_mf`: login por el microcliente core; envía token Bearer.
- `recibos_service`: publicada en WSO2 AM; valida el token en `/oauth2/userinfo` con caché de 60 min; 401 si falta o no es válido (`utils_oas/auditoria`, modo enforcer).
- Autorización: rol único Admisiones, Registro y Control en `configuracion_cliente`, verificado en el backend en cada petición; nunca se confía en permisos enviados por el cliente.
- Bases de datos: usuarios técnicos de mínimo privilegio; Oracle solo lectura; MySQL solo tablas `solicitud*`.

### T18: Cifrado
[Answer]: a — Todo cifrado en reposo y en tránsito. HTTPS/TLS + HSTS; TLS hacia Oracle y MySQL; S3 con cifrado; SSM `SecureString`. **Confirmado por el usuario: las bases existentes están cifradas en reposo.**

### T19: Validación de entradas
[Answer]: c — Ambas.
- API: pydantic; errores con el sobre `{Success, Status, Message, Data}`.
- Archivo: solo `.xls`, tamaño máximo, verificación del tipo real, nombre interno generado por el sistema, encabezados y número de columnas (pregrado 13 sin Reingreso; posgrado 29).
- Filas: código numérico, fechas válidas con año completo, porcentajes 0–100, cuotas 1–3 en posgrado.
- Salida: escape por defecto de Angular; sin HTML armado a mano.

### T20: Secretos
[Answer]: a — AWS SSM Parameter Store (`SecureString`), rutas `/{parameterStore}/recibos_service/db/username|password` (y equivalente MySQL). `.env` local fuera del repo; secretos del pipeline en Drone; variables no secretas en Tuleap; ningún secreto en el repositorio.

### T21: Cumplimiento
[Answer]: x — Ley 1581 de 2012 + checklist de seguridad OAS (`qa/validación_seguridad.md`) + OWASP Top 10, ASVS y API Security Top 10.
Verificación cruzada T17–T20 vs T21: coherentes (mínimo privilegio, cifrado total, secretos fuera del código, logs sin datos personales).

---

## ✅ Sección T6 completa — aprobada
**Registrado**: 2026-11-24T00:08:00Z
Aprobación del usuario: "aprobar"

---

## Sección T7 — Pruebas · T22–T25
**Registrado**: 2026-11-24T00:12:00Z
Respuesta del usuario (verbatim): "t22 solo unitarias, t23 ok, t24 ok para las unitarias, t25 en drone"

### T22: Tipos de prueba exigidos
[Answer]: a — Solo unitarias (reglas de cuotas, exenciones, conceptos, fechas extraordinarias con festivos y validación de plantillas).
Posible contradicción con el rol de Negocio (para open-questions): Q9 indica pruebas de carga y de usuario en dev y revisión de Seguridad en test; Q10 exige 100% de equivalencia con el sistema actual; Q18.6 asigna la validación al Coordinador funcional con lotes de periodos anteriores. Interpretación pendiente de confirmar: "solo unitarias" = únicas pruebas automatizadas a cargo del equipo de desarrollo; las demás las ejecutan otros grupos según el proceso OAS.

### T23: Cobertura
[Answer]: ok — ≥80% en `recibos_service`; 100% en reglas de cálculo; gate SonarQube OAS: 0 bugs, 0 vulnerabilidades, ≤50% duplicación (L39).

### T24: Herramientas
[Answer]: ok para las unitarias.

| Tipo | Herramienta |
|---|---|
| Unitarias backend | pytest + pytest-cov |
| Unitarias frontend | La que trae `oas_cliente` (Jasmine/Karma o Jest; `*.spec.ts`) |

### T25: Controles antes de integrar / desplegar
[Answer]: x — Los controles se ejecutan en Drone: SonarQube (gate L39), pruebas unitarias y escaneo de dependencias.

---

## Sección T7 — Aclaración T22
**Registrado**: 2026-11-24T00:15:00Z
Respuesta del usuario (verbatim): "a no incluyas otras en el ciclo"

### T22 (aclaración)
[Answer]: a — El ciclo de desarrollo de este proyecto solo incluye **pruebas unitarias automatizadas**. Las pruebas de carga (líder de seguridad), funcionales y de usuario/equivalencia (Coordinador funcional de Admisiones, Registro y Control) y la revisión de Seguridad (equipo de Seguridad) las realizan otros grupos según el proceso OAS, **fuera del ciclo de desarrollo**. AI-DLC no debe planear ni generar esas otras pruebas.

## ✅ Sección T7 completa — aprobada
Aprobación: el usuario respondió la aclaración indicada como condición de cierre de la sección.

---

## Sección T8 — Patrones de código de ejemplo · T26–T29
**Registrado**: 2026-11-24T00:18:00Z
Respuesta del usuario (verbatim): "t26 ok, t27 ok, t28 ok, t29 ok"

### T26: Endpoint
[Answer]: b — `codigo-fuente/lineamientos_oas/api_flask/refactorizacion_api_flask.md` §3.3–3.5 (Blueprint + controlador) como estructura, sin el endpoint `/v1/` que expone variables de entorno (L8), con el sobre `{Success, Status, Message, Data}` (`utils_oas/requestresponse`).

### T27: Función / módulo
[Answer]: b — Contratos de `codigo-fuente/utils_oas/`: `customerrorv2/custom_errorv2.go`, `auditoria/auditoria.go`, `security/security_headers.go`, `database/oracle.go` + `ssm/ssm.go`; reimplementados en Python según `interview/technical/utils-oas-analysis.md`.

### T28: Prueba
[Answer]: c — Omitir; convenciones de pytest (`tests/test_*.py`, fixtures) y de `oas_cliente` para `*.spec.ts`. Pregunta abierta: no hay ejemplo de prueba Python de referencia (L10).

### T29: Infraestructura
[Answer]: b — `codigo-fuente/lineamientos_oas/generacion_de_apis/cicd/.drone.yml` (Sonar → build → ECR → ECS) adaptado a Python/Angular, y `generacion_de_apis/cicd/sonar-project.properties.md`. Infraestructura AWS gestionada por el grupo de infraestructura; sin CDK/Terraform en alcance.

---

## ✅ Sección T8 completa — aprobada
**Registrado**: 2026-11-24T00:20:00Z
Aprobación del usuario: "aprobar"

---

## Sección T9 — Sistema existente · TB1–TB4
**Registrado**: 2026-11-24T00:25:00Z
Respuesta del usuario (verbatim): "tb1 ok, tb2 ok, tb3 ok, tb4 ok usa clean arquitecture y restful"

### TB1: Inventario del stack existente
[Answer]: ok

| Lenguaje / framework | Uso actual | Dirección |
|---|---|---|
| PHP 5 + framework "weboffice" (bloques) | Módulo `registro_lote_recibo` y consultas | Retirar tras las pruebas en paralelo |
| php-excel-reader (`Spreadsheet_Excel_Reader`) | Lectura de `.xls` | Retirar → xlrd |
| HTML con tablas + `funciones.js` | Interfaz | Retirar → Angular / single-spa (`recibos_mf`) |
| Sesión en MySQL, niveles 4/110/114/132 | Autenticación y permisos | Retirar → WSO2 + rol único |
| Oracle académico (`mntac`) | Datos académicos y PL/SQL | Mantener (solo lectura) |
| MySQL (`solicitudRecibo`, `solicitudCuota`, `solicitudExencion`, `solicitudConcepto`, `solicitudLote`, `exencion`, `fechaPagoFacultad`) | Solicitudes y parámetros | Mantener |
| Módulo "Solicitados" | Generación e impresión de recibos | Mantener sin cambios |
| Carpeta local `documento/solicitudes/` | Archivos cargados | Retirar → S3 privado |

### TB2: Lo que no se toca
[Answer]: ok
- Oracle académico (`ACEST`, `ACCRA`, `ACASPERI`, `ACASPERIEVENTOS`, `ACCALEVENTOS`, `ACCERELECTORAL`, `ACRANGOSPAGO`, `V_ACESTMATBRUTO`, `ACESTMAT`, `ACVLRSCS`; funciones `fua_verifica_evento`, `mntac.fua_verifica_diferido`): solo lectura.
- Estructura de las tablas MySQL `solicitud*`, `exencion`, `fechaPagoFacultad` y los formatos que lee "Solicitados": fechas como timestamp Unix, porcentajes 0–100, `estado` (0 = sin imprimir, 2 = cancelada), IDs actuales de conceptos y exenciones.
- "Solicitados" y el sistema PHP durante las pruebas en paralelo.
- Registro en WSO2 y modelo de datos aprobado.

### TB3: Patrones prohibidos
[Answer]: ok (a)
- SQL por concatenación; permisos tomados de parámetros del cliente; lógica mezclada con HTML; reglas activadas comentando código; IDs fijos en el código; escrituras relacionadas sin transacción; archivos `0777` en disco local; configuración global con credenciales; parámetros cifrados en la URL como seguridad; lógica duplicada (`action.php` vs `funcion.class.php`).
- Excepción: los formatos de datos de las tablas existentes se mantienen (TB2).

### TB4: Origen de los ejemplos
[Answer]: a — Archivos reales de `codigo-fuente/lineamientos_oas/` y `codigo-fuente/utils_oas/` (T26, T27, T29); `codigo-fuente/weboffice/` solo como referencia de reglas de negocio.
Indicación adicional del usuario: **usar Clean Architecture y RESTful.**
- RESTful: ya definido en T13.
- Clean Architecture: modifica T16 (capas). Propuesta de mapeo presentada para aprobación (ver tech-env-questions / chat).

---

## Sección T9 — Cambio aprobado · T16 (Clean Architecture)
**Registrado**: 2026-11-24T00:30:00Z
Respuesta del usuario (verbatim): "aprobar" / "continua"

### T16 (actualizada)
[Answer]: Repositorios `recibos_service` (backend) y `recibos_mf` (frontend), con **Clean Architecture** y API **RESTful**:

`recibos_service`:
- Raíz (lineamiento OAS): `api.py`, `conf/`, `swagger/`, `Dockerfile`, `docker-compose.yml`, `sonar-project.properties`, `README.md`, `requirements.txt`.
- `app/domain/`: entidades (Lote, Solicitud, Cuota, Exención, Concepto) y reglas de cálculo; Python puro, sin Flask ni BD; 100% de cobertura.
- `app/application/`: casos de uso (cargar lote, procesar lote, consultar lote) y puertos (repositorios, lector de plantilla, almacenamiento).
- `app/infrastructure/`: adaptadores Oracle (python-oracledb), MySQL (SQLAlchemy), S3, SSM, lector xlrd, cliente userinfo WSO2.
- `app/interfaces/`: `routers/` y `controllers/` (Blueprints), esquemas pydantic, sobre `{Success, Status, Message, Data}`, middlewares de seguridad y auditoría.
- Regla: las dependencias apuntan hacia adentro.

`recibos_mf`: estructura de `oas_cliente` con `core/`, `shared/`, `features/lotes/`; componentes de presentación; acceso a la API en servicios.

## ✅ Sección T9 completa — aprobada
Entrevista Técnica completa (33/33).

---

## Corrección por consolidación final (C-1..C-6)
**Registrado**: 2026-11-24T00:55:00Z
Respuesta del usuario (verbatim): "para c1 consultara y actualizara a un servicio externo de nopmbre parametros, la sintaxis se explicara despues por ahora debe quedar indicado, c2 dejalo sincrono, c3 debe tomar 13, las pruebas se evaluan independientes, c4 sera posterior, c5 en este caso no importa, c6 el desarrollo es guiado por ia por lo que no aplica el alcance, b"

- T15 (corrige): **todo síncrono**; el lote (hasta 1000 estudiantes) se procesa en la misma petición. Se cierra la pregunta del mecanismo asíncrono.
- T11 / T15 (agrega): integración REST síncrona con el **servicio externo "parametros"** para consultar y actualizar reglas parametrizadas; contrato por definir (OQ-T-11).
- T19 (precisa): pregrado solo 13 columnas; el formato de 14 se rechaza. Pruebas de cada sistema independientes.
- T16 (precisa): nombres `recibos_service` / `recibos_mf` aceptados.
- Equivalencia: herramienta de comparación en etapa posterior.
- Plazo vs alcance: no aplica (desarrollo guiado por IA).
- Visual sketch: **b — no**.

---
