# Plan de generación de código — U1 `recibos_service`

- Etapa: CONSTRUCTION → U1 `recibos_service` → Code Generation, Parte 1 (planificación)
- Inicio: 2026-11-25T19:43:44Z
- Plan aprobado por el usuario el 2026-11-25T19:50:22Z: "aprobar plan"
- Este plan es la única fuente de verdad de la generación. Se ejecuta paso por paso, en orden, y cada casilla se marca en cuanto el paso termina
- Ubicación del código: `recibos_service/`, en la raíz del workspace, armada como raíz de su futuro repositorio (Units Generation, Q1 = A). Nada de código va en `aidlc-docs/`; ahí solo van los resúmenes en Markdown (`aidlc-docs/construction/recibos_service/code/`)
- Infrastructure Design de U1 quedó aplazada por el usuario el 2026-11-25T19:39:46Z ("omitir la infraestructura,  dejarlo para después, pasa al paso de generar el codigo"). Lo que eso deja pendiente está en §5
- Extensiones: seguridad, con todas sus reglas bloqueantes; PBT parcial, con PBT-02, 03, 07, 08 y 09 bloqueantes y las demás orientativas; resiliencia desactivada (N17 = b)

## 1. Contexto de la unidad

| Tema | Detalle |
|---|---|
| Historias | US-01 y US-02 del lado del servidor, y US-03 a US-15. Listas: US-01, 02, 04, 06, 09, 10, 12, 13, 14 y 15. Con insumos pendientes: US-03 y US-07 (D1), US-05 y la variante SMLV de US-08 (D2), US-11 (D4) |
| Contrato | `inception/application-design/api-contract.md`: `POST /v1/lotes`, `GET /v1/lotes`, `GET /` y `GET /health`; sobre `{Success, Status, Message, Data}`; cabeceras `X-Request-Id` y `Cache-Control` |
| Dependencias en ejecución | WSO2 IS (`/oauth2/userinfo`), "parametros", Oracle académico (solo lectura), MySQL (`solicitud*`, `exencion` y festivos), S3 y SSM. U2 no es una dependencia: consume el contrato |
| Datos | El servicio no es dueño de ninguna tabla. Escribe en `solicitudLote`, `solicitudRecibo`, `solicitudCuota`, `solicitudExencion` y `solicitudConcepto`, y lee `exencion`, la tabla de festivos (D5) y Oracle. No hay migraciones; el índice de N19 va como script de referencia para el DBA |
| Límites | Toda regla de negocio y todo control de seguridad viven en U1 |
| Diseño que se sigue | `functional-design/`, `nfr-requirements/`, `nfr-design/`, y en `inception/application-design/`: `components.md`, `component-methods.md`, `services.md`, `component-dependency.md` y AD-01 a AD-36 |

## 2. Herramientas
- Python 3.15 no está instalado en la máquina (tiene 3.14.10). Las dependencias, ruff, mypy y pytest corren en un contenedor `python:3.15-slim` con la versión exacta; Docker 29 ya está instalado.
- Si una dependencia no se instala en Python 3.15 desde un wheel, todo el proyecto pasa a 3.14 y queda escrito en `tech-stack-decisions.md` (N1).
- Las versiones exactas, con hashes, salen de `pip-compile --generate-hashes`; pip-audit no debe reportar vulnerabilidades.
- python-dotenv no se agrega: `docker-compose.yml` carga el `.env` local con `env_file`, así que no hace falta una dependencia más (SECURITY-10).

## 3. Pasos

### Paso 1 — Entorno y dependencias
- [x] Bajar `python:3.15-slim` y anotar su versión exacta.
- [x] `recibos_service/pyproject.toml`: metadatos; `requires-python = ">=3.15,<3.16"`; dependencias directas (Flask 3.1, flask-cors 6.0, pydantic 2.14 o superior, SQLAlchemy 2.1, python-oracledb 26, PyMySQL 1.2, xlrd 2.0, requests 2.34, boto3 y gunicorn 27); dependencias de desarrollo (pytest 9, pytest-cov, Hypothesis 6, ruff, mypy, pre-commit, pip-tools, pip-audit y cyclonedx-bom); configuración de ruff, de mypy (estricto en `app/domain` y `app/application`), de pytest y de coverage (80% en total y 100% en `app/domain`).
- [x] `requirements.txt` y `requirements-dev.txt` con hashes, generados en el contenedor.
- [x] Instalar con `--require-hashes` y correr pip-audit.
- Nota: imagen python:3.15.2-slim (sha256:63bb298d2b7b…); todas las dependencias se instalan desde wheels en Python 3.15; pip-audit sin vulnerabilidades en requirements.txt. La revisión de requirements-dev.txt no terminó a tiempo y se repite en el paso 18.

### Paso 2 — Estructura del proyecto
- [ ] Carpetas `app/domain`, `app/application`, `app/infrastructure` (con sus subpaquetes), `app/interfaces` (routers, controllers, schemas y middlewares), `conf/`, `swagger/`, `db/` y `tests/` (espejo de `app/`, más `fixtures/`).
- [ ] `.gitignore` (plantilla de Python, con `.env`, `.hypothesis/` y `coverage.xml`), `.env.example` (solo nombres de variables), `.pre-commit-config.yaml` (ruff y mypy con versiones fijas) y `sonar-project.properties` (fuentes en `app/`, pruebas en `tests/`, `coverage.xml`).

### Paso 3 — Lógica de negocio (`app/domain/`)
- [x] `modelos.py`: los tipos de `component-methods.md` §1.1, como dataclasses inmutables.
- [x] `reglas.py`: `ReglasLiquidacion` y sus métodos (§1.2).
- [x] `plantillas.py`: las tres especificaciones (`domain-entities.md` §2.3), identificación, validación de formato con el mensaje propio de la plantilla con "Reingreso" y extracción de filas (BR-L08 a BR-L11). Pregrado y SMLV con los valores provisionales de §4.
- [x] `validacion_filas.py`: lectura de celdas (`business-logic-model.md` §4.2), código (BR-F01) y datos de posgrado (BR-D01 a BR-D05).
- [x] `validacion_estudiante.py`: BR-E02 a BR-E07, en el orden de §4.3.
- [x] `fechas.py`: fecha extraordinaria (BR-Q04) y conversión a timestamp Unix de la medianoche en America/Bogota (BR-S04).
- [x] `cuotas.py`, `exenciones.py`, `conceptos.py` y `generador_solicitud.py` (BR-Q01 a BR-Q04, BR-X01 a BR-X07, BR-C01, BR-C02 y BR-S01 a BR-S04).
- [x] `mensajes.py`: los textos de `business-rules.md` §10 y la construcción de cada `Rechazo`.
- Historias: US-03, US-04, US-05, US-06, US-07, US-08, US-11 y US-12.

### Paso 4 — Pruebas de la lógica de negocio
- [x] `tests/estrategias.py`: generadores de Hypothesis para filas de cada plantilla, códigos, fechas, porcentajes, reglas, estudiantes, contextos y festivos, en un solo lugar (PBT-07).
- [x] `tests/conftest.py`: perfiles `dev` y `ci` de Hypothesis, con la reducción de casos activa y `print_blob` para repetir un caso que falla (PBT-08).
- [x] Pruebas de ejemplo (`test_<módulo>_ejemplos.py`) con los escenarios de las historias y las tablas de decisión del diseño funcional (§4.6 y §4.8).
- [x] Pruebas de propiedades (`test_<módulo>_propiedades.py`) con todas las propiedades del dominio de `business-logic-model.md` §9: ida y vuelta (PBT-02), invariantes (PBT-03), idempotencia (PBT-04) y oráculos (PBT-05).
- [x] `tests/test_arquitectura.py`: `app/domain` solo importa la biblioteca estándar, y ninguna capa importa lo que `component-dependency.md` §1 no permite (NFR-M01).
- [x] Correr ruff, mypy y pytest en el contenedor; 100% de cobertura en `app/domain`.
- Nota: 159 pruebas bien; ruff y mypy estricto sin errores; 100% de líneas y ramas en app/domain.

### Paso 5 — Resumen de la lógica de negocio
- [x] `aidlc-docs/construction/recibos_service/code/dominio.md`: módulos, reglas que implementa cada uno, pruebas y huecos por insumos pendientes.

### Paso 6 — Casos de uso (`app/application/`)
- [x] `puertos.py`: los puertos de `component-methods.md` §2.1, con `SesionFilas` y el `plazo` en los de la fase previa.
- [x] `errores.py`: errores de aplicación, incluidos `ErrorPersistencia`, `ErrorConexionBD` y `BloqueoNoObtenido`.
- [x] `presupuesto.py`: `Plazo` y `PlazoVencido` (AD-34).
- [x] `procesar_lote.py`: UC-01 según `business-logic-model.md` §4.1 y §4.9: plazo del lote, presupuesto de la fase previa, una sesión de MySQL para las filas, bloqueo por estudiante, corte por MySQL (AD-35) y datos para la auditoría.
- [x] `consultar_lotes.py` (UC-02) y `autorizar_usuario.py` (UC-03).
- Historias: US-02, US-06, US-09, US-10, US-12, US-13 y US-15.
- Nota: se agregó `contexto.py`, con la `ContextVar` del `request_id` que comparten las capas. `Plazo` recibe la función `segundos` del reloj en lugar del `Reloj`, para no crear una importación circular con `puertos.py`.

### Paso 7 — Pruebas de los casos de uso
- [ ] `tests/application/dobles.py`: dobles en memoria de cada puerto, incluido un reloj de prueba y una sesión de MySQL que falla a pedido.
- [ ] Pruebas de ejemplo de UC-01 a UC-03: escenarios de US-02, US-06, US-09, US-10, US-12, US-13 y US-15, y las situaciones de `business-logic-model.md` §5.
- [ ] Pruebas de propiedades de `procesar_lote` y de `Plazo` (§9): cada fila aparece una vez, nunca se cancela por un código inválido, repetido o no encontrado, `TIEMPO_AGOTADO`, corte por MySQL y dos lotes en paralelo con el bloqueo (PBT-06, orientativa).
- [ ] Correr ruff, mypy y pytest en el contenedor.

### Paso 8 — Resumen de los casos de uso
- [ ] `aidlc-docs/construction/recibos_service/code/aplicacion.md`.

### Paso 9 — Capa de API (`api.py`, `conf/` y `app/interfaces/`)
- [ ] `conf/conf.py`: lee y valida las variables `RECIBOS_SERVICE_*` con sus límites (`logical-components.md` §4); los secretos como `SecretStr`; si algo falta o está fuera de rango, el proceso no arranca y lo registra sin valores.
- [ ] `app/interfaces/schemas/`: `respuesta.py` (sobre institucional y mensajes por defecto) y `lotes.py` (`ConsultaLotes`, `ResumenLoteDTO`, `RechazoDTO`, `LoteDTO`).
- [ ] `app/interfaces/middlewares/`: `contexto_peticion`, `cors`, `autenticacion`, `auditoria` (con `db/captura_sql`), `cabeceras_seguridad` y `errores`, en el orden de `nfr-design-patterns.md` §7.1.
- [ ] `app/interfaces/routers/` y `controllers/`: `estado` (`GET /` y `GET /health`) y `lotes` (`POST /v1/lotes` y `GET /v1/lotes`), con la validación del archivo (BR-L01 a BR-L03).
- [ ] `api.py`: `create_app()` arma la configuración, los adaptadores, los casos de uso, los middlewares, `ProxyFix` y los límites de Werkzeug, y expone `app` para gunicorn.
- Historias: US-01, US-02, US-12, US-13 y US-14.

### Paso 10 — Pruebas de la capa de API
- [ ] Con el cliente de pruebas de Flask y dobles de los casos de uso: health checks; 401 y 403; 400, 413 y 415 del archivo; 201 y 422; 502 y 503; el sobre en cada código; las 10 cabeceras, `Cache-Control` y `X-Request-Id`; CORS con la lista de orígenes; la línea de auditoría sin datos personales; la validación de la configuración.
- [ ] Propiedades: ida y vuelta de `schemas/lotes` (PBT-02) y la IP del cliente con N proxies de confianza (AD-29).
- [ ] Correr ruff, mypy y pytest en el contenedor.

### Paso 11 — Resumen de la capa de API
- [ ] `aidlc-docs/construction/recibos_service/code/api.md`.

### Paso 12 — Repositorios y adaptadores (`app/infrastructure/`)
- [ ] `reloj.py`, `registro.py` (formateador JSON y filtro de `request_id`) y `http.py` (sesión por hilo, un reintento si falla la conexión, sin redirecciones).
- [ ] `config/ssm.py`, `s3/almacenamiento_s3.py` y `xls/lector_xlrd.py`.
- [ ] `wso2/proveedor_identidad.py` y `parametros/` (`modelos.py` y `fuente_reglas.py`, con las 17 reglas en paralelo y la conversión de AD-21).
- [ ] `db/motores.py` y `db/captura_sql.py` (TLS, tiempos de espera y pools de `logical-components.md` §2.4).
- [ ] `oracle/repositorio_academico.py`: tres consultas en bloque, con `call_timeout` según el plazo.
- [ ] `mysql/repositorio_solicitudes.py`: registro e historial de lotes, porcentajes de `exencion` y `SesionFilasMySQL` (bloqueo, cancelación, guardado, plazo por sentencia y separación de las fallas de conexión).
- [ ] `festivos/fuente_festivos.py`: la tabla de festivos según la configuración de §4 (D5).
- Historias: US-01, US-02, US-06, US-09, US-10, US-11, US-13, US-14 y US-15.

### Paso 13 — Pruebas de los repositorios y adaptadores
- [ ] Copiar a `tests/fixtures/` las plantillas oficiales de `documentacion/plantillas-recibos/`, si no traen datos de estudiantes, y probar el lector con ellas.
- [ ] Probar el SQL y los parámetros enlazados con conexiones de prueba que registran las sentencias; la clasificación de los errores de MySQL (2003, 2006, 2013, 2055, 1205 y 1213); el plazo por sentencia; `call_timeout` en Oracle; la conversión de "parametros" con su ida y vuelta (PBT-02); los reintentos HTTP; la configuración de boto3 con el `Stubber` de botocore; el formateador JSON.
- [ ] Correr ruff, mypy y pytest en el contenedor.

### Paso 14 — Resumen de los repositorios y adaptadores
- [ ] `aidlc-docs/construction/recibos_service/code/infraestructura.md`.

### Paso 15 — Script de referencia para el DBA
- [ ] `recibos_service/db/indice_solicitudRecibo.sql`: el índice no único por (`codigo_est`, `estado`) de N19, para el DBA si D17 muestra que falta. El servicio no lo ejecuta y no tiene permisos para hacerlo.

### Paso 16 — Documentación
- [ ] `swagger/swagger.yml`: Swagger 2.0, igual a `api-contract.md`.
- [ ] `README.md`: lo que pide L48 (tecnologías y versiones, variables de entorno, ejecución con Docker y docker-compose, pruebas, estado de CI, modelo de datos y licencia) y los insumos pendientes de §4.

### Paso 17 — Artefactos de despliegue
- [ ] `Dockerfile`: dos etapas; imagen base `python:3.15-slim` con versión exacta; instalación con `--require-hashes`; imagen final sin herramientas de compilación, con un usuario sin privilegios y lista para un sistema de archivos de solo lectura.
- [ ] `.dockerignore`.
- [ ] `gunicorn.conf.py`: los valores de `logical-components.md` §2.1, incluida la cabecera `Server` vacía.
- [ ] `docker-compose.yml`: el servicio con el `.env` local y, solo en local, el contenedor oficial de Swagger UI con versión fija.
- [ ] `.drone.yml`: revisión de la rama y de los commits, ruff, mypy, pruebas con cobertura y la semilla de Hypothesis en el registro (PBT-08), pip-audit, SBOM, SonarQube, construcción de la imagen sin publicarla y aviso por Telegram; imágenes del pipeline con versión fija. Sin publicación en ECR ni despliegue en ECS (§5).

### Paso 18 — Verificación final
- [ ] ruff, mypy y pytest con cobertura en el contenedor (80% en total y 100% en `app/domain`).
- [ ] pip-audit y SBOM sin errores; construcción de la imagen; búsqueda de secretos en `recibos_service/`.
- [ ] Marcar las historias en §6, actualizar los resúmenes y presentar la compuerta.

## 4. Supuestos para los insumos pendientes
El código queda listo para recibirlos: cada uno se cambia en un solo lugar, sin tocar la lógica.

| Insumo | Qué falta | Cómo queda el código | Dónde se cambia |
|---|---|---|---|
| D1 | Plantilla de pregrado nueva: encabezados y posición de la fecha ordinaria | Especificación provisional: las 13 columnas de hoy sin "Reingreso" y la fecha ordinaria en las columnas 14, 15 y 16 | `app/domain/plantillas.py` y sus pruebas |
| D2 | Plantilla SMLV | Igual que créditos, con el texto de A1 de `domain-entities.md` §2.3 y "SMLV" en la columna 2 (A6) | `app/domain/plantillas.py` y sus pruebas |
| D4 | DDL, prefijo de las tablas y llaves | Nombres de tablas y columnas del código PHP (`sql.class.php`); prefijo por configuración, vacío por defecto; la longitud máxima del nombre del archivo, por configuración | `RECIBOS_SERVICE_MYSQL_PREFIJO` y `mysql/repositorio_solicitudes.py` |
| D5 | Tabla de festivos | Base, tabla y columna por configuración, con nombres validados como identificadores | Variables `RECIBOS_SERVICE_FESTIVOS_*` |
| D6 | Campo del valor de cada regla, ids por ambiente, URL y autenticación | El id, el campo y el formato de cada una de las 17 reglas en un JSON de configuración que se valida al arrancar | `RECIBOS_SERVICE_PARAMETROS_REGLAS` y `RECIBOS_SERVICE_PARAMETROS_URL` |
| D7 | Rutas de SSM | La ruta base por configuración; los nombres de cada secreto, fijos debajo de ella | `RECIBOS_SERVICE_SSM_RUTA` |
| D8 | Identificador del rol de ARC | Por configuración | `RECIBOS_SERVICE_ROL_AUTORIZADO` |
| D13 | Proxies de confianza | 0 por defecto: se usa la dirección de la conexión | `RECIBOS_SERVICE_PROXIES_CONFIANZA` |
| D14 | Servicio TCPS de Oracle y certificados de las CA | DSN y rutas de los certificados por configuración | Variables `RECIBOS_SERVICE_ORACLE_*` y `RECIBOS_SERVICE_MYSQL_*` |
| D17 | Motor de las tablas, versión de MySQL e índice | El código supone InnoDB y MySQL 5.7.5 o superior para `GET_LOCK`; el README lo dice | README y `db/indice_solicitudRecibo.sql` |

Las variables nuevas se agregan a `.env.example` y al README, sin valores.

## 5. Lo que queda para Infrastructure Design (aplazada)
- `.drone.yml` no publica en ECR ni despliega en ECS: depende de I5 (imagen por commit o `latest`).
- `gunicorn.conf.py` sirve HTTP en el puerto 8080, como supone la opción recomendada de I4; si se elige HTTPS, se agrega después.
- No se definen la definición de tarea, el balanceador, el bucket, las alarmas, los permisos ni la red. Las listas de `nfr-design/logical-components.md` §5 y §6 siguen siendo el insumo, junto con I1 a I5, D7 y D11 a D16.
- Las partes de infraestructura de SECURITY-02, 06, 07 y 14 quedan pendientes. No bloquean esta etapa, porque el código no las define, pero sí el primer despliegue en test.

## 6. Historias
Se marcan cuando su código y sus pruebas quedan generados.

- [ ] US-01 Acceso con el rol de ARC (pasos 9, 10 y 12)
- [ ] US-02 Carga del archivo (pasos 6, 9, 10 y 12)
- [ ] US-03 Formato de pregrado (pasos 3 y 4; provisional hasta D1)
- [ ] US-04 Formato de posgrado por créditos (pasos 3, 4 y 13)
- [ ] US-05 Formato de posgrado SMLV (pasos 3 y 4; provisional hasta D2)
- [ ] US-06 Validación de estudiantes en Oracle (pasos 3, 4, 6, 7, 12 y 13)
- [ ] US-07 Solicitudes de pregrado (pasos 3 y 4; provisional hasta D1)
- [ ] US-08 Solicitudes de posgrado (pasos 3 y 4; la variante SMLV, provisional hasta D2)
- [ ] US-09 Cancelación de las sin imprimir (pasos 6, 7, 12 y 13)
- [ ] US-10 Solicitud completa o ninguna (pasos 6, 7, 12 y 13)
- [ ] US-11 Entrega a "Solicitados" (pasos 3, 12 y 13; provisional hasta D4)
- [ ] US-12 Resumen del lote (pasos 3, 6, 9 y 10)
- [ ] US-13 Historial de lotes (pasos 6, 9, 10 y 12)
- [ ] US-14 Auditoría de cada petición (pasos 9, 10 y 12)
- [ ] US-15 Reglas desde "parametros" (pasos 6, 7, 12 y 13)

## 7. Cumplimiento de las extensiones en esta etapa

| Regla | Dónde se cumple |
|---|---|
| SECURITY-01 | TLS hacia Oracle, MySQL, S3, SSM y los servicios HTTP (paso 12) |
| SECURITY-03 | Registro JSON con `request_id`, sin secretos ni datos personales (pasos 9 y 12) |
| SECURITY-04 | Las 10 cabeceras, `Server` vacía y `Cache-Control` (pasos 9 y 17) |
| SECURITY-05 | Límites del cuerpo y del formulario, validación del archivo y de las filas, pydantic y parámetros enlazados (pasos 3, 9 y 12) |
| SECURITY-08 | Token en cada petición, rol en el servicio y CORS con lista explícita (paso 9) |
| SECURITY-09 | Errores genéricos, `DEBUG` apagado, sin documentación servida, imagen mínima con un usuario sin privilegios (pasos 9 y 17) |
| SECURITY-10 | Versiones exactas con hashes, pip-audit, SBOM e imágenes con versión fija (pasos 1 y 17) |
| SECURITY-11 | Límites, plazos y casos de abuso de `business-rules.md` §13 y `nfr-design-patterns.md` §7.7 (pasos 3, 6 y 9) |
| SECURITY-12 | Secretos solo en SSM y en memoria como `SecretStr`; ninguno en el código ni en `.env.example` (pasos 9 y 12) |
| SECURITY-13 | xlrd y pydantic como lectores seguros; auditoría de lo creado y cancelado (pasos 6, 9 y 12) |
| SECURITY-15 | Manejo explícito de cada falla, falla cerrada, liberación de recursos y manejador global (pasos 6, 9 y 12) |
| SECURITY-02, 06, 07 y 14 | Sus partes de infraestructura quedan para Infrastructure Design (§5); el código deja los eventos de las alarmas (paso 12) |
| PBT-02 y PBT-03 | Pruebas de propiedades de ida y vuelta e invariantes de `business-logic-model.md` §9 (pasos 4, 7, 10 y 13) |
| PBT-07 | Generadores del dominio en `tests/estrategias.py` (paso 4) |
| PBT-08 | Reducción activa, `print_blob` y semilla en el registro de Drone (pasos 4 y 17) |
| PBT-09 | Hypothesis en `requirements-dev.txt` (paso 1) |
| PBT-01, 04, 05, 06 y 10 (orientativas) | Las propiedades de §9 se usan como lista de pruebas; idempotencia, oráculos y el caso con estado de dos lotes; pruebas de ejemplo y de propiedades en archivos separados |

## 8. Cómo se verifica
- Cada paso de pruebas corre ruff, mypy y pytest en el contenedor de Python 3.15, y no avanza con errores.
- Build and Test, la etapa siguiente, deja las instrucciones y el reporte completo.
