# Librerías institucionales `utils_oas` vs. el proyecto de recibos (contexto para la entrevista técnica)

- Fecha: 2026-11-23T23:40:00Z
- Fuente: `codigo-fuente/utils_oas/` (clon local, rama `master`, `cdb2441`, tag `v0.6.2`; `go.mod`: Go 1.26, Beego v1.12.3, AWS SDK v2, X-Ray SDK v2)
- Alcance: lectura de `.go` y `.md`. No se compiló, ejecutó ni modificó nada.

## Conclusión principal

`utils_oas` está escrita **en Go para Beego** (`README.md`: "paquete de librerías y utilidades generales para las aplicaciones desarrolladas en el framework beego"). **No se puede importar desde Python/Flask.** Lo que sí se puede integrar son sus **contratos**: formato de respuestas, cabeceras de seguridad, formato del log de auditoría, validación del token, health check y ubicación de secretos. Para cumplir T6 ("sin otros lenguajes"), el backend debe reimplementar esos contratos en un módulo Python propio del proyecto.

Esto resuelve varios vacíos del análisis de lineamientos (L11, L12, L40) y responde por anticipado T17 y T20.

## Librería por librería

| Paquete | Qué hace (fuente) | ¿Aplica a recibos? | Cómo se integra en Python |
|---|---|---|---|
| `apiStatusLib` | `GET /` responde `{"status": "ok"}` (`apiStatusLib/apistatus.go`). Requisito para desplegar en la infraestructura OAS (`README.md`). | **Sí** | Ruta `GET /` con el mismo JSON, además del `/health` del lineamiento Flask (L6). Opcional: verificar conexión a Oracle y MySQL (equivalente a `InitWithHandler`, `apiStatusLib/README.md`). |
| `customerrorv2` + `requestresponse` | Errores y respuestas con el sobre `{"Success", "Status", "Message", "Data"}` (`customerrorv2/custom_errorv2.go`; `requestresponse/responses_format.go` `APIResponseDTO`, `APIResponseMetadataDTO` con `Metadata`). v2 "mitiga la exposición de información confidencial en la estructura de errores" (`README.md`). | **Sí** | Usar ese mismo sobre JSON en todas las respuestas y errores de la API Flask (400, 401, 404, 409, 500…). Compatible con WSO2. |
| `responseformat` | Formato alterno `{"Type", "Code", "Body"}` (`responseformat/README.md`), marcado "Por definir". | No | No usar; se elige el formato de `requestresponse` para no mezclar dos. |
| `security` | Cabeceras fijas en todas las respuestas (`security/security_headers.go`): `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`, `Cross-Origin-Resource-Policy: cross-origin`, `Permissions-Policy: geolocation=(), microphone=(), camera=()`, `Referrer-Policy: no-referrer`, `Server: ""`, `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`, `X-XSS-Protection: 1; mode=block`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-Permitted-Cross-Domain-Policies: none`. | **Sí** (restricción Q9 "cabeceras") | Hook `after_request` de Flask con exactamente esas cabeceras. |
| `auditoria` | Middleware sobre `/:version/*` (`auditoria/auditoria.go`): (1) lee `Authorization`, valida el token contra `https://autenticacion.portaloas.udistrital.edu.co/oauth2/userinfo`, guarda en caché `sub` del usuario 60 min; con `InitWithAuthEnforcer` responde **401** si falta o falla el token (salvo modo dev). (2) Tras cada petición escribe un log JSON con `app_name, agent, data, date, host, ip_user, method, path, query, schema, sql_statement, status, trace_id, user`. | **Sí** (Q9 "logs siempre habilitados", mínimo privilegio) | Middleware Flask `before_request` (validar token con userinfo + caché, 401 si no es válido) y `after_request` (log JSON con los mismos campos). Mejoras: capturar el SQL **por petición** (el propio código advierte que en Go no es por petición) y **no registrar datos personales** en `data` (Ley 1581). |
| `ssm` + `database` | Credenciales en **AWS SSM Parameter Store** con descifrado: `/{parameterStore}/{appname}/db/username` y `/password` (`ssm/ssm.go`, `database/oracle.go`). Sin `parameterStore` usa variables locales `ORuser`/`ORpass`. Conexión Oracle `oracle://user:pass@ORhost:ORport/ORservice`. | **Sí** (T20) | `boto3` → `ssm.get_parameter(Name=..., WithDecryption=True)` con la misma convención de rutas; variables locales solo en desarrollo. Para MySQL se sugiere la misma convención (`/db-mysql/...` u otra que defina infraestructura). |
| `xray` | AWS X-Ray; dirección del daemon en SSM `/{parameterStore}/utils/xray/DaemonAddr`; cabecera `X-Amzn-Trace-Id` (`xray/xray.go`). | Recomendado | `aws-xray-sdk` para Python (o ADOT), mismo parámetro SSM. Alimenta `trace_id` del log de auditoría. |
| `time_bogota` | Hora en `America/Bogota` sin depender de la zona del contenedor (`time_bogota/time_bogota.go`). | **Sí** | `zoneinfo.ZoneInfo("America/Bogota")` para fechas de pago, festivos y `date` del log. |
| `request` / `requestmanager` | Cliente HTTP hacia otras APIs OAS; extrae `Data` del sobre (`request/transaction_tools.go`). | Solo si se consumen APIs OAS | `httpx`/`requests` con la misma lógica de extracción del campo `Data`. |
| `ruler` | Motor de reglas Prolog (`golog`) servido por `rulerService` (`ruler/ruler_tools.go`). | No para la PoC | Las reglas de recibos van en tablas de parámetros (Q10, Q14). |
| `xlsx2pdf` | Convierte `.xlsx` a PDF con excelize + gofpdf. | No | Las plantillas son `.xls` y la impresión sigue en "Solicitados" (Q16). |
| `customerror` (v1), `errorctrl`, `errorctrlPrueba`, `errorhandler`, `formatdata`, `optimize`, `planeacion` | Utilidades Beego antiguas o de otros dominios. | No | — |

## Librerías Python que se agregan a T9

| Librería | Para qué | Equivale a |
|---|---|---|
| `boto3` | Leer credenciales de SSM Parameter Store | `ssm`, `database` |
| `aws-xray-sdk` | Trazas X-Ray | `xray` |
| `httpx` o `requests` | Validar el token en `/oauth2/userinfo` | `auditoria` |
| `cachetools` | Caché de 60 min del usuario por token | `auditoria` |

## Respuestas técnicas que quedan sugeridas

- **T17 (autenticación):** OAuth2/OIDC con WSO2 (`autenticacion.portaloas.udistrital.edu.co`), token Bearer validado en `/oauth2/userinfo`; 401 sin token fuera de dev.
- **T19 (validación de entradas):** pydantic + sobre de error `customerrorv2`.
- **T20 (secretos):** AWS SSM Parameter Store, ruta `/{parameterStore}/{appname}/db/...`; variables locales solo en dev; secretos del pipeline en Drone (L43).
- **T25 / seguridad:** cabeceras `security`, log `auditoria`, health `apiStatusLib`.

## Pregunta para el equipo

¿Existe (o se planea) una versión Python de `utils_oas` en la OATI? Si existe, se usaría en lugar de reimplementar los contratos.
