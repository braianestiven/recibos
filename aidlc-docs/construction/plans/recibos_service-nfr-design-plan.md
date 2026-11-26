# Plan de diseño de los requisitos no funcionales — U1 `recibos_service`

- Etapa: CONSTRUCTION → U1 `recibos_service` → NFR Design, profundidad estándar (`inception/plans/execution-plan.md`)
- Inicio: 2026-11-25T18:54:52Z
- Fuentes: `construction/recibos_service/nfr-requirements/` (`nfr-requirements.md` y `tech-stack-decisions.md`, aprobados el 2026-11-25T18:44:18Z); el diseño funcional de U1; AD-01 a AD-33
- Extensiones: seguridad, con todas sus reglas bloqueantes. PBT parcial: en esta etapa no aplica ninguna regla; las pruebas se escriben en Code Generation y la semilla se configura en Build and Test. Resiliencia desactivada (N17 = b)
- Cómo responder: después de cada `[Answer]:` de este archivo, o en el chat con el formato "n18 a, n19 a, n20 a"

## Pasos
- [x] 1. Analizar los requisitos no funcionales y las decisiones de tecnología de U1
- [x] 2. Escribir este plan con las preguntas N18 a N20
- [x] 3. Recibir las respuestas y revisar que ninguna quede ambigua
- [x] 4. `nfr-design-patterns.md`: patrones de rendimiento, tiempos, resiliencia, escalabilidad, concurrencia, seguridad y observabilidad, con sus valores
- [x] 5. `logical-components.md`: componentes lógicos de cada tarea, su configuración y la capacidad de conexiones
- [x] 6. Llevar los cambios a los documentos anteriores: componentes nuevos en `components.md` y `component-methods.md`, la hora de llegada de la petición en el pseudocódigo del diseño funcional, NFR-R03 e insumo D16
- [x] 7. Validar los diagramas y las tablas, revisar el cumplimiento de seguridad y presentar la compuerta

## Categorías revisadas
| Categoría | ¿Hay pregunta? | Por qué |
|---|---|---|
| Resiliencia | N20 | Falta decidir qué pasa si MySQL falla a mitad del lote (BR-T04). Lo demás ya está decidido: reintentos (NFR-R03), parada ordenada (NFR-A04) y dependencias caídas (NFR-A07) |
| Escalabilidad | No | La capacidad está fijada en NFR-C01 y NFR-C02; el número de procesos y de conexiones sale de ahí (decisiones de abajo) y el DBA confirma los límites (insumo nuevo D16) |
| Rendimiento | N19 | El tiempo de cada fila depende de un índice que todavía no sabemos si existe (D4) |
| Seguridad | N18 | Falta decidir cómo se toman las contraseñas nuevas cuando se cambian. Lo demás está en NFR-S01 a NFR-S12 |
| Componentes lógicos | No | No hacen falta colas, cachés ni circuit breakers (decisiones de abajo) |

## Decisiones que no necesitan pregunta
Se aplican salvo que digas otra cosa.
- **Procesos y conexiones por tarea:** gunicorn con 2 procesos de 4 hilos cada uno, es decir, 8 peticiones a la vez: más del doble del pico de 3 lotes (NFR-C02). Por proceso, hasta 6 conexiones a MySQL (4 fijas y 2 de reserva) y 4 a Oracle (2 y 2). Con dos tareas son hasta 24 conexiones a MySQL y 16 a Oracle, y el doble durante un despliegue. El DBA confirma que las bases lo permiten (insumo nuevo D16).
- **Cadena de tiempos de espera:** límite propio de 90 s, contado desde que llega la petición; balanceador, 120 s; WSO2 AM, 130 s; `recibos_mf`, 150 s. En gunicorn: 120 s para el worker, 125 s de keep-alive (más que el balanceador, para evitar errores 502 al reutilizar conexiones) y 100 s de parada ordenada. ECS espera 120 s al detener una tarea y el balanceador la desregistra en 100 s.
- **Fase previa a las filas:** 30 s en total (DN-03), contados desde el inicio del caso de uso. Cada llamada usa el tiempo que le queda; si se acaba, el lote termina con 503 sin procesar filas.
- **Reglas de "parametros":** las 17 se leen en paralelo, hasta 8 a la vez, con un tope de 10 s para todas. AD-20 sigue igual: se leen en cada lote, sin caché.
- **Tiempos por llamada:** WSO2 `/oauth2/userinfo`, 2 s para conectar y 5 s para responder; "parametros", 2 s y 3 s; S3, 2 s y 5 s; Oracle, 5 s para conectar y hasta 20 s por llamada, sin pasar de lo que quede de la fase previa; MySQL, 3 s para conectar, 10 s para leer o escribir y 5 s de espera por bloqueos de filas; bloqueo por estudiante, 5 s de espera.
- **Un reintento al guardar el archivo en S3:** si falla la conexión o S3 responde con un error temporal. Es una escritura, pero va a un nombre nuevo en cada lote (BR-L06), así que repetirla deja el mismo archivo. Esto ajusta NFR-R03, que hoy dice que ninguna escritura se reintenta; para las bases sigue igual.
- **Filas en orden:** se procesan una tras otra, en el orden de la plantilla. Con lo estimado alcanza para los 60 s, y se respeta el orden que piden F2 y BR-T05.
- **Sin colas, cachés ni circuit breakers:** el procesamiento es síncrono (C-2), las reglas se leen en cada lote (AD-20), el token se valida en cada petición (AD-09), y una dependencia caída se detecta en segundos porque todas las llamadas tienen tiempo de espera.
- **Sin antivirus para los archivos:** se guardan en un bucket privado, nadie los descarga y se leen con una librería que no ejecuta macros.
- **Errores de las bases en los registros:** pueden traer valores, como códigos de estudiantes; se registran el tipo de error y un mensaje sin valores.
- **`request_id`:** la parte `Root` de `X-Amzn-Trace-Id`, si tiene el formato que pone el balanceador; si no, un UUID nuevo. No se acepta cualquier valor que mande el cliente.
- **Límites del formulario (Werkzeug):** cuerpo de 2 MB más 64 KB para el sobre multipart, 4 partes como máximo y el archivo de 2 MB como máximo.
- **Limitación por usuario:** se pide a Arquitectura una política de WSO2 AM para `POST /v1/lotes` con pocas peticiones por minuto por usuario (D12).

## Preguntas

### Pregunta N18 — Cambio de las contraseñas de las bases
Las contraseñas de Oracle y MySQL se leen de SSM al arrancar. Si el DBA las cambia, ¿cómo las toma el servicio?

A) Infraestructura despliega de nuevo el servicio después del cambio: las tareas se reemplazan una a una, sin cortar el servicio (NFR-A03), y leen las contraseñas nuevas. Recomendada: es lo más simple, y con dos tareas no hay interrupción

B) El servicio vuelve a leer SSM cada 15 minutos y, si las contraseñas cambiaron, renueva sus conexiones sin reiniciar

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Aclaración del usuario: "los dbas no cambian la claves"

### Pregunta N19 — Índice de `solicitudRecibo` por estudiante
Cada fila cancela las solicitudes sin imprimir del estudiante con una consulta por `codigo_est` y `estado`, como hace hoy el PHP. Si la tabla no tiene un índice por esas columnas, cada fila recorre la tabla completa, que guarda las solicitudes de varios años, y un lote de 1000 filas puede no caber en 60 segundos. El DDL (D4) dirá si el índice existe.

A) Si no existe, se pide al DBA un índice no único por (`codigo_est`, `estado`). No cambia columnas, datos ni lo que lee "Solicitados". Recomendada

B) No se toca la tabla: si es lenta, el límite propio corta el lote y ARC vuelve a cargar las filas que falten

C) Other (please describe after [Answer]: tag below)

[Answer]: A

### Pregunta N20 — MySQL falla a mitad del lote (BR-T04)
Si MySQL deja de responder a mitad de un lote, cada fila que falta espera su tiempo de espera antes de fallar.

A) Después de 5 filas seguidas con falla de conexión a MySQL, el servicio deja de intentar: las filas que faltan salen con `ERROR_GUARDADO` ("Error al guardar la solicitud. Vuelva a cargar a este estudiante.") y responde enseguida. Las filas con errores de datos no cuentan para el corte. Recomendada: ARC recibe el reporte en segundos

B) Intentar todas las filas hasta el límite propio: cada una espera su tiempo de espera, y las que no se alcancen salen con `TIEMPO_AGOTADO`

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Resultado (2026-11-25T19:29:06Z)
- Respuestas (2026-11-25T18:58:07Z): "n18 a, los dbas no cambian la claves, n19 a, n20 a". Ninguna quedó ambigua: la aclaración de N18 no cambia la opción elegida y queda escrita en `nfr-design-patterns.md` §7.5.
- Artefactos en `aidlc-docs/construction/recibos_service/nfr-design/`: `nfr-design-patterns.md` y `logical-components.md`.
- Cambios frente a este plan: el límite propio también se revisa antes de cada sentencia de MySQL, así que una petición dura unos 100 s como máximo, y la parada ordenada de gunicorn y el desregistro del balanceador pasan de 100 a 110 s; en la fase previa, una llamada de tiempo fijo (S3 o MySQL) solo empieza si le cabe su peor caso; se agregan `Cache-Control: no-store`, la cabecera `Server` vacía desde `gunicorn.conf.py` y el insumo D17 (motor de las tablas, versión de MySQL e índice).
- Corrección: la línea vigente de gunicorn es la 27.x (la 27.0.0 salió el 2026-11-10); `tech-stack-decisions.md` decía 26.x.
Aprobado por el usuario el 2026-11-25T19:31:30Z: "Continuar a la siguiente etapa - Aprobar el diseño de NFR y pasar a Infrastructure Design de U1".
