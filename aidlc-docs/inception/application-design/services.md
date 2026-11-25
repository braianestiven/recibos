# Casos de uso y orquestación

## UC-01 — Procesar lote (`POST /v1/lotes`)

Historias: US-02 a US-12, US-15. Todo ocurre en la misma petición (C-2).

| Paso | Responsable | Acción | Si falla |
|---|---|---|---|
| 1 | Middlewares | Token válido (401) y rol ARC (403) | La petición no llega al caso de uso |
| 2 | Controller | El campo `archivo` existe (400); el nombre original no pasa de la longitud de la columna `nombreOriginal` (D4) y no lleva rutas ni caracteres de control (400, SECURITY-05); el tamaño no pasa del máximo (413, `MAX_CONTENT_LENGTH`); la extensión es `.xls` y los primeros bytes son la firma OLE2 `D0 CF 11 E0 A1 B1 1A E1` (415) | No se guarda ni se registra nada |
| 3 | `FuenteReglas.obtener` | Lee las reglas en "parametros": una llamada `GET /v1/parametro/{id}` por regla. Valida el sobre, que `Data.Id` sea el pedido y que `Data.Activo` sea verdadero, y convierte el valor (AD-21). Después lee de la tabla MySQL `exencion` los porcentajes de las exenciones del mapa (F11) | 503 si no responde; 502 si la regla no existe, está inactiva o su valor no se puede convertir, o si a una exención del mapa le falta el porcentaje en `exencion`, con el nombre de la regla o el id en el mensaje. No se registra nada |
| 4 | `AlmacenamientoArchivos.guardar` | Guarda el archivo con nombre interno `lotes/{aaaa}/{mm}/{uuid4}.xls` | 503 |
| 5 | `RepositorioSolicitudes.registrar_lote` | Inserta en `solicitudLote` (documento, nombre original, nombre interno, IP según AD-29, fecha) | 503. El archivo queda en S3 y lo elimina la política de retención |
| 6 | `LectorPlantilla.leer` + `plantillas` | Lee la hoja, identifica el tipo y valida el formato | 422 con `id_lote` y el motivo. El lote queda registrado (P-9) |
| 7 | `plantillas.extraer_filas` | Filas desde la fila inicial; omite las vacías, y una celda con solo espacios cuenta como vacía (F4). Una fila con datos y sin código queda como rechazo `CODIGO_INVALIDO` (F3) | — |
| 8 | Caso de uso | Si hay más filas con datos que el máximo (1000), rechaza el lote completo con 422, sin procesar ninguna, y el mensaje dice el máximo y cuántas filas trae (F1) | El lote queda registrado (P-9) |
| 9 | `validacion_filas.validar_codigo` | Separa los códigos válidos de los inválidos. Si un código se repite, solo sigue la primera aparición (F2) | El inválido queda como rechazo de esa fila; las apariciones repetidas quedan como `CODIGO_REPETIDO` y no cancelan nada |
| 10 | `RepositorioAcademico` | Tres lecturas en bloque: estudiantes, contextos de los proyectos curriculares y certificados electorales | 503. Todavía no se escribió ninguna solicitud |
| 11 | `FuenteFestivos` (las dos plantillas: en pregrado la fecha extraordinaria también se calcula, F8) | Festivos de la tabla que usa hoy weboffice (F9; el DBA la identifica, D5), desde la menor fecha ordinaria hasta la mayor más un margen | 503 |
| 12 | Dominio, fila por fila | `validacion_estudiante.validar`, y luego `generador_solicitud.generar` | Queda un rechazo con su motivo y sigue la fila siguiente |
| 13 | `RepositorioSolicitudes.cancelar_sin_imprimir` | Cada fila con estudiante conocido, válida o rechazada (AD-30, A12): cancela en su propia transacción sus solicitudes sin imprimir de cualquier periodo (C8) | Fila válida: no se inserta la nueva y queda `ERROR_GUARDADO`. Fila rechazada: conserva su motivo. Sigue la fila siguiente |
| 14 | `RepositorioSolicitudes.guardar_solicitud` | Solo filas válidas: una transacción con recibo, cuotas, exenciones y conceptos | Se revierte la solicitud nueva y la cancelación se mantiene (RE-02); queda `ERROR_GUARDADO` y sigue la fila siguiente (US-10) |
| 15 | Controller | Devuelve `ResumenLote` con los estudiantes que se subieron y los que no, con su motivo (RF-11 CA3) | 201 |

Reglas de la orquestación:
- Las filas se procesan en el orden de la plantilla. Si un código se repite, solo se procesa su primera aparición; las siguientes quedan como `CODIGO_REPETIDO` y no cancelan nada (F2). Hoy la fila siguiente cancela la solicitud de la anterior.
- Las tres lecturas de Oracle del paso 10 reemplazan las cerca de 5 consultas por estudiante que hace el PHP (AD-06). El resultado es el mismo.
- El caso de uso no conoce HTTP, Flask ni SQL. Los códigos de respuesta los pone `middlewares/errores` a partir de los errores de aplicación.
- Si MySQL se cae a mitad del lote, cada estudiante que falta queda como `ERROR_GUARDADO`. NFR Design decidirá si conviene cortar el lote después de varios fallos de conexión seguidos.

## UC-02 — Consultar lotes (`GET /v1/lotes`)

Historia: US-13.

| Paso | Acción | Si falla |
|---|---|---|
| 1 | Middlewares: token (401) y rol (403) | — |
| 2 | Valida `limit` (1–100, por defecto 20) y `offset` (≥ 0, por defecto 0) con pydantic | 400 |
| 3 | `RepositorioSolicitudes.listar_lotes`, del más reciente al más antiguo | 503 |
| 4 | Responde 200 con la lista en `Data` y `total`, `limit`, `offset` en `Metadata`; si no hay lotes, `Data` es `[]` (L31) | — |

## UC-03 — Autorizar usuario (en cada petición a `/v1/*`)

Historia: US-01.

1. `ProveedorIdentidad.usuario(token)` llama a `/oauth2/userinfo` en cada petición, sin caché (AD-09, SECURITY-08). Si el token falta o es inválido: 401. Antes de llegar a la API, WSO2 AM también valida el token y la suscripción.
2. `AutorizarUsuario` verifica que `roles` incluya el rol configurado (D8). Si no: 403.
3. Si el usuario no trae `documento`: 403, porque no se puede registrar `id_usuario` (A8).
4. El backend nunca lee roles, niveles ni permisos de la petición.

## Transversales

| Tema | Cómo |
|---|---|
| Auditoría | Antes de cada petición a `/v1/*` se reinicia la captura de SQL. Después se escribe una línea JSON con los campos de `utils_oas/auditoria`. `data` lleva solo tipo de plantilla, tamaño, `id_lote` y totales; nunca códigos ni nombres de estudiantes. `sql_statement` lleva el texto SQL sin valores. En `POST /v1/lotes`, `data` lleva además los ids de las solicitudes creadas y canceladas, con el cambio de estado (AD-25) |
| Registro de aplicación | JSON a stdout con fecha, nivel, mensaje, módulo y `request_id`; sin tokens ni datos personales (AD-24) |
| Cabeceras de seguridad | En todas las respuestas, incluidas las de error y los health checks |
| Errores | Toda excepción termina en el sobre `{Success, Status, Message, Data}`. Los 500 no muestran trazas ni mensajes internos; el detalle queda en el log |
| Trazas | Un segmento de X-Ray por petición y un subsegmento por llamada a "parametros", WSO2, S3, Oracle y MySQL |
| Configuración | Variables `RECIBOS_SERVICE_*`; los secretos se leen de SSM al arrancar; en local se usa `.env` fuera del repositorio |

## Errores de aplicación → respuesta HTTP

| Error | HTTP | `Message` |
|---|---|---|
| `NoAutenticado` | 401 | "No autorizado" |
| `AccesoDenegado` | 403 | "Prohibido" |
| `ParametrosConsultaInvalidos` | 400 | Detalle del parámetro inválido |
| `ArchivoNoPermitido` (tamaño) | 413 | Indica el tamaño máximo |
| `ArchivoNoPermitido` (tipo) | 415 | "Solo se aceptan plantillas .xls" |
| `FormatoPlantillaInvalido` | 422 | Motivo del rechazo del lote; `Data` lleva `id_lote` |
| `RespuestaInvalida` (dependencia) | 502 | "Mal gateway" |
| `DependenciaNoDisponible` | 503 | "Servicio no disponible" |
| Cualquier otro | 500 | "Error interno del servidor" |
