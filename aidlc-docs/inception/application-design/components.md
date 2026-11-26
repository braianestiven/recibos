# Componentes

Las dependencias apuntan hacia adentro: `interfaces` → `application` → `domain`. `infrastructure` implementa los puertos de `application`. `domain` no importa Flask, SQLAlchemy, boto3 ni requests.

## recibos_service

### Raíz (lineamiento OAS)

| Componente | Responsabilidad |
|---|---|
| `api.py` | `create_app()`: crea la app Flask, conecta adaptadores con casos de uso, registra Blueprints y middlewares, y expone `app` para gunicorn (`api:app`) |
| `conf/conf.py` | Lee variables `RECIBOS_SERVICE_*` (L33); `DEBUG=False` por defecto (corrige L8); ningún endpoint devuelve estos valores; si falta una variable o un secreto, el proceso no arranca |
| `swagger/swagger.yml` | Especificación Swagger 2.0, igual a `api-contract.md`; se publica en WSO2 AM y en local la muestra Swagger UI desde `docker-compose.yml` (AD-13) |
| `gunicorn.conf.py` | 2 procesos de 4 hilos (`gthread`), latido de 120 s, parada ordenada de 110 s, keep-alive de 125 s, reciclado cada 1000 peticiones, registro de accesos a stdout y cabecera `Server` vacía (AD-36). Valores en `construction/recibos_service/nfr-design/logical-components.md` §2.1 |
| `pyproject.toml` | Metadatos, `requires-python`, dependencias directas y configuración de ruff, mypy, pytest y coverage (AD-26) |

### Dominio — `app/domain/` (Python puro, cobertura 100%)

| Componente | Responsabilidad | Historias |
|---|---|---|
| `modelos` | Entidades y objetos de valor: `TipoPlantilla`, `HojaPlantilla`, `FilaPlantilla`, `Usuario`, `Estudiante`, `Periodo`, `ContextoCarrera`, `FechasPago`, `Cuota`, `Solicitud`, `MotivoRechazo`, `Rechazo`, `Procesado`, `ResumenLote`, `NuevoLote`, `Lote`, `Pagina` | Todas |
| `reglas` | `ReglasLiquidacion`: todos los valores que llegan de "parametros" (estados, eventos, IDs de conceptos y exenciones, porcentajes, mapas columna → id, plazo de la fecha extraordinaria). Las fechas de pago vienen de la plantilla (C3) | US-06 a US-08, US-15 |
| `plantillas` | Estructura de las tres plantillas (texto de A1, fila inicial, número de columnas, encabezados, rangos de columnas), identificación del tipo, validación de formato y extracción de filas | US-03, US-04, US-05 |
| `validacion_filas` | Reglas de fila: código numérico; en posgrado, número de cuotas obligatorio de 1 a 3, fecha válida con año completo para cada cuota, porcentajes 0–100 y suma 100 | US-06, US-08 |
| `validacion_estudiante` | Validaciones académicas en el orden actual: existencia, valor de matrícula, estado, proyecto activo, terminación de materias; después, periodo vigente y nivel frente a la plantilla (BR-E01 a BR-E07) | US-06 |
| `fechas` | Sumar días calendario y saltar festivos | US-08 |
| `cuotas` | Cuota única de pregrado con las fechas de la plantilla (C3); cuotas de posgrado con porcentajes por defecto por posición | US-07, US-08 |
| `exenciones` | Como máximo un descuento más la votación y, en posgrado, la Secretaría de Educación, que no cuenta como descuento (C2, F12); con más de un descuento la fila no se sube. La votación, marcada o automática (la automática con un descuento o la Secretaría marcados: C1, C6, F15), se registra si el descuento y la votación juntos no pasan de 100%, sin contar la Secretaría (C7, F14). Orden: votación, descuento y Secretaría (BR-X01 a BR-X07) | US-07, US-08 |
| `conceptos` | Concepto de matrícula, concepto exclusivo de pregrado y conceptos marcados | US-07, US-08 |
| `generador_solicitud` | Arma la `Solicitud` completa de un estudiante válido | US-07, US-08, US-11 |

### Aplicación — `app/application/`

| Componente | Responsabilidad | Historias |
|---|---|---|
| `puertos` | Interfaces que implementa la infraestructura: `LectorPlantilla`, `AlmacenamientoArchivos`, `RepositorioAcademico`, `RepositorioSolicitudes`, `FuenteReglas`, `FuenteFestivos`, `ProveedorIdentidad`, `Reloj` | — |
| `procesar_lote` | UC-01: carga y procesamiento síncrono del lote, con el límite propio de 90 s desde que llega la petición (AD-31, AD-34), los 30 s de la fase previa (AD-34), el bloqueo por estudiante (AD-32) y el corte después de 5 fallas de conexión seguidas a MySQL (AD-35) | US-02 a US-12 |
| `consultar_lotes` | UC-02: historial paginado | US-13 |
| `autorizar_usuario` | UC-03: verifica que el usuario tenga el rol ARC | US-01 |
| `errores` | Errores de aplicación: `ArchivoNoPermitido`, `FormatoPlantillaInvalido`, `DependenciaNoDisponible`, `RespuestaInvalida`, `NoAutenticado`, `AccesoDenegado`, `ParametrosConsultaInvalidos`, `ErrorPersistencia`, `ErrorConexionBD` (un `ErrorPersistencia` que cuenta para el corte, AD-35) y `BloqueoNoObtenido` | — |
| `presupuesto` | `Plazo` y `PlazoVencido`: el plazo del lote y el de la fase previa, y cuánto tiempo le queda a cada llamada (AD-34). *Nuevo en U1 NFR Design* | US-12 |

### Infraestructura — `app/infrastructure/`

| Componente | Implementa | Responsabilidad |
|---|---|---|
| `config/ssm` | — | Lee secretos de SSM Parameter Store (`SecureString`) con boto3 al arrancar cada proceso y los guarda como `SecretStr`; un cambio de contraseña se toma con un despliegue nuevo (N18) |
| `db/motores` | — | Motores SQLAlchemy de Oracle (`oracle+oracledb`, modo thin) y MySQL (`mysql+pymysql`), con TLS, tiempos de espera y pools por proceso (MySQL 4 + 2, Oracle 2 + 2); `innodb_lock_wait_timeout` de 5 s (AD-34) |
| `db/captura_sql` | — | Listener `before_cursor_execute`: guarda el texto SQL (sin valores) en el contexto de la petición para la auditoría |
| `oracle/repositorio_academico` | `RepositorioAcademico` | Consultas de solo lectura, en bloque, con parámetros enlazados y `call_timeout` según el plazo de la fase previa (AD-34) |
| `mysql/repositorio_solicitudes` | `RepositorioSolicitudes` | Registro y listado de `solicitudLote`; cancelación de las sin imprimir en su propia transacción y una transacción por cada solicitud nueva (AD-30); bloqueo con nombre por estudiante entre la cancelación y el guardado (AD-32). `SesionFilas`: una conexión para todas las filas del lote, ninguna sentencia después del plazo y las fallas de conexión separadas de los demás errores (AD-34, AD-35) |
| `s3/almacenamiento_s3` | `AlmacenamientoArchivos` | Guarda el archivo en el bucket privado con cifrado del lado del servidor; 2 s para conectar, 5 s de respuesta y un reintento (AD-34) |
| `xls/lector_xlrd` | `LectorPlantilla` | Lee el `.xls` en memoria con xlrd 2.x y devuelve solo las celdas con contenido |
| `wso2/proveedor_identidad` | `ProveedorIdentidad` | Valida el token en `/oauth2/userinfo` con el cliente de `http` en cada petición, sin caché (AD-09): 2 s para conectar, 5 s de respuesta y un reintento si falla la conexión |
| `parametros/fuente_reglas` | `FuenteReglas` | Cliente de "parametros" en solo lectura: `GET /v1/parametro/{id}` por cada regla, con los ids tomados de la configuración. Extrae `Data` del sobre CRUD (`Status` como texto), exige `Activo` verdadero (AD-22) y convierte el valor según el mapeo de AD-21. Lee las 17 reglas en paralelo, 8 a la vez y con 10 s para todas (AD-34) |
| `festivos/fuente_festivos` | `FuenteFestivos` | Origen de los festivos (D5) |
| `reloj` | `Reloj` | Hora actual en America/Bogota y reloj monotónico para los plazos |
| `http` | — | Una sesión de requests por hilo, un reintento si falla la conexión y sin seguir redirecciones; una sola función hace las llamadas HTTP (AD-08, AD-34). *Nuevo en U1 NFR Design* |
| `registro` | — | Formateador JSON y filtro de `request_id` para los registros de la aplicación y de gunicorn (AD-24). *Nuevo en U1 NFR Design* |

### Interfaces — `app/interfaces/`

| Componente | Responsabilidad | Historias |
|---|---|---|
| `routers/estado` | Blueprint sin prefijo: `GET /`, `GET /health` | — |
| `routers/lotes` | Blueprint `/v1/lotes`: `POST`, `GET` | US-02, US-13 |
| `controllers/estado_controller` | Respuestas de estado | — |
| `controllers/lotes_controller` | Lee la petición, llama al caso de uso y arma la respuesta | US-02, US-12, US-13 |
| `schemas/lotes` | Modelos pydantic de parámetros y respuestas (`ConsultaLotes`, `ResumenLoteDTO`, `RechazoDTO`, `LoteDTO`) | US-12, US-13 |
| `schemas/respuesta` | Sobre `{Success, Status, Message, Data}` y `Metadata`; mensajes por defecto por código | Todas |
| `middlewares/contexto_peticion` | El primero: guarda la hora de llegada (`recibida_en`) y el `request_id`, y agrega `X-Request-Id` a la respuesta (AD-33, AD-34). *Nuevo en U1 NFR Design* | US-12, US-14 |
| `middlewares/cors` | CORS (AD-14) | — |
| `middlewares/autenticacion` | Token obligatorio en `/v1/*` (401) y rol ARC (403) | US-01 |
| `middlewares/auditoria` | Log JSON por petición a `/v1/*` (AD-10, AD-11) | US-14 |
| `middlewares/cabeceras_seguridad` | Las 10 cabeceras de `security_headers.go` en todas las respuestas y `Cache-Control: no-store` en `/v1/*` (AD-36). La cabecera `Server` vacía la pone `gunicorn.conf.py` | — |
| `middlewares/trazas` | *No va en el MVP (AD-33)*: las trazas se agregan después con OpenTelemetry. Las peticiones se siguen con `request_id` | — |
| `middlewares/errores` | Convierte errores en el sobre institucional; nunca expone trazas ni mensajes internos | US-10 |

## recibos_mf

| Componente | Responsabilidad | Historias |
|---|---|---|
| `core/` | Lo que trae `oas_cliente`: entorno (URL base de la API), sesión y token del core (D9) | US-01 |
| `shared/` | Mensajes de error, indicador de carga y lectura del sobre de respuesta | Todas |
| `features/lotes/pages/carga-lote` | Selecciona el `.xls`, lo envía, bloquea un segundo envío mientras procesa y muestra el resumen | US-02, US-12 |
| `features/lotes/components/resumen-lote` | Presentación: totales, tabla de los que se subieron (fila, código) y tabla de los que no (fila, código, motivo) | US-12 |
| `features/lotes/pages/historial-lotes` | Tabla paginada de lotes (usuario, fecha, archivo, IP) | US-13 |
| `features/lotes/services/lotes.service` | Único acceso a la API: `cargarLote`, `listarLotes` | US-02, US-12, US-13 |
| `features/lotes/models` | Interfaces TypeScript del contrato (`api-contract.md`) | — |

Reglas del frontend: sin `localStorage` ni cookies para token o datos personales; solo el escape por defecto de Angular (sin `innerHTML` armado a mano); Angular Material con el tema del root.
