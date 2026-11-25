# Aclaraciones de Reverse Engineering

- Etapa: INCEPTION → Reverse Engineering (2026-11-25)
- Estado: C1 a C5 respondidas el 2026-11-25 ("c5 b, c1 a, c2 b..., c3 b, c4 a") y aplicadas a los requisitos, las historias, el diseño y Discovery. C6 a C8 respondidas el 2026-11-25 ("c6 b, c7 a, porque no supera el 100%, c8 a") y aplicadas
- Origen: respuestas del usuario a `reverse-engineering-questions.md`. Las demás respuestas ya se aplicaron a los requisitos, las historias y el diseño
- Mientras C1, C2 y C3 no tengan respuesta, US-07 y US-08 quedan bloqueadas (regla Q3 = b de User Stories). C4 y C5 no bloquean historias
- C5 se agregó el 2026-11-25, después de leer completo `admin_consultasCoordinador`
- C6, C7 y C8 se agregaron el 2026-11-25: C6 por la respuesta del usuario a A14; C7 y C8 después de leer completo `admin_solicitudCoordinador` ("Solicitados", RE-23 y RE-26). Mientras no tenían respuesta, US-07 y US-08 sumaban C6 y C7, y US-09 quedaba bloqueada por C8
- Puedes responder aquí, después de `[Answer]:`, o en el chat con el formato "c6 a, c7 a, c8 a"

## Ambigüedad 1: votación automática (RE-01)
Tu respuesta a la pregunta 1 dice cuántas exenciones puede llevar una solicitud: la votación y un descuento. No dice qué pasa con la votación automática, la que sale del certificado electoral activo en `ACCERELECTORAL` sin estar marcada en la plantilla. Hoy esa consulta solo se hace si la fila tiene alguna columna de exención marcada.

### Aclaración C1
Para un estudiante con certificado electoral activo y sin ninguna columna de exención marcada en la plantilla, ¿qué hace el sistema nuevo?

A) No registra la votación, como hoy. Recomendada: mantiene la coincidencia del 100% y lo que pidió P-13

B) Registra la votación (10%). El valor del recibo cambia frente al sistema actual y queda como cambio acordado

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario (2026-11-25): "c1 a"

## Posible contradicción 1: "máximo dos descuentos" frente a P-12 y P-13
Respondiste "solo se puede marcar máximo dos descuentos, solo el de votación con cualquier otro". Lo aprobado hasta ahora es:
- P-12: si la fila trae varios descuentos marcados, se registra solo el de mayor porcentaje; la fila no se rechaza.
- P-13: en pregrado, la votación marcada no se registra si también hay marcado un descuento de las columnas 8 a 13 (terminación de materias, beneficiario, matrícula de honor, deportista, distinguido, mérito académico). En posgrado se registra con cualquier descuento.

### Aclaración C2
¿Tu regla cambia alguna de esas dos decisiones?

A) No cambia ninguna: es la misma regla aprobada (un descuento más la votación). Recomendada

B) Cambian las dos: una fila con más de un descuento marcado, sin contar la votación, no se sube y aparece en el reporte; y la votación se registra con cualquier descuento, también en pregrado con las columnas 8 a 13

C) Solo cambia P-12: la fila con más de un descuento marcado no se sube y aparece en el reporte; la excepción de pregrado de P-13 se mantiene

D) Solo cambia P-13: la votación se registra con cualquier descuento; con varios descuentos marcados se sigue registrando el de mayor porcentaje

E) Other (please describe after [Answer]: tag below)

[Answer]: B, con una precisión. Respuesta del usuario: "c2 b pero solo pueden tener un descuento por votación mas otro pero en ese de dos descuentos sumados solo se pueden con el de votacion y otro". Se aplica: como máximo dos exenciones, la votación y un descuento; con más de un descuento la fila no se sube; la votación marcada se registra con cualquier descuento. La votación automática conserva su tope de 90% (supuesto A14)

## Ambigüedad 2: origen de las fechas de pago en pregrado (RE-06)
Respondiste que las fechas de pago vienen de la plantilla. Eso es así en posgrado (columnas 18 a 26). La plantilla de pregrado no trae fechas: hoy salen de la tabla de fechas de cada facultad, y lo aprobado es leerlas del servicio "parametros" (P-15). En los dos casos ya quedó aplicada tu regla: si faltan las fechas, la fila no se sube y aparece en el reporte con el motivo.

### Aclaración C3
En pregrado, ¿de dónde salen las fechas de pago?

A) De las fechas de la facultad en "parametros", como está aprobado. Recomendada

B) De la plantilla: la nueva plantilla de pregrado de 13 columnas (D1) traerá columnas de fecha. Cambia RF-02, RF-05, P-15 y la especificación de la plantilla, y hace falta el archivo oficial

C) Other (please describe after [Answer]: tag below)

[Answer]: B. Respuesta del usuario: "c3 b". Las columnas de fecha, su formato y si viene la fecha extraordinaria quedan en D1

## Ambigüedad 3: versiones (máquina de desarrollo)
Pediste usar en la máquina de desarrollo las versiones actualizadas de los lenguajes y herramientas. El proyecto fija Python 3.12 para el backend (`technical-environment.md`, AD-27) y la máquina tiene Python 3.14.

### Aclaración C4
¿Qué versiones usa el proyecto?

A) La última versión estable con soporte de cada lenguaje y herramienta en todo el proyecto (máquina, imagen Docker y CI): Python 3.14 o la más reciente al empezar U1 Code Generation, Node LTS activa y Angular con soporte vigente. Se actualizan `technical-environment.md` y AD-27, y la compatibilidad de las librerías se revisa en U1 NFR Requirements. Recomendada

B) Python 3.12 en el proyecto, como está fijado; en la máquina se actualizan las herramientas (Node LTS activa, Docker) y las pruebas de U1 corren en un contenedor con Python 3.12

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "c4 a"

## Ambigüedad 4: alcance del módulo de notas de ARC (RE-19)
Indicaste que `admin_consultasCoordinador` es la lógica del usuario de Registro y Control y que el nombre está mal. Ya se corrigió el nombre en todos los documentos. El módulo hace consultas de notas, no de recibos: lista los proyectos activos, deja escoger el periodo, muestra el control de notas parciales y el histórico de notas, y enlaza a la carga de novedades de notas. La Visión lo tenía fuera del proyecto, y así sigue mientras no respondas.

### Aclaración C5
¿Cambia el alcance de ese módulo?

A) Sigue fuera del proyecto; solo se corrige el nombre. Recomendada: no tiene relación con los recibos y el plazo es el 15/12/2026

B) Fuera de la primera versión, pero se migra en una fase posterior (Fase 2), como la consulta histórica por estudiante

C) Entra en la primera versión: se agrega a las funcionalidades IN y hay que hacer sus requisitos, historias y diseño (otra API y otras pantallas, con datos personales de docentes). Afecta el plazo

D) Other (please describe after [Answer]: tag below)

[Answer]: B. Respuesta del usuario: "c5 b"


## Ambigüedad 5: votación automática según la respuesta sobre A14
Se preguntó si la votación automática conservaba el tope de 90%. La respuesta del 2026-11-25 fue: "si no esta marcado en el archivo y si lo encuentras en la tabla ACCERELECTORAL aplica el descuento". La regla no pone condiciones, así que cambia dos cosas: las filas sin ningún descuento marcado (C1) y los descuentos de más de 90% (C7).

### Aclaración C6
Para un estudiante con certificado electoral activo en `ACCERELECTORAL`, sin la votación marcada y **sin ningún descuento marcado**, ¿qué hace el sistema nuevo?

A) Registra la votación (10%). Es lo que dice la respuesta. Cambia C1 de A a B: hoy esas filas no la reciben, así que la matrícula baja 10% frente al sistema actual y queda como cambio acordado

B) No la registra, como se decidió en C1. La respuesta aplica solo a las filas con un descuento marcado

C) Other (please describe after [Answer]: tag below)

[Answer]: B. Respuesta del usuario (2026-11-25): "c6 b". La votación automática solo se registra en las filas con un descuento marcado; se mantiene C1

## Hallazgo RE-23: descuento y votación por encima de 100%
"Solicitados" calcula la matrícula como valor bruto × (1 − (descuento + votación) / 100), con los porcentajes de la tabla `exencion` y sin tope. Si la suma pasa de 100%, la matrícula queda negativa, y la cuota 1 se inserta igual en Oracle (`ACESTMAT` y `ACREFEST`) con ese valor. El tope de 90% de la votación automática y la regla de pregrado que quitaba la votación marcada con las columnas 8 a 13 lo evitaban. Con C2 y con la respuesta sobre A14, un descuento de 100% más la votación deja la matrícula en −10% del valor bruto.

### Aclaración C7
Si un estudiante tiene un descuento y la votación (marcada o de `ACCERELECTORAL`) y la suma pasa de 100%, ¿qué hace el sistema nuevo?

A) Registra solo el descuento. Con un descuento de 100% el estudiante ya paga 0 de matrícula, así que no pierde nada. Vale para las dos plantillas y para la votación marcada y la automática. Recomendada

B) No sube la fila y la muestra en el reporte con un motivo nuevo ("La suma de los descuentos pasa de 100%"). La votación automática no se puede quitar desde la plantilla, así que esos estudiantes no podrían subirse

C) Registra las dos, como dicen hoy C2 y la respuesta sobre A14. "Solicitados" generaría recibos con matrícula negativa. No recomendada

D) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario (2026-11-25): "c7 a, porque no supera el 100%". Si el descuento y la votación pasan de 100%, se registra solo el descuento, en las dos plantillas y para la votación marcada o la automática

## Hallazgo RE-26: solicitudes sin imprimir de periodos anteriores
En P-7 se decidió que la cancelación solo toque el periodo vigente; hoy el lote cancela las de todos los periodos. "Solicitados" tiene una búsqueda por estudiante que muestra todas sus solicitudes en estado 0, de cualquier periodo, y al generar usa siempre el periodo vigente. Con P-7, la solicitud vieja de un estudiante que se vuelve a cargar queda junto a la nueva y se puede generar como recibo del periodo actual, con sus exenciones y fechas viejas.

### Aclaración C8
¿Qué solicitudes sin imprimir se cancelan?

A) Las de todos los periodos, como hoy. Cambia P-7 y A12: para cancelar basta con conocer al estudiante. Recomendada

B) Solo las del periodo vigente, como se decidió en P-7. Las solicitudes viejas siguen visibles en la búsqueda por estudiante de "Solicitados", y ARC no debe generarlas

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario (2026-11-25): "c8 a". Se cancelan las solicitudes sin imprimir de todos los periodos, como hoy; revierte P-7 y cambia A12
