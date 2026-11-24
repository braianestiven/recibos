# AI-DLC State

- Created / Last Updated: 2026-11-24T00:00:00Z
- Project Type: Brownfield (migración / modernización)
- Product: Migración del módulo de recibos por lote (weboffice)
- Current Phase: INCEPTION
- Requirements Depth: Comprehensive (migración de alto riesgo, 15 preguntas abiertas pre-declaradas)
- Interaction: conversational (desde 2026-11-24, a pedido del usuario: las preguntas se hacen en el chat cuando cada etapa las necesita, y se registran en archivos)
- Workspace Root: c:\Users\estiv\OneDrive\Escritorio\recibos
- Code Location: `recibos_service/` (U1) y `recibos_mf/` (U2) en la raíz del workspace, cada una armada como raíz de su futuro repositorio (Units Generation, Q1 = A)
- Rule Details: aws-aidlc-rule-details/ (detectado 2026-11-24 durante Units Generation; antes no estaba en el workspace)

## Current Status
- **Lifecycle Phase**: INCEPTION
- **Current Stage**: Units Generation — Parte 2 (generación) completa
- **Next Stage**: CONSTRUCTION — U1 recibos_service, Functional Design
- **Status**: esperando la aprobación de Units Generation. Diseño ajustado por la extensión de seguridad (AD-09, AD-13 y AD-14 revisadas; AD-23 a AD-28 nuevas)

## Extension Configuration
| Extension | Enabled | Decided At |
|---|---|---|
| Security Baseline | Yes — todas las reglas SECURITY bloqueantes | Requirements Analysis (pregunta hecha tarde, en Units Generation, 2026-11-24) |
| Resiliency Baseline | No | Requirements Analysis (pregunta hecha tarde, en Units Generation, 2026-11-24) |
| Property-Based Testing | Partial — bloqueantes PBT-02, PBT-03, PBT-07, PBT-08 y PBT-09; las demás son orientativas | Requirements Analysis (pregunta hecha tarde, en Units Generation, 2026-11-24) |

Reglas cargadas: `extensions/security/baseline/security-baseline.md` y `extensions/testing/property-based/property-based-testing.md`. La de resiliencia no se carga. Las preguntas debían ir en Requirements Analysis (paso 5.1); se hicieron en Units Generation porque las reglas no estaban en el workspace en esa etapa.
- Last Updated: 2026-11-24T01:05:00Z

## Inputs cargados (Discovery → Requirements)
- [x] Product-Definition/vision-document.md
- [x] Product-Definition/technical-environment.md
- [x] Product-Definition/open-questions.md
- [x] Product-Definition/interview/technical/existing-system-analysis.md (soporte)
- [x] Product-Definition/interview/technical/templates-analysis.md (soporte)

## Stages (INCEPTION)
- [x] Workspace Detection — Brownfield; Discovery completo; sin aidlc-state previo
- [ ] Reverse Engineering — N/A: ya existe el análisis de Discovery (existing-system-analysis.md); se referencia, no se regenera
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
- [~] Units Generation — EN CURSO (mínima): U1 recibos_service, U2 recibos_mf → inception/plans/unit-of-work-plan.md
  - [x] Parte 1 Planificación: Q1 = A (carpetas en la raíz); extensiones: seguridad sí, resiliencia no, PBT parcial
  - [x] Parte 2 Generación: unit-of-work.md, unit-of-work-dependency.md, unit-of-work-story-map.md
  - [ ] Aprobación del usuario (PENDIENTE)

## Stages (CONSTRUCTION) — según execution-plan.md
- [ ] U1 recibos_service: Functional Design (completa), NFR Requirements (estándar), NFR Design (estándar), Infrastructure Design (mínima), Code Generation
- [ ] U2 recibos_mf: Functional Design (mínima), NFR Requirements (mínima), NFR Design (omitida), Infrastructure Design (mínima), Code Generation
- [ ] Build and Test (ajustada: compilación, pruebas unitarias y CI)

## Pendientes abiertos (se preguntan en el chat según execution-plan.md §4)
- [x] P-12 → b: se registra el descuento de mayor porcentaje (empates: A9) — 2026-11-24
- [x] P-13 → b: se conserva la regla actual de la votación — 2026-11-24
- [ ] P-1, P-2, P-6, P-10, P-14 — U1 Functional Design
- Historias: 10 listas, 5 bloqueadas (US-03 D1, US-05 D2, US-08 D5/D2, US-11 D3/D4, US-15 D6)
- [ ] D1, D2, D3 (acotada), D5 (acotada) — U1 Functional Design
- [ ] D7 — U1 Infrastructure Design
- [ ] D4 (ampliada: prefijo y llaves), D8 (rol ARC) — U1 Code Generation
- [~] D6 acotada: consulta y formato del sobre conocidos; falta el campo del valor de cada regla, ids por ambiente, URL y autenticación — preguntado 2026-11-24
- [x] P-15 → a: todas las reglas de "parametros" — 2026-11-24
- [ ] D10 crear los parámetros de las reglas en "parametros" (OATI/ARC) — la lista sale en U1 Functional Design
- [ ] D9 (token del core en oas_cliente) — U2 Functional Design
- Historias: 11 listas, 4 bloqueadas (US-03 D1, US-05 D2, US-08 D5/D2, US-11 D3/D4)

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
