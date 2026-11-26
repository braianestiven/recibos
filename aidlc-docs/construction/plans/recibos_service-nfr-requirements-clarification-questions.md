# Aclaraciones de los requisitos no funcionales — U1 `recibos_service`

- Etapa: CONSTRUCTION → U1 `recibos_service` → NFR Requirements, paso 4 del plan (respuestas que chocan con otras decisiones o con una regla)
- Fecha: 2026-11-25T18:25:20Z
- Origen: N10 = b choca con SECURITY-09 y con N1 = a; N6 = c abre tres puntos
- Respondidas el 2026-11-25 ("n14 c, n15 a, n16 a, n17 b") y aplicadas a los artefactos de la etapa y a los documentos anteriores
- Puedes responder aquí, después de `[Answer]:`, o en el chat con el formato "n14 a, n15 a, n16 a, n17 a"

## Hallazgo: el SDK de X-Ray pierde el soporte el 25 de febrero de 2027
AWS dejará de dar soporte al SDK y al daemon de X-Ray el 25 de febrero de 2027 ([AWS](https://docs.aws.amazon.com/xray/latest/devguide/document-history.html)); desde el 25 de febrero de 2026 solo reciben arreglos de seguridad. Además, el SDK para Python declara compatibilidad solo hasta Python 3.11 ([PyPI](https://pypi.org/project/aws-xray-sdk/)), y en N1 elegiste 3.15. SECURITY-09 exige versiones con soporte vigente, así que con N10 = b el servicio tendría un hallazgo de seguridad bloqueante unos dos meses después de llegar a test.

La fecha también aplica al daemon institucional que usan las APIs en Go, así que la OAS tendrá que reemplazarlo de todos modos. El agente de CloudWatch recibe trazas tanto del SDK de X-Ray como de OpenTelemetry, y AWS lo propone para tener menos agentes ([AWS](https://docs.aws.amazon.com/xray/latest/devguide/xray-daemon.html)). El contenido de las fuentes se resumió con otras palabras, por las restricciones de licencia.

### Aclaración N14 — Trazas

A) OpenTelemetry, como en la opción A de N10: el servicio envía las trazas a un colector en la tarea de ECS (el agente de CloudWatch o el ADOT Collector), y el colector las manda a X-Ray. Si el colector no está listo para test, las trazas se apagan por configuración y el servicio funciona igual. Recomendada

B) El SDK de X-Ray, con una excepción a SECURITY-09 escrita y con fecha: se cambia a OpenTelemetry antes del 25 de febrero de 2027. Hasta entonces corre en Python 3.15, fuera de la compatibilidad que declara el SDK

C) Sin trazas en el MVP: quedan la auditoría y los registros, y las trazas se agregan después con OpenTelemetry. Cambia RNF-5

D) Other (please describe after [Answer]: tag below)

[Answer]: C. Respuesta del usuario (2026-11-25): "n14 c". Sin trazas en el MVP; quedan la auditoría y los registros, y las trazas se agregan después con OpenTelemetry. Cambia RNF-5

## Puntos que abre N6 = c (24/7 con 99,9%)
99,9% al mes son unos 43 minutos sin servicio. Cada carga depende de WSO2, "parametros", Oracle, MySQL y S3, que tienen otros responsables.

### Aclaración N15 — Qué mide el 99,9%

A) La disponibilidad propia del servicio: que responda y que su health check esté bien. Las caídas de las dependencias no cuentan, pero el servicio las registra y tienen sus propias alarmas. Recomendada: es lo que este equipo controla

B) La disponibilidad de punta a punta, con las dependencias incluidas. Hace falta que los responsables de Oracle, MySQL, WSO2 y "parametros" se comprometan con 99,9% o más, sin ventanas de mantenimiento

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario (2026-11-25): "n15 a". El 99,9% mide la disponibilidad propia del servicio; las caídas de las dependencias no cuentan

### Aclaración N16 — Quién atiende las alarmas fuera del horario

A) El grupo de infraestructura de la OAS, con el canal y los turnos que ya usa. Recomendada

B) Los desarrolladores del proyecto, por turnos semanales

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario (2026-11-25): "n16 a". El grupo de infraestructura de la OAS, con su canal y sus turnos

### Aclaración N17 — Extensión de resiliencia
En Requirements Analysis elegiste no aplicar la extensión de resiliencia. Con N6 = c el servicio pasa a ser crítico para el negocio. La extensión revisa en cada etapa buenas prácticas del pilar de confiabilidad de AWS Well-Architected, en 15 áreas, entre ellas alta disponibilidad, recuperación, observabilidad y gestión de cambios. No garantiza el 99,9%: orienta el diseño.

A) Activarla desde esta etapa: sus reglas se revisan en NFR Requirements, NFR Design e Infrastructure Design de U1 y U2, y en Code Generation. Recomendada: alinea el diseño con el objetivo que elegiste

B) No activarla: el 99,9% se cubre con lo decidido en N6 (dos o más tareas en zonas distintas, alarmas y turnos), sin la lista de la extensión

C) Other (please describe after [Answer]: tag below)

[Answer]: B. Respuesta del usuario (2026-11-25): "n17 b". La extensión de resiliencia sigue desactivada
