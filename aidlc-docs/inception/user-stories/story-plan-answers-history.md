# User Stories — Historial de respuestas de planificación (append-only)

## Lote 1 (Q1–Q6) — validado 2026-11-24T00:35:00Z

| Pregunta | Respuesta | ¿Coincide con la recomendación? |
|---|---|---|
| Q1 Granularidad | a) Por capacidad de usuario; reglas de cálculo como criterios de aceptación | Sí |
| Q2 Alcance vs OUT | a) Solo historias para funcionalidades IN (RF-01..RF-16) | Sí |
| Q3 Dependencias D1–D7 | **b) Marcar las historias como "borrador/bloqueadas" hasta tener el insumo** | **No** (recomendado: a) |
| Q4 Personas | a) ARC persona principal; Estudiante y Seguridad como actores secundarios | Sí |
| Q5 Formato de criterios | a) Given/When/Then (Dado/Cuando/Entonces) para flujos con rechazos; viñetas para historias simples | Sí |
| Q6 Idioma y prioridad | a) Español; orden del flujo; MoSCoW = Must para todo el MVP | Sí |

### Interpretación aplicada a Q3 (b)
- Regla: una historia queda **🔒 Borrador — bloqueada** cuando un insumo pendiente (D1–D6) puede
  cambiar sus criterios de aceptación (qué se acepta, qué se rechaza o qué se escribe).
- Los insumos que solo afectan detalles de implementación con comportamiento ya conocido (tipos del
  DDL, rutas SSM, límites de S3 y destino de logs con valor por defecto A1–A3) se anotan como
  **dependencia técnica** y no bloquean la historia.
- Las historias bloqueadas se escriben igual con todo lo conocido; los huecos se marcan
  `[PENDIENTE Dx]`. Pasan a **✅ Lista** cuando llega el insumo y se revisan de nuevo.
- Para limitar el alcance del bloqueo, la validación de formato se separa por tipo de plantilla
  (pregrado, posgrado créditos, posgrado SMLV), así la plantilla de créditos, que sí está
  disponible, no queda bloqueada por las otras dos.

---

## Lote 2 (puntos por confirmar, modo conversacional) — validado 2026-11-24T01:00:00Z

Respuesta literal del usuario: "p3 los descuentos no son acumulables  y votacion es el unico acumulable y se registra una sola vez, p5 si, p7 al vigente, p11 solo consulta el servicio de parametros, apruebo historias de usuario hazme las preguntas por esta interfaz para desbloquear a medida que se requiera"

| Punto | Respuesta | Aplicado en |
|---|---|---|
| P-3 | Los descuentos no son acumulables; la votación es la única acumulable y se registra una sola vez | RF-06 CA3–CA4; US-07, US-08 |
| P-5 | Sí, los porcentajes de las cuotas de posgrado deben sumar 100 | RF-05 CA2; US-08 |
| P-7 | La cancelación aplica solo al periodo vigente | RF-08 CA4; US-09 |
| P-11 | `recibos_service` solo consulta el servicio "parametros" | RF-09 CA4; US-15 |
| Historias | Aprobadas | — |
| Modo | Preguntas en el chat, a medida que cada etapa las necesite (modo conversacional) | aidlc-state.md |

Interpretaciones:
- P-5: un porcentaje vacío toma el valor por defecto de su posición, como hoy; se agrega la validación de la suma.
- P-3 y P-7 cambian el comportamiento actual (hoy se registran todas las exenciones marcadas y se cancelan las solicitudes sin imprimir de todos los periodos). Quedan como cambios acordados en `requirements.md` §12.3.
- P-3 abre P-12 (varios descuentos en una fila) y P-13 (tope de la votación).

---

## Lote 3 (P-12, P-13, modo conversacional) — validado 2026-11-24T01:20:00Z

Respuesta literal del usuario: "p12 b, p13 b"

| Punto | Respuesta | Aplicado en |
|---|---|---|
| P-12 | b) Si hay varios descuentos marcados, se aplica solo el de mayor porcentaje | RF-06 CA4; US-07 esc. 5; US-08 esc. 8 |
| P-13 | b) Se conserva exactamente la regla actual de la votación, incluida la diferencia entre pregrado y posgrado | RF-06 CA3; US-07 esc. 6–8; US-08 esc. 9–10 |

Interpretaciones:
- Empate entre descuentos con el mismo porcentaje: se registra el de la columna que aparece primero (supuesto A9). El valor a pagar no cambia.
- Las fechas de tipo "terminación de materias" dependen de que la columna 8 esté marcada, como hoy, aunque se registre otro descuento de mayor porcentaje.
- El tope de la votación automática (≤ 90%) se evalúa con el porcentaje del descuento que queda registrado.
- Nuevo punto para U1 Functional Design: P-14 (avisar en el resumen cuando se descarta un descuento).

---
