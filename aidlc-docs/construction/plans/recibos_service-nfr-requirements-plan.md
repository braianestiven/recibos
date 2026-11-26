# Plan de requisitos no funcionales — U1 `recibos_service`

- Etapa: CONSTRUCTION → U1 `recibos_service` → NFR Requirements, profundidad estándar (`inception/plans/execution-plan.md`)
- Inicio: 2026-11-25T18:08:21Z
- Fuentes: el diseño funcional de U1 (`construction/recibos_service/functional-design/`, aprobado el 2026-11-25T17:55:25Z); `requirements.md` §5 (RNF-1 a RNF-8); `Product-Definition/technical-environment.md`; AD-01 a AD-30; `unit-of-work.md` §5 y §6
- Extensiones: seguridad, con todas sus reglas bloqueantes; PBT parcial. En esta etapa aplica PBT-09 (elegir el framework de pruebas basadas en propiedades), que es bloqueante
- Cómo responder: después de cada `[Answer]:` de este archivo, o en el chat con el formato "n1 a, n2 a, …"

## Pasos
- [x] 1. Analizar el diseño funcional de U1 y los requisitos no funcionales aprobados
- [x] 2. Revisar en la web las versiones vigentes y el estado de mantenimiento de las librerías del stack (2026-11-25)
- [x] 3. Escribir este plan con las preguntas N1 a N13
- [x] 4. Recibir las respuestas y revisar que ninguna quede ambigua; si alguna lo es, abrir un archivo de aclaraciones — N1 a N13 respondidas el 2026-11-25T18:25:20Z; N10 y N6 abren las aclaraciones N14 a N17 en `recibos_service-nfr-requirements-clarification-questions.md`, respondidas el mismo día (n14 c, n15 a, n16 a, n17 b)
- [x] 4a. Analizar `firma_electronica_mid`, la API Python de la OAS que indicó el usuario → `construction/recibos_service/nfr-requirements/firma-electronica-mid-analysis.md` (2026-11-25T18:25:20Z)
- [x] 5. `nfr-requirements.md`: rendimiento, capacidad, disponibilidad, seguridad y cumplimiento, confiabilidad, observabilidad, mantenibilidad y pruebas; cada requisito con un valor que se pueda medir
- [x] 6. `tech-stack-decisions.md`: lenguaje, librerías y herramientas, con versión, razón y alternativas descartadas, incluido el framework de PBT (PBT-09)
- [x] 7. Revisar el cumplimiento de seguridad y de PBT, y presentar la compuerta de la etapa (2026-11-25T18:31:09Z)

## Lo que encontré al revisar el stack (2026-11-25)
| Tema | Dato | Efecto en el stack aprobado | Fuente |
|---|---|---|---|
| Python | 3.15.0 salió el 9 de octubre de 2026. La máquina tiene 3.14.10 | C4 pide la última versión estable: pregunta N1 | [python.org](https://www.python.org/downloads/release/python-3150/), [novedades de 3.15](https://docs.python.org/3/whatsnew/3.15.html) |
| Librerías con código compilado | pydantic 2.14 es la primera versión con soporte para 3.15. python-oracledb 26.0 (septiembre de 2026) agregó soporte inicial para 3.15. SQLAlchemy 2.0 llega hasta 3.15, y la serie 2.1 pide 3.11 o superior. gunicorn pide 3.12 o superior | Python 3.15 es viable | [pydantic](https://pydantic.dev/articles/pydantic-v2-14-release), [python-oracledb](https://python-oracledb.readthedocs.io/en/latest/release_notes.html), [SQLAlchemy](https://www.sqlalchemy.org/docs/21/changelog/migration_21.html), [gunicorn](https://gunicorn.org/install/) |
| SDK de X-Ray | Desde el 25 de febrero de 2026 el SDK y el daemon de X-Ray están en mantenimiento: solo reciben arreglos de seguridad. AWS recomienda OpenTelemetry, que en Python soporta 3.10 o superior | `aws-xray-sdk` deja de ser la opción recomendada: pregunta N10 | [AWS](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html), [OpenTelemetry](https://opentelemetry.io/docs/languages/python/) |
| httpx | Sin versiones desde diciembre de 2024 (0.28.1). Proyectos grandes migran a httpx2, un fork que mantiene Pydantic | SECURITY-10 no permite dependencias abandonadas: AD-08 cambia, pregunta N11 | [PyPI](https://pypi.org/project/httpx/), [FastAPI](https://github.com/fastapi/fastapi/pull/16358) |
| requests | La mantiene la PSF; la versión 2.34.2 es de mayo de 2026 | Alternativa a httpx | [GitHub](https://github.com/psf/requests/releases) |
| flasgger | La última versión, 0.9.7.1, es de mayo de 2023 | Riesgo de SECURITY-10 si llega a producción: pregunta N12 | [PyPI](https://pypi.org/project/flasgger/) |
| python-oracledb en modo thin | No soporta el cifrado nativo de Oracle (NNE); solo cifra con TLS | Depende de cómo cifra hoy Oracle: pregunta N9 | [python-oracledb](https://python-oracledb.readthedocs.io/en/stable/user_guide/initialization.html) |
| xlrd | 2.0.2, de junio de 2025, sin vulnerabilidades conocidas | Se mantiene | [PyPI](https://pypi.org/project/xlrd/2.0.2/) |
| Flask, flask-cors, Hypothesis | Flask 3.1.3 es de febrero de 2026; flask-cors 6.0.5 no tiene vulnerabilidades conocidas; Hypothesis publica versiones cada pocos días | Se mantienen | [Flask](https://github.com/pallets/flask/releases), [flask-cors](https://guide.sonatype.com/component/pypi/flask-cors/6.0.5/vulnerabilities), [Hypothesis](https://pypi.org/project/hypothesis/) |

El contenido de las fuentes se resumió con otras palabras, por las restricciones de licencia. Las versiones exactas se fijan con sus hashes en Code Generation (AD-26).

## Decisiones que no necesitan pregunta
Se aplican salvo que digas otra cosa.
- PBT-09: el framework de pruebas basadas en propiedades es Hypothesis. Tiene lo que pide la regla: generadores propios para los tipos del dominio, reducción automática de los casos que fallan, semilla reproducible e integración con pytest. Va en las dependencias de desarrollo.
- Dependencias en dos archivos con versiones exactas y hashes (pip-tools, AD-26): `requirements.txt` para producción y `requirements-dev.txt` para pruebas y herramientas. La imagen de producción solo instala `requirements.txt`.
- Escaneo de vulnerabilidades de las dependencias con pip-audit y SBOM con cyclonedx-py, en Drone (SECURITY-10). El escaneo de la imagen se define en Infrastructure Design.
- Cada llamada externa (WSO2, "parametros", S3, Oracle y MySQL) tiene un tiempo de espera explícito. Los valores se fijan en NFR Design, dentro del tiempo objetivo de N2.
- Reintentos: uno solo, en las lecturas por HTTP ("parametros" y `/oauth2/userinfo`), cuando falla la conexión. Las escrituras no se reintentan, para no duplicar solicitudes.
- `GET /health` solo indica que el proceso responde; no consulta las bases. Así, una caída de Oracle no hace que el balanceador reinicie las tareas.
- TLS 1.2 o superior en todo el tráfico. S3 con cifrado administrado por AWS (SSE-S3), que no tiene costo adicional, salvo que Seguridad pida llaves propias (Infrastructure Design).
- SECURITY-12: la autenticación, el segundo factor y el bloqueo por intentos fallidos los maneja WSO2 IS. Se pide a Seguridad confirmar que WSO2 IS exige segundo factor a los usuarios con el rol de ARC, porque pueden cancelar y crear solicitudes de cualquier estudiante.
- Riesgo aceptado, igual que hoy: si "Solicitados" genera el recibo de una solicitud justo cuando el lote la cancela, la solicitud queda generada, porque "Solicitados" cambia el estado sin revisar el anterior (RE-20). El sistema nuevo no puede evitarlo sin cambiar "Solicitados", que no se modifica.

## Lo que se deriva de las respuestas (2026-11-25)
Se aplican a `requirements.md`, `application-design.md`, `unit-of-work.md`, `components.md` y `technical-environment.md` cuando se generen los artefactos de la etapa, junto con las aclaraciones.
- N1 = a: imagen `python:3.15-slim` con la versión exacta fija. Antes de Code Generation hay que instalar Python 3.15 en la máquina, que hoy tiene 3.14.10. Si una dependencia no se instala en 3.15, se usa 3.14 y se deja escrito.
- N2 = a: el tiempo se mide dentro del servicio, desde que llega la petición hasta que sale la respuesta.
- N3 = a: el límite propio es de 90 segundos (una vez y media el objetivo). Los tiempos de espera van de adentro hacia afuera, cada uno mayor que el anterior: el límite propio, gunicorn, el balanceador, WSO2 AM y el navegador, todos de 120 segundos o más; los valores se fijan en NFR Design. Las filas que no se alcanzan a procesar salen con el motivo nuevo `TIEMPO_AGOTADO` ("No se alcanzó a procesar en el tiempo del lote; vuelva a cargar esta fila") y no cancelan nada. El motivo nuevo se agrega al diseño funcional y a `api-contract.md`.
- N4 = a: con N6, cada tarea debe atender sola los 3 lotes del pico, por si la otra falla.
- N5 = a: el bloqueo por estudiante vive en MySQL, así que funciona aunque haya varias tareas. Corrige `business-rules.md` §13.
- N6 = c: en producción, dos tareas o más en zonas distintas; despliegues sin interrupción; al detener una tarea, se espera a que termine el lote en curso (más que el límite de N3); alarmas 24/7. En test basta una tarea. Lo demás depende de N15, N16 y N17.
- N7 = a: 2 MB; reemplaza los 10 MB del supuesto A1.
- N8 = a: 365 días para los archivos de S3 (se borran solos), los registros de CloudWatch Logs y los registros de acceso del balanceador y de WSO2 AM.
- N9 = a: modo thin. Las dos conexiones exigen TLS y verifican el certificado del servidor. Insumo nuevo D14 (DBA): servicio TCPS y puerto de Oracle, y el certificado de la CA de cada base.
- N10 = b: reemplazada por N14 = c (sin trazas en el MVP), porque el SDK de X-Ray pierde el soporte el 2027-02-25.
- N14 = c: sin trazas distribuidas en el MVP; la correlación se hace con `request_id` (AD-33).
- N15 = a: el 99,9% mide la disponibilidad propia del servicio (NFR-A01).
- N16 = a: las alarmas las atiende el grupo de infraestructura de la OAS (insumo D15).
- N17 = b: la extensión de resiliencia sigue desactivada.
- N11 = a: requests 2.34 o superior; una sola función hace todas las llamadas, siempre con tiempo de espera. Cambia AD-08.
- N12 = b: flasgger sale del proyecto. `swagger/swagger.yml` sigue siendo la fuente y se publica en WSO2 AM. En local se ve con el contenedor oficial de Swagger UI, con versión fija, en `docker-compose.yml`. Cambia AD-13 y la lista de frameworks obligatorios del entorno técnico, como decidiste.
- N13 = a: ruff en todo el código y mypy estricto en `app/domain` y `app/application`, antes de cada commit y en Drone; un error detiene el pipeline.

## Lo que se toma de `firma_electronica_mid` (2026-11-25)
Detalle en `construction/recibos_service/nfr-requirements/firma-electronica-mid-analysis.md`. Se adoptan: `pyproject.toml` para los metadatos y la configuración de las herramientas, con las dependencias bloqueadas con hashes; el arranque que se detiene si falta configuración; el reciclado de los workers de gunicorn y su registro de accesos a stdout; Swagger 2.0, como el ejemplo del lineamiento; los pasos del pipeline institucional (revisión de la rama y de los commits, SonarQube, ECR, ECS y aviso por Telegram); el README y el `.gitignore`. No se adoptan las prácticas que chocan con decisiones aprobadas o con las reglas de seguridad (CORS abierto, llamadas sin tiempo de espera, errores con el texto de la excepción, dependencias sin hashes, imagen con root).

## Preguntas

### Pregunta N1 — Versión de Python
En C4 decidiste usar la última versión estable con soporte "al empezar U1 Code Generation". Hoy hay dos opciones.

A) Python 3.15 (salió el 9 de octubre de 2026; soporte hasta octubre de 2031). Las librerías con código compilado ya publican soporte para 3.15. Hay que instalar 3.15 en la máquina, que hoy tiene 3.14.10, y usar la imagen `python:3.15-slim`. Si al fijar las dependencias en Code Generation alguna no se instala en 3.15, se usa 3.14 y se deja escrito. Recomendada: es lo que decidiste en C4

B) Python 3.14 (salió en octubre de 2025; soporte hasta octubre de 2030). Lleva un año de arreglos, ya está en la máquina y todas las librerías la soportan

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "N1 a". Python 3.15, con 3.14 como respaldo si una dependencia no se instala

### Pregunta N2 — Tiempo de respuesta de un lote (RNF-1)
Todo el lote se procesa en una sola petición. Estimo entre 15 y 40 segundos para 1000 estudiantes: la mayor parte se va en cancelar y guardar la solicitud de cada estudiante en MySQL. El tiempo objetivo fija cuánto deben esperar gunicorn, el balanceador y WSO2 AM; el balanceador de AWS espera 60 segundos si no se cambia.

A) 1000 estudiantes en 60 segundos o menos en 95 de cada 100 lotes, y un lote de hasta 10 estudiantes en 5 segundos o menos. Los tiempos de espera de gunicorn, el balanceador y WSO2 AM suben a unos 2 minutos. Recomendada: cumple con margen lo que estimo, y las maquetas ya avisan que con muchos estudiantes la carga puede tardar

B) 1000 estudiantes en 120 segundos o menos; los tiempos de espera suben a unos 3 minutos

C) 1000 estudiantes en 30 segundos o menos; obliga a optimizar el guardado desde el principio, por ejemplo insertando en bloque

D) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "N2 a". 1000 estudiantes en 60 s o menos (95 de cada 100 lotes); hasta 10 estudiantes en 5 s o menos

### Pregunta N3 — Lote que pasa del tiempo previsto
Si un lote tarda más de lo previsto, por ejemplo porque MySQL está lento, alguno de los intermediarios corta la conexión. Las filas ya guardadas quedan guardadas, pero ARC no recibe el reporte y no sabe cuáles se subieron.

A) El servicio tiene un límite propio, menor que los tiempos de espera de los intermediarios. Al llegar a ese límite deja de procesar filas y responde con el reporte: las filas que no alcanzó aparecen como no subidas con un motivo nuevo ("No se alcanzó a procesar; vuelva a cargar esta fila"), y esas filas no cancelan nada. Recomendada: ARC siempre sabe qué se subió

B) Sin límite propio: si un intermediario corta la conexión, ARC ve un error y revisa en "Solicitados" qué quedó guardado

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "N3 a". Límite propio; las filas que no se alcanzan salen como no subidas con un motivo nuevo

### Pregunta N4 — Lotes al mismo tiempo
¿Cuántos lotes pueden estar procesándose a la vez en el momento de más carga, por ejemplo al inicio del semestre? Con ese número se calculan en NFR Design los procesos de gunicorn y las conexiones a las bases. Si no lo sabes, el DBA lo puede contar en `solicitudLote`, que guarda la fecha de cada lote. Sin un dato mejor, se diseña con A.

A) Hasta 3 a la vez

B) Hasta 10 a la vez

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "N4 a". Hasta 3 lotes a la vez

### Pregunta N5 — Dos lotes al mismo tiempo con el mismo estudiante
Cada fila cancela las solicitudes sin imprimir del estudiante y después guarda la nueva, en dos transacciones (AD-30). Si dos lotes con el mismo estudiante se procesan a la vez, las dos cancelaciones pueden ocurrir antes de los dos guardados, y el estudiante queda con dos solicitudes sin imprimir. Pasa también si se carga el mismo archivo en dos pestañas. El diseño funcional decía que quedaba la del último lote; eso solo se cumple con un control adicional.

A) Bloqueo por estudiante: antes de cancelar y guardar a un estudiante, el servicio toma en MySQL un bloqueo con su código y lo suelta al terminar esa fila. Los lotes corren en paralelo, y para un mismo estudiante queda la solicitud del lote que guarda de último. Recomendada

B) Un solo lote a la vez en todo el servicio: si llega otro mientras uno se procesa, responde "Hay otro lote en proceso. Intente en unos minutos." Es más simple, pero dos personas de ARC no pueden cargar al mismo tiempo

C) Sin control: se acepta el riesgo y ARC coordina las cargas. No recomendada

D) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "N5 a". Bloqueo por estudiante en MySQL

### Pregunta N6 — Disponibilidad en producción
El MVP va primero a test (15/12/2026). ¿Qué se espera en producción?

A) Dos tareas en ECS, en zonas de disponibilidad distintas: si una falla o se despliega una versión nueva, la otra sigue atendiendo. Sin recuperación ante desastres propia: se apoya en AWS y en las copias de seguridad de las bases que ya maneja el DBA. Objetivo: el servicio disponible el 99,5% del tiempo en días hábiles de 7:00 a 19:00. Recomendada

B) Una sola tarea, que cuesta menos: si falla, ECS la reinicia en uno o dos minutos y el lote que se estaba procesando se corta (lo guardado queda, pero ARC no recibe el reporte); cada despliegue interrumpe el servicio unos segundos

C) Servicio 24/7 con 99,9% de disponibilidad, alarmas fuera del horario laboral y alguien de turno

D) Other (please describe after [Answer]: tag below)

[Answer]: C. Respuesta del usuario: "N6 C". 24/7 con 99,9%, alarmas fuera del horario laboral y alguien de turno. Abre las aclaraciones N15, N16 y N17

### Pregunta N7 — Tamaño máximo del archivo
El supuesto A1 fijó 10 MB. Una plantilla de 1000 filas pesa menos de 0,5 MB; las plantillas oficiales, con pocas filas, pesan entre 10 y 13 KB. Un límite más bajo reduce la memoria de cada carga y el margen para archivos armados para tumbar el servicio.

A) 2 MB. Recomendada

B) 10 MB, como en A1

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "N7 a". 2 MB

### Pregunta N8 — Cuánto tiempo se guardan los archivos y los registros
Los archivos cargados en S3 tienen códigos de estudiantes. Los registros de auditoría y de la aplicación, en CloudWatch Logs, dicen quién cargó cada lote y qué solicitudes se crearon y se cancelaron. SECURITY-14 pide guardar los registros al menos 90 días. Si la tabla de retención documental de la Universidad fija otro plazo, se usa ese (D7).

A) Archivos y registros, 1 año; después se borran solos. Recomendada: cubre los reclamos de un año académico

B) Archivos y registros, 90 días

C) Archivos, 5 años, y registros, 1 año, si ARC necesita el archivo como soporte de los recibos de varios años

D) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "N8 a". Archivos y registros, 1 año

### Pregunta N9 — Cifrado de las conexiones a Oracle y MySQL (SECURITY-01)
El driver de Oracle en modo thin, sin el cliente de Oracle en la imagen, solo cifra con TLS; no soporta el cifrado nativo de Oracle (NNE). ¿Cómo se cifran hoy las conexiones a las bases?

A) Oracle acepta TLS (TCPS) y MySQL acepta TLS. Se usa el modo thin, y las dos conexiones exigen TLS y verifican el certificado del servidor. Recomendada

B) Oracle solo tiene el cifrado nativo (NNE): se usa el modo thick, con el cliente de Oracle (Instant Client) en la imagen. La imagen crece y hay más paquetes que mantener al día

C) No lo sé: el DBA lo confirma antes de U1 Infrastructure Design (insumo nuevo D14). Mientras tanto se diseña con A

D) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "N9 a". Oracle y MySQL aceptan TLS; modo thin

### Pregunta N10 — Trazas (RNF-5)
El SDK de X-Ray que estaba en el diseño entró en mantenimiento el 25 de febrero de 2026: solo recibe arreglos de seguridad, y AWS recomienda OpenTelemetry. `utils_oas` usa el SDK de X-Ray con el daemon institucional.

A) OpenTelemetry: el servicio envía las trazas a un colector (ADOT Collector o el agente de CloudWatch) que infraestructura agrega a la tarea de ECS, y el colector las manda a X-Ray. Si el colector no está listo para test, las trazas se apagan por configuración y el servicio funciona igual. Recomendada

B) El SDK de X-Ray con el daemon institucional, como `utils_oas`. Funciona sin cambios de infraestructura, pero el SDK ya no recibe mejoras

C) Other (please describe after [Answer]: tag below)

[Answer]: B. Respuesta del usuario: "N10 b". SDK de X-Ray con el daemon institucional. Choca con SECURITY-09 y con N1: aclaración N14

### Pregunta N11 — Cliente HTTP (AD-08)
httpx, el cliente elegido para llamar a WSO2 y a "parametros", no publica versiones desde diciembre de 2024. SECURITY-10 no permite dependencias abandonadas, así que hay que cambiarlo.

A) requests, de la PSF: madura, con versiones frecuentes y ya permitida en el entorno técnico. No trae tiempo de espera por defecto, así que todas las llamadas pasan por una función propia que siempre lo pone. Recomendada

B) httpx2, el fork de httpx que mantiene Pydantic desde 2026: el mismo uso que httpx, pero es un proyecto nuevo

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "N11 a". requests

### Pregunta N12 — flasgger
El entorno técnico pone flasgger como obligatorio para la documentación Swagger (L6, L41). Su última versión es de mayo de 2023. Solo se usa en local, para ver `swagger/swagger.yml` (AD-13).

A) Se queda solo como dependencia de desarrollo: muestra la documentación en local y no se instala en la imagen de producción. Cumple el lineamiento y no lleva a producción una librería sin mantenimiento. Recomendada

B) Se quita: `swagger/swagger.yml` sigue siendo la fuente y se publica en WSO2 AM; en local se ve con el contenedor oficial de Swagger UI en `docker-compose.yml`. Cambia la lista de frameworks obligatorios del entorno técnico

C) Other (please describe after [Answer]: tag below)

[Answer]: B. Respuesta del usuario: "N12 b". Se quita flasgger; Swagger UI en un contenedor para local

### Pregunta N13 — Revisión automática del código
Los lineamientos piden SonarQube en Drone, con 0 bugs, 0 vulnerabilidades y máximo 50% de duplicación.

A) Además de SonarQube: ruff (estilo y errores comunes) en todo el código y mypy (tipos) en `app/domain` y `app/application`, en Drone y antes de cada commit; un error detiene el pipeline. Recomendada: encuentra errores antes de llegar a Sonar y casi no agrega tiempo

B) Solo SonarQube, como piden los lineamientos

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "N13 a". ruff y mypy además de SonarQube

## Resultado (2026-11-25T18:31:09Z)
Artefactos en `aidlc-docs/construction/recibos_service/nfr-requirements/`: `nfr-requirements.md` (requisitos NFR-P, NFR-C, NFR-A, NFR-S, NFR-R, NFR-O, NFR-M, NFR-T y NFR-U; decisiones DN-01 a DN-03; cumplimiento de las extensiones), `tech-stack-decisions.md` (versiones, archivos del repositorio y PBT-09) y `firma-electronica-mid-analysis.md` (referencia).
Aprobado por el usuario el 2026-11-25T18:44:18Z: "Continuar a la siguiente etapa - Aprobar los requisitos no funcionales y pasar a NFR Design de U1".
