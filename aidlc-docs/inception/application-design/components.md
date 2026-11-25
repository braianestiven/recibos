# Componentes

Las dependencias apuntan hacia adentro: `interfaces` → `application` → `domain`. `infrastructure` implementa los puertos de `application`. `domain` no importa Flask, SQLAlchemy, boto3 ni httpx.

## recibos_service

### Raíz (lineamiento OAS)

| Componente | Responsabilidad |
|---|---|
| `api.py` | `create_app()`: crea la app Flask, conecta adaptadores con casos de uso, registra Blueprints y middlewares, y expone `app` para gunicorn (`api:app`) |
| `conf/conf.py` | Lee variables `RECIBOS_SERVICE_*` (L33); `DEBUG=False` por defecto (corrige L8); ningún endpoint devuelve estos valores |
| `swagger/swagger.yml` | Especificación OpenAPI; la usa flasgger y se publica en WSO2 AM |
| `gunicorn.conf.py` | Workers, hilos y tiempo de espera (se fijan en NFR Design) |

### Dominio — `app/domain/` (Python puro, cobertura 100%)

| Componente | Responsabilidad | Historias |
|---|---|---|
| `modelos` | Entidades y objetos de valor: `TipoPlantilla`, `HojaPlantilla`, `FilaPlantilla`, `Usuario`, `Estudiante`, `Periodo`, `ContextoCarrera`, `FechasPago`, `Cuota`, `Solicitud`, `MotivoRechazo`, `Rechazo`, `Procesado`, `ResumenLote`, `NuevoLote`, `Lote`, `Pagina` | Todas |
| `reglas` | `ReglasLiquidacion`: todos los valores que llegan de "parametros" (estados, eventos, IDs de conceptos y exenciones, porcentajes, mapas columna → id, plazo de la fecha extraordinaria). Las fechas de pago vienen de la plantilla (C3) | US-06 a US-08, US-15 |
| `plantillas` | Estructura de las tres plantillas (texto de A1, fila inicial, número de columnas, encabezados, rangos de columnas), identificación del tipo, validación de formato y extracción de filas | US-03, US-04, US-05 |
| `validacion_filas` | Reglas de fila: código numérico; en posgrado, número de cuotas obligatorio de 1 a 3, fecha válida con año completo para cada cuota, porcentajes 0–100 y suma 100 | US-06, US-08 |
| `validacion_estudiante` | Validaciones académicas en el orden actual: existencia, valor de matrícula, estado, proyecto activo, terminación de materias | US-06 |
| `fechas` | Sumar días calendario y saltar festivos | US-08 |
| `cuotas` | Cuota única de pregrado con las fechas de la plantilla (C3); cuotas de posgrado con porcentajes por defecto por posición | US-07, US-08 |
| `exenciones` | Como máximo un descuento más la votación; con más de un descuento la fila no se sube (C2); la votación, marcada o automática (la automática solo con un descuento marcado: C1, C6, A14), se registra si el descuento y la votación juntos no pasan de 100%; si pasan, queda solo el descuento (C7) | US-07, US-08 |
| `conceptos` | Concepto de matrícula, concepto exclusivo de pregrado y conceptos marcados | US-07, US-08 |
| `generador_solicitud` | Arma la `Solicitud` completa de un estudiante válido | US-07, US-08, US-11 |

### Aplicación — `app/application/`

| Componente | Responsabilidad | Historias |
|---|---|---|
| `puertos` | Interfaces que implementa la infraestructura: `LectorPlantilla`, `AlmacenamientoArchivos`, `RepositorioAcademico`, `RepositorioSolicitudes`, `FuenteReglas`, `FuenteFestivos`, `ProveedorIdentidad`, `Reloj` | — |
| `procesar_lote` | UC-01: carga y procesamiento síncrono del lote | US-02 a US-12 |
| `consultar_lotes` | UC-02: historial paginado | US-13 |
| `autorizar_usuario` | UC-03: verifica que el usuario tenga el rol ARC | US-01 |
| `errores` | Errores de aplicación: `ArchivoNoPermitido`, `FormatoPlantillaInvalido`, `DependenciaNoDisponible`, `NoAutenticado`, `AccesoDenegado`, `ParametrosConsultaInvalidos` | — |

### Infraestructura — `app/infrastructure/`

| Componente | Implementa | Responsabilidad |
|---|---|---|
| `config/ssm` | — | Lee secretos de SSM Parameter Store (`SecureString`) con boto3 |
| `db/motores` | — | Motores SQLAlchemy de Oracle (`oracle+oracledb`, modo thin) y MySQL (`mysql+pymysql`), con TLS y pool de conexiones |
| `db/captura_sql` | — | Listener `before_cursor_execute`: guarda el texto SQL (sin valores) en el contexto de la petición para la auditoría |
| `oracle/repositorio_academico` | `RepositorioAcademico` | Consultas de solo lectura, en bloque, con parámetros enlazados |
| `mysql/repositorio_solicitudes` | `RepositorioSolicitudes` | Registro y listado de `solicitudLote`; cancelación de las sin imprimir en su propia transacción y una transacción por cada solicitud nueva (AD-30) |
| `s3/almacenamiento_s3` | `AlmacenamientoArchivos` | Guarda el archivo en el bucket privado con cifrado del lado del servidor |
| `xls/lector_xlrd` | `LectorPlantilla` | Lee el `.xls` en memoria con xlrd 2.x y devuelve solo las celdas con contenido |
| `wso2/proveedor_identidad` | `ProveedorIdentidad` | Valida el token en `/oauth2/userinfo` con httpx en cada petición, sin caché (AD-09) |
| `parametros/fuente_reglas` | `FuenteReglas` | Cliente de "parametros" en solo lectura: `GET /v1/parametro/{id}` por cada regla, con los ids tomados de la configuración. Extrae `Data` del sobre CRUD (`Status` como texto), exige `Activo` verdadero (AD-22) y convierte el valor según el mapeo de AD-21 |
| `festivos/fuente_festivos` | `FuenteFestivos` | Origen de los festivos (D5) |
| `reloj` | `Reloj` | Hora actual en America/Bogota |

### Interfaces — `app/interfaces/`

| Componente | Responsabilidad | Historias |
|---|---|---|
| `routers/estado` | Blueprint sin prefijo: `GET /`, `GET /health` | — |
| `routers/lotes` | Blueprint `/v1/lotes`: `POST`, `GET` | US-02, US-13 |
| `controllers/estado_controller` | Respuestas de estado | — |
| `controllers/lotes_controller` | Lee la petición, llama al caso de uso y arma la respuesta | US-02, US-12, US-13 |
| `schemas/lotes` | Modelos pydantic de parámetros y respuestas (`ConsultaLotes`, `ResumenLoteDTO`, `RechazoDTO`, `LoteDTO`) | US-12, US-13 |
| `schemas/respuesta` | Sobre `{Success, Status, Message, Data}` y `Metadata`; mensajes por defecto por código | Todas |
| `middlewares/cors` | CORS (AD-14) | — |
| `middlewares/autenticacion` | Token obligatorio en `/v1/*` (401) y rol ARC (403) | US-01 |
| `middlewares/auditoria` | Log JSON por petición a `/v1/*` (AD-10, AD-11) | US-14 |
| `middlewares/cabeceras_seguridad` | Las 10 cabeceras de `security_headers.go` en todas las respuestas | — |
| `middlewares/trazas` | Segmento de X-Ray por petición; dirección del daemon desde SSM | — |
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
