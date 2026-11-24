---
inclusion: always
---

# Mapa visual del flujo AI-DLC

- Cada vez que una etapa de AI-DLC se complete, se apruebe, o cambie la fase o la etapa actual, regenera `aidlc/mapa-aidlc.html` leyendo el estado real de `aidlc-state.md`.
- Antes de dar por cerrado un turno en el que avanzó el flujo, confirma que el HTML refleja la etapa actual.

## Cómo regenerarlo

- Fuente de verdad: `aidlc-docs/aidlc-state.md` (Inception, Construction, Operation) y `Product-Definition/state/session-index.md` (Ideation/Discovery). No inventes estados.
- Muestra las cuatro fases (Ideation, Inception, Construction, Operation) con sus etapas; cada etapa con estado: completada, en curso, pendiente u omitida (SKIP).
- Marca "Estás aquí" en la etapa actual con el agente activo y la próxima acción.
- Archivo único autocontenido (sin CSS/JS externos), en español, legible para personas no técnicas, con fecha y hora de la última actualización y `<meta http-equiv="refresh" content="5">`.
- Solo escribe `aidlc/mapa-aidlc.html`. No modifiques archivos del framework AI-DLC ni `aidlc-state.md` para esto.
