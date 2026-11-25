# Aclaraciones del diseño funcional — U1 `recibos_service`

- Etapa: CONSTRUCTION → U1 `recibos_service` → Functional Design, paso 5 de la regla (respuestas que chocan con otras decisiones)
- Fecha: 2026-11-25T17:18:02Z
- Origen: F12 = b (la Secretaría de Educación no cuenta como descuento). C1, C6 y C7 se decidieron cuando la Secretaría contaba como un descuento más, así que quedan dos puntos abiertos
- Mientras no tengan respuesta, no se generan los artefactos de la etapa y US-08 queda bloqueada
- Puedes responder aquí, después de `[Answer]:`, o en el chat con el formato "f14 a, f15 a"

## Contexto
"Solicitados" calcula la matrícula así: valor bruto × (1 − (descuento + votación) / 100) × (1 − Secretaría / 100). La Secretaría se aplica sobre el valor que queda, así que no puede dejar la matrícula negativa: el riesgo que evita C7 está solo en descuento + votación. Hoy, en el lote, la votación automática solo se agrega si la suma de todas las exenciones marcadas, Secretaría incluida, es de 90% o menos.

### Aclaración F14
¿La Secretaría de Educación entra en la suma de C7 (el descuento y la votación juntos no pasan de 100%)?

A) No: la suma sigue siendo solo descuento + votación, porque la Secretaría se aplica sobre lo que queda y el total nunca pasa de 100%. Consecuencia: con la Secretaría y un descuento de más de 20% (y hasta 90%), la votación automática se agrega, y hoy no. Recomendada: sigue tu razón para C7, "porque no supera el 100%"

B) Sí: Secretaría + descuento + votación no pasan de 100%. Para la votación automática da el mismo resultado que hoy, pero quita la votación marcada en casos en que la matrícula no quedaría negativa. Por ejemplo, con la Secretaría (70%) y un descuento de 30%, hoy se registra la votación marcada, y con esta opción no

C) Other (please describe after [Answer]: tag below)

[Answer]: 

### Aclaración F15
Una fila de posgrado con solo la Secretaría marcada, sin votación ni otro descuento, de un estudiante con certificado electoral activo: ¿recibe la votación automática?

A) Sí, como hoy: para la votación automática cuenta cualquier exención marcada, también la Secretaría. Es lo que decidiste en C1 ("como hoy"). Recomendada

B) No: con F12 = b la Secretaría no es un descuento, y C6 dice que la votación automática solo va con un descuento marcado

C) Other (please describe after [Answer]: tag below)

[Answer]: 
