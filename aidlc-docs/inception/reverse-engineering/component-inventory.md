# Inventario de componentes

- Etapa: INCEPTION → Reverse Engineering (2026-11-25)
- "Paquete" = cada carpeta de primer nivel con código o artefactos propios: un bloque de weboffice, una librería o un conjunto de documentos

## Paquetes de aplicación

- `weboffice/bloque/registro_lote_recibo` — Carga de solicitudes de recibo por lote. Es el sistema que se migra.
- `weboffice/bloque/admin_consultasCoordinador` — Consultas de notas de Admisiones, Registro y Control; el nombre dice "coordinador" por error (RE-19). Queda para la Fase 2 (C5).
- `weboffice/bloque/admin_historicoPorEstudiante` — Formulario del histórico de recibos por estudiante. Fuera del MVP (Fase 2).
- `weboffice/bloque/admin_solicitudCoordinador` — "Solicitados": lista las solicitudes sin imprimir y genera los recibos en Oracle. Consume lo que escribe el lote; no se migra y no cambia (RF-16). Está en el workspace desde el 2026-11-25 (RE-20).

## Paquetes de infraestructura

- Ninguno. No hay CDK, Terraform, CloudFormation ni scripts de despliegue. Los ejemplos de `lineamientos_oas/generacion_de_apis/cicd/` (`.drone.yml`, `Dockerfile`) son plantillas, no infraestructura de este sistema.

## Paquetes compartidos

- `weboffice/clase` — Utilidades — `funcionGeneral.class.php`, clase base de los bloques.
- `utils_oas` — Utilidades y clientes (Go, Beego) — 21 paquetes institucionales. Detalle abajo.
- `lineamientos_oas` — Documentación — Lineamientos de la OAS/OATI (L1–L50 en `institutional-guidelines-analysis.md`).
- `documentacion/plantillas-recibos` — Modelos de entrada — Plantillas `.xls` oficiales.

### Paquetes de `utils_oas`

| Paquete | Uso para recibos (`utils-oas-analysis.md`) |
|---|---|
| `apiStatusLib` | Sí: contrato de `GET /` |
| `auditoria` | Sí: campos del log; se corrigen la caché del token (AD-09) y la captura de SQL (AD-10) |
| `customerrorv2`, `requestresponse` | Sí: sobre de respuesta (AD-04) |
| `security` | Sí: las 10 cabeceras |
| `ssm`, `database` | Sí: convención de rutas en SSM (OQ-T-7) |
| `xray` | Sí: trazas |
| `time_bogota` | Sí: zona America/Bogota (AD-15) |
| `request` | Sí: extracción de `Data` y reenvío del token (AD-20, A11) |
| `customerror`, `errorctrl`, `errorctrlPrueba`, `errorhandler`, `formatdata`, `optimize`, `planeacion`, `requestmanager`, `responseformat`, `ruler`, `xlsx2pdf` | No |

## Paquetes de pruebas

- No hay paquetes de pruebas separados.
- `utils_oas/apiStatusLib/apistatus_test.go` — Unitaria — Prueba `Init`.
- `utils_oas/xray/xray_test.go` — Unitaria — Prueba segmentos y la detección de localhost.
- `lineamientos_oas/generacion_de_apis/src/*.jmx` — Carga (JMeter) — Ejemplos de los lineamientos; no prueban este sistema.
- `weboffice` — Ninguna prueba.

## Referenciados que no están en el repositorio

| Componente | Lo usa | Efecto |
|---|---|---|
| `index.php`, `bloque.class.php`, `sql.class.php` base | Todos los bloques | El sistema no se puede ejecutar (R16) |
| `dbConexion`, `sesion`, `datosGenerales`, `validacion_usu_wo`, `encriptar`, `alerta`, `html`, `navegacion` | Conexión, sesión, permisos, presentación | Comportamiento deducido solo por el uso (`api-documentation.md`) |
| `datosSolicitud.class.php` | Fechas de pago por facultad | Columnas de `fechaPagoFacultad` desconocidas (D4, RE-08) |
| `calendario.class.php` | Festivos | Origen de los festivos desconocido (D5) |
| `subir_archivo.class.php`, `reader.class.php` | Carga y lectura del `.xls` | Versión del lector desconocida |
| `estilo/basico/tema.php`, `estilo.php`, `funciones.js` | Presentación | Ninguno para la migración |
| `admin_generados`, `borrar_registro` | Recibos generados e histórico; borrado de una solicitud desde "Solicitados" | Ninguno para el lote: lo que lee "Solicitados" ya se conoce por su código (RE-20, RE-21). No se sabe qué estado deja `borrar_registro` |
| `adminReportesExcelCoordinador`, `registro_notasDocente`, `registro_cargarNovedadesNotasCurso`, `registro_plan_trabajo`, `adminListaCursos`, `admin_usuario` | Módulo de notas de ARC (enlaces y redirecciones) | Ninguno para recibos |

## Unidades nuevas (todavía no existen)

- `recibos_service` (U1) y `recibos_mf` (U2), en la raíz del workspace (`unit-of-work.md`).

## Total

- **Total de paquetes**: 8
- **Aplicación**: 4
- **Infraestructura**: 0
- **Compartidos**: 4 (`utils_oas` tiene 21 paquetes Go dentro)
- **Pruebas**: 0 paquetes separados (2 archivos de prueba en `utils_oas` y 2 planes de JMeter de ejemplo)
