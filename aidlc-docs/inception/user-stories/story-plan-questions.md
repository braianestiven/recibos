# User Stories — Preguntas de planificación (Parte 1)

Modo: batch. Rellena cada `[Answer]:` y responde `ready`.
Lote activo: Q1–Q6. (Es el primer y único lote de planificación; nada se pierde.)

Contexto: historias trazadas a RF-01..RF-16 del documento de requisitos aprobado. Actor
principal = Admisiones, Registro y Control (ARC). Procesamiento síncrono, 1000 estudiantes/lote.

---

### Q1: Granularidad de las historias
¿Qué nivel de desglose prefieres para las historias de usuario?

a) **Por capacidad de usuario** (una historia por flujo observable: cargar lote, ver resumen, consultar historial, iniciar sesión). Menos historias, más legibles para negocio.
b) **Por regla/requisito** (una historia por RF, incluidas las reglas de cálculo). Más historias, máxima trazabilidad 1:1 con los RF.
c) Other

**Recommendation:** (a) por capacidad de usuario, con las reglas de cálculo (RF-05/06/07) como **criterios de aceptación** dentro de la historia de "procesar lote", no como historias separadas. Equilibra legibilidad y trazabilidad; las reglas igual quedan cubiertas por pruebas unitarias al 100%.

[Answer]:a

---

### Q2: Alcance de las historias frente a "Fuera de alcance"
¿Confirmas que NO se escriben historias para lo que está en §6 (OUT/deny): pantalla de parámetros, consulta histórica por estudiante, impresión del recibo, migración de históricos?

a) Sí, solo historias para las funcionalidades IN (RF-01..RF-16).
b) Incluir además historias "placeholder" de Fase 2 (marcadas fuera de MVP) para dar contexto.
c) Other

**Recommendation:** (a). El límite de alcance es la lista IN; las de Fase 2 no se detallan ahora.

[Answer]:a

---

### Q3: Tratamiento de las dependencias bloqueantes (D1–D7)
Varias historias dependen de insumos externos (plantilla pregrado 13 col., SMLV, contrato "Solicitados", DDL, festivos, contrato "parametros"). ¿Cómo las reflejo en las historias?

a) Escribir la historia completa y añadir una nota **"Dependencia (Dx): bloquea implementación en Construction"** en sus criterios de aceptación.
b) Marcar esas historias como **"borrador/bloqueadas"** hasta tener el insumo.
c) Other

**Recommendation:** (a). Las historias y sus criterios se definen ahora (no dependen del insumo); solo la codificación en Construction espera. Así User Stories y Application Design no se bloquean.

[Answer]:b

---

### Q4: Personas
¿Qué personas documento?

a) Solo **ARC** (rol operativo único) como persona principal, y **Estudiante** y **Seguridad** como actores secundarios/indirectos en una nota.
b) Personas detalladas para ARC, Estudiante y Seguridad por separado.
c) Other

**Recommendation:** (a). ARC es el único rol operativo; Estudiante es indirecto y Seguridad consume logs fuera del ciclo.

[Answer]:
 a
---

### Q5: Formato de criterios de aceptación
¿Qué formato prefieres para los criterios de aceptación?

a) **Given/When/Then** (Gherkin), bueno para escenarios de validación y rechazo.
b) Lista de criterios en viñetas (como en requirements.md).
c) Other

**Recommendation:** (a) Given/When/Then para los flujos con muchos caminos de éxito/rechazo (carga, validación), y viñetas para historias simples. Facilita las pruebas unitarias posteriores.

[Answer]:a

---

### Q6: Idioma y priorización
a) Historias en **español**, priorizadas por orden del flujo (login → cargar → validar → generar → resumen → historial) con etiqueta MoSCoW (Must para todo el MVP).
b) Otro idioma u otra priorización.
c) Other

**Recommendation:** (a). Español (consistente con los demás documentos) y todo el MVP es "Must" por el plazo del 15/12/2026.

[Answer]:a

---

Cuando termines, responde `ready`. Con tus respuestas genero las historias en
`aidlc-docs/inception/user-stories/` (Parte 2) y vuelvo a pedir aprobación.
