# AI-DLC Audit Log

## Requirements Analysis — inicio
**Timestamp**: 2026-11-24T00:00:00Z
**User Input**: "Using AI-DLC, start Requirements Analysis for this product. Before anything else, load these inputs from Product-Definition/: vision-document.md — business vision: problem, target users, success metrics, MVP scope (IN/OUT), risks. technical-environment.md — technical constraints: languages, frameworks, cloud, architecture, security, testing. open-questions.md — 15 pre-declared ambiguities; resolve them before User Stories or Application Design. Treat the MVP \"Features IN\" list as the scope boundary. Honour the allow/deny lists in technical-environment.md as constraints, not suggestions."
**AI Response**: Cargados los tres inputs de Product-Definition/ más los artefactos de soporte (existing-system-analysis.md, templates-analysis.md). Confirmado Brownfield con Discovery completo; no existe aidlc-state previo ni rule-details de requirements-analysis en el workspace, así que se sigue el workflow adaptativo de core-workflow.md en profundidad Comprehensive. Creada la estructura aidlc-docs/. Generando el documento de requisitos con la resolución de las 15 preguntas abiertas.
**Context**: INCEPTION → Requirements Analysis (Comprehensive). Scope boundary = MVP "Funcionalidades IN". Allow/deny de technical-environment.md = restricciones duras.

---

## Requirements Analysis — documento generado, solicitando aprobación
**Timestamp**: 2026-11-24T00:10:00Z
**AI Response**: Generado aidlc-docs/inception/requirements/requirements.md (Comprehensive): análisis de intención, alcance trazado a las 10 funcionalidades IN (RF-01..RF-16), 8 RNF, fuera de alcance explícito (OUT/deny), y resolución de las 15 preguntas abiertas (6 negocio + 9 técnicas) con estados Decidida / Decidida-supuesto / Requiere-insumo-externo. Identificadas 7 dependencias bloqueantes para Construction (D1–D7) y 7 supuestos anulables (A1–A7). Presentada la compuerta de aprobación de 2 opciones. NO se avanza a User Stories ni Application Design sin aprobación explícita.
**Context**: INCEPTION → Requirements Analysis. Pendiente de aprobación del usuario.

---

## Requirements Analysis — aprobado + decisión OQ-B-5
**Timestamp**: 2026-11-24T00:20:00Z
**User Input**: "usa una bd en pruebas por lo que no sobreescribe requerimientos, aprobar"
**AI Response**: Aplicada la decisión de OQ-B-5 en requirements.md: base de datos de pruebas dedicada (copia con datos de periodos anteriores); la regla de cancelación RF-08 no sobrescribe solicitudes de producción del sistema PHP. Actualizados RF-08 CA3, §7 OQ-B-5 (de recomendación a decisión del usuario) y §9 A5. Requirements Analysis APROBADO. Avanzando a User Stories (Parte 1 - Planning).
**Context**: INCEPTION → Requirements Analysis aprobado. OQ-B-5 cerrada por decisión del usuario. Siguiente etapa: User Stories.

---

## User Stories — Parte 1 (Planning): preguntas presentadas
**Timestamp**: 2026-11-24T00:25:00Z
**AI Response**: Evaluación inteligente: User Stories APLICA (funcionalidad de usuario nueva, múltiples escenarios de validación/rechazo, criterios de aceptación necesarios). Creado aidlc-docs/inception/user-stories/story-plan-questions.md con 6 preguntas de planificación (Q1 granularidad, Q2 alcance vs OUT, Q3 dependencias D1-D7, Q4 personas, Q5 formato de criterios, Q6 idioma/priorización), modo batch. Esperando respuestas del usuario (`ready`) antes de generar historias.
**Context**: INCEPTION → User Stories, Parte 1 (Planning). Pendiente de respuestas del usuario.

---

## User Stories — respuestas de planificación y generación
**Timestamp**: 2026-11-24T00:40:00Z
**User Input**: "ready" (respuestas en story-plan-questions.md: Q1=a, Q2=a, Q3=b, Q4=a, Q5=a, Q6=a)
**AI Response**: Validadas las respuestas y guardadas en user-stories/story-plan-answers-history.md. Q3=b difiere de la recomendación: se aplicó la regla "bloqueada cuando un insumo pendiente puede cambiar los criterios de aceptación"; la validación de formato se separó por tipo de plantilla para que créditos no quede bloqueada. Generados personas.md y stories.md: 15 historias en 5 épicas, 9 Listas y 6 Bloqueadas (US-03 D1, US-05 D2, US-07 D5, US-08 D5, US-11 D3/D4, US-15 D6), matriz RF→US completa (16/16) y 11 puntos por confirmar (P-1..P-11) con propuesta por defecto. Presentada compuerta de aprobación.
**Context**: INCEPTION → User Stories, Parte 2 completada. Pendiente de aprobación del usuario.

---

## User Stories — aprobación y decisiones sobre puntos por confirmar
**Timestamp**: 2026-11-24T01:00:00Z
**User Input**: "p3 los descuentos no son acumulables  y votacion es el unico acumulable y se registra una sola vez, p5 si, p7 al vigente, p11 solo consulta el servicio de parametros, apruebo historias de usuario hazme las preguntas por esta interfaz para desbloquear a medida que se requiera"
**AI Response**: Historias APROBADAS. Aplicadas P-3 (descuentos no acumulables; votación única acumulable, una sola vez), P-5 (porcentajes de posgrado suman 100; vacíos con valor por defecto de su posición, como hoy), P-7 (cancelación solo en el periodo vigente) y P-11 (parametros solo lectura) en requirements.md y stories.md. Se leyó el código PHP (funcion.class.php, sql.class.php) para contrastar: P-3 y P-7 cambian el comportamiento actual (hoy se registran todas las exenciones marcadas y cancelarSolicitud no filtra por periodo), registrados como cambios acordados en requirements.md §12.3. El código resolvió: periodo (periodoActual, evento 80), fechas de pregrado (fechaPagoFacultad por facultad y tipo; tipo 3 con terminación de materias), validaciones de proyecto activo y valor de matrícula, estado H, columnas escritas en solicitud* y solicitudLote, historial sin totales. Corregido un error propio en §4.A: la fecha extraordinaria de posgrado es +8 días calendario y luego salta festivos (no 8 días hábiles). US-07 pasa a bloqueada por P-12/P-13 (ya no por D5); US-13 ajustada al alcance de IN-8; D3 y D5 acotadas; nuevo supuesto A8 (id_usuario = claim documento de WSO2). Modo de interacción cambiado a conversacional.
**Context**: INCEPTION → User Stories aprobado. Siguiente etapa: Workflow Planning.

---

## Workflow Planning — plan presentado y preguntas P-12/P-13
**Timestamp**: 2026-11-24T01:05:00Z
**AI Response**: Creado aidlc-docs/inception/plans/execution-plan.md: Reverse Engineering omitida; Application Design estándar; Units Generation mínima (U1 recibos_service → U2 recibos_mf); U1 con todas las etapas de Construction (Functional Design completa); U2 mínima sin NFR Design; Build and Test ajustada a compilación, pruebas unitarias y CI por restricción de technical-environment.md; calendario de preguntas por etapa (§4); D6 identificado en la ruta crítica. Diagramas Mermaid revisados (flowchart TD/LR, etiquetas entre comillas, sin palabras reservadas como id). Solicitada aprobación del plan y preguntadas en el chat P-12 y P-13, que desbloquean US-07 y US-08.
**Context**: INCEPTION → Workflow Planning. Pendiente de aprobación del usuario y de respuestas P-12/P-13.

---

## Workflow Planning — respuestas P-12 y P-13
**Timestamp**: 2026-11-24T01:20:00Z
**User Input**: "p12 b, p13 b"
**AI Response**: Aplicadas P-12 (b: se registra solo el descuento de mayor porcentaje) y P-13 (b: se conserva la regla actual de la votación, incluida la diferencia entre pregrado y posgrado) en requirements.md (RF-05 CA1, RF-06 CA3–CA5, §4.A, §9 A9, §12) y stories.md (US-07 esc. 5–10, US-08 esc. 8–11, tablas de bloqueos, puntos y registro de cambios). Verificado en el código que "marcada" = celda con contenido (isset). Supuesto nuevo A9: en empate, el descuento de la columna que aparece primero. Las fechas de terminación de materias siguen a la columna 8 marcada. Nuevo punto P-14 para U1 Functional Design. US-07 pasa a Lista; quedan 10 listas y 5 bloqueadas. El usuario no se pronunció sobre el plan de Workflow Planning: NO se infiere aprobación; se vuelve a pedir.
**Context**: INCEPTION → Workflow Planning. Pendiente de aprobación explícita del execution-plan.md.

---

## Workflow Planning — aprobado
**Timestamp**: 2026-11-24T01:30:00Z
**User Input**: "aprobado"
**AI Response**: Workflow Planning APROBADO (execution-plan.md). Se inicia Application Design (profundidad estándar): plan con casillas, recolección de los contratos institucionales (lineamientos Flask, endpoints, utils_oas, clientes), y generación de components.md, component-methods.md, services.md, component-dependency.md, api-contract.md y application-design.md. Preguntas al usuario solo si una decisión de diseño las necesita (modo conversacional).
**Context**: INCEPTION → Workflow Planning aprobado. Siguiente etapa: Application Design.

---

## Application Design — sintaxis de "parametros" y artefactos
**Timestamp**: 2026-11-24T02:10:00Z
**User Input**: "para consultar un parametro usa el id y lo pasa en un get usando una estructura como esta /v1/parametro/9"
**AI Response**: El usuario interrumpió la generación de component-methods.md para entregar parte del contrato D6. Ya estaban creados application-design.md y components.md. Se incorporó la sintaxis: cada regla se lee por su id con GET /v1/parametro/{id}, una llamada por regla al inicio de cada lote, sin caché entre lotes, con los ids en configuración (AD-20) y reenviando el token del usuario (A11). Actualizados RF-09 CA2, OQ-T-11, D6 (acotada), §9 A10–A11, US-15 (pasa a Lista: el formato queda como dependencia técnica) y el plan de ejecución. US-14 escenario 1 ajustado por AD-11 (los health checks no se auditan), pendiente de aprobación del diseño. Generados component-methods.md, services.md, component-dependency.md y api-contract.md. Diagramas Mermaid revisados (flowchart y sequenceDiagram sin ';' ni llaves en los mensajes). Historias: 11 listas, 4 bloqueadas. Se pregunta en el chat el formato de la respuesta de "parametros" (D6) y la fuente de porcentajes y fechas (P-15), y se pide la aprobación de Application Design.
**Context**: INCEPTION → Application Design, pendiente de aprobación.

---

## Application Design — P-15 y ejemplo de respuesta de "parametros"
**Timestamp**: 2026-11-24T02:30:00Z
**User Input**:
```text
p 15 a ejemplo de parametros 
    "Data": {
        "Id": 9,
        "Nombre": "Constancia de estudio",
        "Descripcion": "",
        "CodigoAbreviacion": "41",
        "Activo": false,
        "NumeroOrden": 0,
        "FechaCreacion": "2020-12-15 14:52:59.75962 +0000 +0000",
        "FechaModificacion": "2020-12-15 14:52:59.759703 +0000 +0000",
        "TipoParametroId": {
            "Id": 2,
            "Nombre": "",
            "Descripcion": "",
            "CodigoAbreviacion": "",
            "Activo": false,
            "NumeroOrden": 0,
            "FechaCreacion": "",
            "FechaModificacion": "",
            "AreaTipoId": null
        },
        "ParametroPadreId": null
    },
    "Message": "Request successful",
    "Status": "200",
    "Success": true}
```
**AI Response**: Aplicada P-15 (a): todas las reglas, incluidos los porcentajes de exención y las fechas por facultad, salen de "parametros". Ya no se leen las tablas MySQL `exencion` ni `fechaPagoFacultad`; la cuenta de MySQL solo necesita las tablas `solicitud*`. El ejemplo muestra el sobre CRUD (`Status` como texto) y un objeto `Parametro` sin campo de valor. Decisiones nuevas: AD-21 (cada regla declara en configuración id, campo y formato) y AD-22 (regla inexistente, inactiva o con valor inválido: el lote no se procesa, 502). Nuevo insumo D10: crear los parámetros de las reglas en "parametros" (dev y test), con la lista que entrega U1 Functional Design. US-15 recibe el escenario 5. Se registra el riesgo aceptado de mantener los porcentajes en dos lugares. El usuario no se pronunció sobre la aprobación de Application Design: NO se infiere; se vuelve a pedir.
**Context**: INCEPTION → Application Design, pendiente de aprobación.

---

## Application Design — aprobado
**Timestamp**: 2026-11-24T02:40:00Z
**User Input**: "aprobado"
**AI Response**: Application Design APROBADO (AD-01 a AD-22, api-contract.md). Con la aprobación quedan aceptados los ajustes a historias ya aprobadas: US-14 escenario 1 (los health checks no se auditan, AD-11) y US-15 escenario 5 (regla inexistente, inactiva o con valor inválido, AD-22). Se inicia Units Generation (profundidad mínima): U1 recibos_service → U2 recibos_mf.
**Context**: INCEPTION → Application Design aprobado. Siguiente etapa: Units Generation.

---

## Units Generation — Parte 1 (planificación) y reglas de AI-DLC detectadas
**Timestamp**: 2026-11-24T02:50:00Z
**AI Response**: Se detectó en el workspace la carpeta `aws-aidlc-rule-details/` (reglas detalladas de AI-DLC, sin versionar en git), que no existía al iniciar Requirements Analysis. Desde Units Generation se siguen esas reglas. Cargadas: `inception/units-generation.md`, `common/question-format-guide.md`, `common/content-validation.md` y los tres `*.opt-in.md` de `extensions/` (seguridad, resiliencia, pruebas basadas en propiedades). Las reglas completas de las extensiones no se cargan hasta que el usuario las active. Las preguntas de activación debían ir en Requirements Analysis (paso 5.1); se hacen ahora y se registran en `requirements/extension-opt-in-questions.md`. Hasta la decisión, el workflow las aplica por defecto. Se creó `plans/unit-of-work-plan.md` con la evaluación de las seis categorías de preguntas; solo "Organización del código" queda abierta (Q1). Conflicto de reglas: `question-format-guide.md` prohíbe preguntar en el chat, pero el usuario pidió preguntas por el chat ("hazme las preguntas por esta interfaz"). Se resuelve así: las preguntas se escriben en archivos con `[Answer]:` y se presentan también en el chat. La configuración de git se leyó en `.git/config` (remoto `braianestiven/recibos`, rama main) porque la terminal no devuelve la salida de los comandos.
**Context**: INCEPTION → Units Generation, Parte 1. Esperando Q1 y la activación de las extensiones.

---

## Corrección del registro — horas
**Timestamp**: 2026-11-24T21:17:00Z (16:17 -05:00, hora real del equipo)
**AI Response**: Las horas de las entradas anteriores de este registro (2026-11-24T00:00:00Z a 2026-11-24T02:50:00Z) no son reales: se escribieron como aproximaciones crecientes porque no había un reloj disponible. El orden de las entradas sí es correcto. Desde esta entrada se usa la hora real del equipo (leída con Get-Date). Verificación del entorno: solo git 2.46.0 está instalado. No hay Python (solo el alias de Microsoft Store), Node, npm ni Docker, así que en esta máquina no se pueden correr las pruebas unitarias. Se preguntará al usuario antes de U1 Code Generation.
**Context**: Corrección de un artefacto de AI-DLC producido por el agente.

---

## Units Generation — respuestas, extensiones y generación
**Timestamp**: 2026-11-24T21:30:00Z (hora aproximada: la terminal no devolvió la hora en este turno; la última lectura real fue 21:17Z)
**User Input**: "q1 a, e1 a, e2 b, e3 b"
**AI Response**: Q1 = A: el código va en `recibos_service/` y `recibos_mf/`, en la raíz del workspace. Extensiones: seguridad activa (todas las reglas bloqueantes), resiliencia no activa, pruebas basadas en propiedades en modo parcial (bloqueantes PBT-02, 03, 07, 08 y 09). Registrado en aidlc-state.md, `## Extension Configuration`. Se cargaron las reglas completas `security-baseline.md` y `property-based-testing.md`; la de resiliencia no se cargó. Aprobación del plan (paso 9 de units-generation.md): el usuario respondió después de que se le anunció que con sus respuestas se generarían los artefactos; se tomó como aprobación del plan y se generó la Parte 2. Se generaron unit-of-work.md, unit-of-work-dependency.md y unit-of-work-story-map.md, y se verificaron 15 de 15 historias asignadas. Los árboles de carpetas de application-design.md se pasaron a ASCII (ascii-diagram-standards.md).
**Hallazgos de seguridad bloqueantes** (revisión de las 15 reglas contra el diseño aprobado; todos resueltos en esta etapa):
- SECURITY-08: la validación del token se guardaba 60 min en caché, así que un token vencido o revocado se seguía aceptando. Resuelto en AD-09, RF-14 CA2, US-01 y UC-03: validación en cada petición, sin caché.
- SECURITY-08: CORS aceptaba `*` en dev y `*.udistrital.edu.co` en los demás ambientes. Resuelto en AD-14: lista explícita de orígenes por ambiente (insumo nuevo D11).
- SECURITY-04 y SECURITY-09: `/apidocs` (HTML con scripts) quedaba expuesto en dev. Resuelto en AD-13: solo en local.
- SECURITY-11: no había limitación de tráfico ni casos de abuso documentados. Resuelto en AD-23 (throttling en WSO2 AM, insumo nuevo D12) y en application-design.md §9.
- SECURITY-03: faltaba un registro de aplicación con nivel, mensaje e id de petición. Resuelto en AD-24.
- SECURITY-13: las cancelaciones no registraban quién, cuándo ni el estado antes y después. Resuelto en AD-25.
- SECURITY-10: faltaban versiones exactas, archivos de bloqueo y SBOM. Resuelto en AD-26 (se quita cachetools).
- SECURITY-09: faltaba el endurecimiento de los contenedores. Resuelto en AD-27.
- SECURITY-01, 02, 06, 07 y 14: controles de infraestructura sin especificar. Resueltos como requisitos para el grupo de infraestructura en AD-28; se verifican en Infrastructure Design.
- SECURITY-05: el nombre original del archivo no tenía límite de longitud ni de caracteres. Resuelto en services.md, UC-01 paso 2.
**PBT**: ninguna regla aplica a Units Generation; todas quedan N/A en esta etapa. Hypothesis queda preseleccionado para U1; se confirma en U1 NFR Requirements (PBT-09).
**Context**: INCEPTION → Units Generation, Parte 2 completa. Se presenta el mensaje de finalización con las dos opciones de las reglas; queda pendiente la aprobación del usuario.

---
