# Plan de diseño funcional — U1 `recibos_service`

- Etapa: CONSTRUCTION → U1 `recibos_service` → Functional Design, profundidad completa (`inception/plans/execution-plan.md`)
- Inicio: 2026-11-25T17:03:33Z
- Fuentes: `unit-of-work.md` y `unit-of-work-story-map.md` (U1 participa en US-01 a US-15); `requirements.md` (RF-01 a RF-16, §4.A, cambios acordados de §12.3, supuestos A1 a A15); `stories.md`; `components.md`, `component-methods.md`, `services.md`, `api-contract.md` y AD-01 a AD-30; hallazgos RE-01 a RE-26; aclaraciones C1 a C8
- Alcance: la lógica de negocio del backend, sin infraestructura. U1 no tiene interfaz: las pantallas son de U2, así que esta etapa no produce `frontend-components.md`
- Extensiones: seguridad, con todas sus reglas bloqueantes; PBT parcial, con PBT-02, PBT-03, PBT-07, PBT-08 y PBT-09 bloqueantes. PBT-01 (identificar las propiedades en esta etapa) es orientativa, pero se hace igual, porque PBT-03 exige probar los invariantes que salgan de aquí
- Cómo responder: después de cada `[Answer]:` de este archivo, o en el chat con el formato "f1 a, f2 a, …"

## Pasos
- [x] 1. Analizar el contexto de U1: definición, historias, requisitos, diseño de aplicación y hallazgos del código
- [x] 2. Escribir este plan con las preguntas F1 a F13
- [~] 3. Recibir las respuestas y revisar que ninguna quede ambigua; si alguna lo es, abrir un archivo de aclaraciones — F1 a F13 respondidas el 2026-11-25T17:18:02Z; F12 = b abre F14 y F15 en `recibos_service-functional-design-clarification-questions.md`
- [ ] 4. `domain-entities.md`: entidades y objetos de valor, estados de `solicitudRecibo` (0, 1 y 2) y relaciones
- [ ] 5. `business-rules.md`: cada regla con su identificador y su origen; orden de las validaciones; motivos de rechazo con su texto final; límites; lista de reglas que hay que crear en "parametros" (D10)
- [ ] 6. `business-logic-model.md`: el algoritmo de `ProcesarLote` por lote y por fila, la cancelación y el guardado, el resumen, el historial y la auditoría, con diagramas y su texto equivalente
- [ ] 7. Propiedades comprobables por componente (PBT-01), con los invariantes de PBT-03 y las idas y vueltas de PBT-02
- [ ] 8. Casos de abuso y controles de entrada y de error (SECURITY-05, SECURITY-11, SECURITY-13 y SECURITY-15)
- [ ] 9. Validar los artefactos (sintaxis Mermaid y contenido) y preparar los resúmenes de cumplimiento de seguridad y de PBT
- [ ] 10. Presentar la compuerta de la etapa

## Decisiones de diseño que no necesitan pregunta
Se aplican salvo que digas otra cosa.
- El máximo de filas (1000) y el tamaño máximo del archivo (10 MB, A1) son configuración del servicio, no reglas de "parametros": protegen el tiempo de respuesta (RNF-1) y no cambian por periodo.
- Código del estudiante: se quitan los espacios del inicio y del final; solo dígitos, hasta 15. Una celda numérica de Excel con valor entero (por ejemplo, 20271020001,0) se lee como ese entero.
- Porcentajes de las cuotas de posgrado: números enteros de 0 a 100, como define `Cuota.porcentaje`. Un decimal se rechaza con `PORCENTAJE_INVALIDO`. Hoy se acepta cualquier número de hasta 100, así que es un cambio acordado más.
- `total_filas` del resumen = filas subidas + filas no subidas.
- Los textos finales de los motivos de rechazo se proponen en `business-rules.md` y los revisas en la compuerta de esta etapa.

## Lo que se deriva de las respuestas (2026-11-25)
- F2 = b: las apariciones repetidas no se procesan, así que tampoco cancelan solicitudes; si cancelaran, borrarían la que acaba de crear la primera aparición. Si la primera aparición se rechaza, el estudiante queda sin solicitud aunque una fila posterior sea válida.
- F3 y F4: una fila cuyas celdas solo tienen espacios es una fila vacía y se omite.
- F5 = a: el nivel se valida después de las validaciones de hoy y del periodo vigente. Como cualquier rechazo de un estudiante conocido, cancela sus solicitudes sin imprimir (RE-02).
- F8 = a, F9 = c y F10 = a: también en pregrado la fecha extraordinaria se calcula; solo la mueven los días que están en la tabla de festivos de weboffice.
- F9 = c: D5 queda reducida a identificar la tabla (base, nombre y columnas) con el DBA. Es una dependencia técnica: ya no bloquea historias.
- F11 = a: los porcentajes salen de la tabla `exencion`, como hoy en el lote PHP; revierte P-15 en ese punto. Una exención del mapa sin porcentaje en la tabla detiene el lote, como una regla que falta (AD-22).
- F12 = b: la Secretaría de Educación no cuenta para C2. Las exenciones se guardan en el orden votación, descuento y Secretaría (RE-24). F14 y F15 aclaran cómo encaja con C6 y C7.

## Insumos que siguen pendientes
- D1: archivo oficial de la plantilla de pregrado. F8 define cómo trae las fechas; el archivo fija las posiciones de las columnas y los encabezados.
- D5: el DBA identifica la tabla de festivos de weboffice (F9).
- D2: archivo oficial de la plantilla de posgrado SMLV. Mientras no llegue, se usa el supuesto A6: igual a la de créditos, con "SMLV" en la columna 2.
- D4 (DDL) y D6 (formato del valor de cada regla en "parametros") no bloquean el diseño funcional; se usan en Code Generation.

## Preguntas

### Pregunta F1 — Lote con más de 1000 filas (P-1)
Si la plantilla trae más filas con datos que el máximo (1000), ¿qué hace el sistema?

A) Rechaza el lote completo sin procesar ninguna fila (422), y el mensaje dice el máximo y cuántas filas trae. El lote queda registrado, como los demás rechazos de formato (P-9). Recomendada: ARC divide el archivo y no quedan lotes a medias

B) Procesa las primeras 1000 filas y muestra las demás como no subidas, con un motivo nuevo

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "f1 a". Un lote con más de 1000 filas con datos se rechaza completo (422) y el lote queda registrado

### Pregunta F2 — Código repetido en el mismo lote (P-2)
Hoy cada fila se procesa en orden: la segunda aparición cancela la solicitud que acaba de crear la primera, así que queda la de la última fila. ¿Qué hace el sistema nuevo?

A) Procesa solo la última aparición. Las anteriores aparecen como no subidas con el motivo nuevo `CODIGO_REPETIDO` ("Reemplazada por la fila N"). El resultado final es el de hoy, sin crear y cancelar solicitudes de más. Si la última fila se rechaza, el estudiante queda sin solicitud, como hoy. Recomendada

B) Procesa solo la primera aparición. Las siguientes aparecen como no subidas con `CODIGO_REPETIDO` ("El código ya está en la fila N"). Cambia el resultado de hoy cuando las filas traen datos distintos

C) No sube ninguna aparición: todas aparecen con `CODIGO_REPETIDO` y, como en cualquier rechazo, se cancelan las solicitudes sin imprimir del estudiante (RE-02). ARC corrige el archivo y vuelve a cargar a ese estudiante

D) Other (please describe after [Answer]: tag below)

[Answer]: B. Respuesta del usuario: "f2 b". Solo se procesa la primera aparición; las siguientes no se suben (`CODIGO_REPETIDO`)

### Pregunta F3 — Fila con datos pero sin código
Hoy se omite en silencio toda fila sin código, aunque tenga marcas en otras columnas, y no aparece en el reporte. ¿Qué hace el sistema nuevo?

A) La muestra como no subida con el motivo `CODIGO_INVALIDO` ("Falta el código del estudiante"). Las filas totalmente vacías se siguen omitiendo. Recomendada: ARC ve el error en el reporte

B) La omite en silencio, como hoy

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "f3 a". La fila con datos y sin código aparece como no subida (`CODIGO_INVALIDO`, "Falta el código del estudiante")

### Pregunta F4 — Celda que solo tiene espacios
Una columna cuenta como marcada si su celda tiene contenido. Una celda con solo espacios no se ve en Excel, pero hoy cuenta como marcada. ¿Cuenta en el sistema nuevo?

A) No: una celda con solo espacios no cuenta como marcada. Recomendada: una marca invisible puede agregar un concepto, o rechazar la fila por descuentos no acumulables, sin que ARC lo note

B) Sí, como hoy

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "f4 a". Una celda con solo espacios no cuenta como marcada

### Pregunta F5 — Estudiante de otro nivel en la plantilla
Hoy no se revisa que el estudiante sea del nivel de la plantilla. "Solicitados" calcula el valor según el tipo de plantilla: un estudiante de pregrado en la plantilla de posgrado por créditos sale con un recibo en 0, y en las demás combinaciones el valor sale de una fórmula que no le corresponde (RE-22). ¿Se valida?

A) Sí: la plantilla de pregrado solo acepta estudiantes de proyectos de pregrado, y las de posgrado solo de posgrado. Si no corresponde, la fila no se sube con el motivo nuevo `NIVEL_NO_CORRESPONDE`. El nivel sale de Oracle (`ACCRA` y `ACTIPCRA`), la misma relación que usa "Solicitados". Recomendada

B) No, como hoy

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "f5 a". Se valida el nivel; si no corresponde, `NIVEL_NO_CORRESPONDE`

### Pregunta F6 — Créditos o SMLV de la columna 2 en posgrado (P-6)
Hoy no se valida. "Solicitados" multiplica ese número para calcular el valor bruto, así que con 0 o vacío el recibo sale en 0 (RE-22). ¿Qué se valida?

A) Es obligatorio y mayor que 0: en créditos, un número entero; en SMLV, un número con hasta dos decimales. Si no cumple, la fila no se sube con el motivo nuevo `UNIDAD_INVALIDA`. Si el DDL (D4) muestra que `unidad` solo guarda enteros, SMLV también se limita a enteros. Recomendada

B) Es obligatorio, mayor que 0 y entero en las dos plantillas

C) No se valida, como hoy

D) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "f6 a". Obligatorio y mayor que 0; entero en créditos, hasta dos decimales en SMLV (`UNIDAD_INVALIDA`)

### Pregunta F7 — Fechas vencidas o en desorden
Lo aprobado exige que cada fecha exista y tenga el año completo. ¿Se valida algo más?

A) No, solo eso

B) Además, ninguna fecha ordinaria puede ser anterior al día de la carga, y en posgrado cada cuota debe vencer después de la anterior. Si no se cumple, la fila no se sube con `FECHA_INVALIDA`, y el detalle dice la cuota. Recomendada: evita recibos que nacen vencidos y cuotas en desorden. Es un cambio frente a hoy

C) Other (please describe after [Answer]: tag below)

[Answer]: B. Respuesta del usuario: "f7 b". Ninguna fecha ordinaria anterior al día de la carga; en posgrado, cada cuota vence después de la anterior

### Pregunta F8 — Fechas de la plantilla de pregrado (D1)
Desde C3 las fechas de pregrado vienen de la plantilla. Hoy salen de la tabla de cada facultad, que trae la ordinaria y la extraordinaria. En pregrado el valor extraordinario es igual al ordinario, y con una sola cuota "Solicitados" pone la fecha extraordinaria en el recibo (RE-25), así que esa fecha tiene que existir. ¿Cómo las trae la plantilla nueva?

A) Solo la fecha ordinaria, en tres columnas (día, mes y año), como en posgrado. La extraordinaria se calcula igual que en posgrado: 8 días calendario después y, si cae en festivo, el siguiente día que no lo sea

B) Las dos fechas, la ordinaria y la extraordinaria, cada una en tres columnas (día, mes y año)

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "f8 a". La plantilla trae solo la fecha ordinaria (día, mes y año); la extraordinaria se calcula como en posgrado

Cuando tengas el archivo oficial, ponlo en `documentacion/plantillas-recibos/`: de él salen las posiciones de las columnas y los encabezados.

### Pregunta F9 — De dónde salen los festivos (D5)
La fecha extraordinaria salta los festivos. Hoy los busca `calendario.class.php`, que no está en el repositorio. ¿De dónde los toma el sistema nuevo?

A) De los festivos oficiales de Colombia, calculados por el propio servicio, incluidos los que se trasladan al lunes. No depende de otra base ni de otro servicio. Recomendada, salvo que hoy weboffice cuente también días que no son festivos oficiales (por ejemplo, cierres de la Universidad)

B) De una lista de fechas en "parametros" que OATI o ARC actualizan cada año

C) De la tabla de festivos que usa hoy weboffice; el DBA tiene que identificarla

D) Other (please describe after [Answer]: tag below)

[Answer]: C. Respuesta del usuario: "f9 c". La tabla de festivos que usa hoy weboffice; el DBA la identifica (D5)

### Pregunta F10 — Sábados y domingos (D5)
Si la fecha extraordinaria cae en sábado o domingo, ¿se mueve? El código de hoy llama a `buscar_festivo`, cuya clase no está en el repositorio, así que no se sabe qué hace con los fines de semana.

A) No: solo los festivos mueven la fecha

B) Sí: si cae en sábado, domingo o festivo, pasa al siguiente día hábil

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "f10 a". Solo los festivos mueven la fecha

### Pregunta F11 — De dónde salen los porcentajes de las exenciones (revisa P-15)
En P-15 se decidió leerlos de "parametros". "Solicitados" cobra con los de la tabla MySQL `exencion` (RE-22). Con C7, el sistema decide con esos porcentajes si el descuento y la votación pasan de 100%; si las dos fuentes no coinciden, pueden volver a salir recibos negativos. ¿De dónde se leen?

A) De la tabla `exencion` de MySQL, en solo lectura: son los mismos con los que cobra "Solicitados". En "parametros" quedan los ids y los mapas de columna a exención. Recomendada

B) De "parametros", como se decidió en P-15; cada cambio de porcentaje se hace en los dos lugares

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "f11 a". De la tabla `exencion` de MySQL, en solo lectura; en "parametros" quedan los ids y los mapas

### Pregunta F12 — Secretaría de Educación en posgrado (columna 16, exención 16)
"Solicitados" trata esta exención aparte: la aplica después de las demás, sobre el valor que queda, como un pago de la Secretaría. Con C2, ¿cuenta como un descuento?

A) Sí: es un descuento más; con otro descuento marcado, la fila no se sube (C2 tal como está). Recomendada: es la regla que diste, y evita un defecto de "Solicitados", que con tres exenciones solo cuenta dos y depende del orden en que las lee (RE-24)

B) No: se suma a la votación y a un descuento, como lo calcula hoy "Solicitados". La fila puede llevar votación, un descuento y la Secretaría. El sistema las guarda en el orden en que "Solicitados" las cuenta bien (votación, descuento y al final la Secretaría), aunque su consulta no garantiza ese orden

C) Other (please describe after [Answer]: tag below)

[Answer]: B. Respuesta del usuario: "f12 b". La Secretaría no cuenta como descuento: puede ir con la votación y un descuento. Abre las aclaraciones F14 y F15

### Pregunta F13 — Exportar la lista de no subidos (P-10)
¿ARC necesita descargar la lista de las filas que no se subieron?

A) No en el MVP: el reporte se ve en pantalla, como en las maquetas aprobadas. Recomendada: no está en la lista IN de la Visión

B) Sí: un botón descarga la lista en CSV desde la pantalla del reporte. Lo arma U2 con la respuesta del servicio, sin otro endpoint

C) Other (please describe after [Answer]: tag below)

[Answer]: A. Respuesta del usuario: "f13 a". No se exporta en el MVP
