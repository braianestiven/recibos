# Unidades de trabajo

- Etapa: INCEPTION → Units Generation (profundidad mínima)
- Fecha: 2026-11-24
- Base: `application-design.md` (AD-01 a AD-28), `api-contract.md`, `plans/execution-plan.md`
- Estado: **pendiente de aprobación del usuario**

## 1. Resumen

El sistema se divide en dos unidades. Cada una es un servicio desplegable en su propio contenedor de ECS.

| Unidad | Carpeta | Qué es | Despliegue |
|---|---|---|---|
| U1 | `recibos_service/` | API Flask con Clean Architecture | Imagen en ECR → servicio ECS `recibos_service_test` (cluster `test`) y `recibos_service_prod` (cluster `oas`); se publica en WSO2 AM |
| U2 | `recibos_mf/` | Microcliente Angular con single-spa, que monta el root institucional | Imagen con un servidor estático en ECR → servicio ECS; el root institucional lo registra en su import map |

Orden de construcción: U1 completa (diseño y código) y después U2. U2 se construye contra `api-contract.md`, así que no espera a que U1 esté desplegada.

## 2. U1 — `recibos_service`

| Aspecto | Detalle |
|---|---|
| Propósito | Cargar y procesar lotes de forma síncrona, consultar el historial y dejar la auditoría |
| Responsabilidades | Validar archivo y plantilla; validar estudiantes en Oracle; calcular cuotas, exenciones y conceptos; cancelar las solicitudes sin imprimir en su propia transacción y escribir cada solicitud nueva en otra (AD-30); leer reglas de "parametros"; autenticar y autorizar cada petición; registrar la auditoría |
| Componentes | `app/domain`, `app/application`, `app/infrastructure`, `app/interfaces` (`components.md`) |
| Historias | US-01 y US-02 (lado servidor), US-03 a US-15 |
| Tecnología | Python 3.15 (N1; 3.14 de respaldo), Flask con Blueprints, gunicorn, SQLAlchemy 2.1 Core (python-oracledb en modo thin con TLS, PyMySQL), xlrd 2.0, pydantic 2.14 o superior, requests, boto3 y flask-cors. Sin flasgger (N12), sin SDK de X-Ray (N14) y sin httpx (N11). Detalle: `construction/recibos_service/nfr-requirements/tech-stack-decisions.md` |
| Pruebas | pytest y pytest-cov (≥ 80%; 100% en `app/domain`). Hypothesis para las pruebas basadas en propiedades (confirmado en NFR Requirements, PBT-09). ruff y mypy antes de cada commit y en Drone (N13) |
| Etapas de Construction | Functional Design (completa), NFR Requirements (estándar), NFR Design (estándar), Infrastructure Design (mínima), Code Generation |

Orden interno de construcción, para que los insumos pendientes no frenen el resto:

1. `app/domain`: reglas puras con sus pruebas, incluidas las de propiedades. Ningún insumo externo la bloquea; los datos de prueba de pregrado y SMLV se ajustan cuando lleguen D1 y D2.
2. `app/application`: casos de uso y puertos, probados con dobles de los puertos.
3. `app/interfaces`: Flask, sobre de respuesta, middlewares (autenticación, auditoría, cabeceras, CORS, errores) y `swagger/swagger.yml`.
4. `app/infrastructure`: primero xlrd, S3, SSM, reloj y WSO2; después Oracle; al final MySQL (D4) y "parametros" (D6, D10).

Definición de terminado:
- Las historias listas están implementadas y probadas. Las bloqueadas, hasta donde lo permite el insumo, con el hueco marcado.
- Cobertura de al menos 80%, con 100% en `app/domain`; gate de SonarQube aprobado (0 bugs, 0 vulnerabilidades, máximo 50% de duplicación).
- Cumplimiento de las extensiones activas: seguridad y pruebas basadas en propiedades en modo parcial.
- `swagger/swagger.yml` coincide con `api-contract.md`; README con el contenido mínimo de L48.

## 3. U2 — `recibos_mf`

| Aspecto | Detalle |
|---|---|
| Propósito | Interfaz de ARC para cargar lotes, ver el resumen y consultar el historial |
| Responsabilidades | Seleccionar y enviar el archivo sin permitir un segundo envío mientras procesa; mostrar el resumen y los rechazados; mostrar el historial paginado; interpretar el sobre de respuesta y los errores (incluido 429 de WSO2 AM); usar el token que entrega el core sin guardarlo |
| Componentes | `core/`, `shared/`, `features/lotes/` (`components.md`) |
| Historias | US-01 (interfaz), US-02 (interfaz), US-12, US-13 |
| Tecnología | Angular y single-spa-angular desde `oas_cliente` (`feature/clientes_nuevos`), Angular Material con el tema del root, TypeScript 5.x. Versiones de Angular y Node con soporte vigente (OQ-T-1, SECURITY-09) |
| Pruebas | Las que trae `oas_cliente` (`*.spec.ts`). Pruebas basadas en propiedades solo si U2 tiene funciones puras o conversiones de ida y vuelta; si no, se marca N/A con su razón en U2 NFR Requirements |
| Etapas de Construction | Functional Design (mínima), NFR Requirements (mínima), Infrastructure Design (mínima), Code Generation. NFR Design se omite |

Definición de terminado:
- US-01, US-02, US-12 y US-13 funcionan contra `api-contract.md`.
- Sin `localStorage` ni cookies para el token o datos personales; sin HTML armado a mano; sin páginas de ejemplo de la plantilla.
- El servidor estático pone las cabeceras de seguridad a lo que sirve y no lista directorios (AD-27).
- `package-lock.json` versionado; gate de SonarQube aprobado.

## 4. Organización del código (Q1 = A)

```text
recibos/                          # raíz del workspace (repositorio braianestiven/recibos)
+-- aidlc-docs/                   # documentación de AI-DLC; nunca código
+-- codigo-fuente/                # sistema PHP, lineamientos y utils_oas; no se modifica
+-- Product-Definition/           # entradas de Discovery
+-- recibos_service/              # U1, raíz de su futuro repositorio
|   +-- api.py, conf/, swagger/, app/, tests/
|   +-- Dockerfile, docker-compose.yml, .drone.yml, sonar-project.properties
|   +-- pyproject.toml, requirements.txt y requirements-dev.txt (versiones exactas con hashes), .pre-commit-config.yaml
|   +-- .gitignore, .env.example, README.md
+-- recibos_mf/                   # U2, raíz de su futuro repositorio (desde oas_cliente)
    +-- src/app/core/, src/app/shared/, src/app/features/lotes/
    +-- Dockerfile, docker-compose.yml, .drone.yml, sonar-project.properties
    +-- package.json, package-lock.json
    +-- .gitignore, README.md
```

Reglas:
- Cada carpeta funciona sola: se puede copiar a su repositorio institucional (`udistrital/recibos_service`, `udistrital/recibos_mf`) sin depender del resto del workspace. Para conservar el historial se usa `git subtree split --prefix recibos_service` (o `recibos_mf`).
- `codigo-fuente/` no se modifica.
- Ningún secreto entra en las carpetas: solo `.env.example` con los nombres de las variables, sin valores. El `.gitignore` de la raíz ya excluye `.env`, `node_modules/`, `.venv/` y `__pycache__/`. Cada unidad tiene además el suyo, para cuando sea su propio repositorio.
- Un cambio en `api-contract.md` obliga a revisar las dos unidades.

## 5. Reglas de seguridad por unidad

Extensión de seguridad activa. Dónde se implementa o verifica cada regla:

| Regla | U1 | U2 | Etapa |
|---|---|---|---|
| SECURITY-01 Cifrado | TLS hacia Oracle y MySQL; S3 cifrado, con política que rechaza peticiones sin TLS; SSM `SecureString` | No guarda datos | NFR Design, Infrastructure Design |
| SECURITY-02 Registros de acceso | Balanceador y WSO2 AM (AD-28) | Balanceador del servidor estático | Infrastructure Design |
| SECURITY-03 Registro de aplicación | JSON con nivel y `request_id` (AD-24) | Registros de acceso del servidor estático, en JSON | NFR Design (U1), Infrastructure Design (U2) |
| SECURITY-04 Cabeceras HTML | No sirve HTML en ambientes desplegados (AD-13); cabeceras institucionales en todas las respuestas | Cabeceras en el servidor estático; el HTML principal lo sirve el root institucional | Code Generation, Infrastructure Design |
| SECURITY-05 Validación de entradas | pydantic, firma y tamaño del archivo, nombre del archivo, parámetros enlazados | Validación básica en el formulario; el control real está en U1 | Functional Design, Code Generation |
| SECURITY-06 Mínimo privilegio | Oracle solo lectura; MySQL: `solicitud*` y solo lectura de `exencion` (F11); solo lectura de la tabla de festivos de weboffice (F9, D5); rol de tarea sin comodines | Sin permisos de AWS ni acceso a datos | Infrastructure Design |
| SECURITY-07 Red | API solo accesible por WSO2 AM; bases solo desde las tareas de U1 | Solo el balanceador público en 443 | Infrastructure Design |
| SECURITY-08 Control de acceso | Token en cada petición, sin caché; rol en el backend; CORS explícito (AD-09, AD-14) | No decide permisos | Code Generation |
| SECURITY-09 Endurecimiento | Imagen mínima, usuario sin privilegios, sin documentación desplegada (AD-27) | Versión de Angular con soporte; sin páginas de ejemplo; sin listado de directorios | NFR Requirements, Code Generation |
| SECURITY-10 Cadena de suministro | Versiones exactas con hashes, escaneo y SBOM (AD-26) | `package-lock.json`, `npm ci`, escaneo y SBOM | Code Generation, Infrastructure Design |
| SECURITY-11 Diseño seguro | Throttling (AD-23), casos de abuso (§9 del diseño), seguridad aislada en middlewares | No carga scripts externos sin SRI | Functional Design, NFR Design |
| SECURITY-12 Autenticación | Delegada en WSO2 IS; sin credenciales en el código | Sesión del core; no guarda el token | N/A para contraseñas, MFA y bloqueo por intentos (los maneja WSO2 IS) |
| SECURITY-13 Integridad | xlrd y pydantic como lectores seguros; auditoría con estado antes y después (AD-25); dependencias con hashes | Integridad del `package-lock.json` | Code Generation |
| SECURITY-14 Alertas | Alarmas por 401, 403 y 5xx, atendidas 24/7 por el grupo de infraestructura (N6, N16); retención de 365 días (N8); sin permiso de borrado (AD-28) | Retención de los registros de acceso | Infrastructure Design |
| SECURITY-15 Excepciones | Manejador global, falla cerrada (AD-22), rollback por estudiante | Manejo de errores HTTP sin mostrar detalles internos | Code Generation |

## 6. Reglas de pruebas basadas en propiedades por unidad (modo parcial)

| Regla | U1 | U2 |
|---|---|---|
| PBT-02 Ida y vuelta | Conversión fecha ↔ timestamp Unix (America/Bogota) | Por evaluar en U2 NFR Requirements |
| PBT-03 Invariantes | Los porcentajes suman 100; la fecha extraordinaria no cae en festivo y es al menos 8 días después de la ordinaria; una solicitud lleva como máximo un descuento, y una fila con más de uno no se sube (C2); el descuento y la votación de una solicitud suman como máximo 100%, sin contar la Secretaría (C7, F14); la votación aparece como máximo una vez; las exenciones van en el orden votación, descuento y Secretaría. Lista completa: `construction/recibos_service/functional-design/business-logic-model.md` §9 | Por evaluar |
| PBT-07 Generadores | Generadores de filas de plantilla, fechas, porcentajes y reglas que respetan los límites del negocio | — |
| PBT-08 Reducción y reproducibilidad | Hypothesis con semilla registrada en CI | — |
| PBT-09 Framework | Hypothesis (confirmado en U1 NFR Requirements) | fast-check, solo si aplica |

Las propiedades exactas se identifican en U1 Functional Design. En modo parcial PBT-01 es orientativa, pero PBT-03 exige que cada invariante documentado tenga su prueba.
