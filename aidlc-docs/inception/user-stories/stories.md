# Historias de usuario — Migración del módulo de recibos por lote

- Etapa: INCEPTION → User Stories (Parte 2)
- Fuente: `aidlc-docs/inception/requirements/requirements.md` (aprobado 2026-11-24)
- Persona principal: Profesional de ARC (`personas.md`)
- Decisiones de planificación: Q1-a (por capacidad), Q2-a (solo IN), **Q3-b (borradores bloqueados)**, Q4-a, Q5-a (Dado/Cuando/Entonces), Q6-a (español, Must)
- Estado: **aprobadas 2026-11-24**. Actualizadas el mismo día con las decisiones P-3, P-5, P-7 y P-11 y con lo que muestra el código PHP actual (ver §Registro de cambios)

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
| US-03 | Validar el formato de la plantilla de pregrado (13 columnas) | E2 Carga | RF-02 | 🔒 Bloqueada (D1) |
| US-04 | Validar el formato de la plantilla de posgrado por créditos | E2 Carga | RF-02 | ✅ Lista |
| US-05 | Validar el formato de la plantilla de posgrado SMLV | E2 Carga | RF-02 | 🔒 Bloqueada (D2) |
| US-06 | Validar cada estudiante contra Oracle académico | E3 Procesamiento | RF-03 | ✅ Lista |
| US-07 | Generar solicitudes de pregrado | E3 Procesamiento | RF-04, RF-05, RF-06, RF-07 | ✅ Lista |
| US-08 | Generar solicitudes de posgrado | E3 Procesamiento | RF-04, RF-05, RF-06, RF-07 | 🔒 Bloqueada (D5; variante SMLV: D2) |
| US-09 | Cancelar solicitudes anteriores sin imprimir | E3 Procesamiento | RF-08 | ✅ Lista |
| US-10 | Guardar cada solicitud completa o no guardarla | E3 Procesamiento | RF-10 | ✅ Lista |
| US-11 | Entregar las solicitudes a "Solicitados" | E3 Procesamiento | RF-16, RF-04 | 🔒 Bloqueada (D3 acotada, D4) |
| US-12 | Ver el resumen del lote procesado | E4 Resultados | RF-11 | ✅ Lista |
| US-13 | Consultar el historial de lotes | E4 Resultados | RF-12 | ✅ Lista |
| US-14 | Registrar la auditoría de cada petición | E4 Resultados | RF-13 | ✅ Lista |
| US-15 | Obtener las reglas desde el servicio "parametros" | E5 Reglas | RF-09 | ✅ Lista |

Total: 15 historias. 11 listas, 4 bloqueadas.

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

- Reglas: el token y los datos personales no se guardan en `localStorage` ni en cookies sin protección. El backend valida el token en cada petición, sin caché (SECURITY-08).
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
  Y su tamaño no supera el máximo configurado (por defecto 10 MB)
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
```

- Reglas: el archivo no queda en el disco local del contenedor. El nombre original no se usa como nombre de almacenamiento. El lote se registra al cargarse, antes de validar el formato, como hoy; los archivos rechazados por tipo o tamaño no se guardan ni se registran (la petición queda en la auditoría, US-14).
- Dependencias técnicas: tamaño máximo y retención en S3 (A1, D7); documento del usuario desde WSO2 (A8).
- Puntos por confirmar: `[P-1]` lotes con más de 1000 estudiantes.

### US-03 — Validar el formato de la plantilla de pregrado (13 columnas)
- **Estado:** 🔒 Borrador — bloqueada (**D1**: plantilla oficial de pregrado de 13 columnas, OQ-B-3)
- **Prioridad:** Must · **Trazabilidad:** RF-02 CA1, CA4 · IN-1 · C-3
- **Historia:** Como profesional de ARC, quiero que el sistema reconozca la plantilla de pregrado y rechace cualquier formato distinto, para no generar solicitudes a partir de datos mal ubicados.

```text
Escenario 1: Plantilla de pregrado vigente
  Dado un archivo cuya celda A1 dice "PLANTILLA GENERAL PREGRADOS" [PENDIENTE D1: confirmar texto]
  Y tiene exactamente 13 columnas con los encabezados oficiales [PENDIENTE D1: encabezados finales]
  Cuando el sistema valida el formato
  Entonces lo identifica como tipo 1 (pregrado)
  Y lee los datos desde la fila 4 [PENDIENTE D1: confirmar fila inicial]

Escenario 2: Plantilla anterior de 14 columnas (con "Reingreso")
  Dado un archivo de pregrado con 14 columnas
  Cuando el sistema valida el formato
  Entonces rechaza el lote con un motivo que indica que se debe usar la plantilla vigente de 13 columnas

Escenario 3: Columnas o encabezados que no coinciden
  Dado un archivo de pregrado con otro número de columnas o con encabezados en otro orden
  Cuando el sistema valida el formato
  Entonces rechaza el lote completo con el motivo
  Y no procesa ninguna fila
```

- Columnas esperadas (supuesto hasta D1, según `templates-analysis.md` sin la columna 14): 1 Código del estudiante · 2 Seguro Estudiantil · 3 Carnet Estudiantil · 4 Sistematización · 5 10% votación · 6 2do Hermano · 7 3er Hermano · 8 Terminación de Materias · 9 Beneficiario · 10 Matrícula de Honor · 11 Deportista de alto rendimiento · 12 Estudiante Distinguido / Cultural-Científico · 13 Mérito Académico.
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
  Dado una fila cuyo código de estudiante no es numérico
  Cuando el sistema procesa la fila
  Entonces rechaza ese estudiante con el motivo "Código inválido"
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
```

- Reglas: Oracle se consulta solo en lectura, con parámetros enlazados. ARC procesa estudiantes de cualquier proyecto curricular activo (comportamiento actual del nivel 132). Las validaciones se aplican en el orden de los escenarios 3 a 7, como hoy, y el motivo es el de la primera que falla. Como H no está en la lista de estados permitidos, un estudiante en H se rechaza en el escenario 5 (comportamiento actual, P-8 resuelto). La lista de estados y el número de evento vienen de los parámetros (US-15), no del código.
- Dependencias técnicas: valores de los parámetros (D6).
- Puntos por confirmar: `[P-2]` estudiante repetido en el mismo lote.

### US-07 — Generar solicitudes de pregrado
- **Estado:** ✅ Lista (desbloqueada 2026-11-24 con P-12 y P-13; el código actual ya mostró el origen del periodo y de las fechas de la facultad)
- **Prioridad:** Must · **Trazabilidad:** RF-04, RF-05 CA1, RF-06, RF-07 · IN-3
- **Historia:** Como profesional de ARC, quiero que cada estudiante de pregrado válido reciba una solicitud con una sola cuota, sus exenciones y sus conceptos, para que su recibo salga con el valor y las fechas correctas.

```text
Escenario 1: Cuota única
  Dado un estudiante de pregrado válido
  Cuando el sistema genera su solicitud
  Entonces crea exactamente una cuota al 100%
  Y toma la fecha ordinaria y la extraordinaria de las fechas de pago de la facultad de su proyecto curricular (tipo normal)
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

Escenario 5: Varios descuentos (no acumulables)
  Dado una fila con dos o más descuentos marcados en las columnas 6 a 13
  Cuando el sistema genera la solicitud
  Entonces registra solo el descuento de mayor porcentaje
  Y si dos tienen el mismo porcentaje, registra el de la columna que aparece primero

Escenario 6: Votación marcada
  Dado una fila con la columna "10% votación" marcada
  Y ningún descuento marcado en las columnas 8 a 13
  Cuando el sistema genera la solicitud
  Entonces registra la exención de votación una sola vez, además del descuento si lo hay

Escenario 7: Votación marcada con un descuento de las columnas 8 a 13
  Dado una fila con la columna "10% votación" marcada
  Y algún descuento marcado en las columnas 8 a 13
  Cuando el sistema genera la solicitud
  Entonces no registra la votación marcada
  Y la votación solo puede registrarse por la regla automática (escenario 8)

Escenario 8: Votación automática
  Dado un estudiante sin votación registrada por los escenarios 6 o 7
  Y con certificado electoral activo en ACCERELECTORAL
  Y sin descuento, o con un descuento registrado menor o igual a 90%
  Cuando el sistema genera la solicitud
  Entonces registra la exención de votación una sola vez

Escenario 9: Conceptos
  Dado un estudiante de pregrado válido
  Cuando el sistema genera la solicitud
  Entonces registra el concepto de matrícula y el concepto exclusivo de pregrado (hoy 1 y 19)
  Y registra seguro, carnet y sistematización (hoy 2, 3 y 4) según las columnas 2 a 4

Escenario 10: Terminación de materias
  Dado una fila con la columna "Terminación de Materias" marcada (columna 8)
  Cuando el sistema genera la solicitud
  Entonces toma las fechas de pago de la facultad del tipo "terminación de materias" (hoy tipo 3) en lugar de las normales
  Y las usa aunque se registre otro descuento de mayor porcentaje (escenario 5)
  Y registra la exención de terminación de materias (hoy id 4) solo si es el descuento que queda registrado
```

- Reglas: una columna está marcada si su celda tiene cualquier contenido, como hoy. Los IDs, porcentajes, fechas de la facultad y el mapa columna → exención vienen de los parámetros (US-15). Salvo los cambios acordados, la solicitud coincide con la del sistema actual.
- Cambios acordados: sin diferido ni cuotas al 0%; "Seguro" no es cuota; sin "Reingreso"; descuentos no acumulables, se registra el de mayor porcentaje (P-3, P-12; hoy se registran todos los marcados). La regla de la votación no cambia (P-13).
- Dependencias técnicas: las fechas de la facultad y el porcentaje de cada exención se leen de "parametros" (P-15 a; formato D6, creación D10).
- Supuesto: A9 (empate entre descuentos).
- Puntos por confirmar: `[P-14]` avisar en el resumen cuando se descarta un descuento.

### US-08 — Generar solicitudes de posgrado
- **Estado:** 🔒 Borrador — bloqueada (**D5**: origen de los festivos y si sábados y domingos cuentan; la variante SMLV depende además de **D2**). P-12 y P-13 ya están resueltas.
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
  Y si ese día es festivo, avanza un día a la vez hasta el primero que no lo sea [PENDIENTE D5: origen de los festivos y si sábados y domingos cuentan]

Escenario 6: Número de cuotas inválido
  Dado una fila con cuotas fuera de 1 a 3
  Cuando el sistema procesa la fila
  Entonces rechaza ese estudiante con el motivo "Número de cuotas inválido"

Escenario 7: Fecha o porcentaje inválido
  Dado una fila en la que alguna de sus N cuotas no tiene fecha, tiene una fecha inexistente o sin año completo, o tiene un porcentaje fuera de 0 a 100
  Cuando el sistema procesa la fila
  Entonces rechaza ese estudiante indicando la cuota y la columna con error

Escenario 8: Descuentos
  Dado una fila de posgrado con uno o más descuentos marcados en las columnas 8 a 17
  Cuando el sistema genera la solicitud
  Entonces registra solo el descuento de mayor porcentaje según el mapa columna → exención de posgrado
  Y si dos tienen el mismo porcentaje, registra el de la columna que aparece primero

Escenario 9: Votación marcada en posgrado
  Dado una fila de posgrado con la columna "10% votación" (columna 7) marcada
  Cuando el sistema genera la solicitud
  Entonces registra la votación una sola vez, aunque el descuento sea del 100%, como hoy

Escenario 10: Votación automática en posgrado
  Dado un estudiante de posgrado sin la columna 7 marcada
  Y con certificado electoral activo en ACCERELECTORAL
  Y sin descuento, o con un descuento registrado menor o igual a 90%
  Cuando el sistema genera la solicitud
  Entonces registra la votación una sola vez

Escenario 11: Conceptos
  Dado un estudiante de posgrado válido
  Cuando el sistema genera la solicitud
  Entonces registra el concepto de matrícula y los de seguro, carnet y sistematización según las columnas 4 a 6
  Y no registra el concepto exclusivo de pregrado
```

- Reglas: los porcentajes por defecto, el plazo de 8 días y el mapa de exenciones vienen de los parámetros (US-15).
- Cambios acordados: los porcentajes deben sumar 100 (P-5; hoy no se valida); descuentos no acumulables, se registra el de mayor porcentaje (P-3, P-12); validación estricta de fechas (Entorno técnico; hoy solo se revisa día ≤ 31 y mes ≤ 12). La regla de la votación no cambia (P-13), por eso en posgrado el total puede pasar de 100%, como hoy.
- Supuesto: A9 (empate entre descuentos).
- Para desbloquear: origen de los festivos y si sábados y domingos cuentan (D5, DBA/OATI); plantilla SMLV para esa variante (D2).
- Puntos por confirmar: `[P-6]`.

### US-09 — Cancelar solicitudes anteriores sin imprimir
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-08 · IN-4
- **Historia:** Como profesional de ARC, quiero que al generar una nueva solicitud se cancelen las anteriores del mismo estudiante que no se imprimieron en el periodo vigente, para que solo quede vigente la más reciente.

```text
Escenario 1: Solicitud anterior sin imprimir del periodo vigente
  Dado un estudiante con una solicitud anterior en estado 0 (sin imprimir) del periodo vigente
  Cuando el sistema genera su nueva solicitud
  Entonces la anterior pasa a estado 2 (cancelada)
  Y la cancelación y la nueva solicitud se guardan en la misma transacción (US-10)

Escenario 2: Solicitud anterior ya impresa
  Dado un estudiante con una solicitud anterior en un estado distinto de 0
  Cuando el sistema genera su nueva solicitud
  Entonces no modifica esa solicitud

Escenario 3: Estudiante rechazado
  Dado un estudiante rechazado en la validación (US-06) o en la generación
  Cuando el sistema procesa la fila
  Entonces no cancela ninguna de sus solicitudes anteriores

Escenario 4: Solicitud sin imprimir de otro periodo
  Dado un estudiante con una solicitud en estado 0 de un periodo anterior
  Cuando el sistema genera su nueva solicitud
  Entonces no modifica esa solicitud
```

- Reglas: el periodo vigente es el año y periodo del proyecto curricular del estudiante, los mismos de la nueva solicitud (evento 80). Las pruebas en paralelo con el sistema PHP se hacen sobre una base de datos de pruebas dedicada (OQ-B-5), así que esta regla nunca cancela solicitudes de producción.
- Cambio acordado (P-7): hoy el PHP cancela las solicitudes sin imprimir del estudiante en todos los periodos.
- Dependencias técnicas: DDL real de `solicitudRecibo` (D4).

### US-10 — Guardar cada solicitud completa o no guardarla
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-10 · IN-6
- **Historia:** Como profesional de ARC, quiero que cada solicitud quede guardada completa o no quede, para no tener solicitudes sin cuotas o sin conceptos que "Solicitados" no pueda imprimir.

```text
Escenario 1: Guardado exitoso
  Dado un estudiante válido con su solicitud calculada
  Cuando el sistema la guarda
  Entonces en una sola transacción cancela las anteriores sin imprimir del periodo vigente (US-09)
  Y escribe solicitudRecibo, solicitudCuota, solicitudExencion y solicitudConcepto

Escenario 2: Falla a mitad del guardado
  Dado que falla la escritura de cualquiera de esas tablas para un estudiante
  Cuando el sistema detecta el error
  Entonces revierte la transacción completa de ese estudiante, incluida la cancelación
  Y lo marca como rechazado con el motivo "Error al guardar la solicitud"
  Y continúa con el siguiente estudiante

Escenario 3: Verificación posterior
  Dado un lote procesado
  Cuando se consultan las solicitudes del lote
  Entonces no existe ninguna solicitud sin cuotas o sin conceptos
```

- Reglas: el detalle técnico del error queda en el log; el motivo mostrado al usuario no expone SQL ni datos internos.
- Dependencias técnicas: DDL real (D4).

### US-11 — Entregar las solicitudes a "Solicitados"
- **Estado:** 🔒 Borrador — bloqueada (**D3** acotada: valor de `cuota` en pregrado y demás estados, OQ-B-4; **D4**: DDL real y modelo aprobado, OQ-T-9)
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
  Y en pregrado el campo cuota de solicitudRecibo vale [PENDIENTE D3] (hoy depende, por el defecto, de la columna "Seguro Estudiantil": 0, 1 o 2)

Escenario 3: Estructura sin cambios
  Dado las tablas solicitud*, exencion y fechaPagoFacultad
  Cuando el sistema nuevo entra en funcionamiento
  Entonces su estructura es la misma que antes [PENDIENTE D4: DDL de referencia]
```

- Reglas: `id_usuario` = documento de identidad del usuario (claim `documento` de WSO2, A8); `unidad` = créditos o SMLV en posgrado y vacía en pregrado, como hoy; `fecha` = momento de creación; `tipoPlantilla` = 1, 2 o 3.
- Para desbloquear: valor de `cuota` en pregrado y demás estados (D3: DBA, dueño o código de "Solicitados"); DDL real (D4: DBA).

---

## E4 — Resultados y trazabilidad

### US-12 — Ver el resumen del lote procesado
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-11 · IN-7
- **Historia:** Como profesional de ARC, quiero ver al terminar la carga cuántos estudiantes se procesaron y cuáles se rechazaron con su motivo, para corregir los rechazados y volver a cargarlos.

```text
Escenario 1: Lote con procesados y rechazados
  Dado que cargué un lote de N estudiantes
  Cuando termina el procesamiento (en la misma petición)
  Entonces veo el total de procesados y de rechazados
  Y para cada rechazado veo su código, la fila y el motivo

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
```

- Reglas: la pantalla muestra solo los datos necesarios para corregir (código, fila, motivo) y usa el escape por defecto de Angular. El resumen no se guarda: solo se ve al terminar la carga (ver US-13).
- Puntos por confirmar: `[P-10]` exportar los rechazados.

### US-13 — Consultar el historial de lotes
- **Estado:** ✅ Lista · **Prioridad:** Must · **Trazabilidad:** RF-12 · IN-8
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
- **Historia:** Como integrante de Seguridad, quiero un log de auditoría de cada petición al backend, para rastrear quién hizo qué y desde dónde sin exponer datos personales.

```text
Escenario 1: Petición registrada
  Dado cualquier petición a /v1/* de recibos_service, exitosa o fallida (los health checks no se auditan, AD-11)
  Cuando termina
  Entonces se escribe un log JSON con app_name, agent, data, date, host, ip_user, method, path, query, schema, sql_statement, status, trace_id y user

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
  Y el usuario ve un motivo claro (el tiempo de espera y los reintentos se fijan en NFR Design)

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
- Dependencias técnicas: campo y formato del valor de cada regla, id de cada regla por ambiente, URL y autenticación (D6, acotada); creación de los parámetros en el servicio (D10). Todas las reglas, incluidos los porcentajes de exención y las fechas por facultad, salen de "parametros" (P-15 a).

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
| D1 Plantilla pregrado 13 columnas | US-03 | ARC |
| D2 Plantilla posgrado SMLV | US-05 (y la variante SMLV de US-08) | ARC |
| D3 Valor de `cuota` en pregrado y demás estados (acotada) | US-11 | DBA / dueño de "Solicitados" |
| D4 DDL real y modelo aprobado | US-11 (dependencia técnica en US-09, US-10) | DBA |
| D5 Origen de los festivos y si sábados y domingos cuentan (acotada) | US-08 | DBA / OATI |
| D6 Campo del valor de cada regla e ids por ambiente (acotada) | Ninguna (dependencia técnica en US-06, US-07, US-08, US-15) | Usuario / OATI |
| D10 Crear los parámetros de las reglas en "parametros" | Ninguna (dependencia técnica en US-15; sin ellos no se procesa ningún lote en test) | OATI / ARC |
| D7 SSM, logs, S3 | Ninguna (dependencia técnica en US-02, US-14) | Infraestructura / Seguridad |

---

## Puntos por confirmar

| ID | Pregunta | Historia | Estado |
|---|---|---|---|
| P-1 | ¿Qué pasa con un lote de más de 1000 estudiantes? | US-02 | Pendiente (U1 Functional Design). Propuesta: rechazar el lote completo e indicar el máximo |
| P-2 | ¿Qué pasa si un código aparece dos veces en el mismo lote? | US-06 | Pendiente (U1 Functional Design). Hoy la segunda fila cancela la solicitud que creó la primera |
| P-3 | Votación y descuentos | US-07, US-08 | **Resuelto (usuario):** los descuentos no son acumulables; la votación es la única acumulable y se registra una sola vez. Abre P-12 y P-13 |
| P-4 | ¿Qué representa el concepto 19? | US-07 | **Resuelto (código):** se graba siempre en pregrado; se conserva. Su nombre se documenta con el contrato de "parametros" |
| P-5 | ¿Los porcentajes de posgrado deben sumar 100? | US-08 | **Resuelto (usuario):** sí. Un porcentaje vacío toma el valor por defecto de su posición, como hoy |
| P-6 | ¿Se valida el valor de la columna 2 (créditos o SMLV)? | US-08 | Pendiente (U1 Functional Design). Hoy no se valida. Propuesta: numérico mayor que 0 |
| P-7 | ¿La cancelación aplica a todos los periodos o solo al vigente? | US-09 | **Resuelto (usuario):** solo al vigente. Cambio frente al sistema actual |
| P-8 | ¿El estado H se acepta con terminación de materias? | US-06 | **Resuelto (código):** H no está en la lista de permitidos y hoy se rechaza antes; se conserva |
| P-9 | ¿Se registran los lotes rechazados? ¿Dónde quedan los totales? | US-02, US-13 | **Resuelto (código):** el lote se registra al cargarse, antes de validar; `solicitudLote` no tiene columnas para totales |
| P-10 | ¿ARC necesita exportar la lista de rechazados? | US-12 | Pendiente (U1 Functional Design). Propuesta: no en el MVP (no está en la lista IN) |
| P-11 | ¿`recibos_service` actualiza reglas en "parametros"? | US-15 | **Resuelto (usuario):** solo consulta |
| P-12 | Si una fila trae dos o más descuentos marcados, ¿qué hace el sistema? | US-07, US-08 | **Resuelto (usuario):** se registra solo el de mayor porcentaje; en empate, el de la columna que aparece primero (A9) |
| P-13 | ¿El tope de la votación (descuento ≤ 90%) aplica también a la votación marcada y en las dos plantillas? | US-07, US-08 | **Resuelto (usuario):** se conserva la regla actual, incluida la diferencia entre pregrado y posgrado |
| P-14 | ¿El resumen del lote debe avisar cuando se descartó un descuento por no ser acumulable? | US-07, US-08, US-12 | Pendiente (U1 Functional Design). Propuesta: no en el MVP (IN-7 pide procesados y rechazados con motivo) |
| P-15 | ¿Los porcentajes de las exenciones y las fechas por facultad se leen de "parametros" o de las tablas MySQL actuales (`exencion`, `fechaPagoFacultad`)? | US-07, US-08, US-15 | **Resuelto (usuario):** todo de "parametros" (a). Si un porcentaje cambia, se cambia también en la tabla `exencion` que usa "Solicitados" |

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
