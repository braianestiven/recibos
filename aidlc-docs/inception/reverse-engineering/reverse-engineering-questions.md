# Preguntas de Reverse Engineering

- Etapa: INCEPTION → Reverse Engineering (2026-11-25)
- Origen: los hallazgos de `story-code-traceability.md` que necesitan una decisión
- Estado: respondidas el 2026-11-25; quedan aclaraciones en `reverse-engineering-clarification-questions.md`
- Modo: las preguntas también se hacen en el chat (modo conversacional desde el 2026-11-24). Puedes responder aquí, después de `[Answer]:`, o en el chat con el formato "q1 a, q2 a..."
- Con las respuestas se actualizan `requirements.md`, `stories.md` y `component-methods.md`, y se anota cada cambio en su registro de cambios

## Pregunta 1 (RE-01)
En el sistema actual, la votación automática (certificado activo en `ACCERELECTORAL`) solo se evalúa si la fila tiene al menos una columna de exención marcada (`funcion.class.php` 477). Las historias aprobadas (US-07 escenario 8, US-08 escenario 10) y RF-06 CA3 (b) la aplican también a las filas sin ninguna exención marcada. ¿Qué regla sigue el sistema nuevo?

A) La del código actual: si la fila no tiene ninguna columna de exención marcada, no se registra la votación automática. Se corrigen RF-06 CA3 (b), §4.A punto 4, US-07 escenario 8, US-08 escenario 10 y `component-methods.md`. Recomendada, porque es lo que pidió P-13 y mantiene la coincidencia del 100%, salvo que ARC sepa que hoy esos estudiantes reciben la votación por otro camino o que el comportamiento actual es un error

B) La de las historias: la votación automática se evalúa en todas las filas. Se agrega como cambio acordado en `requirements.md` §12.3; el valor del recibo cambia frente al sistema actual para los estudiantes con certificado y sin exenciones marcadas

C) Other (please describe after [Answer]: tag below)

[Answer]: C (Other). Respuesta del usuario (2026-11-25): "solo se puede marcar maximo dos descuentos, solo el de votacion con cualquier otro, los demas descuentos entre si no se pueden sumar". La respuesta fija el máximo de exenciones, pero no dice qué pasa con la votación automática en las filas sin exenciones marcadas, y puede cambiar P-12 y P-13. Se aclara en C1 y C2 (`reverse-engineering-clarification-questions.md`)

## Pregunta 2 (RE-03)
En posgrado, si la columna 3 (cuotas) está vacía, hoy se genera una cuota (`funcion.class.php` 805–810). Las historias no dicen qué hacer en ese caso. ¿Qué hace el sistema nuevo?

A) Lo mismo que hoy: una cuota, con la fecha de la cuota 1 y el porcentaje de la columna 27 o 100 por defecto. Recomendada, por equivalencia

B) Rechazar la fila con el motivo `CUOTAS_INVALIDAS`

C) Other (please describe after [Answer]: tag below)

[Answer]: B. Respuesta del usuario: "si no tiene numero de cuotas que no suba el registro y muestre un reporte de los que no se subieron y el porque y de los que si se subieron"

## Pregunta 3 (RE-07)
Hoy `solicitudRecibo.unidad` se guarda como `0` en pregrado (`funcion.class.php` 255). US-11 dice "vacía en pregrado, como hoy". ¿Qué valor escribe el sistema nuevo?

A) `0`, como hoy. Se corrige la regla de US-11 y el tipo de `Solicitud.unidad` en `component-methods.md`. Recomendada: "Solicitados" sigue leyendo lo mismo

B) Vacío. Se agrega como cambio acordado

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "esta correcto guardar como 0"

## Pregunta 4 (RE-02, RE-04, RE-05, RE-06)
El diseño aprobado ya cambia estos comportamientos, pero no están en la lista de cambios acordados de `requirements.md` §12.3. Sin esa lista, la comparación de equivalencia los contaría como errores:
- RE-02: hoy un estudiante rechazado por terminación de materias o por fechas de posgrado pierde sus solicitudes sin imprimir; en el sistema nuevo no pierde nada.
- RE-04: hoy, en posgrado, con cuotas 0 o texto se guarda una solicitud sin cuotas, y con 4 o más el resultado es imprevisible; en el sistema nuevo la fila se rechaza (`CUOTAS_INVALIDAS`).
- RE-05: hoy, si el proyecto curricular no tiene periodo vigente, la solicitud se guarda sin año ni periodo; en el sistema nuevo se rechaza (`SIN_PERIODO_VIGENTE`).
- RE-06: hoy, si la facultad no tiene fechas de pago, la cuota de pregrado se guarda sin fechas; en el sistema nuevo se rechaza (`SIN_FECHAS_FACULTAD`).

¿Se agregan a la lista de cambios acordados?

A) Sí, las cuatro. Recomendada

B) Solo algunas: indica después de `[Answer]:` cuáles no

C) Other (please describe after [Answer]: tag below)

[Answer]: C (Other). Respuestas del usuario por hallazgo: RE-02 "si por alguna razon fue rechazado el estudiante que se cancelen las solicitudes" (lo contrario de la propuesta: un rechazado sí pierde sus solicitudes sin imprimir); RE-04 "deben ser las cuotas deben ser minimo 1 y maximo 3" (sí); RE-05 "debe indicar el año y el periodo porque estos datos vienen de la base de datos, si esta esta desactualizada que le arroge un mensaje de error que diga que no hay periodo vigente para que lo reponten al area de sistema" (sí, con ese mensaje); RE-06 "las fechas de pago viene de la plantilla, si no estan las fechas en la plantilla que no suba el registro y muestre un reporte de los que no se subieron y el porque y de los que si se subieron" (sí; el origen de las fechas en pregrado se aclara en C3). Las cuatro quedan como cambios acordados 8 a 11 en `requirements.md` §12.3

## Otras decisiones del usuario (2026-11-25)

- RE-13: "que la tome de X-Forwarded-For". Se aplica con la dirección que agrega el último proxy de confianza, no con la primera de la lista (AD-29, D13).
- Funcionalidades nuevas: "en la parte de sin cambios, agregar esas funcionalidades nuevas". El historial de lotes (US-13) y la auditoría (US-14) quedan registrados como funcionalidades nuevas del MVP (`requirements.md` §12.7).
- Reporte: el resumen muestra los estudiantes que se subieron y los que no, con el motivo (RF-11 CA3).
- Máquina de desarrollo: "usar las versiones de los lenguajes y demas actualizadas". Se aclara en C4 si eso cambia Python 3.12 en el proyecto.
