# Reglas de negocio — U1 `recibos_service`

- Etapa: CONSTRUCTION → U1 `recibos_service` → Functional Design (2026-11-25)
- Fuentes: `requirements.md` (RF-01 a RF-16, §4.A y los cambios acordados de §12.3), `stories.md`, AD-01 a AD-30, hallazgos RE-01 a RE-26, aclaraciones C1 a C8 y respuestas F1 a F15
- Cada regla tiene un identificador estable (BR-…) que usan las pruebas y el código
- Actualizado el 2026-11-25 en U1 NFR Requirements: BR-L02 (2 MB, N7), BR-L16 (límite propio, N3), BR-T05 (bloqueo por estudiante, N5) y §13
- Actualizado el 2026-11-25 en U1 NFR Design: BR-L16 (el límite cuenta desde que llega la petición y también se revisa antes de cada sentencia de MySQL) y BR-T04 (corte después de 5 fallas de conexión seguidas, N20)
- "Frente a hoy" dice si la regla hace lo mismo que el PHP ("Igual"), si es un cambio acordado ("Cambio", con su número de §12.3 de `requirements.md`) o si no existe hoy ("Nueva")
- Los valores entre corchetes, como [80], son los actuales. Vienen de "parametros" (§11), de la tabla `exencion` o de la configuración; ninguno queda fijo en el código (RF-09 CA1)

## 1. Acceso (UC-03, cada petición a `/v1/*`)

| ID | Regla | Si no se cumple | Frente a hoy | Origen |
|---|---|---|---|---|
| BR-A01 | La petición trae un token Bearer válido; se valida en `/oauth2/userinfo` en cada petición, sin caché | 401 | Cambio: hoy la sesión de weboffice | RF-14, AD-09 |
| BR-A02 | El usuario tiene el rol de ARC configurado | 403 | Cambio: hoy el nivel 132 de la sesión | RF-15, D8 |
| BR-A03 | El usuario trae `documento`, que se guarda como `id_usuario` | 403 | — | A8 |
| BR-A04 | Ningún rol, nivel ni permiso se toma de la petición | — | Corrige el riesgo R3 de hoy (TD-17) | RF-15 CA2 |

## 2. Lote (UC-01, antes de procesar filas)

Las reglas se evalúan en este orden; la primera que falla corta el lote.

| ID | Regla | Si no se cumple | ¿Queda registrado el lote? | Frente a hoy | Origen |
|---|---|---|---|---|---|
| BR-L01 | Hay un campo `archivo`. El nombre original no lleva rutas ni caracteres de control y no pasa de la longitud de `nombreOriginal` (D4) | 400 | No | Nueva | SECURITY-05 |
| BR-L02 | El archivo no pasa del tamaño máximo de configuración [2 MB] | 413 | No | Cambio 21 | RF-01 CA2, N7 |
| BR-L03 | La extensión es `.xls` y el contenido empieza con la firma OLE2 `D0 CF 11 E0 A1 B1 1A E1` | 415 | No | Cambio 7 | RF-01 CA1 |
| BR-L04 | Todas las reglas de §11 existen en "parametros", están activas y su valor se puede convertir a su formato | 502 si falta, está inactiva o no se convierte (el mensaje nombra la regla); 503 si el servicio no responde | No | Nueva | RF-09, AD-22 |
| BR-L05 | Todas las exenciones de los dos mapas de columna tienen porcentaje en la tabla `exencion` | 502 (el mensaje nombra la exención); 503 si MySQL no responde | No | Cambio: hoy se omite sin aviso (RE-12) | F11 |
| BR-L06 | El archivo se guarda en S3 con un nombre interno que no sale del nombre original | 503 | No | Cambio: hoy disco local | RF-01 CA3 |
| BR-L07 | El lote se registra en `solicitudLote` antes de validar el formato | 503 | — | Igual | RF-12 CA2, P-9 |
| BR-L08 | El archivo se puede leer como libro de Excel 97-2003 | 422 "No se pudo leer la plantilla" | Sí | Nueva | SECURITY-13 |
| BR-L09 | El texto de A1 corresponde a una de las tres plantillas | 422 | Sí | Igual | RF-02 |
| BR-L10 | El número de columnas y los encabezados son los de la especificación. La plantilla de pregrado con "Reingreso" tiene su propio mensaje | 422 | Sí | Cambio 1 y 7 | RF-02 CA1 a CA4 |
| BR-L11 | Las filas de datos van desde la fila inicial; se omiten las vacías, y una celda con solo espacios cuenta como vacía. Debe haber al menos una fila y como máximo [1000] | 422 si no hay filas o si pasan del máximo | Sí | Cambios 13 y 16 | F1, F3, F4 |
| BR-L12 | Se leen en bloque los estudiantes, los contextos de sus proyectos y los certificados electorales | 503 | Sí, sin solicitudes | Igual en resultado (AD-06) | RF-03 |
| BR-L13 | Se leen los festivos desde la menor fecha ordinaria del lote más 8 días hasta la mayor más 8 días y un margen de 30. Cada año en que cae alguna fecha ordinaria más 8 días debe tener al menos un festivo en la tabla. Las fechas que no se pueden leer no cuentan; esas filas se rechazan después (BR-D03) | 503 si no responde; 502 si un año no tiene festivos ("No hay festivos registrados para el año AAAA. Repórtelo al área de sistemas") | Sí, sin solicitudes | Nueva | F9, DF-07 |
| BR-L14 | Las filas se procesan en el orden de la plantilla, y el resultado de una fila no depende de las demás, salvo los repetidos (BR-F02) | — | — | Igual | RF-10 CA2 |
| BR-L15 | Al terminar, la respuesta es 201 con el resumen, aunque todas las filas se hayan rechazado | — | — | Igual | RF-11 |
| BR-L16 | El lote tiene un límite propio de [90] s, de configuración, contado desde que llega la petición. Antes de cada fila se revisa el tiempo; si se llegó al límite, esa fila y las siguientes no se procesan: salen con `TIEMPO_AGOTADO`, no se validan y no cancelan nada. Si el límite llega con una fila a medias, no sale ninguna sentencia más hacia MySQL: la fila sale con `TIEMPO_AGOTADO` si no había confirmado la cancelación, o con `ERROR_GUARDADO` si ya la había confirmado, y la cancelación se mantiene. *Precisado en U1 NFR Design* | — | Sí | Cambio 20 | N3, AD-31 |

Ninguna regla de lote cancela solicitudes: si el lote se corta, no se cancela nada (A12).

## 3. Fila: código y repetidos

| ID | Regla | Motivo | Frente a hoy | Origen |
|---|---|---|---|---|
| BR-F01 | El código se toma de la columna 1 sin espacios al inicio y al final. Debe tener solo dígitos, de 1 a 15. Una celda numérica con valor entero (por ejemplo, 20271020001,0) se lee como ese entero. Si la fila tiene datos y no tiene código, el mensaje lo dice | `CODIGO_INVALIDO` | Cambio 15 (la fila sin código hoy se omite) | RF-03, F3, DF-02 |
| BR-F02 | Si un código ya apareció en una fila anterior del lote, la fila nueva no se procesa: no se valida, no se cancela nada y no se guarda nada. Se comparan los códigos ya normalizados | `CODIGO_REPETIDO` | Cambio 14 (hoy queda la última aparición) | F2, P-2 |

## 4. Fila: estudiante (en este orden)

El motivo es el de la primera regla que falla. Las reglas BR-E01 a BR-E05 van en el orden de hoy; BR-E06 y BR-E07 son nuevas y van después (RF-03 CA6).

| ID | Regla | Motivo | Frente a hoy | Origen |
|---|---|---|---|---|
| BR-E01 | El estudiante existe en `ACEST` | `ESTUDIANTE_NO_ENCONTRADO` | Igual | RF-03 |
| BR-E02 | Tiene valor de matrícula en `V_ACESTMATBRUTO` | `SIN_VALOR_MATRICULA` | Igual | RF-03 CA5 |
| BR-E03 | Su estado está en `estados_permitidos` [V, J, T, A, Q, B] | `ESTADO_NO_PERMITIDO` | Igual | RF-03 CA1 |
| BR-E04 | Su proyecto está activo (`cra_estado = 'A'`) y no está en `proyectos_excluidos` [0, 999] | `CARRERA_INACTIVA` | Igual | RF-03 CA2 |
| BR-E05 | Si el evento `evento_terminacion` [82] está activo para su proyecto, su estado está en `estados_terminacion` [T, H] | `NO_TERMINACION_MATERIAS` | Igual | RF-03 CA3 |
| BR-E06 | Su proyecto tiene exactamente un periodo vigente para el evento `evento_periodo` [80] | `SIN_PERIODO_VIGENTE` | Cambio 10 | RE-05, A13 |
| BR-E07 | El nivel de su proyecto corresponde a la plantilla: la de pregrado exige `nivel_pregrado` [PREGRADO]; las de posgrado exigen uno de `niveles_posgrado` [POSGRADO, ESPECIALIZACION, MAESTRIA, DOCTORADO]. Un nivel vacío o desconocido no corresponde a ninguna | `NIVEL_NO_CORRESPONDE` | Cambio 17 | F5 |

## 5. Fila: datos de la plantilla (en este orden)

| ID | Regla | Motivo | Frente a hoy | Origen |
|---|---|---|---|---|
| BR-D01 | Posgrado: el número de cuotas (columna 3) es un entero de 1 a 3. Una celda numérica con valor entero vale como entero | `CUOTAS_INVALIDAS` | Cambio 8 | RE-03, RE-04 |
| BR-D02 | Posgrado: la columna 2 es obligatoria y mayor que 0. En créditos, un entero de hasta 3 cifras; en SMLV, un número de hasta 3 cifras enteras y 2 decimales, con coma o punto. Se guarda con punto y sin ceros sobrantes (por ejemplo, "4,50" queda "4.5") | `UNIDAD_INVALIDA` | Cambio 18 | F6, P-6, DF-03 |
| BR-D03 | Cada fecha ordinaria (una en pregrado, N en posgrado) tiene día, mes y año enteros, con año de 4 cifras, y es una fecha que existe. No es anterior al día de la carga (America/Bogota). En posgrado, cada una es posterior a la de la cuota anterior. Se revisan cuota por cuota, y el mensaje dice la cuota y el problema | `FECHA_INVALIDA` | Cambios 7, 11 y 19 | RE-06, F7 |
| BR-D04 | Posgrado: cada porcentaje de las cuotas 1 a N está vacío o es un entero de 0 a 100. Una celda con formato de porcentaje en Excel guarda una fracción (0,6 para 60%), así que no vale | `PORCENTAJE_INVALIDO` | Cambio 7 y 18 | RF-05 CA6, DF-01 |
| BR-D05 | Posgrado: después de completar los vacíos (BR-Q03), los porcentajes suman 100 | `PORCENTAJES_NO_SUMAN_100` | Cambio 5 | P-5 |
| BR-D06 | Posgrado: las celdas de fecha y porcentaje de las cuotas que pasan de N no se miran | — | Igual | — |

## 6. Fila: exenciones

| ID | Regla | Frente a hoy | Origen |
|---|---|---|---|
| BR-X01 | Una columna de exención está marcada si su celda tiene contenido. Cada columna marcada se traduce a un id con el mapa de su plantilla (§11). Cada id se clasifica: `id_exencion_votacion` [1] es la votación, `id_exencion_secretaria` [16] es la Secretaría de Educación y cualquier otro es un descuento | Cambio 16 (celdas con espacios) | RF-06 CA1, CA5, F4 |
| BR-X02 | Si hay más de un descuento marcado, la fila no se sube con `DESCUENTOS_NO_ACUMULABLES`. Ni la votación ni la Secretaría cuentan como descuento | Cambio 4 | C2, F12 |
| BR-X03 | Si la votación está marcada, se registra | Igual en posgrado; cambio 4 en pregrado con las columnas 8 a 13 | C2 |
| BR-X04 | Si la votación no está marcada, se registra la votación automática cuando se cumplen las dos condiciones: la fila tiene marcado un descuento o la Secretaría, y el estudiante tiene certificado activo en `ACCERELECTORAL` (`cer_estado = 'A'`). Una fila sin ninguna exención marcada no la recibe | Igual, salvo el caso de BR-X05 | C1, C6, F15, A14 |
| BR-X05 | Si hay votación (marcada o automática) y un descuento, y el porcentaje del descuento más el de la votación pasa de 100, se quita la votación y queda solo el descuento. Un total de exactamente 100 se permite. La Secretaría no entra en la suma, porque "Solicitados" la aplica sobre el valor que queda. Los porcentajes salen de la tabla `exencion` | Cambio 4. Con la votación en 10%, la automática da lo de hoy, salvo con la Secretaría y un descuento de más de 20%: hoy no se agrega y ahora sí (F14) | C7, F14, F11 |
| BR-X06 | Las exenciones se guardan en este orden: votación, descuento y Secretaría. "Solicitados" solo cuenta las dos primeras filas para la votación y el descuento, y busca la Secretaría aparte (RE-24) | Cambio: hoy van en el orden de las columnas, con la votación automática al final, y con tres exenciones "Solicitados" puede ignorar una | F12, RE-24 |
| BR-X07 | La exención "Reingreso" [18] no se registra: la plantilla de pregrado nueva no tiene esa columna | Cambio 1 | RF-06 CA2 |

## 7. Fila: conceptos, cuotas y solicitud

| ID | Regla | Frente a hoy | Origen |
|---|---|---|---|
| BR-C01 | Conceptos: siempre `concepto_matricula` [1]; en pregrado, además `concepto_exclusivo_pregrado` [19]; y los de las columnas de concepto marcadas, traducidos con el mapa de su plantilla (§11): seguro [2], carnet [3] y sistematización [4] | Igual | RF-07 |
| BR-C02 | Los conceptos se guardan en este orden: matrícula, exclusivo de pregrado y luego los marcados en el orden de las columnas. "Solicitados" usa la posición de cada concepto al armar los totales del recibo (TD-22), así que el orden es el de hoy | Igual | RE-22 |
| BR-Q01 | Pregrado: una sola cuota, número 1, al 100%, con la fecha ordinaria de la plantilla | Cambio 2 y 12 | RF-05 CA1, F8 |
| BR-Q02 | Posgrado: N cuotas (BR-D01), numeradas de 1 a N, con su fecha ordinaria de la plantilla | Cambio 8 | RF-05 CA2 |
| BR-Q03 | Posgrado: un porcentaje vacío toma el valor de su posición en `porcentajes_por_defecto` [1 cuota: 100; 2: 60 y 40; 3: 40, 30 y 30] | Igual | P-5 |
| BR-Q04 | Fecha extraordinaria de cada cuota, en las dos plantillas: la ordinaria más `dias_fecha_extraordinaria` [8] días calendario; mientras esa fecha esté en la tabla de festivos, se suma un día. Un sábado o un domingo que no esté en la tabla no mueve la fecha | Igual en posgrado; cambio 12 en pregrado | RF-05 CA3, F8, F9, F10 |
| BR-S01 | La solicitud usa el periodo vigente del proyecto (BR-E06) y el código del proyecto del estudiante | Igual | RF-04 |
| BR-S02 | `unidad` vale "0" en pregrado y la columna 2 normalizada en posgrado (BR-D02) | Igual en pregrado | RE-07 |
| BR-S03 | `solicitudRecibo.cuota` vale 1 en pregrado y N en posgrado | Cambio 3 (hoy en pregrado sale de "Seguro Estudiantil") | A15 |
| BR-S04 | Las fechas se guardan como timestamp Unix de la medianoche en America/Bogota | Igual | A10, AD-15 |

## 8. Cancelación, guardado y resumen

| ID | Regla | Frente a hoy | Origen |
|---|---|---|---|
| BR-T01 | Por cada fila procesada cuyo estudiante es conocido (código válido y existe en Oracle), válida o rechazada, se pasan de estado 0 a 2 todas sus solicitudes sin imprimir, de cualquier periodo, en una transacción propia. No se cancela nada en las filas con `CODIGO_INVALIDO`, `CODIGO_REPETIDO` o `ESTUDIANTE_NO_ENCONTRADO`, ni cuando el lote se corta | Cambio 9 (hoy no cancelan los rechazados por estado, matrícula o proyecto) | RE-02, C8, A12, AD-30 |
| BR-T02 | Si la cancelación falla: en una fila válida, no se guarda la solicitud nueva y la fila queda con `ERROR_GUARDADO`; en una fila rechazada, la fila conserva su motivo y el mensaje agrega que no se pudieron cancelar sus solicitudes anteriores | Nueva | RF-08 CA2, DF-09 |
| BR-T03 | Si la fila es válida, la solicitud se guarda en una transacción: `solicitudRecibo` en estado 0, sus cuotas, sus exenciones y sus conceptos. Si algo falla, se revierte la solicitud, la cancelación se mantiene y la fila queda con `ERROR_GUARDADO` | Cambio: hoy sin transacción | RF-10, RE-02 |
| BR-T04 | Si MySQL falla por la conexión en [5] filas seguidas, el lote deja de intentar: las filas que faltan quedan con `ERROR_GUARDADO`, no se validan y no cancelan nada, y el servicio responde con el reporte. Las fallas que muestran que MySQL responde (el bloqueo que no llega a tiempo, la espera por bloqueos de filas u otro error de la base) no cuentan y vuelven la cuenta a cero. *Decidido en U1 NFR Design (N20 = a)* | Nueva | `services.md`, N20 |
| BR-T05 | La cancelación y el guardado de un estudiante se hacen con un bloqueo por su código en MySQL. Si dos lotes con el mismo estudiante se procesan a la vez, queda la solicitud del que guarda de último. Si el bloqueo no se obtiene a tiempo, la fila queda como si fallara la cancelación (BR-T02) | Nueva | N5, AD-32 |
| BR-R01 | El resumen trae una entrada por cada fila con datos: en `procesados` las solicitudes guardadas (fila y código) y en `rechazados` el resto (fila, código, motivo y mensaje), en el orden de las filas. `total_filas` es la suma de las dos listas | Cambio: hoy HTML | RF-11 CA3 |
| BR-R02 | El resumen no se guarda ni se exporta en el MVP | Igual | RF-11 CA4, F13 |
| BR-R03 | Los mensajes son los de §10 de este documento y nunca muestran detalles internos | Nueva | SECURITY-15 |

## 9. Historial y auditoría

| ID | Regla | Frente a hoy | Origen |
|---|---|---|---|
| BR-H01 | `GET /v1/lotes` acepta `limit` de 1 a 100 (por defecto 20) y `offset` de 0 o más (por defecto 0); otros valores dan 400 | Nueva | US-13 |
| BR-H02 | Los lotes salen del más reciente al más antiguo, con usuario, fecha, nombre del archivo e IP, sin totales | Nueva | RF-12 CA3 |
| BR-H03 | Sin lotes, la respuesta es 200 con una lista vacía | Nueva | L31 |
| BR-U01 | Cada petición a `/v1/*` deja un registro de auditoría con los campos de `utils_oas/auditoria`; los health checks no | Nueva | RF-13, AD-11 |
| BR-U02 | En un lote, `data` lleva el tipo de plantilla, el tamaño, `id_lote`, los totales y los ids de las solicitudes creadas y canceladas con su cambio de estado (0 → 2) | Nueva | AD-25, SECURITY-13 |
| BR-U03 | Ningún registro lleva tokens, códigos ni nombres de estudiantes | Nueva | Ley 1581, AD-24 |

## 10. Textos de los mensajes

Mensajes de las filas (`Rechazo.mensaje`). Entre llaves van los datos de la fila.

| Motivo | Mensaje |
|---|---|
| `CODIGO_INVALIDO` | "Código de estudiante inválido: debe tener solo números, hasta 15." Sin código: "Falta el código del estudiante." |
| `CODIGO_REPETIDO` | "El código ya está en la fila {fila}; solo se procesa la primera vez que aparece." |
| `ESTUDIANTE_NO_ENCONTRADO` | "El código no está registrado en el sistema académico." |
| `SIN_VALOR_MATRICULA` | "Sin información de matrícula; solicitar por oficio." |
| `ESTADO_NO_PERMITIDO` | "El estado del estudiante ({estado}) no permite generar el recibo." |
| `CARRERA_INACTIVA` | "El proyecto curricular del estudiante no está activo." |
| `NO_TERMINACION_MATERIAS` | "El estado del estudiante es diferente de terminación de materias." |
| `SIN_PERIODO_VIGENTE` | "No hay periodo vigente para el proyecto curricular del estudiante. Repórtelo al área de sistemas." |
| `NIVEL_NO_CORRESPONDE` | "El proyecto curricular del estudiante es de {nivel} y la plantilla es de {pregrado o posgrado}." |
| `CUOTAS_INVALIDAS` | "El número de cuotas es obligatorio y debe estar entre 1 y 3." |
| `UNIDAD_INVALIDA` | Créditos: "Los créditos son obligatorios: un número entero mayor que 0." SMLV: "Los SMLV son obligatorios: un número mayor que 0, con hasta dos decimales." |
| `FECHA_INVALIDA` | "Cuota {n}: falta la fecha de pago." / "Cuota {n}: la fecha de pago no existe o no tiene el año completo." / "Cuota {n}: la fecha de pago es anterior al día de la carga." / "Cuota {n}: vence el mismo día o antes que la cuota {n − 1}." En pregrado, sin "Cuota {n}:" |
| `PORCENTAJE_INVALIDO` | "Cuota {n}: el porcentaje debe ser un número entero de 0 a 100." |
| `PORCENTAJES_NO_SUMAN_100` | "Los porcentajes de las cuotas deben sumar 100; suman {suma}." |
| `DESCUENTOS_NO_ACUMULABLES` | Pregrado: "Solo se puede marcar un descuento además de la votación." Posgrado: "Solo se puede marcar un descuento además de la votación y de la Secretaría de Educación." |
| `TIEMPO_AGOTADO` | "No se alcanzó a procesar en el tiempo del lote; vuelva a cargar esta fila." |
| `ERROR_GUARDADO` | "Error al guardar la solicitud. Vuelva a cargar a este estudiante." |
| Agregado de BR-T02 | " Además, no se pudieron cancelar sus solicitudes sin imprimir; vuelva a cargarlo." |

Mensajes del lote (`Message` del sobre):

| Caso | Código | Mensaje |
|---|---|---|
| Falta el archivo o el nombre no es válido | 400 | "Falta el archivo de la plantilla." / "El nombre del archivo no es válido." |
| Archivo grande | 413 | "El archivo supera el tamaño máximo de {max} MB." |
| Tipo no permitido | 415 | "Solo se aceptan plantillas .xls (Excel 97-2003)." |
| Archivo ilegible | 422 | "No se pudo leer la plantilla. Guárdela otra vez como Excel 97-2003 y vuelva a cargarla." |
| A1 no reconocido | 422 | "La plantilla no es una de las vigentes: revise el texto de la celda A1." |
| Pregrado con "Reingreso" | 422 | "La plantilla de pregrado no es la vigente: trae la columna Reingreso." |
| Columnas o encabezados distintos | 422 | "La plantilla de {tipo} no tiene las columnas esperadas: {detalle}." |
| Sin filas | 422 | "La plantilla no tiene estudiantes." |
| Más filas que el máximo | 422 | "El lote tiene {n} filas con datos y el máximo es {max}. Divida el archivo." |
| Regla de "parametros" | 502 | "No se pudo leer la regla {regla} del servicio de parámetros. Repórtelo al área de sistemas." |
| Porcentaje de una exención | 502 | "La exención {id} no tiene porcentaje en el catálogo de exenciones. Repórtelo al área de sistemas." |
| Año sin festivos | 502 | "No hay festivos registrados para el año {año}. Repórtelo al área de sistemas." |
| Dependencia que no responde | 503 | "Un servicio que necesita la carga no está disponible. Intente más tarde." |
| Error inesperado | 500 | "Ocurrió un error inesperado. Intente más tarde." |

En las respuestas 422 posteriores al registro, `Data` lleva `id_lote` (`api-contract.md`). Los 502 y 503 nombran la regla o la exención, pero nunca el servidor, la consulta ni la traza (SECURITY-15).

## 11. Reglas que hay que crear en "parametros" (D10)

Hay que crearlas en dev y test antes de procesar lotes. El id de cada parámetro por ambiente y el campo del objeto `Parametro` que lleva el valor dependen de D6 (AD-21). El formato es el que espera el servicio para convertir el valor.

| Regla | Valor actual | Formato | Regla de negocio |
|---|---|---|---|
| `estados_permitidos` | V, J, T, A, Q, B | Lista | BR-E03 |
| `estados_terminacion` | T, H | Lista | BR-E05 |
| `evento_periodo` | 80 | Entero | BR-E06 |
| `evento_terminacion` | 82 | Entero | BR-E05 |
| `proyectos_excluidos` | 0, 999 | Lista de enteros | BR-E04 |
| `nivel_pregrado` | PREGRADO | Texto | BR-E07 |
| `niveles_posgrado` | POSGRADO, ESPECIALIZACION, MAESTRIA, DOCTORADO | Lista | BR-E07 |
| `concepto_matricula` | 1 | Entero | BR-C01 |
| `concepto_exclusivo_pregrado` | 19 | Entero | BR-C01 |
| `conceptos_columna_pregrado` | `{"2": 2, "3": 3, "4": 4}` | JSON | BR-C01 |
| `conceptos_columna_posgrado` | `{"4": 2, "5": 3, "6": 4}` | JSON | BR-C01 |
| `exenciones_columna_pregrado` | `{"5": 1, "6": 2, "7": 3, "8": 4, "9": 5, "10": 6, "11": 7, "12": 8, "13": 9}`; se confirma con D1 | JSON | BR-X01 |
| `exenciones_columna_posgrado` | `{"7": 1, "8": 10, "9": 11, "10": 12, "11": 5, "12": 13, "13": 14, "14": 15, "15": 2, "16": 16, "17": 17}`; vale para créditos y SMLV | JSON | BR-X01 |
| `id_exencion_votacion` | 1 | Entero | BR-X01 |
| `id_exencion_secretaria` | 16 | Entero | BR-X01, BR-X02 |
| `porcentajes_por_defecto` | `{"1": [100], "2": [60, 40], "3": [40, 30, 30]}` | JSON | BR-Q03 |
| `dias_fecha_extraordinaria` | 8 | Entero | BR-Q04 |

No van en "parametros":
- Los porcentajes de las exenciones: se leen de la tabla `exencion` (F11).
- Los festivos: se leen de la tabla de weboffice (F9, D5).
- El tope de 100% de BR-X05: es el límite del cálculo de "Solicitados", no una regla que cambie por periodo.
- El tamaño máximo del archivo y el máximo de filas: son configuración del servicio (`RECIBOS_SERVICE_*`), porque protegen el tiempo de respuesta.
- La estructura de las plantillas (§2.3 de `domain-entities.md`): cambia solo con una plantilla oficial nueva (AD-16).

## 12. Decisiones de diseño de esta etapa

Se tomaron para cerrar detalles que las preguntas no cubrían. Se pueden cambiar en la revisión.

| ID | Decisión | Por qué |
|---|---|---|
| DF-01 | Los porcentajes de las cuotas de posgrado son enteros (anunciada en el plan) | Así los define el diseño aprobado (`Cuota.porcentaje`) |
| DF-02 | Código: solo dígitos, de 1 a 15, sin espacios al inicio y al final (anunciada en el plan) | Límite de entrada (SECURITY-05); `est_cod` es numérico |
| DF-03 | Créditos de hasta 3 cifras y SMLV de hasta 3 cifras enteras y 2 decimales; coma o punto como separador | Límite de entrada; ningún valor real se acerca a 999 |
| DF-04 | El tamaño máximo del archivo y el máximo de filas son configuración (anunciada en el plan) | No cambian por periodo |
| DF-05 | `total_filas` = procesados + rechazados (anunciada en el plan) | Cada fila con datos aparece una vez |
| DF-06 | Una plantilla sin filas con datos se rechaza con 422 | ARC ve el error en lugar de un reporte vacío |
| DF-07 | Si un año del rango de fechas no tiene festivos en la tabla, el lote se detiene (502) | Falla cerrada: una tabla sin cargar movería mal las fechas extraordinarias sin aviso |
| DF-08 | El código del rechazo se devuelve recortado a 30 caracteres | Límite de salida; un código válido tiene hasta 15 |
| DF-09 | Si falla la cancelación de una fila rechazada, el mensaje lo dice | ARC sabe que debe volver a cargar al estudiante |
| DF-10 | Las validaciones nuevas del estudiante van después de las de hoy: periodo (BR-E06) y luego nivel (BR-E07) | Los motivos de hoy no cambian para las filas que ya fallaban |

## 13. Casos de abuso y controles (SECURITY-11)

| Caso | Control |
|---|---|
| Un usuario sin el rol de ARC intenta cargar o consultar lotes | BR-A01 a BR-A04; el rol nunca sale de la petición |
| Un archivo enorme, o un `.xls` armado para agotar memoria o tiempo | BR-L02, BR-L03, BR-L08 y BR-L11; lectura con una librería que no ejecuta macros ni fórmulas; throttling de WSO2 AM (AD-23) |
| Un nombre de archivo con rutas o con HTML | BR-L01; el nombre interno no sale del original; U2 muestra el nombre con el escape de Angular |
| Una IP falsa en `X-Forwarded-For` | Se toma la entrada del último proxy de confianza (AD-29, D13) |
| Un usuario de ARC carga un lote solo para cancelar solicitudes ajenas | Solo ARC puede cargar; la auditoría guarda quién canceló qué solicitudes y cuándo (BR-U02); el throttling limita la repetición |
| Dos lotes al mismo tiempo con el mismo estudiante | Cada fila toma un bloqueo por el código del estudiante en MySQL entre la cancelación y el guardado (BR-T05, N5), así que queda la solicitud del lote que guarda de último; la auditoría registra los dos lotes. *Corregido el 2026-11-25, después de la aprobación* |
| Un lote que tarda demasiado y deja a ARC sin reporte | Límite propio del lote (BR-L16), además de los máximos de tamaño y de filas |
| Textos con HTML o script en las celdas | Las celdas solo se usan como números o como marcas; el código del rechazo se recorta (DF-08) y U2 lo escapa |
| Inyección de SQL con el contenido de las celdas | Las consultas usan parámetros enlazados (SECURITY-05); el código se valida como número antes de consultarlo |
| Una regla, un porcentaje o un festivo que falta | El lote no se procesa (BR-L04, BR-L05, BR-L13): falla cerrada (SECURITY-15) |
| Descuento y votación que dejarían el recibo negativo | BR-X05 |

## 14. Trazabilidad

| Historia | Reglas |
|---|---|
| US-01 | BR-A01 a BR-A04 |
| US-02 | BR-L01 a BR-L07, BR-L11 |
| US-03, US-04, US-05 | BR-L08 a BR-L10 |
| US-06 | BR-F01, BR-F02, BR-E01 a BR-E07 |
| US-07 | BR-D03, BR-X01 a BR-X07, BR-C01, BR-C02, BR-Q01, BR-Q04, BR-S01 a BR-S04 |
| US-08 | BR-D01 a BR-D06, BR-X01 a BR-X06, BR-C01, BR-C02, BR-Q02 a BR-Q04, BR-S01 a BR-S04 |
| US-09 | BR-T01, BR-T02, BR-T05 |
| US-10 | BR-T02 a BR-T05 |
| US-11 | BR-S01 a BR-S04, BR-X06, BR-C02, `domain-entities.md` §4 |
| US-12 | BR-R01 a BR-R03, BR-L16, §10 |
| US-13 | BR-H01 a BR-H03 |
| US-14 | BR-U01 a BR-U03 |
| US-15 | BR-L04, BR-L05, §11 |
