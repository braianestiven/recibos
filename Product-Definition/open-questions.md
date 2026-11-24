# Preguntas abiertas para AI-DLC

Ambigüedades y decisiones pendientes detectadas durante Discovery.
AI-DLC debe resolverlas al inicio de Requirements Analysis.

Última generación: 2026-11-24T00:55:00Z

## Preguntas abiertas de Negocio (Visión)

### OQ-B-1: Fecha de reemplazo del sistema PHP
- **Sección de origen**: Resumen ejecutivo (Q5) / Riesgos y preguntas abiertas (Q18.1)
- **Pregunta**: ¿En qué fecha se retira PHP 5 y el sistema nuevo reemplaza definitivamente al actual en producción?
- **Razonamiento del usuario**: "1 indefinido"; "solo funcionan en paralelo para pruebas luego se reemplazan".
- **Ruta de resolución sugerida** (IA): Definirla con Admisiones, Registro y Control y la OATI después de la revisión de Seguridad en test (15/12/2026); idealmente antes de generar los recibos de 2027-1.

### OQ-B-2: Plantilla oficial de posgrado SMLV
- **Sección de origen**: Riesgos y preguntas abiertas (Q18.5)
- **Pregunta**: ¿Cuál es el archivo oficial vigente de `PLANTILLA GENERAL POSTGRADOS SALARIOS MINIMOS LEGALES`? ¿Tiene las mismas 29 columnas que la de créditos?
- **Razonamiento del usuario**: Encabezados pegados en el chat; en `documentacion/plantillas-recibos/` solo están pregrado y posgrado créditos (dos copias).
- **Ruta de resolución sugerida** (IA): Agregar el `.xls` a `documentacion/plantillas-recibos/` y verificarlo contra `interview/technical/templates-analysis.md`.

### OQ-B-3: Nueva plantilla de pregrado sin "Reingreso"
- **Sección de origen**: MVP OUT (Q16) / Riesgos (Q18.5) / C-3
- **Pregunta**: ¿Quién entrega la plantilla de pregrado modificada (13 columnas, sin "Reingreso") y cuándo? ¿Cambia también el texto de la celda A1 o la fila inicial? El sistema nuevo solo aceptará este formato (C-3).
- **Razonamiento del usuario**: "reingresos queda excluido y la plantilla tendra modificacione spara no incluirlo"; "c3 debe tomar 13".
- **Ruta de resolución sugerida** (IA): Admisiones, Registro y Control entrega la versión final antes de construir la validación de formato.

### OQ-B-4: Contrato detallado con "Solicitados"
- **Sección de origen**: Riesgos y preguntas abiertas (Q18.4) / Qué no debe cambiar (QB2, TB2)
- **Pregunta**: ¿Qué campos y estados de `solicitudRecibo` (y `solicitudCuota`, `solicitudExencion`, `solicitudConcepto`) lee "Solicitados", además de los estados 0 (sin imprimir) y 2 (cancelada)?
- **Razonamiento del usuario**: Tablas indicadas: Oracle `acasperi`, `acest`, `acestmat`, `acvlrscs`; MySQL `solicitudrecibo`.
- **Ruta de resolución sugerida** (IA): Obtener el código de "Solicitados" o su documentación; levantar el esquema MySQL real con los DBA.

### OQ-B-5: Base de datos para las pruebas en paralelo
- **Sección de origen**: Qué no debe cambiar (QB2) / C-3
- **Pregunta**: Las pruebas de cada sistema se evalúan de forma independiente (C-3). ¿Se ejecutan contra una copia de la base o contra la base real? Si es la real, la regla "cancelar solicitudes previas sin imprimir" puede cancelar solicitudes creadas por el otro sistema.
- **Razonamiento del usuario**: "a" (mismo `solicitudrecibo`); "las pruebas se evaluan independientes".
- **Ruta de resolución sugerida** (IA): Acordar con DBA un ambiente de pruebas con copia de datos de periodos anteriores.

### OQ-B-6: Migración de solicitudes históricas
- **Sección de origen**: MVP OUT (Q16)
- **Pregunta**: ¿Se necesita migrar o reprocesar solicitudes históricas, dado que el sistema nuevo usa la misma base MySQL?
- **Razonamiento del usuario**: Fila aceptada con fase "Por definir".
- **Ruta de resolución sugerida** (IA): Como la base se mantiene (QB2), probablemente no aplica; confirmarlo y cerrar.

## Preguntas abiertas Técnicas (Entorno técnico)

### OQ-T-1: Versiones de Angular y Node
- **Sección de origen**: Lenguajes (T5)
- **Pregunta**: ¿Qué versiones de Angular, TypeScript y Node se fijan? Los lineamientos recomiendan Node 16, que ya no tiene soporte.
- **Razonamiento del usuario**: T5 aceptado con la nota "por confirmar".
- **Ruta de resolución sugerida** (IA): Tomar las versiones de la rama `feature/clientes_nuevos` de `oas_cliente` y verificar compatibilidad con `single-spa-angular` y con una versión LTS de Node.

### OQ-T-2: ¿Existe una versión Python de `utils_oas`?
- **Sección de origen**: Frameworks y librerías (T9)
- **Pregunta**: ¿La OATI tiene o planea una librería Python equivalente a `utils_oas`?
- **Razonamiento del usuario**: Sin respuesta.
- **Ruta de resolución sugerida** (IA): Consultar al grupo de Arquitectura; si no existe, implementar los contratos dentro de `recibos_service` según `interview/technical/utils-oas-analysis.md`.

### OQ-T-4: Ejemplo de prueba Python
- **Sección de origen**: Ejemplos de código (T28)
- **Pregunta**: ¿Hay una prueba Python de referencia en la OATI? Los lineamientos solo cubren pruebas de Beego/Go.
- **Razonamiento del usuario**: T28 omitido (convenciones de pytest).
- **Ruta de resolución sugerida** (IA): Si no existe, definir en Construction un patrón base de pytest y usarlo como referencia.

### OQ-T-5: Destino de los logs de auditoría
- **Sección de origen**: Servicios en la nube (T11)
- **Pregunta**: ¿Los logs JSON de auditoría van a CloudWatch Logs u otro destino definido por infraestructura? ¿Cuál es su retención?
- **Razonamiento del usuario**: CloudWatch Logs aceptado "por confirmar con infraestructura".
- **Ruta de resolución sugerida** (IA): Confirmar con el integrante de infraestructura del equipo (T4).

### OQ-T-7: Convención SSM para las credenciales de MySQL
- **Sección de origen**: Seguridad (T20)
- **Pregunta**: `utils_oas/database` define la ruta SSM para una sola base (`/{parameterStore}/{appname}/db/...`). ¿Qué ruta usan las credenciales de MySQL y cuál es el valor de `parameterStore`?
- **Razonamiento del usuario**: T20 aceptado ("equivalente para MySQL").
- **Ruta de resolución sugerida** (IA): Definirla con infraestructura y documentarla en el README de `recibos_service`.

### OQ-T-8: Núcleo del framework y fuentes de datos implícitas
- **Sección de origen**: Sistema existente (TB1, TB2)
- **Pregunta**: Faltan en el repositorio clases con lógica necesaria para la equivalencia: `datosSolicitud.class.php` (consulta `fechaPagoFacultad`), `calendario.class.php` (origen de los **festivos**), `datosGenerales.class.php` (año y periodo), `validacion_usu_wo.class.php`. ¿Dónde está ese código? ¿Esos datos pasan ahora al servicio "parametros" (C-1)?
- **Razonamiento del usuario**: El repositorio entregado es un extracto (`existing-system-analysis.md` §1).
- **Ruta de resolución sugerida** (IA): Obtener el núcleo del framework (sin credenciales) o la definición de esas consultas y tablas con los DBA; cruzarlo con el contrato de OQ-T-11.

### OQ-T-9: Modelo de datos aprobado y esquema MySQL real
- **Sección de origen**: Restricciones (Q9) / Qué no debe cambiar (TB2)
- **Pregunta**: ¿Dónde está el modelo de datos aprobado por el comité y el DDL real de las tablas MySQL `solicitud*`, `exencion` y `fechaPagoFacultad`?
- **Razonamiento del usuario**: "La aprobación del modelo de datos por el comité. ya existe la base por los DBA. ya existe".
- **Ruta de resolución sugerida** (IA): Agregarlo a `documentacion/` para que AI-DLC lo cargue en Requirements Analysis.

### OQ-T-10: Límites del archivo cargado y retención en S3
- **Sección de origen**: Seguridad (T19) / Servicios en la nube (T11)
- **Pregunta**: ¿Cuál es el tamaño máximo del archivo y cuánto tiempo se conservan las plantillas cargadas en S3 (Ley 1581)?
- **Razonamiento del usuario**: T11 y T19 aceptados con "tamaño máximo" y "retención definida" sin valores.
- **Ruta de resolución sugerida** (IA): Definirlo con Seguridad y Admisiones, Registro y Control.

### OQ-T-11: Contrato del servicio externo "parametros"
- **Sección de origen**: Consolidación final (C-1) / Mensajería e integración
- **Pregunta**: ¿Cuáles son los endpoints, la autenticación, el formato de respuesta y las reglas de actualización del servicio "parametros", del que `recibos_service` consulta y actualiza conceptos, exenciones, fechas de pago por facultad, porcentajes por defecto, estados permitidos, eventos de calendario, plazo de la fecha extraordinaria y mapa columna → exención?
- **Razonamiento del usuario**: "para c1 consultara y actualizara a un servicio externo de nopmbre parametros, la sintaxis se explicara despues por ahora debe quedar indicado".
- **Ruta de resolución sugerida** (IA): El usuario entregará la sintaxis más adelante. Hasta entonces, modelar el acceso como un puerto en `app/application/` con un adaptador en `app/infrastructure/` para no bloquear el resto del diseño.

### Cerradas en la consolidación final
- OQ-T-3 (mecanismo asíncrono): cerrada — el procesamiento es síncrono (C-2).
- OQ-T-6 (nombres de repositorio): cerrada — `recibos_service` / `recibos_mf` aceptados (C-5).

---

## Contradicciones entre roles (Visión ↔ Entorno técnico) — resueltas

Detectadas en la consolidación final al cruzar `vision-document.md` con `technical-environment.md`. Resueltas por el usuario el 2026-11-24.

| ID | Contradicción | Severidad | Resolución del usuario |
|---|---|---|---|
| C-1 | Reglas "paramétricas" (Q10, MVP) sin tabla donde guardarlas (TB2, T12) | Alta | Se consultan y actualizan en el servicio externo **"parametros"**; sintaxis por definir → OQ-T-11 |
| C-2 | Procesamiento asíncrono (T15) sin almacenamiento de estado del lote | Alta | El procesamiento es **síncrono**; un lote de hasta 1000 estudiantes se procesa en la misma petición |
| C-3 | Plantilla de pregrado de 13 columnas frente a lotes anteriores de 14 y pruebas en paralelo | Alta | El sistema nuevo **solo acepta 13 columnas**; las pruebas de cada sistema se evalúan de forma independiente |
| C-4 | Métrica de equivalencia sin herramienta asignada | Media | Se define en una **etapa posterior** |
| C-5 | Nombres de repositorio frente al lineamiento OAS | Media | **No importa** en este caso; nombres aceptados |
| C-6 | Plazo frente al alcance | Media | **No aplica**: el desarrollo será guiado por IA |

Verbatim: "para c1 consultara y actualizara a un servicio externo de nopmbre parametros, la sintaxis se explicara despues por ahora debe quedar indicado, c2 dejalo sincrono, c3 debe tomar 13, las pruebas se evaluan independientes, c4 sera posterior, c5 en este caso no importa, c6 el desarrollo es guiado por ia por lo que no aplica el alcance, b"

## Resumen

Total de preguntas abiertas: 15 (Negocio: 6, Técnicas: 9)
Contradicciones entre roles: 6 detectadas, 6 resueltas.

Prioridad sugerida: OQ-T-11 (servicio "parametros"), OQ-T-8 (festivos y fechas de pago), OQ-T-9 (DDL), OQ-B-2 y OQ-B-3 (plantillas) → resto.

AI-DLC debe cargar este archivo durante Requirements Analysis y resolver cada entrada
antes de pasar a User Stories o Application Design.
