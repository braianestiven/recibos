# Plan — Application Design

- Etapa: INCEPTION → Application Design (profundidad estándar)
- Entradas: `requirements.md`, `user-stories/stories.md`, `plans/execution-plan.md` (aprobados), `Product-Definition/technical-environment.md`, artefactos de Discovery
- Salida: `aidlc-docs/inception/application-design/`

## Pasos
- [x] Analizar el contexto aprobado (requisitos, historias, plan de ejecución)
- [x] Reunir los contratos institucionales: lineamientos Flask, lineamientos de endpoints, `utils_oas`, lineamientos de clientes
- [x] Definir componentes de `recibos_service` (domain, application, infrastructure, interfaces) y de `recibos_mf` → `components.md`
- [x] Definir métodos de cada componente (firma, entrada, salida) → `component-methods.md`
- [x] Definir casos de uso y su orquestación → `services.md`
- [x] Definir dependencias, comunicación y flujo de datos (diagramas validados) → `component-dependency.md`
- [x] Definir el contrato de la API que consume U2 → `api-contract.md`
- [x] Registrar las decisiones de diseño y sus alternativas → `application-design.md` (AD-01 a AD-20)
- [x] Incorporar la sintaxis de "parametros" dada por el usuario (`GET /v1/parametro/{id}`) → AD-20, RF-09, US-15
- [x] Preguntar al usuario lo que el diseño necesita: P-15 → a; ejemplo de respuesta de "parametros" recibido (AD-21, AD-22)
- [~] Pregunta de seguimiento: campo del valor de cada regla en el objeto `Parametro` (D6) y si el servicio permite listar por tipo
- [x] Aprobación del usuario (2026-11-24), incluidos los ajustes a US-14 (AD-11) y US-15 (AD-22)
