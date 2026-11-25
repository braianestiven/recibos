# Stack tecnológico

- Etapa: INCEPTION → Reverse Engineering (2026-11-25)
- Describe lo que hay en el workspace. El stack del sistema nuevo es una restricción ya decidida en `Product-Definition/technical-environment.md`; aquí solo se indica hacia dónde va cada pieza

## Lenguajes de programación

| Lenguaje | Versión | Uso | Destino |
|---|---|---|---|
| PHP | 5.x a 7.x (probable, no declarada) | `weboffice`. Indicios: etiquetas cortas `<?`, `utf8_encode` y `utf8_decode`, parámetros opcionales antes de obligatorios (R13) | Se retira |
| SQL de Oracle | No declarada | Consultas a `mntac` y funciones PL/SQL `fua_verifica_evento`, `fua_verifica_diferido` | Se mantiene, solo lectura |
| SQL de MySQL | No declarada | Tablas `solicitud*`, `exencion`, `fechaPagoFacultad`; nombres entre comillas invertidas | Se mantiene |
| HTML, CSS y JavaScript | — | Formularios y resumen; tema `basico`; `funciones.js` (`control_vacio`) | Angular en `recibos_mf` |
| Go | 1.26.0 (`go.mod`) | `utils_oas` | No se usa en el sistema nuevo; solo sus contratos |

## Frameworks

| Framework | Versión | Propósito | Destino |
|---|---|---|---|
| Framework propio de weboffice (patrón de bloques) | Sin versión; el bloque declara `0.0.0.2` (`bloque.php`, revisión del 19 de enero de 2009) | Enrutamiento, sesión, conexiones, carga de archivos | Flask con Blueprints |
| Beego | v1.12.3 | Base de `utils_oas` | No aplica (Python) |
| Flask, NestJS, Serverless, Angular con single-spa | Las que citan los lineamientos | Guías de `lineamientos_oas` | Flask y Angular con single-spa (L2, L5) |

## Librerías

| Librería | Versión | Propósito | Destino |
|---|---|---|---|
| `Spreadsheet_Excel_Reader` (php-excel-reader) | Desconocida | Leer `.xls` (BIFF) | xlrd 2.x |
| AWS SDK for Go v2 | v1.48.0 (`config` v1.33.21, `ssm` v1.83.0) | SSM en `utils_oas` | boto3 |
| AWS X-Ray SDK for Go | v2.0.5 | Trazas en `utils_oas` | aws-xray-sdk para Python |
| `go-playground/validator` | v10.30.6 | Validación en `formatdata` | pydantic |
| `xuri/excelize` y `phpdave11/gofpdf` | v2.10.1 y v1.4.3 | `xlsx2pdf` | No aplica |
| `lib/pq`, `mongo-driver` | v1.12.3, v2.10.1 | `responseformat`, `formatdata` | No aplica |
| `mndrix/golog` | 2017-03-30 | Motor de reglas `ruler` | No aplica |

## Infraestructura

| Servicio | Propósito |
|---|---|
| Servidor web con PHP | Ejecuta weboffice. Sistema operativo, servidor web y ubicación desconocidos |
| MySQL | Base del framework y de las solicitudes. Versión desconocida |
| Oracle | Sistema académico `mntac`. Versión desconocida |
| Disco del servidor | `documento/solicitudes/` |
| AWS SSM Parameter Store y X-Ray | Los supone `utils_oas`; weboffice no los usa |
| WSO2 IS | `utils_oas/auditoria` valida el token en `https://autenticacion.portaloas.udistrital.edu.co/oauth2/userinfo`; weboffice usa su propia sesión |

## Herramientas de construcción

| Herramienta | Versión | Propósito |
|---|---|---|
| Ninguna para PHP | — | Los archivos se copian al servidor |
| Go toolchain | 1.26.0 según `go.mod` | Compilar `utils_oas` |
| Drone CI, Docker, SonarQube, ECR y ECS | Las de los ejemplos de `lineamientos_oas` | Pipeline institucional del sistema nuevo (L43, L45, L46) |

## Herramientas de pruebas

| Herramienta | Versión | Propósito |
|---|---|---|
| Ninguna para PHP | — | `weboffice` no tiene pruebas |
| Paquete `testing` de Go | El del toolchain | 2 archivos de prueba en `utils_oas` |
| Apache JMeter | La de los ejemplos | Planes de carga de ejemplo en `lineamientos_oas` |

## Herramientas disponibles en la máquina de desarrollo (verificado el 2026-11-25)

El registro de auditoría del 2026-11-24 decía que solo había git (máquina con Windows). El workspace ahora está en Linux y hay más herramientas:

| Herramienta | Versión | Comentario |
|---|---|---|
| Python | 3.14.10 | El proyecto fija 3.12; las pruebas de U1 se pueden correr en un contenedor `python:3.12` |
| Docker y Podman | 29.10.0 y 5.8.9 | Permiten correr las pruebas y construir las imágenes en local |
| Node | 18.20.8 (nvm) | Sin soporte vigente; U2 necesita una LTS con soporte (OQ-T-1) |
| Go | 1.17.13 | Más antiguo que el que pide `utils_oas` (1.26); no hace falta para este proyecto |
| PHP | No instalado | El sistema actual no se puede ejecutar aquí, y además le falta el núcleo del framework |

Decisión del usuario (2026-11-25): usar en la máquina de desarrollo las versiones actualizadas de los lenguajes y herramientas. Node 18 se cambia por una LTS con soporte antes de U2. Con C4 = a (2026-11-25), todo el proyecto (máquina, imagen Docker y CI) usa la última versión estable con soporte de cada lenguaje y herramienta: Python deja la 3.12 (hoy 3.14), Node pasa a una LTS activa y Angular a una versión con soporte. `technical-environment.md` ya está actualizado. Las versiones exactas y la compatibilidad de las librerías se fijan en NFR Requirements de cada unidad.
