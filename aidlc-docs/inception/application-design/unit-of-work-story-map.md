# Historias por unidad

| Historia | U1 `recibos_service` | U2 `recibos_mf` | Estado |
|---|---|---|---|
| US-01 Iniciar sesión y acceder con el rol ARC | Validación del token en cada petición y del rol (middlewares) | Sesión desde el core, envío del token, acceso desde el menú | ✅ Lista |
| US-02 Cargar un archivo de lote | `POST /v1/lotes`: tipo, tamaño, S3, `solicitudLote` | Selección y envío del archivo; sin segundo envío mientras procesa | ✅ Lista |
| US-03 Formato de pregrado (13 columnas) | Especificación y validación de la plantilla | — | 🔒 D1 |
| US-04 Formato de posgrado por créditos | Especificación y validación de la plantilla | — | ✅ Lista |
| US-05 Formato de posgrado SMLV | Especificación y validación de la plantilla | — | 🔒 D2 |
| US-06 Validar estudiantes en Oracle | Validaciones académicas y lecturas en bloque | — | ✅ Lista |
| US-07 Solicitudes de pregrado | Cuota, exenciones y conceptos | — | ✅ Lista |
| US-08 Solicitudes de posgrado | Cuotas, fechas, exenciones y conceptos | — | 🔒 D5 (SMLV: D2) |
| US-09 Cancelar solicitudes sin imprimir | Cancelación en el periodo vigente | — | ✅ Lista |
| US-10 Guardar la solicitud completa o no guardarla | Transacción por estudiante | — | ✅ Lista |
| US-11 Entregar las solicitudes a "Solicitados" | Escritura en las tablas `solicitud*` | — | 🔒 D3, D4 |
| US-12 Ver el resumen del lote | `ResumenLote` en la respuesta | Pantalla de resumen y rechazados | ✅ Lista |
| US-13 Consultar el historial de lotes | `GET /v1/lotes` paginado | Tabla paginada | ✅ Lista |
| US-14 Auditoría de cada petición | Auditoría y registro de aplicación | — | ✅ Lista |
| US-15 Reglas desde "parametros" | Cliente de "parametros" | — | ✅ Lista |

Verificación: las 15 historias tienen unidad. U1 participa en las 15 y U2 en 4 (US-01, US-02, US-12, US-13). Ninguna queda solo en U2, porque toda regla de negocio y todo control de seguridad viven en U1.

## Requisitos no funcionales por unidad

| Requisito | U1 | U2 |
|---|---|---|
| RNF-1 Rendimiento (lote síncrono de 1000) | Procesamiento y tiempos de espera | Indicador de espera, sin segundo envío |
| RNF-2 Seguridad y cumplimiento | Todas las reglas SECURITY del backend | Token sin guardar, escape de Angular, cabeceras del servidor estático |
| RNF-3 Integridad de datos | Transacción por estudiante | — |
| RNF-4 Mantenibilidad | Clean Architecture y contrato OpenAPI | Estructura de `oas_cliente` |
| RNF-5 Observabilidad | Auditoría, registros y X-Ray | Registros de acceso |
| RNF-6 Pruebas | pytest, Hypothesis, cobertura y SonarQube | `*.spec.ts` y SonarQube |
| RNF-7 Costos | Infraestructura existente | Infraestructura existente |
| RNF-8 Plazo (test, 15/12/2026) | Primero en desplegarse | Después de U1 |
