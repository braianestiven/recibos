# Requisitos no funcionales — U1 `recibos_service`

- Etapa: CONSTRUCTION → U1 `recibos_service` → NFR Requirements (2026-11-25)
- Fuentes: RNF-1 a RNF-8 de `requirements.md`; respuestas N1 a N17 (`construction/plans/recibos_service-nfr-requirements-plan.md` y `recibos_service-nfr-requirements-clarification-questions.md`); el diseño funcional de U1; AD-01 a AD-33; la referencia `firma-electronica-mid-analysis.md`
- Cada requisito tiene un identificador (NFR-…), un valor que se puede medir y la etapa que lo detalla: NFR Design (ND), Infrastructure Design (ID), Code Generation (CG) o Build and Test (BT)
- Extensiones: seguridad, con todas sus reglas bloqueantes; PBT parcial; resiliencia desactivada (confirmado con N17 = b)
- Tecnología elegida: `tech-stack-decisions.md`
- Ajustado el 2026-11-25 en U1 NFR Design: NFR-R03 (un reintento al guardar el archivo en S3) y NFR-O05 (alarma de lotes cortados por MySQL)

## 1. Rendimiento (RNF-1)

| ID | Requisito | Valor | Cómo se verifica | Etapa | Origen |
|---|---|---|---|---|---|
| NFR-P01 | Tiempo de `POST /v1/lotes` con 1000 filas válidas, medido dentro del servicio: desde que llega la petición hasta que sale la respuesta | 60 s o menos en 95 de cada 100 lotes | La auditoría guarda la duración de cada lote (`duracion_ms`). La prueba de carga es de otro grupo, fuera del ciclo | ND, CG | N2 |
| NFR-P02 | Tiempo de un lote de hasta 10 filas | 5 s o menos | Igual que NFR-P01 | ND | N2 |
| NFR-P03 | Tiempo de `GET /v1/lotes` (una página de 20) | 2 s o menos en 95 de cada 100 peticiones | Duración en la auditoría | ND | Decisión de esta etapa (DN-01) |
| NFR-P04 | Límite propio del lote | 90 s. Al llegar, el servicio deja de procesar filas y responde con el reporte. Las filas que no alcanzó salen con `TIEMPO_AGOTADO` y no cancelan nada (BR-L16) | Prueba unitaria con un reloj de prueba | ND, CG | N3 |
| NFR-P05 | Cadena de tiempos de espera | Cada eslabón espera más que el anterior: límite propio (90 s), gunicorn, balanceador, WSO2 AM y `recibos_mf`. Todos, salvo el límite propio, de 120 s o más | Revisión de la configuración | ND, ID | N2, N3 |
| NFR-P06 | Tiempo de espera de cada llamada externa | Cada llamada a WSO2, "parametros", S3, Oracle y MySQL tiene un tiempo de espera explícito. En el peor caso, las llamadas previas a las filas no pasan de 30 s | Revisión de código, ruff y SonarQube | ND, CG | Decisión del plan |
| NFR-P07 | Memoria por lote | El archivo pesa 2 MB como máximo y se lee en memoria una sola vez; el lote no guarda más de 1000 filas | Prueba con un archivo de 2 MB | CG | N7, F1 |

## 2. Capacidad

| ID | Requisito | Valor | Etapa | Origen |
|---|---|---|---|---|
| NFR-C01 | Lotes procesándose a la vez en el pico | 3 | ND | N4 |
| NFR-C02 | Capacidad de cada tarea | Una sola tarea atiende los 3 lotes del pico, más el historial y los health checks, por si la otra falla | ND | N4, N6 |
| NFR-C03 | Filas por lote | 1000 como máximo (BR-L11) | CG | F1 |
| NFR-C04 | Tamaño del archivo | 2 MB como máximo (BR-L02) | CG | N7 |
| NFR-C05 | Conexiones a las bases | El pool de cada tarea alcanza para los lotes del pico sin esperar; no se abren conexiones por fila | ND | N4 |
| NFR-C06 | Escalado | Número fijo de tareas, sin autoescalado (NFR-A02). Se revisa si el uso real pasa de NFR-C01 | ID | N4, RNF-7 |

## 3. Disponibilidad

| ID | Requisito | Valor | Etapa | Origen |
|---|---|---|---|---|
| NFR-A01 | Disponibilidad de producción | 99,9% al mes, 24/7: unos 43 minutos sin servicio en un mes de 30 días. Mide la disponibilidad propia del servicio: minutos del mes con al menos una tarea sana en el grupo de destino del balanceador. Las caídas de Oracle, MySQL, WSO2, "parametros" y S3 no cuentan: tienen otros responsables y sus propias alarmas | ID | N6 = c, N15 = a |
| NFR-A02 | Redundancia | Producción: dos tareas o más, en zonas de disponibilidad distintas. Test: una tarea | ID | N6 |
| NFR-A03 | Despliegue sin interrupción | Las tareas nuevas reciben tráfico cuando su health check está bien, antes de detener las anteriores | ID | N6 |
| NFR-A04 | Parada ordenada | Al detener una tarea, el servicio deja de recibir lotes nuevos y termina el que está procesando. El tiempo de parada es mayor que el límite propio (90 s) | ND, ID | N6, N3 |
| NFR-A05 | Health check | `GET /` y `GET /health` responden en menos de 1 s y no consultan las bases | CG | Decisión del plan |
| NFR-A06 | Atención de alarmas | Las alarmas de NFR-O05 llegan, a cualquier hora, al grupo de infraestructura de la OAS, con su canal y sus turnos (insumo D15) | ID | N6, N16 |
| NFR-A07 | Dependencia caída | El lote no empieza (BR-L04, BR-L05, BR-L12, BR-L13) o la fila queda con su motivo (BR-T04). El servicio sigue respondiendo y deja el registro | CG | N15 |
| NFR-A08 | Recuperación | El servicio no guarda estado: los datos están en las bases y en S3, y se recupera desplegando la misma imagen. No hay recuperación ante desastres propia; las copias de seguridad de las bases son del DBA | ID | N6, N17 |

## 4. Seguridad y cumplimiento (RNF-2)

| ID | Requisito | Valor | Etapa | Regla |
|---|---|---|---|---|
| NFR-S01 | Cifrado en tránsito | TLS 1.2 o superior en todo el tráfico. Oracle por TCPS y MySQL con TLS, los dos con verificación del certificado del servidor (insumo D14). python-oracledb en modo thin | ND, ID | SECURITY-01, N9 |
| NFR-S02 | Cifrado en reposo | S3 con cifrado administrado por AWS (SSE-S3) y una política que rechaza las peticiones sin TLS. Las bases ya están cifradas (Discovery). Secretos en SSM como `SecureString` | ID | SECURITY-01 |
| NFR-S03 | Autenticación y autorización | El token se valida en `/oauth2/userinfo` en cada petición, sin caché, y el rol de ARC se verifica en el servicio. WSO2 IS exige segundo factor a los usuarios de ARC; lo confirma Seguridad | CG | SECURITY-08, SECURITY-12 |
| NFR-S04 | Validación de entradas | Reglas BR-L01 a BR-L11, BR-F y BR-D; archivo de 2 MB como máximo; consultas con parámetros enlazados | CG | SECURITY-05, N7 |
| NFR-S05 | Endurecimiento | Imagen `python:3.15-slim` con versión exacta; compilación en una etapa aparte; la imagen final sin herramientas de compilación y con un usuario sin privilegios; el servicio no sirve documentación; errores sin detalles internos; solo versiones con soporte | CG, ID | SECURITY-09, N1, N12 |
| NFR-S06 | Cadena de suministro | Versiones exactas con hashes; pip-audit y SBOM (CycloneDX) en Drone; imágenes del pipeline con versión fija; ninguna dependencia sin mantenimiento (por eso se cambian httpx y flasgger, y no se usa el SDK de X-Ray) | CG, ID | SECURITY-10, N11, N12, N14 |
| NFR-S07 | Limitación de tráfico | Throttling de WSO2 AM (D12), además de los máximos de tamaño y de filas | ID | SECURITY-11 |
| NFR-S08 | Registros sin datos personales | Ningún registro ni la auditoría llevan tokens, códigos ni nombres de estudiantes | CG | SECURITY-03, Ley 1581 |
| NFR-S09 | Retención | 365 días para los archivos de S3 (se borran solos), los registros de CloudWatch Logs y los registros de acceso del balanceador y de WSO2 AM. La aplicación no puede borrar sus registros | ID | SECURITY-02, SECURITY-14, N8 |
| NFR-S10 | Alertas de seguridad | Alarmas por 401 y 403 repetidos y por errores 5xx (NFR-O05) | ID | SECURITY-14 |
| NFR-S11 | Configuración segura | `DEBUG` apagado fuera de local; secretos solo en SSM; si falta una variable o un secreto, el proceso no arranca y lo deja en el registro | CG | SECURITY-09, SECURITY-15, referencia |
| NFR-S12 | Integridad de los datos | La auditoría guarda quién creó y quién canceló cada solicitud, y cuándo (AD-25). El bloqueo por estudiante evita que dos lotes simultáneos dejen dos solicitudes sin imprimir (BR-T05) | ND, CG | SECURITY-13, N5 |

## 5. Confiabilidad e integridad (RNF-3)

| ID | Requisito | Valor | Etapa | Origen |
|---|---|---|---|---|
| NFR-R01 | Solicitud completa o ninguna | 0 solicitudes incompletas (BR-T03) | CG | RF-10 |
| NFR-R02 | Dos lotes con el mismo estudiante | Bloqueo en MySQL por el código del estudiante, entre la cancelación y el guardado. Queda la solicitud del lote que guarda de último (BR-T05) | ND | N5 |
| NFR-R03 | Reintentos | Uno solo, en las lecturas por HTTP ("parametros" y `/oauth2/userinfo`), cuando falla la conexión. Las escrituras en las bases no se reintentan. *Ajustado en NFR Design (AD-34):* el archivo en S3 se reintenta una vez, porque va a un nombre nuevo de cada lote y repetirlo deja el mismo archivo | ND | Decisión del plan |
| NFR-R04 | Falla cerrada | Toda falla de una dependencia o de la configuración termina en un error controlado, sin datos a medias | CG | SECURITY-15 |
| NFR-R05 | Riesgo aceptado con "Solicitados" | Si "Solicitados" genera el recibo de una solicitud justo cuando el lote la cancela, la solicitud queda generada, igual que hoy (RE-20) | — | Decisión del plan |

## 6. Observabilidad (RNF-5)

| ID | Requisito | Valor | Etapa | Origen |
|---|---|---|---|---|
| NFR-O01 | Registro de la aplicación | JSON a stdout (CloudWatch Logs) con fecha, nivel, mensaje, módulo y `request_id` | CG | SECURITY-03, AD-24 |
| NFR-O02 | Identificador de la petición | El valor de la cabecera `X-Amzn-Trace-Id` que agrega el balanceador, si tiene el formato esperado; si no, uno generado. Va en todos los registros, en el campo `trace_id` de la auditoría y en la cabecera `X-Request-Id` de la respuesta | CG | N14, DN-02 |
| NFR-O03 | Auditoría por petición | La de RF-13, más la duración del lote (`duracion_ms`) y sus totales | CG | RF-13, NFR-P01 |
| NFR-O04 | Trazas distribuidas | No van en el MVP. Se agregan después con OpenTelemetry. El SDK de X-Ray no se usa porque pierde el soporte el 2027-02-25 | — | N14 = c |
| NFR-O05 | Alarmas | Ninguna tarea sana durante 1 minuto; errores 500; p95 de `POST /v1/lotes` por encima de 60 s; 401 o 403 repetidos; lotes con `TIEMPO_AGOTADO`; reinicios de tareas; lotes cortados por MySQL (agregada en NFR Design, N20). Los umbrales se fijan en Infrastructure Design | ID | SECURITY-14, N6, N16 |
| NFR-O06 | Tablero | Un tablero de CloudWatch con la disponibilidad, los errores, la duración de los lotes y el estado de las alarmas | ID | SECURITY-14 |

## 7. Mantenibilidad (RNF-4)

| ID | Requisito | Valor | Etapa | Origen |
|---|---|---|---|---|
| NFR-M01 | Arquitectura | Clean Architecture. Una prueba verifica que `app/domain` solo importa la biblioteca estándar | CG | RNF-4 |
| NFR-M02 | Estilo y tipos | ruff en todo el código y mypy estricto en `app/domain` y `app/application`, antes de cada commit y en Drone; un error detiene el pipeline | CG | N13 |
| NFR-M03 | SonarQube | 0 bugs, 0 vulnerabilidades y 50% de duplicación como máximo (L39), con la configuración de Python y el reporte de cobertura | CG | RNF-6, L39 |
| NFR-M04 | Documentación de la API | `swagger/swagger.yml` en Swagger 2.0, igual a `api-contract.md`, publicado en WSO2 AM. El servicio no sirve documentación; en local se ve con Swagger UI en un contenedor | CG | N12, L41 |
| NFR-M05 | Repositorio | README con lo que pide L48 y el distintivo de CI; `.gitignore` de Python; `.env.example`; ramas y commits con las convenciones que revisa el pipeline (L45) | CG | L45, L48, referencia |
| NFR-M06 | Configuración | Variables `RECIBOS_SERVICE_*` (L33), con `RECIBOS_SERVICE_ENV` (dev, test o prod) y `RECIBOS_SERVICE_PORT` (8080 por defecto, a confirmar con infraestructura) | CG, ID | L33, referencia |

## 8. Pruebas (RNF-6)

| ID | Requisito | Valor | Etapa | Origen |
|---|---|---|---|---|
| NFR-T01 | Cobertura | 80% o más en total y 100% en `app/domain`; por debajo, el pipeline falla | CG, BT | RNF-6 |
| NFR-T02 | Pruebas basadas en propiedades | Hypothesis, con las propiedades de `business-logic-model.md` §9; la semilla queda en el registro de Drone | CG, BT | PBT-02, PBT-03, PBT-07, PBT-08, PBT-09 |
| NFR-T03 | Pruebas de ejemplo | Cada escenario de las historias listas tiene su prueba de ejemplo; las pruebas de propiedades no las reemplazan | CG | RNF-6, PBT-10 (orientativa) |
| NFR-T04 | Alcance | Solo pruebas unitarias en el ciclo; las de carga, equivalencia, usuario y seguridad son de otros grupos | BT | RNF-6 |
| NFR-T05 | Versión de Python de las pruebas | La misma de la imagen (3.15) | CG, BT | N1 |

## 9. Uso de la API

| ID | Requisito | Valor | Origen |
|---|---|---|---|
| NFR-U01 | Mensajes | En español, con los textos de `business-rules.md` §10, sin detalles internos | BR-R03 |
| NFR-U02 | Reporte del lote | ARC siempre recibe el reporte, aunque el lote pase del tiempo previsto (NFR-P04) | N3 |

## 10. Costos (RNF-7)
- Solo se usan servicios que ya existen: ECS, ECR, S3, SSM y CloudWatch. No hay llaves propias de KMS (SSE-S3 no tiene costo adicional) ni trazas en el MVP.
- El costo que sube es la segunda tarea en producción, que pide NFR-A02.

## 11. Decisiones de esta etapa que no vinieron de una pregunta
Se pueden cambiar en la revisión.

| ID | Decisión | Por qué |
|---|---|---|
| DN-01 | `GET /v1/lotes` en 2 s o menos (NFR-P03) | Es una consulta paginada sobre una tabla pequeña |
| DN-02 | La respuesta lleva la cabecera `X-Request-Id` (NFR-O02) | Sin trazas, es la forma de ubicar una petición en los registros cuando ARC reporta un problema |
| DN-03 | Las llamadas previas a las filas tardan 30 s como máximo (NFR-P06) | Deja al menos 60 s del límite propio para procesar las filas |

## 12. Cambios a decisiones anteriores

| Decisión | Antes | Ahora | Por |
|---|---|---|---|
| A1, RF-01 CA2 | 10 MB | 2 MB | N7 |
| A2 | 90 días como mínimo | 365 días | N8 |
| RNF-5 | Trazas de X-Ray | Sin trazas en el MVP; después, OpenTelemetry | N14 |
| AD-08 | httpx | requests | N11 |
| AD-13 | flasgger en local | Swagger UI en un contenedor, en local | N12 |
| AD-24 | `request_id` = id de traza de X-Ray o uno generado | `X-Amzn-Trace-Id` del balanceador o uno generado | N14 |
| AD-26 | `requirements.in` y `requirements.txt` | `pyproject.toml`, `requirements.txt` y `requirements-dev.txt` con hashes | N13, referencia |
| AD-27 | `python:<versión>-slim` | `python:3.15-slim`, con compilación en una etapa aparte | N1 |
| Entorno técnico | flasgger obligatorio; aws-xray-sdk, httpx y cachetools preferidas | Sin flasgger; requests; sin aws-xray-sdk ni cachetools | N11, N12, N14 |
| Diseño funcional | — | `TIEMPO_AGOTADO` (BR-L16), 2 MB (BR-L02) y bloqueo por estudiante (BR-T05) | N3, N5, N7 |
| Nuevas en el diseño | — | AD-31 (límite propio), AD-32 (bloqueo por estudiante), AD-33 (sin trazas en el MVP) | N3, N5, N14 |

## 13. Insumos

| ID | Insumo | Responsable | Etapa |
|---|---|---|---|
| D14 | Servicio TCPS y puerto de Oracle, y el certificado de la CA de Oracle y de MySQL | DBA | U1 Infrastructure Design |
| D15 | Canal y turnos con los que infraestructura atiende las alarmas 24/7 | Infraestructura | U1 Infrastructure Design |
| D7 | Rutas de SSM y destino de los registros (la retención y el tamaño ya se decidieron) | Infraestructura / Seguridad | U1 Infrastructure Design |
| D5 | Tabla de festivos de weboffice | DBA | U1 Code Generation |
| Seguridad | Confirmar que WSO2 IS exige segundo factor a los usuarios de ARC | Seguridad | Antes de test |

## 14. Cumplimiento de las extensiones en esta etapa

| Regla | Estado | Cómo |
|---|---|---|
| SECURITY-01 | Cumple | NFR-S01 y NFR-S02 |
| SECURITY-02 | Cumple | NFR-S09: registros de acceso del balanceador y de WSO2 AM; se configuran en Infrastructure Design |
| SECURITY-03 | Cumple | NFR-O01, NFR-O02 y NFR-S08 |
| SECURITY-04 | Cumple | Cabeceras en todas las respuestas (AD del diseño); el servicio no sirve páginas HTML (NFR-M04) |
| SECURITY-05 | Cumple | NFR-S04 |
| SECURITY-06 | N/A en esta etapa | Los permisos de IAM y de las bases se definen en Infrastructure Design; el requisito ya está en `unit-of-work.md` §5 |
| SECURITY-07 | N/A en esta etapa | La red se define en Infrastructure Design |
| SECURITY-08 | Cumple | NFR-S03 y CORS con lista explícita (AD-14) |
| SECURITY-09 | Cumple | NFR-S05: versiones con soporte; el SDK de X-Ray quedó fuera (N14) |
| SECURITY-10 | Cumple | NFR-S06 |
| SECURITY-11 | Cumple | NFR-S07, el límite propio (NFR-P04) y los casos de abuso de `business-rules.md` §13 |
| SECURITY-12 | Cumple | Autenticación delegada en WSO2 IS (NFR-S03); Seguridad confirma el segundo factor |
| SECURITY-13 | Cumple | NFR-S06 y NFR-S12 |
| SECURITY-14 | Cumple | NFR-S09, NFR-S10, NFR-O05 y NFR-O06 |
| SECURITY-15 | Cumple | NFR-R04, NFR-A07 y NFR-S11 |
| PBT-09 | Cumple | Hypothesis, documentado en `tech-stack-decisions.md` §4 |
| PBT-01 a PBT-08 y PBT-10 | N/A en esta etapa | Las propiedades salieron en el diseño funcional; las pruebas se escriben en Code Generation y la semilla se configura en Build and Test |
| Resiliencia | Desactivada | N17 = b |
