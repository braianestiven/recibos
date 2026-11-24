# Lineamientos institucionales OAS/OATI vs. sistema actual (contexto para la entrevista técnica)

- Fecha: 2026-11-23T21:45:00Z
- Fuente: `codigo-fuente/lineamientos_oas/` (clon local, rama `master`, último commit `ee307b6 feat: Lineamientos de validaciones de seguridad previo al despliegue`)
- Contrastado con: `codigo-fuente/weboffice/` y `interview/technical/existing-system-analysis.md`
- Alcance: solo lectura de archivos `.md`, `.yml` y `.sql`. No se abrieron imágenes, `.pptx`, `.pdf` ni `.xls/.xlsx`. No se modificó ni ejecutó nada.
- Los enlaces externos (por ejemplo `udistrital/arquitectura_docs`, `udistrital/seguridad_calidad_oas`, `oas_cliente`, `utils_oas`) **no se leyeron** porque no están en el workspace.
- Uso: este archivo alimenta las respuestas sugeridas de la entrevista técnica y la sección de restricciones de `technical-environment.md`. No es un entregable final.

Notación: **REQ** = requisito explícito del lineamiento · **REC** = recomendación · **VACÍO** = el lineamiento no cubre el caso · **⚠** = contradicción o práctica insegura dentro del propio lineamiento.

---

## 1. Arquitectura

| ID | Hallazgo | Tipo | Fuente |
|---|---|---|---|
| L1 | La arquitectura definida para los sistemas nuevos es de **microservicios**: APIs **CRUD** (acceso a datos por entidad) + APIs **MID** (lógica de negocio que orquesta CRUDs). | REQ | `README.md` §3 y §5 |
| L2 | El frontend sigue la arquitectura de **microclientes (microfrontends) con single-spa**: una app *root*, un *core* que maneja autenticación, autorización y rutas, y *parcels* por funcionalidad. Angular es compatible. Se desaconseja mezclar frameworks en la misma página. | REQ | `README.md` §3; `single_spa/single_spa.md`; `single_spa/core.md`; `single_spa/root_config.md`; `single_spa/parcel.md` |
| L3 | Los repositorios se nombran `<negocio>_<contexto>`, con contexto `cliente`, `mid` o `crud`, en minúsculas. Ejemplo: `admisiones_crud`, `admisiones_mid`, `admisiones_cliente`. | REQ | `repositorios_institucionales/nombre_repos.md` |
| L4 | Las reglas de negocio deberían ir en un componente "RULE", pero el lineamiento está marcado como "(Falta)". | VACÍO | `README.md` §5 "Generación Reglas de Negocio (RULE)" |

**Contraste con weboffice:** hoy es un monolito PHP con renderizado en el servidor, lógica, SQL y HTML mezclados en `funcion.class.php` (`codigo-fuente/weboffice/bloque/registro_lote_recibo/funcion.class.php`). La migración implica separar al menos tres piezas: cliente Angular, MID (validación de plantilla y reglas de cuotas, exenciones y conceptos) y CRUD de solicitudes.

## 2. Backend Python

| ID | Hallazgo | Tipo | Fuente |
|---|---|---|---|
| L5 | El lineamiento institucional para Python es **Flask** con estructura `api.py`, `conf/`, `controllers/` (incluye `error.py` y `healthCheck.py`), `models/`, `routers/` (Blueprints), `swagger/`, `Dockerfile`, `entrypoint.sh`, `requirements.txt`, `sonar-project.properties`. | REQ | `api_flask/api_flask.md`; `api_flask/estructura.md` |
| L6 | Servidor de aplicación **gunicorn**; documentación con **flasgger/Swagger** en `/apidocs`; health check en `/health`; ruta base `/v1`. | REQ | `api_flask/api_flask.md`; `api_flask/refactorizacion_api_flask.md`; `api_flask/variables_entorno.md` |
| L7 | Configuración por variables de entorno (`python-dotenv`, `conf/conf.py`). | REQ | `api_flask/refactorizacion_api_flask.md` §3.2 |
| L8 ⚠ | El ejemplo de `api.py` **devuelve credenciales** (`NUXEO_PASSWORD`, `NUXEO_USERNAME`) en el endpoint `/v1/`, y `DEBUG` queda en `True` por defecto. **No se debe replicar**, porque contradice `qa/validación_seguridad.md` (exposición de secretos = bloqueante). | ⚠ | `api_flask/refactorizacion_api_flask.md` §3.1–3.2; `api_flask/variables_entorno.md` |
| L9 ⚠ | Las versiones de Python no son consistentes: un Dockerfile tiene dos `FROM` (`python:3.10-slim` y `python:3.8`) y otro usa `python:3.8`, que ya no tiene soporte. | ⚠ | `api_flask/api_flask.md` §4; `api_flask/refactorizacion_api_flask.md` §3.6 |
| L10 | No hay lineamiento de **pruebas unitarias para Python**. Solo existe para Beego/Go. | VACÍO | `README.md` §5.1; `pruebas_unitarias_api_beego/*.md` |
| L11 | El formato estándar de respuestas JSON y el control de errores están definidos solo para Beego (`utils_oas/customerrorv2`). Hay que acordar el equivalente en Flask para que sea compatible con WSO2. | VACÍO | `generacion_de_apis/control_error_json_crud.md`; `generacion_de_apis/control_error_json_mid.md` |
| L12 | Las cabeceras de seguridad, el middleware de auditoría y la trazabilidad (X-Ray) están definidos solo en Go (`security.SetSecurityHeaders()`, `auditoria.InitMiddleware()`, `xray.Init()`). No hay equivalente documentado para Flask. | VACÍO | `generacion_de_apis/configuracion_ci_cd.md` §main.go; `generacion_de_apis/AWS_XRay.md` |
| L13 | En producción, CORS se restringe a `*.udistrital.edu.co`; `*` solo en modo dev. | REQ | `generacion_de_apis/configuracion_ci_cd.md` §main.go |

**Contraste con weboffice:** hoy no hay API. Todo se hace por formularios POST a `index.php` con parámetros cifrados (`bloque.php`, `nuevoRegistro()` en `funcion.class.php`). Tampoco hay health check, Swagger ni configuración por entorno: `$configuracion` es un arreglo global.

## 3. Frontend Angular

| ID | Hallazgo | Tipo | Fuente |
|---|---|---|---|
| L14 | Los clientes nuevos parten del cliente base `oas_cliente` (rama `feature/clientes_nuevos`). Se ajustan `appMenu`, `appname` y los estilos del repositorio `assets`. | REQ | `clientes_nuevos/clientes_nuevos.md` pasos 1–9 |
| L15 | La aplicación, sus **roles y opciones de menú** se registran en **configuracion_cliente** (portal OAS). | REQ | `clientes_nuevos/clientes_nuevos.md` paso 10 |
| L16 ⚠ | Se recomienda **Node 16**, que ya no tiene soporte, e instalar con `--legacy-peer-deps`. No se fija una versión de Angular. | ⚠ | `clientes_nuevos/clientes_nuevos.md` paso 11 |
| L17 | Se usa Angular Material con un tema basado en variables CSS heredadas del root. | REC | `single_spa/core.md` §Estilos |
| L18 ⚠ | Para compartir datos entre microclientes se sugiere `localStorage` o cookies sin advertencias de seguridad. No debe usarse para tokens ni datos personales (Ley 1581). | ⚠ | `single_spa/shared.md` |

**Contraste con weboffice:** HTML con tablas y `funciones.js` (`html.php`, `funcion.class.php::nuevoRegistro`). Los mensajes al usuario se arman con `echo` y entidades HTML.

## 4. Autenticación y autorización

| ID | Hallazgo | Tipo | Fuente |
|---|---|---|---|
| L19 | Las APIs y los clientes se registran en **WSO2**: el cliente en **WSO2 IS**, la aplicación en **WSO2 AM** y las APIs se asocian a esa aplicación. El `client_id` se configura en el cliente. | REQ | `despliegues/lineamientos.md` (pasos 6–7 en dev, test y prod) |
| L20 | Las pruebas requieren access tokens de WSO2 y usuarios por rol. | REQ | `qa/requerimiento_pruebas.md` |
| L21 | El microcliente *core* maneja autenticación y autorización. | REQ | `single_spa/core.md` §Características |

**Contraste con weboffice:** la sesión está en la base MySQL del framework (`rescatarValorSesion` en `codigo-fuente/weboffice/clase/funcionGeneral.class.php`). La autorización usa niveles 4/110/114/132 con una cuenta Oracle por nivel (`funcion.class.php::__construct`). `tipoUser` llega desde `$_REQUEST` (`admin_consultasCoordinador/funcion.class.php` línea 44). El negocio decidió un solo rol, Admisiones, Registro y Control (Q8), que se registrará en configuracion_cliente y WSO2.

## 5. Modelo de datos

| ID | Hallazgo | Tipo | Fuente |
|---|---|---|---|
| L22 | Las bases nuevas son **PostgreSQL**, con 4 bases: `academica`, `administrativa`, `core`, `financiera`. Los esquemas se nombran **por funcionalidad, no por aplicación**. | REQ | `modelo_de_datos/lineamientos_modelos_relacionales.md` §Bases de Datos y Esquemas |
| L23 | Tablas y columnas en singular con `_`. PK `id serial`. FK `<tabla>_id`. Restricciones `pk_`, `fk_`, `uq_`, `ck_`, `idx_`. | REQ | ídem §Tablas, §Columnas, §Claves |
| L24 | Columnas obligatorias: `activo boolean DEFAULT TRUE`, `fecha_creacion timestamp`, `fecha_modificacion timestamp`. | REQ | ídem §Columnas |
| L25 | Moneda en `numeric(20,7)`; porcentaje en `numeric(5,4)`. | REQ | ídem §Columnas |
| L26 | Las tablas paramétricas usan `id, nombre, descripcion, codigo_abreviacion, numero_orden`. | REQ | ídem §Tablas tipo catálogo o paramétricas |
| L27 | **No hay DELETE físico**, solo borrado lógico (inactivar el registro) por auditoría y trazabilidad. | REQ | `README.md` §5 punto 2 |
| L28 | El modelo relacional debe ser **aprobado por el comité de la oficina** (DBeaver). En producción, la base la crea el **grupo de DBA**. | REQ | `metodologias/lineamientos.md` fase 1.3; `despliegues/lineamientos.md` (prod pasos 9–10) |
| L29 | No hay lineamientos sobre **Oracle**, ni sobre integración con el sistema académico existente, ni sobre convivencia con MySQL. | VACÍO | (ausencia en todo `lineamientos_oas/`) |

**Contraste con weboffice** (tablas en `registro_lote_recibo/sql.class.php`):
- `solicitudRecibo`, `solicitudCuota`, `solicitudExencion`, `solicitudConcepto`, `solicitudLote` están en MySQL, con nombres en camelCase, PK `id_solicitud_recibo` y sin `activo` ni fechas de auditoría. Esto **no cumple L23–L24**. Habría que remodelarlas (por ejemplo `solicitud_recibo`, `solicitud_cuota`…), probablemente en la base `financiera`, en un esquema por funcionalidad.
- Las fechas se guardan como timestamp Unix en texto (`time()`, `strtotime`) y deben pasar a `timestamp` (L24).
- Los porcentajes de cuota se guardan como enteros 0–100 (`porcentajeCuota`). L25 exige `numeric(5,4)` (fracción 0–1), lo que implica **conversión de datos**.
- La cancelación cambia `estado` de 0 a 2 con UPDATE (`cancelarSolicitud`). Coincide con el espíritu de L27, pero el estado debería ser una tabla paramétrica (L26).
- Conceptos (IDs 1, 2, 3, 4, 19), exenciones (mapa columna → `id_exencion`), eventos (80, 82) y estados de estudiante (`V, J, T, A, Q, B`) están fijos en el código. Las tablas paramétricas (L26) soportan la meta de negocio Q10: "todas las reglas son paramétricas o llegan en la plantilla".
- El sistema académico en Oracle (`ACEST`, `ACCRA`, `V_ACESTMATBRUTO`, `fua_verifica_evento`, `mntac.fua_verifica_diferido`…) **no tiene lineamiento** (L29). Hay que decidir si se accede directamente, a través de un CRUD institucional existente o con una réplica.

## 6. Diseño de APIs REST

| ID | Hallazgo | Tipo | Fuente |
|---|---|---|---|
| L30 | REST con endpoints **en español**, sin ñ ni tildes, en plural, minúsculas, kebab-case (`-`, no `_`), sin `/` final, **sin verbos CRUD en la URI**. | REQ | `generacion_de_apis/lineamientos-endpoints.md` |
| L31 | Se usan los códigos HTTP correctos, y un resultado vacío responde 2xx. | REQ | ídem §Códigos de respuesta |
| L32 | Versionado **SemVer**: la primera versión en producción es `0.1.0` y la versión estable es `1.0.0`. El sistema también lleva su propia versión. | REQ | `generacion_de_apis/versionado-apis-XYZ.md` |
| L33 | Las variables de entorno se nombran `NOMBRE_API_PARAMETRO` en mayúsculas. | REQ | `generacion_de_apis/variables_en_api.md` §1.1 |
| L34 | Toda API debe tener un **health check** para desplegarse en la infraestructura OAS. | REQ | `generacion_de_apis/endpoint_validacions.md` |

**Ejemplo de aplicación (orientativo, no es diseño):** la carga de un lote sería `POST /v1/lotes-solicitudes` en lugar de `procesar=true` en `index.php`, y la consulta de solicitudes de un estudiante sería `GET /v1/solicitudes-recibo?estudiante=…`.

## 7. Seguridad

| ID | Hallazgo | Tipo | Fuente |
|---|---|---|---|
| L35 | Checklist de desarrollo antes de pedir la revisión de seguridad: código en el repositorio de la Universidad; sin secretos, llaves ni certificados en el repo; entradas validadas; autenticación, usuarios, roles y permisos validados; variables de entorno correctas; arquitectura y APIs documentadas. | REQ | `qa/validación_seguridad.md` §2 |
| L36 | Entregables para Seguridad: nombre, URL de pruebas, repositorio, arquitectura, usuarios y roles, tecnologías, Swagger/OpenAPI y manuales. | REQ | `qa/validación_seguridad.md` §3 |
| L37 | Seguridad verifica con **SonarQube**, **Dependabot**, pruebas de authn/authz (escalamiento de privilegios, sesiones), pruebas de APIs (CORS, tokens, rate limiting) y pruebas web (inyección, XSS…), con referencia a **OWASP Top 10, ASVS y API Security Top 10**. | REQ | `qa/validación_seguridad.md` §4 |
| L38 | **Bloquean el despliegue:** vulnerabilidades críticas sin tratar, vulnerabilidades altas explotables, secretos expuestos, fallas graves de authn/authz, exposición injustificada de información sensible. | REQ | `qa/validación_seguridad.md` §5 |
| L39 | Gate de calidad SonarQube: **0 bugs, 0 vulnerabilidades, máximo 50% de duplicación**. | REQ | `qa/definicion.md` §Check list ítem 4.1 |
| L40 | Los logs están documentados solo para Beego, como archivo en `/var/log/beego/<repo>/`. No hay lineamiento para Python ni para logs de auditoría centralizados. | VACÍO | `generacion_de_apis/logs_api.md` |

**Contraste con weboffice:** los riesgos R1–R5 de `existing-system-analysis.md` (SQL concatenado en todo `sql.class.php`, XSS por `$_REQUEST`, `tipoUser` manipulable, uploads con `0777`, credenciales en `$configuracion`) **caen todos en criterios bloqueantes (L38)**. La migración no puede reproducir esos patrones. Las restricciones de negocio de Q9 (mínimo privilegio, logs siempre habilitados, sesiones seguras, control de dependencias, cabeceras) coinciden con L37, aunque L12 y L40 no tienen equivalente para Python.

## 8. CI/CD, ambientes y despliegue

| ID | Hallazgo | Tipo | Fuente |
|---|---|---|---|
| L41 | Ambientes **dev → test → prod** (ramas `develop`/dev, `release`/test, `master`). Pasar a test y a prod requiere Swagger actualizado, `.drone.yml`, registro en WSO2 y PR revisado por el grupo de Arquitectura. | REQ | `despliegues/lineamientos.md` |
| L42 | Pruebas obligatorias antes de producción: unitarias (líder de desarrollo), **de carga** (líder de seguridad), funcionales (grupo de soporte), **de usuario** (centro de servicios). | REQ | `despliegues/lineamientos.md` §Producción, prerrequisitos |
| L43 | Pipeline **Drone CI**: SonarQube, build, publicación en **AWS ECR** y despliegue en **AWS ECS** (cluster `test` u `oas`). Los secretos van en Drone (`from_secret`). | REQ | `generacion_de_apis/cicd/.drone.yml`; `api_flask/refactorizacion_api_flask.md` §.drone.yml |
| L44 | Las variables de entorno de test y prod se registran en **Tuleap**; las de dev, a través del grupo de infraestructura. Jenkins se usa en dev. | REQ | `despliegues/lineamientos.md` |
| L45 | Cada repositorio tiene `Dockerfile` y `docker-compose.yml` en la raíz. | REQ | `ambientes_dockerizados/dockerizacion.md` |
| L46 | `sonar-project.properties` en la raíz, con plantillas para Angular y Python. | REQ | `generacion_de_apis/cicd/sonar-project.properties.md` |
| L47 | **GitFlow** (feature, develop, release, hotfix, master) y commits con etiquetas `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `devops:`, `management:`. | REQ | `repositorios_institucionales/nombre_branch.md`; `repositorios_institucionales/etiqueta_commits.md` |
| L48 | README con contenido mínimo: tecnologías y versiones, variables de entorno, ejecución (Docker y docker-compose), pruebas, estado de CI, modelo de datos y licencia. | REQ | `repositorios_institucionales/contenido_readme.md` |

**Contraste con weboffice:** el repo tiene 1 commit sin GitFlow (`a247a67 Commit inicial del proyecto`), sin Dockerfile, CI, Sonar, README ni pruebas. Los archivos se guardan en el disco local (`documento/solicitudes/`), lo que choca con contenedores efímeros en ECS: **hay que definir dónde se guardan las plantillas cargadas** (VACÍO).

## 9. Metodología

| ID | Hallazgo | Tipo | Fuente |
|---|---|---|---|
| L49 | **Scrum/OAS**: visión del proyecto, plan general, **modelo relacional aprobado por comité**, épicas, backlog priorizado, plan de lanzamiento. Historias de usuario en **Tuleap**, flujograma en jBPM y prototipo en Pencil. | REQ | `metodologias/lineamientos.md` |
| L50 | Hay una plantilla institucional de historias de usuario. | REC | `metodologias/formatos/Plantilla_Historias_Usuario-OAS_v2.xlsx` (no abierta) |

## 10. Impacto en la fecha límite (15/12/2026)

Hoy es 2026-11-23, así que quedan unos 22 días. El proceso institucional para llegar a producción incluye la aprobación del modelo relacional por comité (L49), la creación de la base por DBA (L28), el registro en WSO2 (L19), Drone/ECS (L43), pruebas de carga, funcionales y de usuario (L42) y la revisión de Seguridad con criterios bloqueantes (L38). **Es poco probable completar todo eso para el 15/12/2026.** Lo factible es una **PoC en ambiente dev o test**. El negocio debe confirmar en qué ambiente se considera cumplida la PoC.

## 11. Preguntas técnicas nuevas que salen de este contraste

| Pregunta | Relación |
|---|---|
| ¿El backend Python debe ser **Flask** (único lineamiento Python), o se permite FastAPI u otro con excepción aprobada? | T8, L5 |
| ¿Qué versiones de Python, Node y Angular se fijan, dado que los lineamientos citan versiones sin soporte (3.8, Node 16)? | T5, L9, L16 |
| ¿Se separa en `recibos_cliente` / `recibos_mid` / `recibos_crud` (o el nombre de negocio que defina la OATI)? | T16, L3 |
| ¿Las tablas de solicitudes se migran a PostgreSQL (base `financiera`, esquema por funcionalidad) o siguen en MySQL durante la PoC? | T14, TB2, L22, L29 |
| ¿Cómo se accede a Oracle académico: directo, vía un CRUD existente o con una réplica? | T14, T15, L29 |
| ¿La autenticación es WSO2 IS/AM más configuracion_cliente para el rol ARC? | T17, L19, L15 |
| ¿Cuál es el equivalente Python de cabeceras de seguridad, auditoría, logs y formato JSON de error? | T18–T19, L11, L12, L40 |
| ¿Dónde se guardan los archivos de plantilla cargados (S3, gestor documental Nuxeo, otro)? | T11, L43 |
| ¿Qué pruebas se exigen a la PoC: solo unitarias y de equivalencia, o también carga, usuario y seguridad? | T22, L42 |

---

## Decisión de negocio posterior (2026-11-23T22:58:00Z)

Según el rol de Negocio (QB2): **los lineamientos OAS aplican solo al código, no a las bases de datos.** Se mantienen Oracle académico y MySQL (`solicitudrecibo` y relacionadas). Por eso los hallazgos **L22–L29 (§5 Modelo de datos) no aplican** a este proyecto. La pregunta de §11 sobre migrar a PostgreSQL queda resuelta: no se migra.
