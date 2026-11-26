# Decisiones de tecnología — U1 `recibos_service`

- Etapa: CONSTRUCTION → U1 `recibos_service` → NFR Requirements (2026-11-25)
- Fuentes: respuestas N1 a N17, `technical-environment.md`, AD-07 a AD-33, la referencia `firma-electronica-mid-analysis.md` y las versiones revisadas en la web el 2026-11-25 (§7)
- "Línea" es la serie de versiones que se usa. La versión exacta, con su hash, se fija en Code Generation con pip-tools (AD-26): la última de la línea que se instale en Python 3.15
- Requisitos no funcionales: `nfr-requirements.md`
- Ajustado el 2026-11-25 en U1 NFR Design: línea de gunicorn (§1)

## 1. Lenguaje y ejecución

| Componente | Decisión | Línea | Razón | Descartado |
|---|---|---|---|---|
| Python | 3.15 | 3.15.x; imagen `python:3.15-slim` con la versión exacta | C4 y N1: la última versión estable, publicada el 2026-10-09, con soporte hasta octubre de 2031. Las librerías con código compilado ya la soportan | 3.14, que queda de respaldo si una dependencia no se instala en 3.15; si se usa, se deja escrito |
| Servidor de aplicación | gunicorn con workers de hilos, configurado en `gunicorn.conf.py` | 27.x (pide Python 3.12 o superior). *Corregido en NFR Design: decía 26.x, pero la 27.0.0 salió el 2026-11-10 y la 27.0.1 el 2026-11-12* | L6. Los hilos sirven para lotes largos que pasan casi todo el tiempo esperando a las bases. Reciclado de workers y registro de accesos a stdout, como `firma_electronica_mid` | El servidor de desarrollo de Flask, prohibido fuera de local |
| Zona horaria | America/Bogota con `zoneinfo` | Biblioteca estándar | A10 | — |

## 2. Librerías de producción (`requirements.txt`)

| Librería | Uso | Línea | Razón | Descartado |
|---|---|---|---|---|
| Flask | API y Blueprints | 3.1.x | L5 | — |
| flask-cors | CORS con lista explícita de orígenes | 6.0.x | AD-14. La 6.0.5 no tiene vulnerabilidades conocidas; la 5.x sí | — |
| pydantic | Validación de entradas y de respuestas externas | 2.14 o superior | SECURITY-05. La 2.14 es la primera con soporte para Python 3.15 | — |
| SQLAlchemy (Core) | Consultas con parámetros enlazados y transacciones | 2.1.x (pide Python 3.11 o superior) | AD-07 | El ORM, que no hace falta |
| python-oracledb | Oracle en modo thin, por TCPS | 26.x | N9. La 26.0 agregó soporte para Python 3.15 | cx_Oracle (prohibido); el modo thick, que no hace falta porque Oracle acepta TLS |
| PyMySQL | MySQL con TLS | 1.2.x | AD-07: no compila nada. Su registro de cambios de 2026 corrige una inyección SQL que solo afecta a juegos de caracteres asiáticos; la conexión usa utf8mb4 | mysqlclient |
| xlrd | Lectura de las plantillas `.xls` | 2.0.x | El lector de BIFF en Python puro; la 2.0.2 no tiene vulnerabilidades conocidas. No ejecuta macros ni fórmulas | pandas (prohibido) |
| requests | `/oauth2/userinfo` y "parametros" | 2.34.x | N11. La mantiene la PSF. Una sola función hace todas las llamadas, con tiempo de espera y conexiones reutilizadas | httpx (sin versiones desde diciembre de 2024); httpx2 (fork nuevo) |
| boto3 | S3 y SSM | La línea vigente | AD-26 | — |

No se usan: aws-xray-sdk (N14 = c), flasgger (N12 = b), httpx (N11), cachetools (AD-26) ni pandas.

## 3. Herramientas de desarrollo y pruebas (`requirements-dev.txt`)
Ninguna se instala en la imagen de producción.

| Herramienta | Uso | Línea | Razón |
|---|---|---|---|
| pytest | Pruebas unitarias | 9.x | RNF-6; la referencia también lo usa |
| pytest-cov | Cobertura y umbrales | La vigente | NFR-T01 |
| Hypothesis | Pruebas basadas en propiedades | 6.x | PBT-09 (§4) |
| ruff | Estilo y errores comunes | La vigente | N13 |
| mypy | Tipos, estricto en `app/domain` y `app/application` | La vigente | N13 |
| pre-commit | ruff y mypy antes de cada commit | La vigente | N13 |
| pip-tools | Bloquear las versiones con hashes | La vigente | AD-26 |
| pip-audit | Vulnerabilidades de las dependencias | La vigente | SECURITY-10 |
| cyclonedx-bom | SBOM en formato CycloneDX | La vigente | SECURITY-10 |
| python-dotenv | Variables desde `.env` en local | La vigente | L7 |

## 4. Framework de pruebas basadas en propiedades (PBT-09)

| Lo que pide PBT-09 | Hypothesis |
|---|---|
| Generadores propios para los tipos del dominio | Estrategias compuestas (`@st.composite`) para filas de cada plantilla, fechas, porcentajes, reglas y contextos de Oracle |
| Reducción automática de los casos que fallan | Incluida |
| Semilla reproducible | Imprime la semilla y el caso mínimo cuando una prueba falla; en Drone se registra la semilla (PBT-08, Build and Test) |
| Integración con el ejecutor de pruebas | Plugin de pytest |
| Dependencia del proyecto | `[project.optional-dependencies].dev` de `pyproject.toml`, bloqueada en `requirements-dev.txt` |

Perfiles: `dev`, con pocas iteraciones para correr rápido en la máquina, y `ci`, con más iteraciones y sin límite de tiempo por caso. Los valores se fijan en Code Generation.

## 5. Archivos del repositorio

| Archivo | Contenido | Origen |
|---|---|---|
| `pyproject.toml` | Metadatos, `requires-python = ">=3.15,<3.16"`, dependencias directas, dependencias de desarrollo y la configuración de ruff, mypy, pytest y coverage | AD-26, N13, referencia |
| `requirements.txt` y `requirements-dev.txt` | Versiones exactas con hashes, generadas con `pip-compile --generate-hashes` desde `pyproject.toml` | AD-26 |
| `.pre-commit-config.yaml` | ruff y mypy | N13 |
| `gunicorn.conf.py` | Workers, hilos, tiempo de espera de 120 s o más, reciclado de workers y registro de accesos; valores en `nfr-design/logical-components.md` §2.1 | AD-17, N2, N3 |
| `Dockerfile` | Dos etapas: una instala con `--require-hashes` y la final copia lo instalado, sin herramientas de compilación y con un usuario sin privilegios | AD-27, N1 |
| `docker-compose.yml` | El servicio y, solo en local, el contenedor oficial de Swagger UI (`swaggerapi/swagger-ui`, versión fija) que lee `swagger/swagger.yml` | N12 |
| `swagger/swagger.yml` | Swagger 2.0, como el ejemplo del lineamiento | AD-13, L41 |
| `sonar-project.properties` | Configuración de Python: fuentes en `app/`, pruebas en `tests/` y `coverage.xml` | NFR-M03 |
| `.drone.yml` | Los pasos del pipeline institucional, más las pruebas con cobertura, ruff, mypy, pip-audit y la SBOM; imágenes con versión fija | L43, AD-26 |
| `.gitignore`, `.env.example`, `README.md` | Plantilla de Python de GitHub; nombres de las variables sin valores; contenido de L48 | L48, referencia |

## 6. Lo que se verifica al empezar Code Generation
- Que cada librería se instale en Python 3.15 desde un wheel, sin compilar en la imagen final. Si alguna no lo hace, todo el proyecto pasa a Python 3.14 y se deja escrito.
- Que Python 3.15 esté instalado en la máquina de desarrollo; hoy tiene 3.14.10.
- Que pip-audit no reporte vulnerabilidades en las versiones fijadas.

## 7. Fuentes (revisadas el 2026-11-25)
- Python 3.15: [python.org](https://www.python.org/downloads/release/python-3150/) y [novedades de 3.15](https://docs.python.org/3/whatsnew/3.15.html).
- Soporte de Python 3.15: [pydantic 2.14](https://pydantic.dev/articles/pydantic-v2-14-release), [python-oracledb](https://python-oracledb.readthedocs.io/en/latest/release_notes.html), [SQLAlchemy 2.1](https://www.sqlalchemy.org/docs/21/changelog/migration_21.html) y [gunicorn](https://gunicorn.org/install/).
- python-oracledb en modo thin y el cifrado nativo de Oracle: [documentación](https://python-oracledb.readthedocs.io/en/stable/user_guide/initialization.html).
- Fin del soporte del SDK y del daemon de X-Ray (2027-02-25): [AWS](https://docs.aws.amazon.com/xray/latest/devguide/document-history.html); compatibilidad del SDK para Python: [PyPI](https://pypi.org/project/aws-xray-sdk/).
- httpx: [PyPI](https://pypi.org/project/httpx/); requests: [GitHub](https://github.com/psf/requests/releases).
- flasgger: [PyPI](https://pypi.org/project/flasgger/); xlrd: [PyPI](https://pypi.org/project/xlrd/2.0.2/); flask-cors: [Sonatype](https://guide.sonatype.com/component/pypi/flask-cors/6.0.5/vulnerabilities).
- PyMySQL: [registro de cambios](https://github.com/PyMySQL/PyMySQL/blob/main/CHANGELOG.md); pytest: [GitHub](https://github.com/pytest-dev/pytest/releases); Hypothesis: [PyPI](https://pypi.org/project/hypothesis/); Flask: [GitHub](https://github.com/pallets/flask/releases).
- gunicorn 27.0 y 27.0.1 (revisado en U1 NFR Design): [PyPI](https://pypi.org/project/gunicorn/) y [registro de cambios](https://github.com/benoitc/gunicorn/blob/master/docs/content/news.md).

El contenido de las fuentes se resumió con otras palabras, por las restricciones de licencia.
