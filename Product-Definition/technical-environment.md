# Documento de Entorno Técnico — Migración del módulo de recibos por lote (weboffice)

Generado por aidlc-discovery el 2026-11-24T00:35:00Z.
Tipo de proyecto: Brownfield (migración / modernización)

Fuentes de contexto: `vision-document.md`, `interview/technical/tech-env-answers-history.md`, `interview/technical/existing-system-analysis.md`, `interview/technical/institutional-guidelines-analysis.md` (hallazgos L#), `interview/technical/utils-oas-analysis.md`, `interview/technical/templates-analysis.md`.

Este documento registra **restricciones** (qué se exige, permite y prohíbe). No es un diseño de la solución.

---

## Resumen técnico del proyecto

- Nombre del proyecto: Migración del módulo de recibos por lote (weboffice)
- Tipo de proyecto: Brownfield
- Entorno de ejecución principal: Solo nube (aplicaciones y bases de datos en AWS)
- Proveedor de nube: AWS
- Modelo de despliegue: Contenedores Docker en AWS ECS (clusters `test` y `oas`)
- Equipo: 6 personas — 3 desarrolladores, 1 infraestructura, 1 base de datos, 1 seguridad. Experiencia por tecnología no especificada.
- Fecha límite: 15/12/2026, desplegado en el ambiente de pruebas (test) para iniciar la revisión de Seguridad (Visión, Q9).

---

## Lenguajes de programación

### Lenguajes obligatorios

| Lenguaje | Versión | Propósito | Justificación |
|----------|---------|---------|-----------|
| Python | 3.12 | Backend (`recibos_service`) | Decisión de negocio; lineamiento Flask de la OAS (L5); 3.8 citado en los lineamientos ya no tiene soporte (L9) |
| TypeScript | 5.x (la que exija la versión de Angular) | Frontend (`recibos_mf`), microcliente single-spa | Decisión de negocio; lineamientos de clientes (L14) |
| SQL | Dialectos Oracle y MySQL | Consultas a Oracle académico (solo lectura) y a las tablas `solicitud*` | Se mantienen las bases actuales |

Versiones de Angular y Node: pendientes (OQ-T-1).

### Lenguajes permitidos

Ninguno; solo se permiten los lenguajes obligatorios. Los archivos de soporte que exige la plataforma (Dockerfile, `.drone.yml`, `entrypoint.sh` si aplica) no se consideran lenguaje de aplicación.

### Lenguajes prohibidos

| Lenguaje | Motivo |
|----------|--------|
| PHP | Es lo que se reemplaza; objetivo de retirar PHP 5 |

### Inventario del stack existente

| Lenguaje / framework | Uso actual | Dirección |
|----------------------|---------------|-----------|
| PHP 5 + framework propio "weboffice" (bloques) | Módulo `registro_lote_recibo` y consultas | Retirar tras las pruebas en paralelo |
| php-excel-reader (`Spreadsheet_Excel_Reader`) | Lectura de plantillas `.xls` | Retirar → xlrd |
| HTML con tablas + `funciones.js` | Interfaz del módulo | Retirar → Angular / single-spa (`recibos_mf`) |
| Sesión del framework en MySQL, niveles 4/110/114/132 | Autenticación y permisos | Retirar → WSO2 + rol único |
| Oracle académico (esquema `mntac`) | Datos académicos y funciones PL/SQL | Mantener (solo lectura) |
| MySQL (`solicitudRecibo`, `solicitudCuota`, `solicitudExencion`, `solicitudConcepto`, `solicitudLote`, `exencion`, `fechaPagoFacultad`) | Solicitudes y parámetros | Mantener |
| Módulo "Solicitados" (fuera del repositorio) | Generación e impresión de recibos | Mantener sin cambios |
| Carpeta local `documento/solicitudes/` | Archivos cargados | Retirar → S3 privado |

---

## Frameworks y librerías

### Frameworks obligatorios

| Framework | Dominio | Justificación |
|-----------|--------|-----------|
| Flask (con Blueprints) | API backend | Único lineamiento Python de la OAS (L5) |
| gunicorn | Servidor de aplicación en el contenedor | Lineamiento Flask (L6) |
| flasgger (Swagger/OpenAPI) | Documentación de la API | Swagger exigido para desplegar en dev, test y prod (L6, L41) |
| Angular + single-spa-angular | Frontend (microcliente) | Arquitectura de microclientes OAS (L2); plantilla `oas_cliente` (L14) |
| Angular Material | Componentes de interfaz | Tema institucional (L17) |

### Librerías preferidas

| Librería | Condiciones de uso |
|-----------|--------------------|
| python-oracledb (modo thin) | Conexión de solo lectura a Oracle académico |
| PyMySQL o mysqlclient | Conexión a MySQL; elección final en diseño |
| SQLAlchemy 2.x (Core) | Consultas parametrizadas y transacciones (cada solicitud se guarda completa o no se guarda) |
| xlrd 2.x | Lectura de las plantillas `.xls` |
| pydantic | Validación de filas de plantilla y de entradas de la API |
| python-dotenv | Variables de entorno en desarrollo local (L7) |
| pytest (+ pytest-cov) | Pruebas unitarias del backend |
| boto3 | Lectura de credenciales en SSM Parameter Store (equivale a `utils_oas/ssm`, `utils_oas/database`) |
| aws-xray-sdk | Trazas X-Ray (equivale a `utils_oas/xray`) |
| httpx o requests | Validación del token en `/oauth2/userinfo` (equivale a `utils_oas/auditoria`) |
| cachetools | Caché de 60 min del usuario por token (equivale a `utils_oas/auditoria`) |

`utils_oas` es Go/Beego y **no se importa**. Sus contratos se reimplementan en un módulo Python del proyecto (ver "Ejemplos de código" y `utils-oas-analysis.md`).

### Librerías y prácticas prohibidas

| Prohibido | Motivo | Usar en su lugar |
|------------|--------|-------------|
| `cx_Oracle` | Reemplazado por su sucesor | `python-oracledb` |
| SQL armado concatenando texto o con f-strings | Inyección SQL; bloqueante en la revisión de Seguridad (L38) | Parámetros enlazados (SQLAlchemy / driver) |
| Servidor de desarrollo de Flask o `DEBUG=True` fuera de local | Expone información; el ejemplo del lineamiento lo trae por defecto (L8) | gunicorn con `DEBUG=False` |
| Devolver variables de entorno o credenciales en un endpoint | El ejemplo `/v1/` del lineamiento lo hace (L8); bloqueante (L38) | `GET /` y `/health` que solo devuelven estado |
| `localStorage` / cookies sin protección para tokens o datos personales | Robo de sesión; Ley 1581 (L18) | Sesión manejada por el microcliente core con WSO2 |
| pandas para leer plantillas | Dependencia pesada innecesaria | xlrd |

### Patrones prohibidos (específicos del sistema actual)

- SQL armado por concatenación (`codigo-fuente/weboffice/bloque/registro_lote_recibo/sql.class.php`).
- Permisos o roles tomados de parámetros del cliente (`$_REQUEST['tipoUser']`).
- Lógica de negocio mezclada con HTML (`echo` en `funcion.class.php`).
- Reglas que se activan o desactivan comentando código (cuotas "COVID", "2020-1").
- IDs de conceptos, exenciones, eventos y estados fijos en el código; deben ir en parámetros.
- Varias escrituras relacionadas sin transacción.
- Archivos con permisos `0777` en disco local.
- Configuración global con credenciales (`$configuracion`).
- Parámetros cifrados en la URL como mecanismo de seguridad (`encriptar::codificar_url`).
- Lógica duplicada (`action.php` frente a `funcion.class.php`).

Excepción: los **formatos de datos** de las tablas existentes (timestamp Unix, porcentaje 0–100, códigos de `estado`) se mantienen porque los lee "Solicitados".

---

## Servicios en la nube

### Lista permitida

| Servicio | Condiciones / notas |
|---------|---------------------|
| ECS (clusters `test` y `oas`) | Contenedores del backend y del microcliente (L43) |
| ECR | Imágenes Docker publicadas por Drone (L43) |
| SSM Parameter Store | Credenciales de BD y parámetros, como `SecureString` |
| X-Ray | Trazas; dirección del daemon en SSM |
| CloudWatch Logs | Logs de auditoría JSON (por confirmar, OQ-T-5) |
| S3 | Plantillas cargadas: bucket privado, cifrado, sin acceso público, retención definida (OQ-T-10) |
| Oracle y MySQL existentes en AWS | Solo los existentes; Oracle en solo lectura |
| Servicio externo "parametros" (institucional) | Consulta y actualización de reglas parametrizadas; contrato por definir (OQ-T-11) |
| WSO2 IS/AM institucional | Autenticación y publicación de la API (L19) |

### Lista prohibida

| Servicio | Motivo |
|---------|--------|
| Buckets S3 públicos o URLs públicas permanentes | Datos personales de estudiantes (Ley 1581) |
| Bases de datos nuevas (RDS, DynamoDB u otras) | Se mantienen las bases actuales |
| Lambda / serverless | Se eligió contenedores en ECS |
| Credenciales en texto plano en variables de la tarea ECS | Deben venir de SSM; bloqueante si se exponen (L38) |

---

## Arquitectura y patrones

### Estilo de API

REST documentada con OpenAPI/Swagger (flasgger). Versión en la ruta (`/v1`); recursos en español, en plural, en minúsculas y kebab-case, sin tildes ni ñ y sin verbos CRUD en la URI; códigos HTTP correctos y respuestas vacías con 2xx (L30–L34, `lineamientos_oas/generacion_de_apis/lineamientos-endpoints.md`). Todas las respuestas y errores usan el sobre `{"Success", "Status", "Message", "Data"}` (`utils_oas/requestresponse/responses_format.go`, `utils_oas/customerrorv2/custom_errorv2.go`). Versionado SemVer: primera versión en producción `0.1.0` (L32). La API se publica en WSO2 AM.

### Patrones de datos

Relacional, usando **solo las bases existentes**:
- **Oracle académico** (solo lectura): estado y carrera del estudiante, periodo, eventos de calendario, certificado electoral, valor de matrícula (`ACEST`, `ACCRA`, `ACASPERI`, `ACASPERIEVENTOS`, `ACCALEVENTOS`, `ACCERELECTORAL`, `ACRANGOSPAGO`, `V_ACESTMATBRUTO`; funciones `fua_verifica_evento`, `mntac.fua_verifica_diferido`).
- **MySQL** (lectura y escritura con transacciones): `solicitudRecibo`, `solicitudCuota`, `solicitudExencion`, `solicitudConcepto`, `solicitudLote`; parámetros en `exencion` y `fechaPagoFacultad`.
- **S3**: archivo de cada plantilla cargada.
- Sin caché distribuida; solo caché en memoria del usuario por token.

Los lineamientos de modelo de datos de la OAS (PostgreSQL, convenciones de nombres; L22–L29) **no aplican**: según el negocio, los lineamientos aplican al código, no a las bases.

### Mensajería / integración

**Todo síncrono** (decisión C-2 de la consolidación final, reemplaza la mezcla de T15): la carga del archivo a S3, el procesamiento de las filas (validar en Oracle, consultar reglas en "parametros", escribir en MySQL) y la respuesta con el resumen de procesados y rechazados ocurren en la misma petición. No se usan colas ni workers.

Tamaño máximo de referencia: **1000 estudiantes por lote**. Restricción derivada: los tiempos de espera de gunicorn, del balanceador y de WSO2 AM deben permitir procesar un lote de 1000 estudiantes en una sola petición.

**Servicio externo "parametros"** (decisión C-1): las reglas parametrizadas (conceptos, exenciones, fechas de pago por facultad, porcentajes por defecto, estados permitidos, eventos de calendario, plazo de la fecha extraordinaria, mapa columna → exención) se **consultan y actualizan** en un servicio externo llamado "parametros", por HTTP REST síncrono. Su contrato (endpoints, autenticación, formato) se definirá después (OQ-T-11). Para consumirlo se aplica el contrato de cliente de `utils_oas/request` (extracción del campo `Data` del sobre institucional).

### Estructura del proyecto

Dos repositorios, con **Clean Architecture** y API **RESTful**; GitFlow; commits `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `devops:`, `management:`; README con contenido mínimo; `Dockerfile`, `docker-compose.yml` y `sonar-project.properties` en la raíz (L45–L48). Los nombres no siguen `<negocio>_cliente|mid|crud` (L3); aceptados para este proyecto (C-5).

**`recibos_service`** (backend):
- Raíz (lineamiento OAS): `api.py`, `conf/`, `swagger/`, `Dockerfile`, `docker-compose.yml`, `sonar-project.properties`, `README.md`, `requirements.txt`.
- `app/domain/`: entidades (Lote, Solicitud, Cuota, Exención, Concepto) y reglas de cálculo. Python puro, sin Flask ni base de datos.
- `app/application/`: casos de uso (cargar lote, procesar lote, consultar lote) y puertos (repositorios, lector de plantilla, almacenamiento).
- `app/infrastructure/`: adaptadores Oracle (python-oracledb), MySQL (SQLAlchemy), S3, SSM, lector xlrd, cliente userinfo de WSO2 y cliente del servicio "parametros".
- `app/interfaces/`: `routers/` y `controllers/` (Blueprints), esquemas pydantic, sobre de respuesta y middlewares de seguridad y auditoría.
- Las dependencias apuntan hacia adentro (`domain` no conoce Flask ni las bases).
- No se crea un repositorio CRUD separado.

**`recibos_mf`** (frontend): a partir de `oas_cliente` (rama `feature/clientes_nuevos`), con `core/`, `shared/` y `features/lotes/`; componentes de presentación; acceso a la API en servicios.

---

## Seguridad

### Autenticación

OAuth2/OIDC con **WSO2 IS** (`autenticacion.portaloas.udistrital.edu.co`).
- `recibos_mf`: inicio de sesión a través del microcliente core; envía el token Bearer en cada llamada.
- `recibos_service`: publicada en **WSO2 AM**; valida el token contra `/oauth2/userinfo` con caché de 60 minutos y responde **401** si falta o no es válido (contrato de `utils_oas/auditoria/auditoria.go`, modo "enforcer").
- Autorización: rol único **Admisiones, Registro y Control**, registrado en `configuracion_cliente`; verificado en el backend en cada petición. Nunca se confía en permisos enviados por el cliente.
- Bases de datos: usuarios técnicos de mínimo privilegio; Oracle solo lectura; MySQL solo sobre las tablas necesarias.

### Cifrado

Todo cifrado en tránsito y en reposo: HTTPS/TLS en todo el tráfico con HSTS; TLS hacia Oracle y MySQL; S3 con cifrado del lado del servidor; parámetros SSM como `SecureString`. Confirmado por el usuario: las bases existentes están cifradas en reposo.

Cabeceras obligatorias en todas las respuestas del backend (contrato de `utils_oas/security/security_headers.go`): `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`, `Cross-Origin-Resource-Policy: cross-origin`, `Permissions-Policy: geolocation=(), microphone=(), camera=()`, `Referrer-Policy: no-referrer`, `Server` vacío, `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`, `X-XSS-Protection: 1; mode=block`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-Permitted-Cross-Domain-Policies: none`. CORS restringido a `*.udistrital.edu.co` fuera de dev (L13).

### Validación de entradas

En la frontera de la API y en la capa de aplicación:
- API: pydantic para parámetros y cuerpos; errores con el sobre institucional.
- Archivo: solo `.xls`; tamaño máximo (valor en OQ-T-10); verificación del tipo real del archivo; nombre interno generado por el sistema; encabezados y número de columnas según `templates-analysis.md` (pregrado **solo 13** columnas, sin "Reingreso" — el formato de 14 se rechaza, decisión C-3; posgrado **29**).
- Filas: código de estudiante numérico; fechas válidas con año completo; porcentajes 0–100; cuotas 1–3 en posgrado.
- Salida: escape por defecto de Angular; sin HTML armado a mano.

### Gestión de secretos

AWS **SSM Parameter Store** (`SecureString`), con la convención de `utils_oas/database/oracle.go`: `/{parameterStore}/recibos_service/db/username` y `/password` (ruta de MySQL por definir, OQ-T-7). En local, archivo `.env` fuera del repositorio. Secretos del pipeline en Drone (`from_secret`). Variables no secretas en Tuleap (L44). Prohibido cualquier secreto, llave o certificado en el repositorio (L35).

### Cumplimiento

- **Ley 1581 de 2012** (protección de datos personales).
- **Checklist de seguridad OAS** previo al despliegue (`lineamientos_oas/qa/validación_seguridad.md`).
- Referencia: **OWASP Top 10, ASVS y API Security Top 10**.

Secciones de este documento derivadas de ese marco: mínimo privilegio (Autenticación), cifrado total y cabeceras (Cifrado), validación de archivo y filas (Validación), secretos fuera del código (Secretos), S3 privado con retención y prohibición de `localStorage` para datos personales (Servicios, Librerías prohibidas).

**Auditoría:** log JSON por petición con los campos de `utils_oas/auditoria`: `app_name, agent, data, date, host, ip_user, method, path, query, schema, sql_statement, status, trace_id, user`. Mejoras obligatorias frente al original: `sql_statement` capturado **por petición**, y `data` **sin datos personales** (Ley 1581). Health check `GET /` → `{"status": "ok"}` (`utils_oas/apiStatusLib`) además de `/health`.

Pendientes: destino y retención de logs (OQ-T-5), tamaño máximo y retención de archivos (OQ-T-10).

### Lo que no debe cambiar

- Oracle académico: esquema, datos, tablas listadas arriba y funciones PL/SQL; solo lectura.
- Estructura de las tablas MySQL `solicitud*`, `exencion` y `fechaPagoFacultad`, incluidos los formatos que lee "Solicitados": fechas como timestamp Unix, porcentajes 0–100, `estado` (0 = sin imprimir, 2 = cancelada; demás en OQ-B-4) e IDs actuales de conceptos y exenciones.
- Módulo "Solicitados" y sistema PHP durante las pruebas en paralelo.
- Registro existente en WSO2 y modelo de datos aprobado (ubicación en OQ-T-9).
- Reglas de cálculo vigentes, salvo los tres cambios acordados en la Visión (sin reingreso, sin diferido en pregrado, sin leer "Seguro" como cuota).

---

## Pruebas

### Tipos de prueba

El ciclo de desarrollo incluye **solo pruebas unitarias automatizadas**: reglas de cuotas, exenciones, conceptos, fechas extraordinarias con festivos y validación de plantillas.

Las pruebas de carga (líder de seguridad), funcionales, de usuario y de equivalencia (Coordinador funcional de Admisiones, Registro y Control) y la revisión de Seguridad (equipo de Seguridad) las realizan otros grupos según el proceso OAS, **fuera del ciclo de desarrollo**. AI-DLC no debe planear ni generar esas pruebas.

### Metas de cobertura

- ≥80% en `recibos_service`.
- 100% en las reglas de cálculo (`app/domain/`).
- Gate de SonarQube OAS: 0 bugs, 0 vulnerabilidades, máximo 50% de duplicación (L39).

### Herramientas

| Tipo de prueba | Herramienta |
|-----------|------|
| Unitarias backend | pytest + pytest-cov |
| Unitarias frontend | La que trae `oas_cliente` (Jasmine/Karma o Jest; archivos `*.spec.ts`) |

### Controles de CI/CD

En Drone: SonarQube (gate L39), pruebas unitarias y escaneo de dependencias.

---

## Ejemplos de código

AI-DLC debe **cargar los archivos indicados** como plantilla de estructura y contratos, aplicando las correcciones señaladas. No hay fragmentos pegados.

### Endpoint

Referencia: `codigo-fuente/lineamientos_oas/api_flask/refactorizacion_api_flask.md` §3.3–3.5 (Blueprint en `routers/router.py` + función en `controllers/`). Correcciones: **no** incluir el endpoint `/v1/` que devuelve variables de entorno (§3.1); `DEBUG=False` fuera de local; responder con el sobre `{Success, Status, Message, Data}`.

### Función / módulo

Referencias (contratos a reimplementar en Python, ver `interview/technical/utils-oas-analysis.md`):
- Errores y respuestas: `codigo-fuente/utils_oas/customerrorv2/custom_errorv2.go`, `codigo-fuente/utils_oas/requestresponse/responses_format.go`.
- Token y log de auditoría: `codigo-fuente/utils_oas/auditoria/auditoria.go`.
- Cabeceras: `codigo-fuente/utils_oas/security/security_headers.go`.
- Credenciales: `codigo-fuente/utils_oas/database/oracle.go`, `codigo-fuente/utils_oas/ssm/ssm.go`.
- Health check: `codigo-fuente/utils_oas/apiStatusLib/apistatus.go`.

### Prueba

No hay ejemplo de referencia (OQ-T-4). Usar convenciones de pytest (`tests/test_*.py`, fixtures) y las de `oas_cliente` para `*.spec.ts`.

### Infraestructura

Referencias: `codigo-fuente/lineamientos_oas/generacion_de_apis/cicd/.drone.yml` (SonarQube → build → ECR → ECS `test`/`oas`), adaptado de Go a Python y Angular; `codigo-fuente/lineamientos_oas/generacion_de_apis/cicd/sonar-project.properties.md` (plantillas Python y Angular). La infraestructura AWS (ECS, S3, SSM) la gestiona el grupo de infraestructura; no hay CDK ni Terraform en el alcance.

### Origen de los ejemplos

Archivos reales del workspace (`codigo-fuente/lineamientos_oas/`, `codigo-fuente/utils_oas/`). El código PHP de `codigo-fuente/weboffice/` es **referencia de reglas de negocio**, no de estilo. Las plantillas oficiales están en `documentacion/plantillas-recibos/`.

---

## Decisiones de la consolidación final (2026-11-24)

- C-1: reglas parametrizadas en el servicio externo "parametros" (ver Mensajería / integración).
- C-2: procesamiento síncrono; cerrada OQ-T-3.
- C-3: solo plantilla de pregrado de 13 columnas; pruebas de cada sistema independientes.
- C-4: herramienta de comparación de equivalencia en etapa posterior (fuera del ciclo de desarrollo).
- C-5: nombres `recibos_service` / `recibos_mf` aceptados; cerrada OQ-T-6.
- C-6: desarrollo guiado por IA; riesgo de alcance no aplica.

## Preguntas abiertas (Técnicas)

Detalle completo en `open-questions.md`.

| ID | Tema |
|---|---|
| OQ-T-1 | Versiones de Angular y Node |
| OQ-T-2 | ¿Existe una versión Python de `utils_oas`? |
| OQ-T-4 | Ejemplo de prueba Python |
| OQ-T-5 | Destino y retención de los logs de auditoría |
| OQ-T-7 | Convención SSM para credenciales de MySQL |
| OQ-T-8 | Núcleo del framework y fuentes de datos implícitas (festivos, fechas de pago, periodo) |
| OQ-T-9 | Modelo de datos aprobado y esquema MySQL real |
| OQ-T-10 | Tamaño máximo del archivo y retención en S3 |
| OQ-T-11 | Contrato del servicio externo "parametros" |

Cerradas: OQ-T-3 (síncrono, C-2), OQ-T-6 (nombres aceptados, C-5).
