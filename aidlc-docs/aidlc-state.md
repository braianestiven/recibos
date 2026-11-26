# AI-DLC State

- Created / Last Updated: 2026-11-24T00:00:00Z / 2026-11-25T18:08:21Z
- Project Type: Brownfield (migración / modernización)
- Product: Migración del módulo de recibos por lote (weboffice)
- Current Phase: CONSTRUCTION
- Requirements Depth: Comprehensive (migración de alto riesgo, 15 preguntas abiertas pre-declaradas)
- Interaction: conversational (desde 2026-11-24, a pedido del usuario: las preguntas se hacen en el chat cuando cada etapa las necesita, y se registran en archivos)
- Workspace Root: /home/Lazius/Documentos/go/src/github.com/udistrital/recibos (Linux, desde 2026-11-25; antes c:\Users\estiv\OneDrive\Escritorio\recibos)
- Code Location: `recibos_service/` (U1) y `recibos_mf/` (U2) en la raíz del workspace, cada una armada como raíz de su futuro repositorio (Units Generation, Q1 = A)
- Rule Details: aws-aidlc-rule-details/ (detectado 2026-11-24 durante Units Generation; antes no estaba en el workspace). Desde 2026-11-25 también está en `.kiro/aws-aidlc-rule-details/`, la primera ruta que busca core-workflow.md; las dos copias son idénticas

## Current Status
- **Lifecycle Phase**: CONSTRUCTION
- **Current Stage**: CONSTRUCTION — U1 recibos_service, Code Generation Parte 2: generación del código en recibos_service/ (plan aprobado el 2026-11-25T19:50:22Z)
- **Next Stage**: U2 recibos_mf, Functional Design (después de aprobar el código de U1)
- **Status**: INCEPTION completa (Units Generation aprobada el 2026-11-25T16:45:50Z, con C6 b, C7 a y C8 a). U1 Functional Design APROBADO el 2026-11-25T17:55:25Z: F1 a F15 respondidas; artefactos en construction/recibos_service/functional-design/. U1 NFR Requirements empezó el 2026-11-25T18:08:21Z: el plan tiene 13 preguntas (N1 a N13) y no se generan artefactos hasta tener las respuestas. Al revisar el stack en la web aparecieron cambios que tocan decisiones aprobadas: salió Python 3.15, el SDK de X-Ray está en mantenimiento, httpx no tiene versiones desde 2024 y flasgger desde 2023. Historias: 10 listas y 5 bloqueadas. Todo lo que se pregunte o responda al usuario va en español. El 2026-11-25T18:25:20Z el usuario respondió N1 a N13 y pidió revisar la API Python `firma_electronica_mid`; el análisis está en construction/recibos_service/nfr-requirements/firma-electronica-mid-analysis.md. N10 = b choca con SECURITY-09 (el SDK de X-Ray pierde el soporte el 2027-02-25 y declara compatibilidad solo hasta Python 3.11) y N6 = c (24/7 con 99,9%) abre tres puntos: aclaraciones N14 a N17. El 2026-11-25T18:31:09Z el usuario respondió N14 a N17 ("n14 c, n15 a, n16 a, n17 b"): sin trazas en el MVP, 99,9% medido sobre el propio servicio, alarmas para infraestructura y la extensión de resiliencia desactivada. Se generaron nfr-requirements.md y tech-stack-decisions.md y se llevaron los cambios a requisitos, historias, diseño, diseño funcional y entorno técnico. U1 NFR Requirements APROBADO el 2026-11-25T18:44:18Z. U1 NFR Design empezó el 2026-11-25T18:54:52Z: el plan tiene 3 preguntas (N18 a N20) y las decisiones de procesos, conexiones y tiempos de espera. El 2026-11-25T18:58:07Z el usuario respondió N18 a N20 ("n18 a, los dbas no cambian la claves, n19 a, n20 a"). Se generaron nfr-design-patterns.md y logical-components.md (construction/recibos_service/nfr-design/) y se llevaron los cambios a los documentos anteriores (AD-34 a AD-36, BR-L16, BR-T04, NFR-R03, NFR-O05, US-10, US-15); insumos nuevos D16 y D17. U1 NFR Design APROBADO el 2026-11-25T19:31:30Z. U1 Infrastructure Design empezó el 2026-11-25T19:37:56Z: el plan tiene 5 preguntas (I1 a I5) y las decisiones de tareas, balanceador, S3, registros, alarmas, IAM, red y pipeline. El 2026-11-25T19:39:46Z el usuario aplazó U1 Infrastructure Design ("omitir la infraestructura,  dejarlo para después, pasa al paso de generar el codigo"): I1 a I5 quedan sin responder y se retoma antes del primer despliegue. U1 Code Generation empezó el 2026-11-25T19:48:59Z: plan de 18 pasos con los supuestos de los insumos pendientes, esperando la aprobación.

## Extension Configuration
| Extension | Enabled | Decided At |
|---|---|---|
| Security Baseline | Yes — todas las reglas SECURITY bloqueantes | Requirements Analysis (pregunta hecha tarde, en Units Generation, 2026-11-24) |
| Resiliency Baseline | No (confirmado el 2026-11-25 en U1 NFR Requirements, N17 = b, después de elegir 24/7 con 99,9%) | Requirements Analysis (pregunta hecha tarde, en Units Generation, 2026-11-24) |
| Property-Based Testing | Partial — bloqueantes PBT-02, PBT-03, PBT-07, PBT-08 y PBT-09; las demás son orientativas | Requirements Analysis (pregunta hecha tarde, en Units Generation, 2026-11-24) |

Reglas cargadas: `extensions/security/baseline/security-baseline.md` y `extensions/testing/property-based/property-based-testing.md`. La de resiliencia no se carga. Las preguntas debían ir en Requirements Analysis (paso 5.1); se hicieron en Units Generation porque las reglas no estaban en el workspace en esa etapa.
- Last Updated: 2026-11-25T16:02:39Z

## Reverse Engineering Status
- [x] Reverse Engineering - Completed on 2026-11-25T14:17:26Z; aprobada el 2026-11-25T15:30:14Z
- **Artifacts Location**: aidlc-docs/inception/reverse-engineering/
- **Hallazgos**: RE-01 a RE-26 en `story-code-traceability.md`; las decisiones del usuario están en su sección 4 (2026-11-25). RE-20 a RE-26 salen de `admin_solicitudCoordinador` ("Solicitados"), analizado después de la aprobación a pedido del usuario: D3 quedó resuelta (A15) y quedan abiertas C6, C7 y C8. Insumos: D1 (ampliada por C3 y RE-25) y D13 (RE-13)

## Inputs cargados (Discovery → Requirements)
- [x] Product-Definition/vision-document.md
- [x] Product-Definition/technical-environment.md
- [x] Product-Definition/open-questions.md
- [x] Product-Definition/interview/technical/existing-system-analysis.md (soporte)
- [x] Product-Definition/interview/technical/templates-analysis.md (soporte)

## Stages (INCEPTION)
- [x] Workspace Detection — Brownfield; Discovery completo; sin aidlc-state previo
- [x] Reverse Engineering — APROBADO (2026-11-25); agregada ese día a pedido del usuario, antes omitida porque existía el análisis de Discovery, que ahora se referencia
  - [x] Análisis del código, las historias (US-01 a US-15) y los casos de uso (UC-01 a UC-03)
  - [x] Artefactos generados → aidlc-docs/inception/reverse-engineering/ (8 de la regla, más story-code-traceability.md y reverse-engineering-questions.md)
  - [x] Respuestas a las preguntas 1 a 4 (2026-11-25), aplicadas a requirements.md, stories.md y application-design/
  - [x] Lectura completa de admin_consultasCoordinador (módulo de notas de ARC) y corrección del nombre en Discovery e Inception (2026-11-25)
  - [x] Aclaraciones C1 a C5 respondidas y aplicadas (2026-11-25) → reverse-engineering-clarification-questions.md
  - [x] Aprobación del usuario ("continuar", 2026-11-25)
- [x] Requirements Analysis — APROBADO (2026-11-24)
  - [x] Cargar inputs y artefactos de soporte
  - [x] Análisis de intención
  - [x] Resolver 15 preguntas abiertas (6 negocio + 9 técnicas)
  - [x] Generar documento de requisitos → aidlc-docs/inception/requirements/requirements.md
  - [x] Aprobación del usuario → APROBADO; OQ-B-5 decidida (bd de pruebas dedicada)
- [x] User Stories — APROBADO (2026-11-24)
  - [x] Parte 1 Planning: Q1–Q6 respondidas (Q3 = b, borradores bloqueados)
  - [x] Parte 2 Generation: personas.md, stories.md (15 historias: 9 listas, 6 bloqueadas)
  - [x] Aprobación del usuario, con decisiones P-3, P-5, P-7, P-11
  - [x] Actualización por evidencia del código PHP (requirements.md §12, stories.md registro de cambios)
- [x] Workflow Planning — APROBADO (2026-11-24) → inception/plans/execution-plan.md
- [x] Application Design — APROBADO (2026-11-24) → inception/application-design/ (AD-01 a AD-22, api-contract.md)
- [x] Units Generation — APROBADA (2026-11-25T16:45:50Z) (mínima): U1 recibos_service, U2 recibos_mf → inception/plans/unit-of-work-plan.md
  - [x] Parte 1 Planificación: Q1 = A (carpetas en la raíz); extensiones: seguridad sí, resiliencia no, PBT parcial
  - [x] Parte 2 Generación: unit-of-work.md, unit-of-work-dependency.md, unit-of-work-story-map.md
  - [x] Aprobación del usuario (2026-11-25T16:45:50Z, "aprobar y continau", junto con C6 b, C7 a y C8 a)

## Stages (CONSTRUCTION) — según execution-plan.md
- [~] U1 recibos_service — EN CURSO
  - [x] Functional Design (completa) — APROBADO (2026-11-25T17:55:25Z) → construction/recibos_service/functional-design/; plan: construction/plans/recibos_service-functional-design-plan.md (F1 a F15)
  - [x] NFR Requirements (estándar) — APROBADO (2026-11-25T18:44:18Z) → construction/recibos_service/nfr-requirements/; plan: construction/plans/recibos_service-nfr-requirements-plan.md (N1 a N17)
  - [x] NFR Design (estándar) — APROBADO (2026-11-25T19:31:30Z) → construction/recibos_service/nfr-design/; plan: construction/plans/recibos_service-nfr-design-plan.md (N18 a N20)
  - [-] Infrastructure Design (mínima) — APLAZADA por el usuario (2026-11-25T19:39:46Z); plan con I1 a I5 sin responder → construction/plans/recibos_service-infrastructure-design-plan.md; se retoma antes del primer despliegue en test
  - [~] Code Generation — Parte 1: plan de 18 pasos APROBADO (2026-11-25T19:50:22Z) → construction/plans/recibos_service-code-generation-plan.md; Parte 2: generación en curso
- [ ] U2 recibos_mf: Functional Design (mínima), NFR Requirements (mínima), NFR Design (omitida), Infrastructure Design (mínima), Code Generation
- [ ] Build and Test (ajustada: compilación, pruebas unitarias y CI)

## Pendientes abiertos (se preguntan en el chat según execution-plan.md §4)
- [x] Reverse Engineering, preguntas 1 a 4 — respondidas 2026-11-25 (RE-02 cancela también a los rechazados; RE-03/RE-04 cuotas obligatorias 1–3; RE-05 sin periodo = no se sube y se reporta; RE-06 sin fechas = no se sube; RE-07 unidad 0)
- [x] C1 a, C2 b, C3 b, C4 a, C5 b — respondidas 2026-11-25 y aplicadas
- [x] RE-13 → IP de `X-Forwarded-For` con el último proxy de confianza (AD-29)
- [ ] D13: número de proxies de confianza — U1 Infrastructure Design
- [x] RE-05: más de un periodo vigente → `SIN_PERIODO_VIGENTE` (supuesto A13, RE-18) — 2026-11-25
- [x] P-12 → b: se registraba el descuento de mayor porcentaje (empates: A9) — 2026-11-24; reemplazada por C2 el 2026-11-25 (más de un descuento: la fila no se sube)
- [x] P-13 → b: se conservaba la regla actual de la votación — 2026-11-24; cambiada por C2 y C1 el 2026-11-25 (votación marcada con cualquier descuento; automática con tope, A14)
- [x] P-1, P-2, P-6, P-10 — resueltos con F1, F2, F6 y F13 (2026-11-25)
- Historias (histórico, 2026-11-24): 10 listas, 5 bloqueadas (US-03 D1, US-05 D2, US-08 D5/D2, US-11 D3/D4, US-15 D6)
- [ ] D1 (archivo de la plantilla de pregrado: A1, encabezados y posición de la fecha ordinaria; F8 fijó la estructura) y D2 (archivo SMLV) — ARC
- [ ] D5 — el DBA identifica la tabla de festivos de weboffice (F9; F10: los fines de semana no mueven la fecha); dependencia técnica, no bloquea historias
- [x] D3: resuelta el 2026-11-25 con el código de "Solicitados" (RE-21, supuesto A15)
- [x] C6 = b, C7 = a, C8 = a — respondidas y aplicadas el 2026-11-25
- [x] F1 a F13 — respondidas el 2026-11-25: f1 a, f2 b, f3 a, f4 a, f5 a, f6 a, f7 b, f8 a, f9 c, f10  a, f11 a, f12 b, f13 a
- [x] F14 = a y F15 = a — respondidas el 2026-11-25
- [x] N1 a N13 — respondidas el 2026-11-25: N1 a, N2 a, N3 a, N4 a, N5 a, N6 c, N7 a, N8 a, N9 a, N10 b, N11 a, N12 b, N13 a
- [x] N14 a N17 — respondidas el 2026-11-25: n14 c, n15 a, n16 a, n17 b
- [ ] D14 (DBA): servicio TCPS y puerto de Oracle, y el certificado de la CA de Oracle y de MySQL (N9) — U1 Infrastructure Design
- [ ] D15 (Infraestructura): canal y turnos de las alarmas 24/7 (N6, N16) — U1 Infrastructure Design
- [x] N18 a N20 (plan de U1 NFR Design) — respondidas el 2026-11-25: A, A y A; en N18 el usuario aclara que los DBA no cambian las claves
- [ ] D16 (DBA): conexiones que puede abrir el servicio a Oracle y a MySQL (hasta 24 a MySQL y 16 a Oracle, el doble durante un despliegue) — U1 Infrastructure Design
- [ ] D17 (DBA): con el DDL (D4), confirmar que las tablas `solicitud*` son InnoDB, la versión de MySQL y si `solicitudRecibo` tiene un índice por (`codigo_est`, `estado`); si no lo tiene, crearlo antes de producción (N19) — antes de U1 Code Generation del repositorio de MySQL
- [ ] I1 a I5 (plan de U1 Infrastructure Design) — preguntadas el 2026-11-25; sin responder porque el usuario aplazó la etapa (2026-11-25T19:39:46Z)
- [ ] Retomar U1 Infrastructure Design antes del primer despliegue en test: I1 a I5, D7, D11 a D16, la definición de tarea, el balanceador, el bucket, las alarmas, los permisos, la red y los pasos de ECR y ECS del pipeline; las partes de infraestructura de SECURITY-02, 06, 07 y 14
- [ ] D7 — U1 Infrastructure Design
- [ ] D4 (ampliada: prefijo y llaves), D8 (rol ARC) — U1 Code Generation
- [~] D6 acotada: consulta y formato del sobre conocidos; falta el campo del valor de cada regla, ids por ambiente, URL y autenticación — preguntado 2026-11-24
- [x] P-15 → a: todas las reglas de "parametros" — 2026-11-24
- [ ] D10 crear los parámetros de las reglas en "parametros" (OATI/ARC) — la lista sale en U1 Functional Design
- [ ] D9 (token del core en oas_cliente) — U2 Functional Design
- Historias (actual, 2026-11-25): 10 listas, 5 bloqueadas (US-03 D1, US-05 D2, US-07 D1, US-08 D2, solo la variante SMLV, US-11 D4)

## Scope boundary (fuente de verdad)
- Límite de alcance = lista "Funcionalidades IN" de vision-document.md.
- Allow/deny de technical-environment.md se tratan como restricciones duras, no sugerencias.

## Open Questions — estado de resolución
Negocio:
- [x] OQ-B-1  resuelta-con-supuesto
- [x] OQ-B-2  requiere-insumo-usuario (bloquea validación de plantilla SMLV)
- [x] OQ-B-3  requiere-insumo-usuario (bloquea validación de plantilla pregrado)
- [x] OQ-B-4  requiere-insumo-DBA/código (bloquea contrato "Solicitados")
- [x] OQ-B-5  resuelta (usuario: bd de pruebas dedicada; no sobrescribe producción)
- [x] OQ-B-6  resuelta
Técnicas:
- [x] OQ-T-1  resuelta-con-supuesto (versiones)
- [x] OQ-T-2  resuelta (reimplementar contratos en Python)
- [x] OQ-T-4  resuelta (patrón pytest base)
- [x] OQ-T-5  resuelta-con-supuesto (CloudWatch Logs)
- [x] OQ-T-7  resuelta-con-supuesto (convención SSM)
- [x] OQ-T-8  requiere-insumo-DBA/código (festivos, fechas de pago, periodo)
- [x] OQ-T-9  requiere-insumo (DDL / modelo aprobado)
- [x] OQ-T-10 resuelta-con-supuesto (límite archivo / retención)
- [x] OQ-T-11 resuelta-con-estrategia (puerto + adaptador; contrato por definir)

Leyenda: "resuelta" = decidida; "resuelta-con-supuesto" = decisión por defecto que el usuario puede
anular; "requiere-insumo-*" = resuelta a nivel de requisito, pero la construcción necesita un artefacto
externo (plantilla, DDL o código de "Solicitados") marcado como dependencia bloqueante.
