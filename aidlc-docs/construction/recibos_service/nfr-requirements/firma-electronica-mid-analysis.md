# Referencia: `firma_electronica_mid`, API Python de la OAS

- Etapa: CONSTRUCTION → U1 `recibos_service` → NFR Requirements (2026-11-25T18:25:20Z)
- Origen: pedido del usuario: "además mira esta api en python para ver cosas generales que usan esas apis"
- Repositorio: `/home/Lazius/Documentos/go/src/github.com/udistrital/firma_electronica_mid`, fuera del workspace y leído sin modificarlo. Rama `release/0.0.1`, commit `05cb420` del 2026-02-16, 25 archivos
- No se copió código. El archivo `.env` local no está versionado y no se leyeron sus valores

## 1. Qué es
Una API MID en Flask que firma documentos PDF, los registra en `documentos_crud` y los sube al gestor documental. Se despliega en ECS con el pipeline institucional de Drone.

## 2. Prácticas generales frente a `recibos_service`

| Tema | `firma_electronica_mid` | `recibos_service` | Base de la decisión |
|---|---|---|---|
| Estructura | `api.py`, `conf/`, `routers/`, `controllers/`, `models/`, `swagger/` y `tests/` en la raíz | La misma raíz (`api.py`, `conf/`, `swagger/`, `tests/`); el código va en `app/`, con Clean Architecture | RNF-4, `unit-of-work.md` §4 |
| Dependencias | `pyproject.toml` con versiones exactas, salvo gunicorn; sin archivo de bloqueo ni hashes | Se adopta `pyproject.toml` para los metadatos, `requires-python` y la configuración de las herramientas. Las versiones se bloquean con hashes en `requirements.txt` y `requirements-dev.txt` (pip-tools) | AD-26, SECURITY-10 |
| Configuración | Variables de entorno; `checkEnv()` detiene la API al arrancar si falta alguna | Se adopta: si falta una variable o un secreto de SSM, el proceso no arranca y lo deja en el registro. Nombres `RECIBOS_SERVICE_*` | L7, L33, SECURITY-15 |
| Ambiente | Variable `ENV`; en `dev` abre CORS a todos los orígenes y publica la documentación | `RECIBOS_SERVICE_ENV` (dev, test o prod). CORS con lista explícita en todos los ambientes, y el servicio no publica documentación | AD-14, N12 |
| CORS | `CORS(api_bp)` sin configuración, que permite cualquier origen, más una expresión regular por ruta | Lista explícita de orígenes por ambiente, sin comodines | AD-14, SECURITY-08 |
| Documentación | flask-restx genera Swagger 2.0 y lo muestra en `/swagger` solo en dev; `swagger.yml` y `swagger.json` en el repositorio | `swagger/swagger.yml` en Swagger 2.0, como el ejemplo del lineamiento (`refactorizacion_api_flask.md` §3.7), escrito a partir de `api-contract.md`. En local se ve con el contenedor de Swagger UI | N12 = b, L41 |
| Rutas | `/v1/firma_electronica` en snake_case; el blueprint se registra dos veces, en `/api` y en la raíz | `/v1/lotes`, en plural y kebab-case | L30 a L34 |
| Health check | `GET /` → `{"Status": "Ok", "Code": "200"}` | `GET /` → `{"status": "ok"}` y `GET /health` → `{"status": "UP"}`; el balanceador solo revisa el código 200 | AD-12 |
| Errores | JSON propio (`Status`, `Code`); los 500 devuelven el texto de la excepción | Sobre `{Success, Status, Message, Data}` y mensajes genéricos | AD-04, SECURITY-15 |
| Llamadas a otras APIs | `requests` sin tiempo de espera y sin token | `requests` con tiempo de espera en todas las llamadas. Si la llamada a "parametros" lleva el token del usuario sigue pendiente en D6 (supuesto A11); esta API llama a las demás sin token | N11 = a, D6 |
| Registro | `logging.error` sin configuración, más el registro de accesos de gunicorn | Registro JSON con `request_id`, más la auditoría por petición | AD-10, AD-24 |
| gunicorn | `entrypoint.sh`: 2 workers, reciclado cada 200 peticiones con variación de 50, tiempo de espera de 50 s, registro de accesos a stdout, puerto `API_PORT` (8080 por defecto) | Se adoptan el reciclado de los workers y el registro de accesos a stdout, en `gunicorn.conf.py`. El tiempo de espera sale de N2 y N3. Puerto `RECIBOS_SERVICE_PORT`, 8080 por defecto, a confirmar con infraestructura. Sin `entrypoint.sh` | AD-17, N2, N3 |
| Imagen | `python:3.11-slim` con gcc, make y otras herramientas de compilación en la imagen final; corre como root | `python:3.15-slim` con versión fija; la compilación va en una etapa aparte; la imagen final no tiene herramientas de compilación y corre con un usuario sin privilegios | N1, AD-27, SECURITY-09 |
| Pipeline | Revisión del nombre de la rama y de los commits (imagen `jjvargass/qa_develoment`), SonarQube, publicación en ECR con el commit y la etiqueta `release` o `latest`, `aws ecs update-service` en el cluster `test` (ramas `release/*`) u `oas` (`master`), servicios `<repositorio>_test` y `<repositorio>_prod`, aviso por Telegram. No corre pruebas ni revisa dependencias | Se adoptan los mismos pasos, nombres de servicios y clusters. Se agregan las pruebas con cobertura, ruff, mypy, pip-audit y la SBOM, y las imágenes del pipeline con versión fija | L43, AD-26, N13 |
| SonarQube | Configurado con patrones de Go (`*_test.go`), así que no reconoce las pruebas de Python ni la cobertura | Configuración de Python: fuentes en `app/`, pruebas en `tests/` y reporte `coverage.xml` | RNF-6 |
| Pruebas | pytest con `unittest.mock` y `parametrize`; sin medir cobertura | pytest, pytest-cov y Hypothesis; dobles de los puertos | RNF-6, PBT-09 |
| README | Tecnologías, variables de entorno, ejecución y estado de CI con el distintivo de `hubci.portaloas.udistrital.edu.co` | Se adopta la misma estructura, con lo que pide L48 | L48 |
| `.gitignore` | Plantilla de Python de GitHub, que incluye `.env`, `.hypothesis/` y `coverage.xml` | Se adopta | — |

## 3. Hallazgos de seguridad de `firma_electronica_mid`
No afectan a `recibos_service`. Se dejan para informarlos a sus responsables, como TD-17 con weboffice.
- `CORS(api_bp)` sin configuración permite cualquier origen y anula la restricción que se pone en cada ruta.
- Los errores 500 devuelven al cliente el texto de la excepción.
- Las llamadas con `requests` no tienen tiempo de espera.
- `flask-cors==5.0.0` tiene vulnerabilidades que se corrigieron en la versión 6.0.0 ([Tenable](https://www.tenable.com/plugins/cloud-security/465141)).
- Las dependencias no tienen hashes, gunicorn no tiene versión fija y hay librerías repetidas (`pdfminer` y `pdfminer.six`, `PyPDF2` y `pypdf`).
- La imagen usa Python 3.11, corre como root e incluye herramientas de compilación.
- El pipeline usa imágenes con la etiqueta `latest` y no corre las pruebas.

El contenido de la fuente externa se resumió con otras palabras, por las restricciones de licencia.

## 4. Lo que cambia en `recibos_service`
- `pyproject.toml` con los metadatos, `requires-python` y la configuración de ruff, mypy, pytest y coverage, junto con los archivos de bloqueo con hashes.
- El arranque se detiene si falta configuración.
- `gunicorn.conf.py` con reciclado de workers y registro de accesos.
- `swagger/swagger.yml` en Swagger 2.0.
- Los pasos del pipeline institucional: revisión de la rama y de los commits, y aviso por Telegram.
- README y `.gitignore` con la misma estructura.

Ninguno cambia los requisitos ni el diseño aprobados. Se llevan a `tech-stack-decisions.md` y a Infrastructure Design.
