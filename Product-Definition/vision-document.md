# Documento de Visión — Migración del módulo de recibos por lote (weboffice)

Generado por aidlc-discovery el 2026-11-23T23:05:00Z.
Tipo de proyecto: Brownfield (migración / modernización)

---

## Resumen ejecutivo

La "Migración del módulo de recibos por lote (weboffice)" es una modernización del módulo con el que la Oficina de Admisiones, Registro y Control genera de forma masiva las solicitudes de recibo de pago de matrícula. El producto permite cargar una plantilla con códigos de estudiantes y generar automáticamente las solicitudes de recibo de pago con sus cuotas, exenciones y conceptos, validando el estado y la carrera de cada estudiante. El problema que resuelve es la obsolescencia tecnológica: el módulo actual corre sobre PHP 5 y un framework propio sin soporte. El resultado buscado es retirar PHP 5 y migrar el módulo a un nuevo stack (frontend Angular, backend Python), con una prueba de concepto para el periodo 2027-1 y la solución desplegada en el ambiente de pruebas el 15 de diciembre de 2026, lista para la revisión de Seguridad.

---

## Contexto de negocio

### Planteamiento del problema

El módulo de carga masiva de solicitudes de recibo funciona sobre PHP 5 y un framework propio de 2005–2009 que ya no tiene soporte. El código no corre en versiones actuales de PHP, solo lee Excel `.xls`, no tiene pruebas y su núcleo no está versionado. Las reglas de cuotas, exenciones y conceptos están escritas directamente en el código y se cambian comentando líneas. Por eso cada periodo depende de las pocas personas que conocen el código.

Además, tiene riesgos de seguridad: el SQL se arma concatenando texto y el navegador puede alterar los permisos. También puede dejar solicitudes incompletas si la carga falla a mitad de camino. La idea es migrarlo a un nuevo stack donde el frontend es Angular y el backend es Python.

### Motivadores de negocio

El proyecto se hace ahora por tres razones: las vulnerabilidades de seguridad del sistema actual, la necesidad de facilitar la integración con otros sistemas y la mantenibilidad. No hay una fecha externa obligatoria, pero sí un hito interno: la solución debe estar en el ambiente de pruebas el 15 de diciembre de 2026.

### Usuarios y partes interesadas

| Rol | Descripción | Necesidad principal |
|------|-------------|--------------|
| Admisiones, Registro y Control | Único rol operativo. Gestiona los recibos de todas las carreras y absorbe los roles actuales de coordinador (4), asistente (110) y secretario (114) | Generar solicitudes masivas de recibo para cualquier proyecto curricular |
| Estudiante (usuario indirecto) | Recibe el recibo de pago | Un recibo con el valor, las cuotas, las exenciones y las fechas correctas |

### Restricciones de negocio

- **Fecha límite: 15 de diciembre de 2026.** La solución debe estar desplegada en el ambiente de pruebas (test), lista para iniciar la revisión de Seguridad.
  - Ya existen: el modelo de datos aprobado por el comité, la base creada por los DBA y el registro en WSO2.
  - Las pruebas de carga y de usuario se hacen en el ambiente de desarrollo.
  - La revisión de Seguridad se hace en el ambiente de pruebas.
- **Normativa y seguridad:** política de protección de datos personales (Ley 1581 de 2012), mínimo privilegio, logs siempre habilitados, gestión segura de sesiones, control de dependencias y cabeceras de seguridad HTTP.
- **Políticas institucionales:** lineamientos para aplicativos de la OAS/OATI (https://github.com/udistrital/lineamientos_oas). **Aplican al código, no a las bases de datos.**

### Métricas de éxito

| Métrica | Estado actual | Estado objetivo | Método de medición |
|--------|---------------|--------------|--------------------|
| PHP 5 en el servidor del módulo | PHP 5 | Ningún componente en PHP 5 | Inventario del servidor |
| Coincidencia con el sistema actual | — | 100% de las solicitudes iguales en cuotas, exenciones y conceptos en los lotes de prueba | Comparación de resultados; pruebas de cada sistema evaluadas de forma independiente; herramienta de comparación por definir en etapa posterior |
| Solicitudes incompletas por fallos en la carga | Pueden ocurrir (sin transacciones) | 0 | Consulta de solicitudes sin cuotas o sin conceptos |
| Vulnerabilidades críticas o altas | Inyección SQL, XSS, permisos manipulables | 0 | Escaneo de seguridad |
| Cambio de reglas en cada periodo | Se edita y se comenta código | 100% de las reglas son paramétricas o llegan en la plantilla; ningún cambio de código por periodo | Registro de cambios por periodo |

---

## Visión completa

### Declaración de visión

Admisiones, Registro y Control genera las solicitudes de recibo de pago de cualquier proyecto curricular desde una aplicación segura que sigue la arquitectura OAS. Las reglas de cuotas, exenciones y conceptos se ajustan por parámetros o por la plantilla, sin tocar código, y cada carga queda completa y registrada.

### Áreas funcionales

- **Carga y validación de plantillas:** subir el archivo, identificar el tipo (pregrado, posgrado por créditos o posgrado en salarios mínimos) y validar el formato.
- **Validación académica del estudiante:** estado, carrera y terminación de materias, contra Oracle académico.
- **Generación de solicitudes:** cuotas, porcentajes y fechas de pago (ordinaria y extraordinaria, saltando festivos), exenciones (incluido el certificado electoral) y conceptos.
- **Administración de parámetros:** conceptos, exenciones, fechas de pago por facultad, porcentajes por defecto, estados permitidos y eventos del calendario.
- **Resultados y trazabilidad:** resumen de procesados y rechazados con motivo, historial de lotes y auditoría.
- **Consulta histórica por estudiante:** solicitudes y recibos generados (hoy `admin_historicoPorEstudiante` / `admin_generados`).
- **Integración con la generación e impresión del recibo:** entregar las solicitudes al módulo que produce el recibo (hoy "Solicitados").

### Extensiones futuras (no comprometidas)

Ninguna. La visión anterior representa todo el alcance considerado.

---

## Alcance de la primera versión — Funcionalidades IN

| Funcionalidad | Justificación | Usuario principal |
|---------|-----------|-------------------|
| Carga de las 3 plantillas vigentes (pregrado, posgrado por créditos, posgrado en salarios mínimos), con validación de formato | Es por donde empieza el proceso actual | Admisiones, Registro y Control |
| Validación del estudiante contra Oracle académico: estado, carrera y terminación de materias | Sin esto se generan solicitudes inválidas | Admisiones, Registro y Control |
| Generación de solicitudes con cuotas, exenciones y conceptos, igual que el sistema actual (con los cambios acordados, ver "Reglas acordadas") | Es la capacidad principal y la métrica de coincidencia del 100% | Admisiones, Registro y Control |
| Cancelación automática de las solicitudes anteriores sin imprimir del mismo estudiante | Regla vigente del sistema actual | Admisiones, Registro y Control |
| Reglas parametrizadas (conceptos, exenciones, fechas por facultad, porcentajes, estados) que se consultan y actualizan en el **servicio externo "parametros"**, sin pantalla de administración propia (contrato del servicio por definir, OQ-T-11) | Meta: ningún cambio de código por periodo | OATI / Admisiones, Registro y Control |
| Cada solicitud se guarda completa o no se guarda | Meta: ninguna solicitud incompleta | Admisiones, Registro y Control |
| Resumen del lote: procesados y rechazados, con el motivo | Ya existe hoy y se usa para gestionar los rechazos | Admisiones, Registro y Control |
| Historial de lotes y auditoría: quién, cuándo, qué archivo y desde qué IP | Restricción: logs siempre habilitados | Admisiones, Registro y Control / Seguridad |
| Inicio de sesión y rol único con WSO2 y `configuracion_cliente` | Restricción de seguridad y lineamientos OAS | Admisiones, Registro y Control |
| Solicitudes escritas en `solicitudrecibo` (MySQL) para que el módulo de impresión actual ("Solicitados") siga funcionando | Sin esto no se pueden imprimir los recibos | Admisiones, Registro y Control / Estudiante |

### Reglas acordadas respecto al sistema actual

- **Sin reingreso:** se excluye la exención "Reingreso" (C-045558). La plantilla de pregrado pasa de 14 a 13 columnas.
- **Sin pago diferido en pregrado:** cada solicitud de pregrado lleva una sola cuota al 100%, con las fechas de pago de la facultad. Se elimina también la variante de cuotas al 0% ("COVID").
- **Sin número de cuotas en pregrado:** el sistema nuevo no lee la columna "Seguro Estudiantil" como cuota, como hace hoy por error.
- **Solo la plantilla nueva de pregrado:** el sistema nuevo acepta únicamente la plantilla de 13 columnas. Las pruebas del sistema nuevo y del actual se evalúan de forma independiente (no se carga el mismo archivo en ambos).

### Decisiones de la consolidación final (2026-11-24)

- C-1: las reglas parametrizadas se consultan y actualizan en el servicio externo **"parametros"**; su sintaxis se definirá después.
- C-2: el procesamiento del lote es **síncrono**.
- C-3: el sistema nuevo solo acepta la plantilla de pregrado de 13 columnas; pruebas independientes.
- C-4: la herramienta de comparación de equivalencia se define en una etapa posterior.
- C-5: los nombres de repositorio `recibos_service` / `recibos_mf` se aceptan.
- C-6: el desarrollo será guiado por IA; el riesgo de alcance frente al plazo no se considera aplicable.

### Prioridades no funcionales de la primera versión

1. **Tiempo de respuesta:** la carga y el procesamiento de un lote deben ser ágiles para el usuario.
2. **Seguridad y protección de datos:** cumplir la Ley 1581 de 2012 y el checklist de seguridad de la OAS (sin secretos en el código, control de acceso, sesiones seguras, logs, cabeceras, control de dependencias).
3. **Costos bajos:** aprovechar la infraestructura y los registros ya existentes (modelo aprobado, bases actuales, WSO2).

---

## Alcance de la primera versión — Funcionalidades OUT

| Funcionalidad excluida | Motivo | Fase objetivo |
|------------------|--------|--------------|
| Pantalla para administrar parámetros (conceptos, exenciones, fechas, porcentajes, estados) | Los parámetros se cargan en tablas; la pantalla no alcanza antes del 15/12/2026 | Fase 2 |
| Consulta histórica por estudiante (`admin_historicoPorEstudiante` / `admin_generados`) | No hace falta para generar las solicitudes de 2027-1 | Fase 2 |
| Generar e imprimir el recibo en el sistema nuevo | Se sigue usando el módulo actual ("Solicitados"); la primera versión solo le entrega las solicitudes | Fase 2 o después |
| Migrar las solicitudes históricas del MySQL actual | La primera versión trabaja solo con solicitudes nuevas | Por definir (ver OQ-B-6) |
| Código que ya no se usa: `action.php`, `html.php`, "PLANTILLA SIMPLE" | No forman parte del flujo actual | No se migra |
| Consultas de notas de Admisiones, Registro y Control (`admin_consultasCoordinador`; el nombre dice "coordinador" por error, corrección del usuario del 2026-11-25) | No tienen relación con los recibos | Fase 2 (decisión del usuario del 2026-11-25, aclaración C5 de Reverse Engineering; antes: fuera del proyecto) |
| Recibos / exención de reingreso (C-045558) | Decisión de negocio; la plantilla de pregrado se modificará para no incluirlo | Excluido |

---

## Riesgos y preguntas abiertas

### Riesgos conocidos

| Riesgo | Impacto | Mitigación |
|------|--------|------------|
| Quedan ~22 días para llegar al ambiente de pruebas | Alto | Alcance cerrado (IN/OUT), parámetros en tablas sin pantalla, usar modelo, BD y WSO2 existentes |
| Malinterpretar reglas que hoy solo están en el código (cuotas, exenciones, conceptos) | Alto | Validar cada regla con Admisiones, Registro y Control; comparar con lotes reales de periodos anteriores |
| Repositorio incompleto (núcleo del framework y módulo "Solicitados") | Alto | Conseguir el código o documentar la conexión con "Solicitados" antes de construir |
| Dependencia de Oracle académico y sus funciones PL/SQL | Medio | Acceso de solo lectura acordado con DBA y probado pronto en dev |
| La revisión de Seguridad puede bloquear el paso a producción | Medio | Cumplir el checklist de seguridad desde el inicio (sin secretos, SonarQube, Dependabot, OWASP) |
| Datos personales de estudiantes (Ley 1581) en archivos y logs | Medio | Mínimo privilegio, retención definida de archivos, no registrar datos sensibles en logs |
| Diferencias de formato en las plantillas | Bajo | Usar las plantillas oficiales vigentes (`documentacion/plantillas-recibos/`) como casos de prueba |

### Decisiones tomadas durante la entrevista

- En 2027-1 los dos sistemas funcionan **en paralelo solo para pruebas**; después el sistema nuevo **reemplaza** al PHP.
- La coincidencia de resultados la valida el **Coordinador funcional de Admisiones, Registro y Control**, con **lotes de prueba de periodos anteriores**.
- Tablas que usa "Solicitados": Oracle `acasperi`, `acest`, `acestmat`, `acvlrscs`; MySQL `solicitudrecibo`.

### Preguntas abiertas

Detalle en `open-questions.md`:

- **OQ-B-1:** Fecha de reemplazo definitivo del sistema PHP (hoy indefinida).
- **OQ-B-2:** Archivo oficial de la plantilla de posgrado SMLV.
- **OQ-B-3:** Entrega de la nueva plantilla de pregrado sin "Reingreso".
- **OQ-B-4:** Campos y estados exactos que lee "Solicitados".
- **OQ-B-5:** Coordinación de cargas durante las pruebas en paralelo (cancelaciones cruzadas en `solicitudrecibo`).
- **OQ-B-6:** Necesidad de migrar solicitudes históricas.

---

## Estado actual

Hoy, Admisiones, Registro y Control carga en weboffice (PHP 5 y un framework propio de la Universidad) una plantilla Excel `.xls` con los códigos de los estudiantes. Hay tres plantillas: pregrado, posgrado por créditos y posgrado SMLV. El módulo `registro_lote_recibo` revisa cada estudiante en el sistema académico de Oracle: su estado, su carrera y el calendario. Luego cancela las solicitudes anteriores que no se imprimieron y crea en MySQL las solicitudes de recibo, con sus cuotas, exenciones y conceptos. Después, el módulo "Solicitados" lee esas solicitudes junto con tablas de Oracle (`acasperi`, `acest`, `acestmat`, `acvlrscs`) y genera e imprime los recibos. Las reglas están escritas directamente en el código, y el sistema no tiene pruebas ni API.

Análisis de soporte: `interview/technical/existing-system-analysis.md`, `interview/technical/templates-analysis.md`.

## Lo que NO debe cambiar

- **Oracle académico:** solo lectura; se mantiene la conexión actual, sin modificar estructura ni datos.
- **Módulo "Solicitados":** no se modifica y sigue leyendo las solicitudes como hoy.
- **Tabla `solicitudrecibo` (MySQL):** se mantienen su estructura y sus estados (0 = sin imprimir, 2 = cancelada; demás por confirmar en OQ-B-4). El sistema nuevo escribe ahí.
- **Sistema PHP actual:** sigue funcionando sin cambios mientras duran las pruebas en paralelo; después se reemplaza.
- **Lo que ya existe:** el modelo de datos aprobado por el comité, la base creada por los DBA y el registro en WSO2 se usan tal como están.
- **Bases de datos:** no se migran a PostgreSQL ni se renombran tablas; los lineamientos OAS aplican solo al código.
- **Reglas de cálculo vigentes:** cuotas de posgrado (1–3 cuotas, porcentajes por defecto 100 / 60-40 / 40-30-30), fecha extraordinaria = ordinaria + 8 días saltando festivos, exenciones y conceptos. Solo cambian las tres reglas acordadas (sin reingreso, sin diferido en pregrado, sin leer "Seguro" como cuota).
