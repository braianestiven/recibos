# Historias de usuario — Migración del módulo de recibos por lote

- Etapa: INCEPTION → User Stories (Parte 2)
- Fuente: `aidlc-docs/inception/requirements/requirements.md` (aprobado 2026-11-24)
- Persona principal: Profesional de ARC (`personas.md`)
- Decisiones de planificación: Q1-a (por capacidad), Q2-a (solo IN), **Q3-b (borradores bloqueados)**, Q4-a, Q5-a (Dado/Cuando/Entonces), Q6-a (español, Must)
- Estado: **aprobadas 2026-11-24**. Actualizadas el mismo día con las decisiones P-3, P-5, P-7 y P-11 y con lo que muestra el código PHP actual (ver §Registro de cambios). Actualizadas el 2026-11-25 con las decisiones de Reverse Engineering y con el análisis de "Solicitados" (mismo registro; D3 resuelta; C6 = b, C7 = a y C8 = a, respondidas el mismo día), y con las respuestas F1 a F13 del diseño funcional de U1 (mismo registro), y con las decisiones de NFR Requirements de U1 (mismo registro), y con las respuestas de NFR Design de U1 (mismo registro)

## Convenciones

- **✅ Lista**: criterios completos; puede pasar a diseño y construcción.
- **🔒 Borrador — bloqueada (Dx / P-n)**: un insumo o una decisión pendiente puede cambiar los criterios de aceptación. La historia se escribe con lo conocido y los huecos se marcan `[PENDIENTE Dx]` o `[PENDIENTE P-n]`. Pasa a ✅ cuando se resuelve.
- **Dependencia técnica**: insumo que solo afecta la implementación, con comportamiento ya conocido o un valor por defecto aprobado (A1–A8). No bloquea la historia.
- **`[P-n]`**: punto por confirmar (ver §Puntos por confirmar).
- **Cambio acordado**: comportamiento que difiere a propósito del sistema actual. La comparación de equivalencia (C-4) lo excluye (`requirements.md` §12.3).
- Dependencias D1–D7 y supuestos A1–A8: ver `requirements.md` §8 y §9.
- Prioridad: todas **Must** (MVP, plazo 15/12/2026). El orden sigue el flujo del usuario.
- Las preguntas pendientes se hacen en el chat, en la etapa que las necesita (`plans/execution-plan.md`).

## Resumen

| ID | Historia | Épica | RF | Estado |
|---|---|---|---|---|
| US-01 | Iniciar sesión y acceder con el rol ARC | E1 Acceso | RF-14, RF-15 | ✅ Lista |
| US-02 | Cargar un archivo de lote | E2 Carga | RF-01, RF-12 | ✅ Lista |
| US-03 | Validar el formato de la plantilla de pregrado (sin Reingreso, con fechas) | E2 Carga | RF-02 | 🔒 Bloqueada (D1) |
| US-04 | Validar el formato de la plantilla de posgrado por créditos | E2 Carga | RF-02 | ✅ Lista |
| US-05 | Validar el formato de la plantilla de posgrado SMLV | E2 Carga | RF-02 | 🔒 Bloqueada (D2) |
| US-06 | Validar cada estudiante contra Oracle académico | E3 Procesamiento | RF-03 | ✅ Lista |
| US-07 | Generar solicitudes de pregrado | E3 Procesamiento | RF-04, RF-05, RF-06, RF-07 | 🔒 Bloqueada (D1) |
| US-08 | Generar solicitudes de posgrado | E3 Procesamiento | RF-04, RF-05, RF-06, RF-07 | 🔒 Bloqueada (solo la variante SMLV: D2) |
| US-09 | Cancelar solicitudes anteriores sin imprimir | E3 Procesamiento | RF-08 | ✅ Lista |
| US-10 | Guardar cada solicitud completa o no guardarla | E3 Procesamiento | RF-10 | ✅ Lista |
| US-11 | Entregar las solicitudes a "Solicitados" | E3 Procesamiento | RF-16, RF-04 | 🔒 Bloqueada (D4) |
| US-12 | Ver el resumen del lote procesado | E4 Resultados | RF-11 | ✅ Lista |
| US-13 | Consultar el historial de lotes | E4 Resultados | RF-12 | ✅ Lista |
| US-14 | Registrar la auditoría de cada petición | E4 Resultados | RF-13 | ✅ Lista |
| US-15 | Obtener las reglas desde el servicio "parametros" | E5 Reglas | RF-09 | ✅ Lista |

Total: 15 historias. 10 listas, 5 bloqueadas. US-13 y US-14 son funcionalidades nuevas, sin equivalente en el sistema actual (`requirements.md` §12.7).

---

## E1 — Acceso

### US-01 — Iniciar sesión y acceder con el rol ARC
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-14, RF-15 · IN-9
- **Historia:** Como profesional de ARC, quiero iniciar sesión con mi cuenta institucional de WSO2 y entrar al módulo de recibos, para gestionar los lotes sin que nadie sin el rol pueda hacerlo.

```text
Escenario 1: Usuario con el rol ARC
  Dado que inicié sesión en el microcliente core con WSO2
  Y tengo el rol "Admisiones, Registro y Control" en configuracion_cliente
  Cuando abro el módulo de recibos
  Entonces veo las opciones de cargar lote y consultar historial
  Y cada llamada a recibos_service lleva mi token Bearer

Escenario 2: Usuario autenticado sin el rol
  Dado que inicié sesión con WSO2
  Y no tengo el rol ARC
  Cuando intento usar cualquier operación de recibos_service
  Entonces el backend responde 403 con el sobre {Success, Status, Message, Data}
  Y no se procesa ninguna acción

Escenario 3: Token ausente o inválido
  Dado una petición a recibos_service sin token o con un token que /oauth2/userinfo rechaza
  Cuando llega al backend
  Entonces responde 401 con el sobre institucional

Escenario 4: El cliente intenta enviar su propio rol o permisos
  Dado una petición que incluye un parámetro de rol, nivel o permisos
  Cuando el backend la procesa
  Entonces ignora ese valor y decide solo con el rol obtenido a partir del token
```

- Reglas: el token y los datos personales no se guardan en `localStorage` ni en cookies sin protección. El backend valida el token en cada petición, sin caché (SECURITY-08). El rol ARC corresponde al nivel 132 de weboffice; en el módulo de notas de ARC (`admin_consultasCoordinador`) ese nivel llega en el parámetro `tipoUser` de la petición (R3, RE-19), y el escenario 4 evita repetir ese defecto.
- Dependencias técnicas: ninguna.

---

## E2 — Carga de lote

### US-02 — Cargar un archivo de lote
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-01, RF-12 · IN-1, IN-8
- **Historia:** Como profesional de ARC, quiero subir el archivo `.xls` de la plantilla, para generar en una sola operación las solicitudes de recibo de un grupo de estudiantes.

```text
Escenario 1: Archivo válido
  Dado que tengo el rol ARC
  Cuando subo un archivo .xls cuyo contenido real es BIFF (Excel 97-2003)
  Y su tamaño no supera el máximo de 2 MB (N7)
  Entonces el archivo se guarda en el bucket S3 privado y cifrado con un nombre interno generado por el sistema
  Y se registra el lote en solicitudLote con mi documento de identidad, el nombre original, el nombre interno, mi IP y la fecha (timestamp Unix)
  Y el sistema continúa con la validación de formato (US-03, US-04, US-05)

Escenario 2: Extensión o tipo real no permitido
  Dado un archivo .xlsx, .csv, o un archivo renombrado a .xls cuyo contenido no es BIFF
  Cuando lo subo
  Entonces el sistema rechaza el lote con el motivo "Solo se aceptan plantillas .xls"
  Y no procesa ningún estudiante

Escenario 3: Archivo demasiado grande
  Dado un archivo que supera el tamaño máximo
  Cuando lo subo
  Entonces el sistema rechaza el lote indicando el tamaño máximo permitido

Escenario 4: Lote con más filas que el máximo
  Dado una plantilla con más de 1000 filas con datos
  Cuando la subo
  Entonces el sistema rechaza el lote completo sin procesar ninguna fila
  Y el mensaje indica el máximo (1000) y cuántas filas trae el archivo
  Y el lote queda registrado en el historial, como los demás rechazos de formato (F1)
```

- Reglas: el archivo no queda en el disco local del contenedor. El nombre original no se usa como nombre de almacenamiento. La IP se toma de `X-Forwarded-For`, con la dirección que agrega el último proxy de confianza (RE-13, D13). El lote se registra al cargarse, antes de validar el formato, como hoy; los archivos rechazados por tipo o tamaño no se guardan ni se registran (la petición queda en la auditoría, US-14).
- Dependencias técnicas: tamaño máximo y retención en S3 (A1, D7); documento del usuario desde WSO2 (A8).
- Decisión F1 (P-1, 2026-11-25): un lote con más de 1000 filas con datos se rechaza completo (escenario 4). Es un cambio frente a hoy, que no tiene máximo.

### US-03 — Validar el formato de la plantilla de pregrado (sin Reingreso, con fechas)
- **Estado:** 🔒 Borrador — bloqueada (**D1**: plantilla oficial de pregrado sin Reingreso y con las fechas de pago, OQ-B-3 y C3)
- **Prioridad:** Must · **Trazabilidad:** RF-02 CA1, CA4 · IN-1 · C-3
- **Historia:** Como profesional de ARC, quiero que el sistema reconozca la plantilla de pregrado y rechace cualquier formato distinto, para no generar solicitudes a partir de datos mal ubicados.

```text
Escenario 1: Plantilla de pregrado vigente
  Dado un archivo cuya celda A1 dice "PLANTILLA GENERAL PREGRADOS" [PENDIENTE D1: confirmar texto]
  Y tiene las columnas y los encabezados oficiales: las 13 de hoy sin "Reingreso" más las de fecha de pago [PENDIENTE D1: número de columnas, encabezados y posición de las fechas]
  Cuando el sistema valida el formato
  Entonces lo identifica como tipo 1 (pregrado)
  Y lee los datos desde la fila 4 [PENDIENTE D1: confirmar fila inicial]

Escenario 2: Plantilla anterior (con "Reingreso")
  Dado un archivo de pregrado con la estructura anterior, que trae la columna "Reingreso"
  Cuando el sistema valida el formato
  Entonces rechaza el lote con un motivo que indica que se debe usar la plantilla vigente

Escenario 3: Columnas o encabezados que no coinciden
  Dado un archivo de pregrado con otro número de columnas o con encabezados en otro orden
  Cuando el sistema valida el formato
  Entonces rechaza el lote completo con el motivo
  Y no procesa ninguna fila
```

- La plantilla anterior se reconoce por sus encabezados, no por el número de columnas, porque la nueva también puede tener 14 o más.
- Columnas esperadas (supuesto hasta D1, según `templates-analysis.md` sin la columna 14; faltan las de fecha, C3): 1 Código del estudiante · 2 Seguro Estudiantil · 3 Carnet Estudiantil · 4 Sistematización · 5 10% votación · 6 2do Hermano · 7 3er Hermano · 8 Terminación de Materias · 9 Beneficiario · 10 Matrícula de Honor · 11 Deportista de alto rendimiento · 12 Estudiante Distinguido / Cultural-Científico · 13 Mérito Académico.
- Para desbloquear: ARC entrega el `.xls` oficial en `documentacion/plantillas-recibos/` y confirma A1, fila inicial y encabezados.

### US-04 — Validar el formato de la plantilla de posgrado por créditos
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-02 CA2, CA4 · IN-1
- **Historia:** Como profesional de ARC, quiero que el sistema reconozca la plantilla de posgrado por créditos y rechace formatos distintos, para que las cuotas, fechas y porcentajes se lean de las columnas correctas.

```text
Escenario 1: Plantilla de créditos vigente
  Dado un archivo cuya celda A1 dice "PLANTILLA GENERAL POSTGRADOS CREDITOS"
  Y tiene 29 columnas con los encabezados oficiales
  Cuando el sistema valida el formato
  Entonces lo identifica como tipo 2 (posgrado por créditos)
  Y lee los datos desde la fila 5

Escenario 2: Número de columnas distinto de 29
  Dado un archivo de créditos con 28 o 30 columnas
  Cuando el sistema valida el formato
  Entonces rechaza el lote completo con el motivo

Escenario 3: Texto de A1 desconocido
  Dado un archivo cuya celda A1 no corresponde a ninguna de las tres plantillas
  Cuando el sistema valida el formato
  Entonces rechaza el lote con el motivo "Plantilla no reconocida"
```

- Columnas: según `templates-analysis.md` (1 código, 2 créditos, 3 cuotas, 4–6 conceptos, 7–17 exenciones, 18–26 fechas de las cuotas 1–3, 27–29 porcentajes).
- Dependencias técnicas: ninguna. Se usa como caso de prueba el archivo oficial de créditos analizado en Discovery.

### US-05 — Validar el formato de la plantilla de posgrado SMLV
- **Estado:** 🔒 Borrador — bloqueada (**D2**: plantilla oficial de posgrado SMLV, OQ-B-2)
- **Prioridad:** Must · **Trazabilidad:** RF-02 CA3, CA4 · IN-1
- **Historia:** Como profesional de ARC, quiero que el sistema reconozca la plantilla de posgrado en salarios mínimos, para generar las solicitudes de los programas que cobran en SMLV.

```text
Escenario 1: Plantilla SMLV vigente
  Dado un archivo cuya celda A1 dice "PLANTILLA GENERAL POSTGRADOS SALARIOS MINIMOS LEGALES"
  Y tiene 29 columnas [PENDIENTE D2: confirmar número y encabezados]
  Cuando el sistema valida el formato
  Entonces lo identifica como tipo 3 (posgrado SMLV)
  Y lee los datos desde la fila 5 [PENDIENTE D2]

Escenario 2: Formato que no coincide
  Dado un archivo SMLV con otro número de columnas o encabezados
  Cuando el sistema valida el formato
  Entonces rechaza el lote completo con el motivo
```

- Supuesto hasta D2 (A6): misma estructura que créditos, con "SMLV" en la columna 2. El código actual procesa los tipos 2 y 3 con la misma lógica.
- Para desbloquear: ARC entrega el `.xls` oficial y se verifica contra `templates-analysis.md`.

---

## E3 — Procesamiento

### US-06 — Validar cada estudiante contra Oracle académico
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-03 · IN-2
- **Historia:** Como profesional de ARC, quiero que el sistema verifique cada estudiante en el sistema académico antes de generar su solicitud, para no emitir recibos a estudiantes que no corresponden.

```text
Escenario 1: Estudiante válido
  Dado una fila con un código de estudiante numérico
  Y el estudiante existe en Oracle académico con valor de matrícula
  Y su estado está en la lista de estados permitidos (hoy V, J, T, A, Q o B)
  Y su proyecto curricular está activo
  Cuando el sistema procesa la fila
  Entonces el estudiante pasa a la generación de la solicitud (US-07 o US-08)

Escenario 2: Código no numérico o vacío
  Dado una fila cuyo código de estudiante no es numérico, o una fila con datos en otras columnas y sin código
  Cuando el sistema procesa la fila
  Entonces rechaza esa fila con el motivo "Código inválido", o "Falta el código del estudiante" si no tiene código (F3)
  Y continúa con las demás filas

Escenario 3: Estudiante inexistente
  Dado un código que no existe en Oracle académico
  Cuando el sistema procesa la fila
  Entonces rechaza ese estudiante con el motivo "Estudiante no encontrado"

Escenario 4: Estudiante sin información de matrícula
  Dado un estudiante que existe en Oracle académico pero no tiene valor de matrícula (V_ACESTMATBRUTO)
  Cuando el sistema procesa la fila
  Entonces rechaza ese estudiante con el motivo "Sin información de matrícula; solicitar por oficio"

Escenario 5: Estado no permitido
  Dado un estudiante cuyo estado no está en la lista de estados permitidos
  Cuando el sistema procesa la fila
  Entonces rechaza ese estudiante indicando su estado

Escenario 6: Proyecto curricular no activo
  Dado un estudiante cuyo proyecto curricular no está activo (cra_estado distinto de 'A') o tiene código 0 o 999
  Cuando el sistema procesa la fila
  Entonces rechaza ese estudiante con el motivo "El proyecto curricular del estudiante no está activo"

Escenario 7: Evento de terminación de materias activo
  Dado que el evento de terminación de materias (hoy 82) está activo para el proyecto curricular del estudiante
  Y el estado del estudiante no es T ni H
  Cuando el sistema procesa la fila
  Entonces rechaza ese estudiante con el motivo "El estado del estudiante es diferente de terminación de materias"

Escenario 8: Proyecto curricular sin periodo vigente
  Dado un estudiante que pasa las validaciones anteriores
  Y su proyecto curricular no tiene año y periodo vigentes en la base académica (evento 80), o tiene más de uno (A13)
  Cuando el sistema procesa la fila
  Entonces no sube ese estudiante
  Y el motivo dice "No hay periodo vigente para el proyecto curricular del estudiante. Repórtelo al área de sistemas"

Escenario 9: Estudiante de otro nivel
  Dado un estudiante de un proyecto de pregrado en una plantilla de posgrado, o de posgrado en la plantilla de pregrado
  Cuando el sistema procesa la fila
  Entonces no sube ese estudiante
  Y el motivo dice "El nivel del proyecto curricular del estudiante no corresponde a la plantilla" (F5)

Escenario 10: Código repetido en el lote
  Dado un código que aparece en dos o más filas del lote
  Cuando el sistema procesa el lote
  Entonces solo procesa la primera aparición
  Y las siguientes aparecen como no subidas con el motivo "El código ya está en la fila N" (F2)
  Y esas filas no cancelan solicitudes
```

- Reglas: Oracle se consulta solo en lectura, con parámetros enlazados. Un estudiante rechazado pierde igualmente sus solicitudes sin imprimir, de cualquier periodo, si su código está registrado (US-09, RE-02, C8). El escenario 8 es un cambio acordado (RE-05): hoy la solicitud se guarda sin año ni periodo. ARC procesa estudiantes de cualquier proyecto curricular activo (comportamiento actual del nivel 132). Las validaciones se aplican en el orden de los escenarios 3 a 9 (los escenarios 3 a 7 en el orden de hoy; el 8 y el 9 son nuevos), y el motivo es el de la primera que falla. Como H no está en la lista de estados permitidos, un estudiante en H se rechaza en el escenario 5 (comportamiento actual, P-8 resuelto). La lista de estados y el número de evento vienen de los parámetros (US-15), no del código. Los escenarios 9 (F5) y 10 (F2) son cambios acordados; las filas repetidas del escenario 10 no se procesan, así que no cancelan solicitudes.
- Dependencias técnicas: valores de los parámetros (D6).
- Decisiones de U1 Functional Design (2026-11-25): F2 (P-2, escenario 10), F3 (escenario 2) y F5 (escenario 9).

### US-07 — Generar solicitudes de pregrado
- **Estado:** 🔒 Borrador — bloqueada (**D1**: archivo oficial de la plantilla de pregrado; posición de las columnas de la fecha). C1, C2 y C3 se resolvieron el 2026-11-25, y C6 y C7 el mismo día. F8 fijó que la plantilla trae solo la fecha ordinaria.
- **Prioridad:** Must · **Trazabilidad:** RF-04, RF-05 CA1, RF-06, RF-07 · IN-3
- **Historia:** Como profesional de ARC, quiero que cada estudiante de pregrado válido reciba una solicitud con una sola cuota, sus exenciones y sus conceptos, para que su recibo salga con el valor y las fechas correctas.

```text
Escenario 1: Cuota única
  Dado un estudiante de pregrado válido
  Cuando el sistema genera su solicitud
  Entonces crea exactamente una cuota al 100%
  Y toma la fecha ordinaria de su fila en la plantilla, en tres columnas: día, mes y año [PENDIENTE D1: posición de las columnas]
  Y calcula la fecha extraordinaria como en posgrado: 8 días calendario después y, si cae en festivo, el siguiente día que no lo sea (F8)
  Y asocia la solicitud al año y periodo vigentes de su proyecto curricular (evento 80 del calendario académico)

Escenario 2: Sin diferido ni cuotas al 0%
  Dado un estudiante de pregrado con diferido aprobado en Oracle
  Cuando el sistema genera su solicitud
  Entonces crea igualmente una sola cuota al 100%
  Y no crea cuotas al 0%

Escenario 3: "Seguro Estudiantil" no es número de cuotas
  Dado una fila con un valor en la columna "Seguro Estudiantil"
  Cuando el sistema genera la solicitud
  Entonces lo registra solo como concepto de seguro
  Y no cambia el número de cuotas

Escenario 4: Un descuento
  Dado una fila con un solo descuento marcado en las columnas 6 a 13
  Cuando el sistema genera la solicitud
  Entonces registra ese descuento con el id que indica el mapa columna → exención
  Y no registra la exención "Reingreso"

Escenario 5: Más de un descuento (no acumulables)
  Dado una fila con dos o más descuentos marcados en las columnas 6 a 13
  Cuando el sistema procesa la fila
  Entonces no sube ese estudiante
  Y aparece en el resumen con el motivo "Solo se puede marcar un descuento además de la votación"

Escenario 6: Votación marcada
  Dado una fila con la columna "10% votación" marcada
  Y como máximo un descuento marcado, que sumado a la votación no pasa de 100%
  Cuando el sistema genera la solicitud
  Entonces registra la exención de votación una sola vez
  Y registra también el descuento, si lo hay

Escenario 7: Votación marcada con un descuento de las columnas 8 a 13
  Dado una fila con la columna "10% votación" marcada
  Y un descuento marcado en las columnas 8 a 13 que, sumado a la votación, no pasa de 100%
  Cuando el sistema genera la solicitud
  Entonces registra la votación y el descuento (hoy la votación se quita)

Escenario 8: Votación automática
  Dado una fila sin la columna "10% votación" marcada
  Y con un descuento marcado que, sumado a la votación, no pasa de 100%
  Y el estudiante tiene certificado electoral activo en ACCERELECTORAL
  Cuando el sistema genera la solicitud
  Entonces registra la exención de votación una sola vez, además del descuento

Escenario 9: Conceptos
  Dado un estudiante de pregrado válido
  Cuando el sistema genera la solicitud
  Entonces registra el concepto de matrícula y el concepto exclusivo de pregrado (hoy 1 y 19)
  Y registra seguro, carnet y sistematización (hoy 2, 3 y 4) según las columnas 2 a 4

Escenario 10: Terminación de materias
  Dado una fila con la columna "Terminación de Materias" marcada (columna 8)
  Cuando el sistema genera la solicitud
  Entonces registra la exención de terminación de materias (hoy id 4) como el descuento de la fila
  Y toma las fechas de pago de la plantilla, como en cualquier otra fila

Escenario 11: Fila sin fechas de pago
  Dado una fila de pregrado sin la fecha de pago, con una fecha inválida o con una fecha anterior al día de la carga (F7) [PENDIENTE D1: posición de las columnas]
  Cuando el sistema procesa la fila
  Entonces no sube ese estudiante
  Y aparece en el resumen con el motivo "Falta la fecha o es inválida"

Escenario 12: Fila sin exenciones marcadas
  Dado una fila sin ninguna columna de exención marcada
  Y el estudiante tiene certificado electoral activo
  Cuando el sistema genera la solicitud
  Entonces no registra la votación automática, como hoy

Escenario 13: Descuento y votación por encima de 100%
  Dado una fila con un descuento marcado que, sumado a la votación, pasa de 100% (por ejemplo, un descuento de 100%)
  Y la columna "10% votación" marcada, o sin marcar y con certificado electoral activo
  Cuando el sistema genera la solicitud
  Entonces registra solo el descuento (C7)
```

- Reglas: una columna está marcada si su celda tiene contenido distinto de espacios (F4; hoy cuenta cualquier contenido). Los IDs y el mapa columna → exención vienen de los parámetros (US-15), y los porcentajes de las exenciones, de la tabla `exencion` (F11); las fechas vienen de la plantilla (C3). Salvo los cambios acordados, la solicitud coincide con la del sistema actual.
- Cambios acordados: sin diferido ni cuotas al 0%; "Seguro" no es cuota; sin "Reingreso"; las fechas vienen de la plantilla y no de las fechas de la facultad, y la columna de terminación de materias ya no cambia las fechas (C3); sin fechas la fila no se sube (RE-06); con más de un descuento marcado la fila no se sube (C2; hoy se registran todos los marcados); la votación marcada se registra con cualquier descuento, también con los de las columnas 8 a 13 (C2; hoy no se registra con esas columnas), salvo que la suma pase de 100%: entonces se registra solo el descuento (C7). Desde F4, F7 y F8 (2026-11-25): una celda con solo espacios no cuenta como marcada, ninguna fecha ordinaria es anterior al día de la carga, y la plantilla trae solo la fecha ordinaria; la extraordinaria se calcula.
- Sin cambio frente a hoy: la votación automática (escenarios 8, 12 y 13; C1, C6 y A14). Con la votación en 10%, la regla de C7 equivale al tope actual de 90%.
- Dependencias técnicas: el porcentaje de cada exención se lee de la tabla `exencion` (F11); los festivos, de la tabla de weboffice que identifique el DBA (F9, D5).
- Para desbloquear: ARC entrega el archivo oficial de la plantilla de pregrado (D1).

### US-08 — Generar solicitudes de posgrado
- **Estado:** 🔒 Borrador — bloqueada (solo la variante SMLV, por **D2**). C1, C2, C6 y C7 se resolvieron el 2026-11-25, y F14 y F15 el mismo día. D5 pasó a dependencia técnica con F9 y F10.
- **Prioridad:** Must · **Trazabilidad:** RF-04, RF-05 CA2–CA3, RF-06, RF-07 · IN-3
- **Historia:** Como profesional de ARC, quiero que cada estudiante de posgrado reciba una solicitud con las cuotas, fechas y porcentajes indicados en la plantilla, para respetar los acuerdos de pago de cada programa.

```text
Escenario 1: Cuotas y porcentajes indicados
  Dado una fila de posgrado con 2 cuotas, sus fechas ordinarias y porcentajes 70 y 30
  Cuando el sistema genera la solicitud
  Entonces crea 2 cuotas con esos porcentajes y fechas ordinarias
  Y registra los créditos o SMLV de la columna 2 como unidad
  Y asocia la solicitud al año y periodo vigentes de su proyecto curricular

Escenario 2: Porcentajes vacíos
  Dado una fila con N cuotas y sin porcentajes
  Cuando el sistema genera la solicitud
  Entonces aplica los porcentajes por defecto: 1 cuota = 100; 2 cuotas = 60/40; 3 cuotas = 40/30/30

Escenario 3: Porcentajes parciales
  Dado una fila de 2 cuotas con porcentaje 60 en la cuota 1 y la cuota 2 vacía
  Cuando el sistema genera la solicitud
  Entonces completa la cuota 2 con su valor por defecto (40), como hoy

Escenario 4: Porcentajes que no suman 100
  Dado una fila cuyos porcentajes, después de completar los vacíos, no suman 100
  Cuando el sistema procesa la fila
  Entonces rechaza ese estudiante con el motivo "Los porcentajes de las cuotas deben sumar 100"

Escenario 5: Fecha extraordinaria
  Dado una cuota con fecha ordinaria D
  Cuando el sistema calcula la fecha extraordinaria
  Entonces suma 8 días calendario a D
  Y si ese día está en la tabla de festivos de weboffice, avanza un día a la vez hasta el primero que no lo esté (F9)
  Y un sábado o un domingo que no esté en esa tabla no mueve la fecha (F10)

Escenario 6: Número de cuotas vacío o inválido
  Dado una fila sin número de cuotas o con un número fuera de 1 a 3
  Cuando el sistema procesa la fila
  Entonces no sube ese estudiante
  Y aparece en el resumen con el motivo "El número de cuotas es obligatorio y debe estar entre 1 y 3"

Escenario 7: Fecha o porcentaje inválido
  Dado una fila en la que alguna de sus N cuotas no tiene fecha, tiene una fecha inexistente, sin año completo o anterior al día de la carga, vence antes que la cuota anterior (F7), o tiene un porcentaje que no es un entero de 0 a 100
  Cuando el sistema procesa la fila
  Entonces rechaza ese estudiante indicando la cuota y la columna con error

Escenario 8: Descuentos
  Dado una fila de posgrado con descuentos marcados en las columnas 8 a 17
  Cuando el sistema procesa la fila
  Entonces, si hay uno, lo registra según el mapa columna → exención de posgrado
  Y si hay más de uno, no sube ese estudiante y el motivo es "Solo se puede marcar un descuento además de la votación y de la Secretaría de Educación"
  Y la Secretaría de Educación (columna 16) no cuenta como descuento: puede ir con la votación y un descuento (F12)

Escenario 9: Votación marcada en posgrado
  Dado una fila de posgrado con la columna "10% votación" (columna 7) marcada
  Cuando el sistema genera la solicitud
  Entonces registra la votación una sola vez
  Y si el descuento sumado a la votación pasa de 100%, registra solo el descuento (C7; hoy registra las dos)

Escenario 10: Votación automática en posgrado
  Dado una fila de posgrado sin la columna 7 marcada
  Y con un descuento marcado que, sumado a la votación, no pasa de 100%
  Y el estudiante tiene certificado electoral activo en ACCERELECTORAL
  Cuando el sistema genera la solicitud
  Entonces registra la votación una sola vez, además del descuento
  Y si la fila no tiene ninguna exención marcada, no registra la votación automática, como hoy

Escenario 11: Conceptos
  Dado un estudiante de posgrado válido
  Cuando el sistema genera la solicitud
  Entonces registra el concepto de matrícula y los de seguro, carnet y sistematización según las columnas 4 a 6
  Y no registra el concepto exclusivo de pregrado

Escenario 12: Créditos o SMLV inválidos
  Dado una fila de posgrado con la columna 2 vacía, en 0, negativa o con texto, o con decimales en la plantilla de créditos, o con más de dos decimales en la de SMLV
  Cuando el sistema procesa la fila
  Entonces no sube ese estudiante
  Y el motivo dice "Los créditos o SMLV son obligatorios y deben ser mayores que 0" (F6)

Escenario 13: Votación, descuento y Secretaría de Educación
  Dado una fila de posgrado con la votación, un descuento y la Secretaría de Educación marcados
  Cuando el sistema genera la solicitud
  Entonces registra las tres exenciones, en el orden votación, descuento y Secretaría (F12, RE-24)
  Y la Secretaría no entra en la suma de C7: si el descuento y la votación pasan de 100%, se quita la votación (F14)

Escenario 14: Solo la Secretaría de Educación marcada
  Dado una fila de posgrado con solo la Secretaría de Educación marcada
  Y el estudiante tiene certificado electoral activo
  Cuando el sistema genera la solicitud
  Entonces registra la votación y la Secretaría, como hoy (F15)
```

- Reglas: los porcentajes por defecto, el plazo de 8 días y el mapa de exenciones vienen de los parámetros (US-15); los porcentajes de las exenciones, de la tabla `exencion` (F11).
- Cambios acordados: el número de cuotas es obligatorio y va de 1 a 3 (RE-03, RE-04; hoy la celda vacía genera 1 cuota); los porcentajes deben sumar 100 (P-5; hoy no se valida); con más de un descuento marcado la fila no se sube (C2; hoy se registran todos); validación estricta de fechas (Entorno técnico; hoy solo se revisa día ≤ 31 y mes ≤ 12). La votación marcada se registra con cualquier descuento mientras la suma no pase de 100%; si pasa, se registra solo el descuento (C7; hoy en posgrado se registran las dos). La votación automática da el mismo resultado que hoy (C1, C6, A14). Desde F6 y F7 (2026-11-25): la columna 2 es obligatoria y mayor que 0, los porcentajes de las cuotas son enteros, ninguna fecha ordinaria es anterior al día de la carga y cada cuota vence después de la anterior. Con la Secretaría y un descuento de más de 20%, la votación automática se agrega (F14; hoy no).
- A14 quedó resuelto el 2026-11-25 con C6 y C7. La regla de C7 evita que "Solicitados" deje la matrícula negativa (RE-23).
- Para desbloquear: plantilla SMLV para esa variante (D2). D5 (identificar la tabla de festivos de weboffice) es una dependencia técnica desde F9 y F10.
- Decisiones de U1 Functional Design (2026-11-25): F6 (P-6, escenario 12), F7 (escenario 7), F9 y F10 (escenario 5), F11 y F12 (escenarios 8 y 13), F14 (escenario 13) y F15 (escenario 14). Reglas detalladas: BR-D01 a BR-X07 en `aidlc-docs/construction/recibos_service/functional-design/business-rules.md`.

### US-09 — Cancelar solicitudes anteriores sin imprimir
- **Estado:** ✅ Lista (C8 se resolvió el 2026-11-25) · **Prioridad:** Must · **Trazabilidad:** RF-08 · IN-4
- **Historia:** Como profesional de ARC, quiero que cada vez que cargo un estudiante, se genere o no su solicitud nueva, se cancelen sus solicitudes anteriores sin imprimir, de cualquier periodo, para que solo quede lo que resulte de la última carga.

```text
Escenario 1: Solicitud anterior sin imprimir
  Dado un estudiante con una solicitud anterior en estado 0 (sin imprimir)
  Cuando el sistema genera su nueva solicitud
  Entonces la anterior pasa a estado 2 (cancelada)
  Y la cancelación se guarda en su propia transacción, antes de la solicitud nueva (US-10)

Escenario 2: Solicitud anterior ya impresa
  Dado un estudiante con una solicitud anterior en un estado distinto de 0
  Cuando el sistema genera su nueva solicitud
  Entonces no modifica esa solicitud

Escenario 3: Estudiante rechazado
  Dado un estudiante rechazado por cualquier motivo en la validación (US-06) o en la generación
  Y su código está registrado en Oracle
  Cuando el sistema procesa la fila
  Entonces cancela igualmente sus solicitudes sin imprimir, de cualquier periodo
  Y no crea una solicitud nueva

Escenario 4: Solicitud sin imprimir de otro periodo
  Dado un estudiante con una solicitud en estado 0 de un periodo anterior
  Cuando el sistema procesa su fila
  Entonces esa solicitud también pasa a estado 2 (cancelada), como hoy (C8)

Escenario 5: Estudiante desconocido
  Dado una fila rechazada por código inválido o estudiante no encontrado
  Cuando el sistema procesa la fila
  Entonces no cancela ninguna solicitud, porque no se sabe quién es el estudiante (A12)

Escenario 6: Proyecto sin periodo vigente
  Dado una fila rechazada porque el proyecto curricular del estudiante no tiene periodo vigente
  Cuando el sistema procesa la fila
  Entonces cancela igualmente las solicitudes sin imprimir del estudiante (RE-02, C8)
```

- Reglas: se cancelan las solicitudes en estado 0 del estudiante de cualquier periodo, como hace hoy `cancelarSolicitud` (C8). Las pruebas en paralelo con el sistema PHP se hacen sobre una base de datos de pruebas dedicada (OQ-B-5), así que esta regla nunca cancela solicitudes de producción.
- Sin cambio frente a hoy (C8, 2026-11-25): se cancelan las de todos los periodos. P-7 (solo el periodo vigente) se revirtió porque "Solicitados" deja generar en el periodo vigente las solicitudes viejas que no se cancelan (RE-26).
- Cambio acordado (RE-02): hoy los rechazados por estado, valor de matrícula o proyecto curricular no cancelan nada; los rechazados por terminación de materias, fechas o error al guardar sí, como en el sistema nuevo.
- Dependencias técnicas: DDL real de `solicitudRecibo` (D4).

### US-10 — Guardar cada solicitud completa o no guardarla
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-10 · IN-6
- **Historia:** Como profesional de ARC, quiero que cada solicitud quede guardada completa o no quede, para no tener solicitudes sin cuotas o sin conceptos que "Solicitados" no pueda imprimir.

```text
Escenario 1: Guardado exitoso
  Dado un estudiante válido con su solicitud calculada
  Cuando el sistema la guarda
  Entonces antes cancela, en su propia transacción, las anteriores sin imprimir (US-09)
  Y después escribe en una sola transacción solicitudRecibo, solicitudCuota, solicitudExencion y solicitudConcepto

Escenario 2: Falla a mitad del guardado
  Dado que falla la escritura de cualquiera de esas tablas para un estudiante
  Cuando el sistema detecta el error
  Entonces revierte la transacción de la solicitud nueva
  Y mantiene la cancelación de las anteriores (RE-02)
  Y lo marca como rechazado con el motivo "Error al guardar la solicitud"
  Y continúa con el siguiente estudiante

Escenario 3: Verificación posterior
  Dado un lote procesado
  Cuando se consultan las solicitudes del lote
  Entonces no existe ninguna solicitud sin cuotas o sin conceptos

Escenario 4: Falla la cancelación
  Dado que falla la cancelación de las solicitudes anteriores de un estudiante válido
  Cuando el sistema detecta el error
  Entonces no escribe la solicitud nueva
  Y lo marca como rechazado con el motivo "Error al guardar la solicitud"
Escenario 5: MySQL deja de responder a mitad del lote
  Dado que fallan por la conexión con MySQL 5 estudiantes seguidos
  Cuando el sistema detecta la quinta falla
  Entonces deja de intentar con los estudiantes que faltan
  Y los marca como rechazados con el motivo "Error al guardar la solicitud"
  Y no cancela nada de esos estudiantes
  Y responde con el reporte del lote
```

- Reglas: el detalle técnico del error queda en el log; el motivo mostrado al usuario no expone SQL ni datos internos.
- Dependencias técnicas: DDL real (D4).

### US-11 — Entregar las solicitudes a "Solicitados"
- **Estado:** 🔒 Borrador — bloqueada (**D4**: DDL real y modelo aprobado, OQ-T-9). D3 quedó resuelta el 2026-11-25 con el código de "Solicitados" (RE-21, A15)
- **Prioridad:** Must · **Trazabilidad:** RF-16, RF-04 CA1 · IN-10
- **Historia:** Como profesional de ARC, quiero que las solicitudes generadas por el sistema nuevo aparezcan en "Solicitados" igual que las del sistema actual, para imprimir los recibos sin cambiar ese módulo.

```text
Escenario 1: Solicitud visible en "Solicitados"
  Dado una solicitud guardada por el sistema nuevo en la base de pruebas
  Cuando un usuario abre "Solicitados"
  Entonces la solicitud aparece como sin imprimir
  Y "Solicitados" genera el recibo sin errores

Escenario 2: Mismos registros que el sistema actual
  Dado una solicitud guardada por el sistema nuevo
  Cuando se revisan sus registros en MySQL
  Entonces solicitudRecibo tiene id_usuario, codigo_est, estado, anno, periodo, fecha, cuota, id_carrera, tipoPlantilla y unidad, como los escribe hoy el PHP
  Y solicitudCuota tiene id_solicitud, cuota, porcentaje, fecha_ordinaria y fecha_extra
  Y solicitudExencion y solicitudConcepto tienen id_solicitud y el id de la exención o del concepto
  Y las fechas están como timestamp Unix y los porcentajes entre 0 y 100
  Y la solicitud nueva queda en estado 0 y las canceladas en estado 2
  Y el campo cuota de solicitudRecibo vale 1 en pregrado y el número de cuotas en posgrado (A15; hoy en pregrado depende, por el defecto, de la columna "Seguro Estudiantil")

Escenario 3: Estructura sin cambios
  Dado las tablas solicitud*, exencion y fechaPagoFacultad
  Cuando el sistema nuevo entra en funcionamiento
  Entonces su estructura es la misma que antes [PENDIENTE D4: DDL de referencia]
```

- Reglas: `id_usuario` = documento de identidad del usuario (claim `documento` de WSO2, A8); `unidad` = créditos o SMLV en posgrado y `0` en pregrado, como hoy (RE-07, confirmado el 2026-11-25); `fecha` = momento de creación; `tipoPlantilla` = 1, 2 o 3. "Solicitados" lee solo el estado 0, recalcula los valores con sus propias reglas y pasa la solicitud a estado 1 al generar (RE-20 a RE-22).
- Para desbloquear: DDL real (D4: DBA).

---

## E4 — Resultados y trazabilidad

### US-12 — Ver el resumen del lote procesado
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-11 · IN-7
- **Historia:** Como profesional de ARC, quiero ver al terminar la carga qué estudiantes se subieron y cuáles no, con su motivo, para corregir los rechazados y volver a cargarlos.

```text
Escenario 1: Lote con procesados y rechazados
  Dado que cargué un lote de N estudiantes
  Cuando termina el procesamiento (en la misma petición)
  Entonces veo el total de procesados y de rechazados
  Y para cada estudiante que se subió veo su código y su fila
  Y para cada uno que no se subió veo su código, la fila y el motivo

Escenario 2: Lote rechazado por formato
  Dado un lote rechazado en la validación de formato
  Cuando termina la petición
  Entonces veo el motivo del rechazo del lote
  Y no se generó ninguna solicitud

Escenario 3: Coherencia con la base
  Dado el resumen de un lote
  Cuando se revisan las solicitudes escritas
  Entonces cada estudiante contado como procesado tiene una solicitud nueva en estado 0 con sus cuotas y conceptos
  Y ningún estudiante rechazado tiene una solicitud nueva

Escenario 4: Lote que llega al límite de tiempo
  Dado un lote que todavía tiene filas cuando el servicio llega a su límite propio de 90 segundos
  Cuando termina la petición
  Entonces veo el reporte con las filas que alcanzó a procesar
  Y las filas que faltaban aparecen como no subidas con el motivo "No se alcanzó a procesar en el tiempo del lote; vuelva a cargar esta fila" (N3)
  Y esas filas no cancelan solicitudes
```

- Reglas: la pantalla muestra solo código, fila y, en los que no se subieron, el motivo (pedido del usuario del 2026-11-25; el PHP actual también lista los códigos procesados) y usa el escape por defecto de Angular. El resumen no se guarda: solo se ve al terminar la carga (ver US-13).
- Decisión F13 (P-10, 2026-11-25): la lista no se exporta en el MVP; el reporte se ve en pantalla.

### US-13 — Consultar el historial de lotes
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-12 · IN-8
- **Funcionalidad nueva:** no existe en el sistema actual; el usuario la confirmó el 2026-11-25 (`requirements.md` §12.7)
- **Historia:** Como profesional de ARC, quiero consultar los lotes cargados, para saber quién cargó cada archivo, cuándo y desde qué IP.

```text
Escenario 1: Listado de lotes
  Dado que tengo el rol ARC
  Cuando abro el historial de lotes
  Entonces veo los lotes con el usuario, la fecha, el nombre original del archivo y la IP
  Y están ordenados del más reciente al más antiguo

Escenario 2: Lotes rechazados por formato
  Dado un lote que se rechazó en la validación de formato
  Cuando abro el historial
  Entonces ese lote también aparece, porque se registró al cargarse
```

- Reglas: se usa `solicitudLote` sin cambiar su estructura (`id_usuario`, `nombreOriginal`, `nombreInterno`, `ip`, `fecha`). Solo lectura. La tabla no guarda totales ni motivos (P-9 resuelto). Volver a ver el resumen de un lote anterior sería una funcionalidad nueva, fuera de la lista IN.

### US-14 — Registrar la auditoría de cada petición
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-13 · IN-8 · Actor: Seguridad
- **Funcionalidad nueva:** no existe en el sistema actual; el usuario la confirmó el 2026-11-25 (`requirements.md` §12.7)
- **Historia:** Como integrante de Seguridad, quiero un log de auditoría de cada petición al backend, para rastrear quién hizo qué y desde dónde sin exponer datos personales.

```text
Escenario 1: Petición registrada
  Dado cualquier petición a /v1/* de recibos_service, exitosa o fallida (los health checks no se auditan, AD-11)
  Cuando termina
  Entonces se escribe un log JSON con app_name, agent, data, date, host, ip_user, method, path, query, schema, sql_statement, status, trace_id y user
  Y trace_id lleva el identificador de la petición, el mismo de los registros de la aplicación (sin trazas de X-Ray en el MVP, N14)

Escenario 2: Sin datos personales
  Dado una petición que procesa datos de estudiantes
  Cuando se escribe el log
  Entonces el campo data no contiene datos personales (Ley 1581)
  Y sql_statement corresponde a las sentencias de esa petición, sin valores personales

Escenario 3: Logs siempre habilitados
  Dado cualquier ambiente desplegado (dev, test, prod)
  Cuando el servicio está en ejecución
  Entonces la auditoría no se puede desactivar por configuración
```

- Dependencias técnicas: destino y retención (A2, D7: CloudWatch Logs por defecto).

---

## E5 — Reglas parametrizadas

### US-15 — Obtener las reglas desde el servicio "parametros"
- **Estado:** ✅ Lista (2026-11-24: el usuario definió la consulta por id; el formato de la respuesta queda como dependencia técnica)
- **Prioridad:** Must · **Trazabilidad:** RF-09 · IN-5 · C-1
- **Historia:** Como profesional de ARC, quiero que las reglas de cada periodo (conceptos, exenciones, fechas, porcentajes, estados y eventos) se ajusten en el servicio "parametros", para no depender de cambios de código cada periodo.

```text
Escenario 1: Reglas vigentes al procesar
  Dado un lote en procesamiento
  Cuando el sistema necesita conceptos, exenciones, fechas de pago por facultad, porcentajes por defecto, estados permitidos, eventos de calendario, plazo de la fecha extraordinaria o el mapa columna → exención
  Entonces los obtiene del servicio "parametros", consultando cada regla por su id (GET /v1/parametro/{id})
  Y no usa valores fijos en el código

Escenario 2: Cambio de regla sin despliegue
  Dado que el responsable del servicio "parametros" actualizó una regla
  Cuando se procesa el siguiente lote
  Entonces se aplica la regla nueva sin cambiar ni desplegar recibos_service

Escenario 3: Servicio "parametros" no disponible
  Dado que "parametros" no responde o responde con error
  Cuando se intenta procesar un lote
  Entonces el lote no se procesa
  Y el usuario ve un motivo claro (cada consulta espera la respuesta hasta 3 s y se repite una vez si falla la conexión; todas juntas tienen 10 s como máximo)

Escenario 4: Solo lectura
  Dado cualquier operación de recibos_service
  Cuando usa el servicio "parametros"
  Entonces solo consulta reglas
  Y nunca crea, modifica ni borra reglas (P-11)

Escenario 5: Regla inexistente, inactiva o con valor inválido
  Dado que una regla no existe en "parametros", tiene Activo en false o su valor no se puede leer
  Cuando se intenta procesar un lote
  Entonces el lote no se procesa
  Y el mensaje indica qué regla falta o está mal
```

- Reglas: el acceso se aísla detrás de un puerto en `app/application/` con un adaptador en `app/infrastructure/` (Application Design no se bloquea).
- Dependencias técnicas: campo y formato del valor de cada regla, id de cada regla por ambiente, URL y autenticación (D6, acotada); creación de los parámetros en el servicio (D10). Salen de "parametros" todas las reglas salvo los porcentajes de las exenciones, que se leen de la tabla `exencion` (F11, que cambia P-15 en ese punto), y los festivos, que se leen de la tabla de weboffice (F9). Las fechas por facultad ya no se usan (C3).

---

## Matriz de trazabilidad RF → historias

| RF | Historias |
|---|---|
| RF-01 Carga del archivo | US-02 |
| RF-02 Formato de plantilla | US-03, US-04, US-05 |
| RF-03 Validación académica | US-06 |
| RF-04 Generación de solicitud | US-07, US-08, US-11 |
| RF-05 Cuotas | US-07, US-08 |
| RF-06 Exenciones | US-07, US-08 |
| RF-07 Conceptos | US-07, US-08 |
| RF-08 Cancelación previa | US-09 |
| RF-09 Parámetros | US-15 (y como regla en US-06, US-07, US-08) |
| RF-10 Atomicidad | US-10 |
| RF-11 Resumen | US-12 |
| RF-12 Historial | US-02, US-13 |
| RF-13 Auditoría | US-14 |
| RF-14 Autenticación | US-01 |
| RF-15 Autorización | US-01 |
| RF-16 Contrato "Solicitados" | US-11 |

Todos los RF tienen al menos una historia. Los RNF (cabeceras, secretos, health check, cobertura, SonarQube) no son historias de usuario: se llevan a NFR Requirements y Code Generation.

## Bloqueos → historias

| Bloqueo | Historias bloqueadas | Responsable |
|---|---|---|
| D1 Plantilla de pregrado sin Reingreso y con las fechas de pago (C3) | US-03, US-07 | ARC |
| D2 Plantilla posgrado SMLV | US-05 (y la variante SMLV de US-08) | ARC |
| D3 ~~Valor de `cuota` en pregrado y demás estados~~ resuelta el 2026-11-25 (RE-21, A15) | — | — |
| D4 DDL real y modelo aprobado | US-11 (dependencia técnica en US-09, US-10) | DBA |
| D5 Origen de los festivos y si sábados y domingos cuentan (acotada) | US-08 | DBA / OATI |
| D6 Campo del valor de cada regla e ids por ambiente (acotada) | Ninguna (dependencia técnica en US-06, US-07, US-08, US-15) | Usuario / OATI |
| D10 Crear los parámetros de las reglas en "parametros" | Ninguna (dependencia técnica en US-15; sin ellos no se procesa ningún lote en test) | OATI / ARC |
| D7 SSM, logs, S3 | Ninguna (dependencia técnica en US-02, US-14) | Infraestructura / Seguridad |
| D13 Proxies de confianza para la IP | Ninguna (dependencia técnica en US-02, US-14) | Infraestructura / Arquitectura |

---

## Puntos por confirmar

| ID | Pregunta | Historia | Estado |
|---|---|---|---|
| P-1 | ¿Qué pasa con un lote de más de 1000 estudiantes? | US-02 | **Resuelto (F1, 2026-11-25):** se rechaza el lote completo y el mensaje indica el máximo |
| P-2 | ¿Qué pasa si un código aparece dos veces en el mismo lote? | US-06 | **Resuelto (F2, 2026-11-25):** solo se procesa la primera aparición; las siguientes no se suben (`CODIGO_REPETIDO`) y no cancelan nada. Hoy queda la última |
| P-3 | Votación y descuentos | US-07, US-08 | **Resuelto (usuario):** los descuentos no son acumulables; la votación es la única acumulable y se registra una sola vez. Abre P-12 y P-13 |
| P-4 | ¿Qué representa el concepto 19? | US-07 | **Resuelto (código):** se graba siempre en pregrado; se conserva. Su nombre se documenta con el contrato de "parametros" |
| P-5 | ¿Los porcentajes de posgrado deben sumar 100? | US-08 | **Resuelto (usuario):** sí. Un porcentaje vacío toma el valor por defecto de su posición, como hoy |
| P-6 | ¿Se valida el valor de la columna 2 (créditos o SMLV)? | US-08 | **Resuelto (F6, 2026-11-25):** obligatorio y mayor que 0; entero en créditos y hasta dos decimales en SMLV (`UNIDAD_INVALIDA`) |
| P-7 | ¿La cancelación aplica a todos los periodos o solo al vigente? | US-09 | **Cambiado (C8, 2026-11-25):** todos los periodos, como hoy, porque "Solicitados" deja generar en el periodo vigente las solicitudes viejas que no se cancelan (RE-26). Antes (2026-11-24): solo al vigente |
| P-8 | ¿El estado H se acepta con terminación de materias? | US-06 | **Resuelto (código):** H no está en la lista de permitidos y hoy se rechaza antes; se conserva |
| P-9 | ¿Se registran los lotes rechazados? ¿Dónde quedan los totales? | US-02, US-13 | **Resuelto (código):** el lote se registra al cargarse, antes de validar; `solicitudLote` no tiene columnas para totales |
| P-10 | ¿ARC necesita exportar la lista de rechazados? | US-12 | **Resuelto (F13, 2026-11-25):** no en el MVP |
| P-11 | ¿`recibos_service` actualiza reglas en "parametros"? | US-15 | **Resuelto (usuario):** solo consulta |
| P-12 | Si una fila trae dos o más descuentos marcados, ¿qué hace el sistema? | US-07, US-08 | **Reemplazado (C2, 2026-11-25):** la fila no se sube y el resumen da el motivo. Antes (2026-11-24): se registraba solo el de mayor porcentaje (A9, que ya no aplica) |
| P-13 | ¿El tope de la votación (descuento ≤ 90%) aplica también a la votación marcada y en las dos plantillas? | US-07, US-08 | **Cambiado (C1, C2, C6 y C7, 2026-11-25):** la votación marcada se registra con cualquier descuento en las dos plantillas; la automática solo con un descuento marcado; si el descuento y la votación pasan de 100%, se registra solo el descuento |
| P-14 | ¿El resumen del lote debe avisar cuando se descartó un descuento por no ser acumulable? | US-07, US-08, US-12 | **Ya no aplica (C2, 2026-11-25):** ningún descuento se descarta; la fila con más de uno no se sube y el resumen da el motivo |
| P-15 | ¿Los porcentajes de las exenciones y las fechas por facultad se leen de "parametros" o de las tablas MySQL actuales (`exencion`, `fechaPagoFacultad`)? | US-07, US-08, US-15 | **Resuelto (usuario):** todo de "parametros" (a). **Cambiado en parte (F11, 2026-11-25):** los porcentajes de las exenciones se leen de la tabla `exencion`, en solo lectura; las fechas por facultad ya no se usan (C3) |

---

## Registro de cambios tras la aprobación (2026-11-24)

| Cambio | Origen | Historias |
|---|---|---|
| Descuentos no acumulables; votación única acumulable, una sola vez | Decisión P-3 | US-07, US-08 |
| Porcentajes de posgrado deben sumar 100 | Decisión P-5 | US-08 |
| Cancelación solo en el periodo vigente | Decisión P-7 | US-09, US-10 |
| "parametros" solo en lectura | Decisión P-11 | US-15 |
| Fecha extraordinaria de posgrado: +8 días calendario y luego salta festivos (no 8 días hábiles) | Código: `guardarCuotas` | US-08 |
| Pregrado: las dos fechas salen de la tabla de la facultad; tipo 3 con terminación de materias | Código: `guardarCuota` | US-07 |
| Periodo vigente por proyecto curricular (evento 80) | Código: `periodoActual` | US-07, US-08, US-09 |
| Rechazos por proyecto curricular inactivo y por falta de valor de matrícula; orden de validaciones | Código: `verificarCodigo`, `carrerasTotales` | US-06 |
| Columnas que se escriben en `solicitud*` y `solicitudLote` | Código: `sql.class.php` | US-02, US-11, US-13 |
| Historial limitado a usuario, fecha, archivo e IP | Código (`insertarLote`) y alcance de IN-8 | US-13 |
| Estado de US-07: bloqueada por P-12/P-13 en lugar de D5 | Consecuencia de lo anterior | US-07 |
| Varios descuentos: se registra el de mayor porcentaje; en empate, el de la columna que aparece primero (A9) | Decisión P-12 | US-07, US-08 |
| Votación: se conserva la regla actual (en pregrado no se registra la marcada si hay descuento de las columnas 8 a 13; la automática solo con descuento ≤ 90%; en posgrado la marcada siempre) | Decisión P-13 | US-07, US-08 |
| Las fechas de terminación de materias dependen de que la columna 8 esté marcada, aunque se registre otro descuento | Código (`guardarCuota`) y P-12 | US-07 |
| Una columna está marcada si su celda tiene cualquier contenido | Código (`conceptoPlantilla`, `exencionPlantilla`) | US-07, US-08 |
| US-07 pasa a ✅ Lista; US-08 queda bloqueada solo por D5 y, en SMLV, por D2 | Consecuencia de P-12 y P-13 | US-07, US-08 |
| Consulta a "parametros" por id (`GET /v1/parametro/{id}`); US-15 pasa a ✅ Lista | Usuario (2026-11-24) | US-15 |
| La auditoría cubre las peticiones a `/v1/*`; los health checks no se auditan | Application Design (AD-11), aprobado 2026-11-24 | US-14 |
| Todas las reglas salen de "parametros", incluidos los porcentajes de exención y las fechas por facultad | Decisión P-15 (a) | US-07, US-08, US-15 |
| Escenario 5 nuevo en US-15: regla inexistente, inactiva o con valor inválido | Ejemplo de respuesta del usuario y AD-22, aprobado 2026-11-24 | US-15 |
| El token se valida en cada petición, sin caché de 60 minutos | Extensión de seguridad (SECURITY-08), Units Generation, pendiente de aprobación | US-01 |
| Un estudiante rechazado por cualquier motivo pierde sus solicitudes sin imprimir del periodo vigente; la cancelación va en su propia transacción y se mantiene si falla la solicitud nueva | Usuario, Reverse Engineering (RE-02), 2026-11-25 | US-06, US-09, US-10 |
| Posgrado: número de cuotas obligatorio, de 1 a 3; la fila que no cumple no se sube | Usuario (RE-03, RE-04), 2026-11-25 | US-08 |
| Proyecto sin periodo vigente: la fila no se sube y el mensaje pide reportarlo al área de sistemas | Usuario (RE-05), 2026-11-25 | US-06 |
| Facultad sin fechas de pago: la fila no se sube (escenario 11) | Usuario (RE-06), 2026-11-25 | US-07 |
| `unidad` = `0` en pregrado | Usuario (RE-07), 2026-11-25 | US-11 |
| La IP se toma de `X-Forwarded-For` con el último proxy de confianza | Usuario (RE-13), 2026-11-25 | US-02 |
| El resumen lista también los estudiantes que se subieron | Usuario, 2026-11-25 | US-12 |
| US-13 y US-14 se marcan como funcionalidades nuevas | Usuario, 2026-11-25 | US-13, US-14 |
| ARC corresponde al nivel 132; `admin_consultasCoordinador` es su módulo de notas (mal nombrado) y queda para la Fase 2 (C5) | Usuario y código (RE-19), 2026-11-25 | US-01, personas |
| Escenario 8 de US-06: más de un periodo vigente se trata como sin periodo (A13) | Código del módulo de notas (RE-18), 2026-11-25 | US-06 |
| Más de un descuento marcado: la fila no se sube (reemplaza P-12 y A9); la votación marcada se registra con cualquier descuento, también en pregrado con las columnas 8 a 13 | Usuario (C2), 2026-11-25 | US-07, US-08 |
| Sin exenciones marcadas no hay votación automática, como hoy; la automática conserva el tope de 90% (A14) | Usuario (C1), 2026-11-25 | US-07, US-08 |
| Las fechas de pregrado vienen de la plantilla; la columna de terminación de materias ya no cambia las fechas; US-07 queda bloqueada por D1 | Usuario (C3), 2026-11-25 | US-03, US-07 |
| P-14 ya no aplica | Consecuencia de C2 | US-12 |
| El módulo de notas de ARC queda para la Fase 2 | Usuario (C5), 2026-11-25 | — |
| US-07 vuelve a bloqueada (C1, C2, C3) y US-08 suma C1 y C2 | Respuesta del usuario a RE-01 y RE-06, con preguntas abiertas | US-07, US-08 |
| D3 resuelta con el código de "Solicitados": `cuota` = 1 en pregrado (A15); US-11 queda bloqueada solo por D4 | Código de `admin_solicitudCoordinador` (RE-21), 2026-11-25 | US-11 |
| La respuesta del usuario sobre A14 (votación automática siempre que el estudiante esté en ACCERELECTORAL) queda en revisión por C6 y C7; US-07 y US-08 suman C6 y C7 | Usuario y código de "Solicitados" (RE-23), 2026-11-25 | US-07, US-08 |
| US-09 queda bloqueada por C8 (cancelación de periodos anteriores) | Código de "Solicitados" (RE-26), 2026-11-25 | US-09 |
| P-6: con `unidad` vacía o en 0, el recibo de posgrado sale en 0 | Código de "Solicitados" (RE-22), 2026-11-25 | US-08 |
| C6 = b: la votación automática solo en filas con un descuento marcado (se mantiene C1). C7 = a: si el descuento y la votación pasan de 100%, se registra solo el descuento, en las dos plantillas. A14 queda resuelto; US-07 y US-08 vuelven a depender solo de D1, y de D5 y D2 | Usuario (C6, C7), 2026-11-25 | US-07, US-08 |
| C8 = a: se cancelan las solicitudes sin imprimir de todos los periodos, como hoy (revierte P-7); un rechazo por proyecto sin periodo vigente también cancela (A12); US-09 vuelve a lista | Usuario (C8), 2026-11-25 | US-06, US-09, US-10 |
| F1: lote de más de 1000 filas rechazado completo (escenario 4 de US-02) | Usuario (U1 Functional Design), 2026-11-25 | US-02 |
| F2, F3 y F5: código repetido (solo la primera aparición), fila sin código y nivel del estudiante (escenarios 2, 9 y 10 de US-06) | Usuario (U1 Functional Design), 2026-11-25 | US-06 |
| F4, F7 y F8: celdas con solo espacios, fechas vencidas o en desorden, y fecha ordinaria de pregrado con la extraordinaria calculada | Usuario (U1 Functional Design), 2026-11-25 | US-07, US-08 |
| F6, F9, F10, F11 y F12: créditos o SMLV, festivos de la tabla de weboffice sin fines de semana, porcentajes de la tabla `exencion` y Secretaría de Educación fuera de C2; US-08 queda bloqueada por F14 y F15 en lugar de D5 | Usuario (U1 Functional Design), 2026-11-25 | US-08, US-15 |
| F13: sin exportación en el MVP | Usuario (U1 Functional Design), 2026-11-25 | US-12 |
| F14 = a y F15 = a: la Secretaría no entra en la suma de C7 y, sola, también permite la votación automática; US-08 queda bloqueada solo en la variante SMLV (D2) | Usuario (U1 Functional Design), 2026-11-25 | US-08 |
| N3: un lote que llega al límite propio de 90 s responde con el reporte; las filas que faltan salen con `TIEMPO_AGOTADO` (escenario 4 de US-12) | Usuario (U1 NFR Requirements), 2026-11-25 | US-12 |
| N7: archivo de 2 MB como máximo (escenario 1 de US-02) | Usuario (U1 NFR Requirements), 2026-11-25 | US-02 |
| N14: sin trazas de X-Ray en el MVP; `trace_id` lleva el identificador de la petición (escenario 1 de US-14) | Usuario (U1 NFR Requirements), 2026-11-25 | US-14 |
| N20: si MySQL falla por la conexión en 5 estudiantes seguidos, el lote deja de intentar y los que faltan salen con "Error al guardar la solicitud" (escenario 5 de US-10) | Usuario (U1 NFR Design), 2026-11-25 | US-10 |
| Tiempos de espera y reintento de "parametros" (escenario 3 de US-15) | U1 NFR Design, 2026-11-25 | US-15 |
