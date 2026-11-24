# Entrevista de Negocio — Historial de respuestas

Registro de solo anexado: aquí se agrega cada pregunta con su respuesta confirmada. Nunca se reescribe ni se borra.

---

## Sección 1 — Resumen ejecutivo · Q1–Q3
**Registrado**: 2026-11-23T20:55:00Z

### Q1: ¿Cuál es el nombre del proyecto y de qué tipo es?
[Answer]: d — Migración / modernización. Nombre de trabajo: "Migración del módulo de recibos por lote (weboffice)" (sugerido; el usuario no dio otro nombre, por confirmar).

### Q2: ¿Quién es el usuario principal, en una sola frase?
[Answer]: oficina de admisiones registro y control

### Q3: ¿Cuál es la capacidad principal del producto, en una frase?
[Answer]: "Cargar una plantilla con códigos de estudiantes y generar automáticamente las solicitudes de recibo de pago con sus cuotas, exenciones y conceptos, validando el estado y la carrera de cada estudiante."

---

## Sección 1 — Resumen ejecutivo · Q4
**Registrado**: 2026-11-23T21:00:00Z

### Q4: ¿Qué problema de negocio resuelve?
[Answer]: x — obsolescencia

### Q5 (pendiente de validación)
Respuesta recibida: "Retirar PHP 5 del servidor antes de una fecha concreta y migrarlo a un nuevo stack tecnologico"
Estado: falta la fecha concreta (número). Se pidió aclaración.

---

## Sección 1 — Resumen ejecutivo · Q5 (validada)
**Registrado**: 2026-11-23T21:05:00Z

### Q5: ¿Cuál es el resultado medible más importante?
[Answer]: Retirar PHP 5 del servidor antes de una fecha concreta y migrarlo a un nuevo stack tecnologico. Hito (opción b): prueba de concepto 2027-1.
Interpretación registrada: una prueba de concepto del módulo de recibos por lote en el nuevo stack, lista para el periodo académico 2027-1.
Nota: queda por confirmar si en 2027-1 la PoC convive con el sistema PHP o ya lo reemplaza, y para cuándo es el retiro definitivo de PHP 5 (candidata a pregunta abierta).

---

## ✅ Sección 1 completa — aprobada
**Registrado**: 2026-11-23T21:08:00Z
Aprobación del usuario: "aprobar"
Pregunta abierta pendiente (para Q18): ¿en 2027-1 la PoC convive con el sistema PHP o lo reemplaza? ¿Cuál es la fecha de retiro definitivo de PHP 5?

---

## Sección 2 — Contexto de negocio · Q6–Q8
**Registrado**: 2026-11-23T21:15:00Z

### Q6: Describe el problema en 1–2 párrafos, de forma concreta.
[Answer]: "El módulo de carga masiva de solicitudes de recibo funciona sobre PHP 5 y un framework propio de 2005–2009 que ya no tiene soporte. El código no corre en versiones actuales de PHP, solo lee Excel .xls, no tiene pruebas y su núcleo no está versionado. Las reglas de cuotas, exenciones y conceptos están escritas directamente en el código y se cambian comentando líneas. Por eso cada periodo depende de las pocas personas que conocen el código. Además, tiene riesgos de seguridad: el SQL se arma concatenando texto y el navegador puede alterar los permisos. También puede dejar solicitudes incompletas si la carga falla a mitad de camino. la idea es migrarlo a un nuevo stack donde el frontend angular y el backend es en python"
Nota cruzada: "frontend Angular, backend Python" es una restricción técnica → se lleva al rol Técnico (T5/T8) para confirmar versiones.

### Q7: ¿Por qué se hace ahora?
[Answer]: x — vulnerabilidades, facilidad de integracion y mantenibilidad. (Sin fecha fija declarada.)

### Q8: Tipos de usuario y necesidad principal
[Answer]: aceptamos la sugerencia pero los roles de coordinador de proyecto curricular y asistente actualmente los hace Admisiones, Registro y Control

| Rol | Descripción | Necesidad principal |
|---|---|---|
| Admisiones, Registro y Control (nivel 132) | Gestiona los recibos de todas las carreras. Hoy también realiza las tareas que el sistema asigna a coordinadores (4) y asistentes (110) | Generar solicitudes masivas de recibo para cualquier proyecto curricular |
| Coordinador de proyecto curricular (nivel 4) | Rol existente en el sistema; en la práctica lo ejerce Admisiones, Registro y Control | Cargar solicitudes solo para los estudiantes de sus carreras |
| Asistente (nivel 110) | Rol existente en el sistema; en la práctica lo ejerce Admisiones, Registro y Control | Cargar solicitudes de los proyectos asignados |
| Secretario (nivel 114) | Apoyo administrativo de los proyectos (pendiente confirmar si sigue en uso) | Cargar solicitudes de los proyectos asignados |
| Estudiante (usuario indirecto) | Recibe el recibo de pago | Un recibo con el valor, las cuotas, las exenciones y las fechas correctas |

Por confirmar: si el sistema nuevo conserva los roles 4/110/114 o los unifica en Admisiones, Registro y Control.

---

## Sección 2 — Contexto de negocio · Q8 (aclaración), Q9–Q10
**Registrado**: 2026-11-23T21:22:00Z

### Q8 (aclaración): ¿El sistema nuevo conserva los roles de coordinador, asistente y secretario?
[Answer]: a — No. Se unifican en un solo rol: Admisiones, Registro y Control.
Tabla Q8 resultante para el sistema nuevo:

| Rol | Descripción | Necesidad principal |
|---|---|---|
| Admisiones, Registro y Control | Único rol operativo; gestiona los recibos de todas las carreras (absorbe coordinador 4, asistente 110 y secretario 114) | Generar solicitudes masivas de recibo para cualquier proyecto curricular |
| Estudiante (usuario indirecto) | Recibe el recibo de pago | Un recibo con el valor, las cuotas, las exenciones y las fechas correctas |

### Q9: ¿Qué restricciones fijas aplican?
[Answer]: b + c + d
- b) Fecha de entrega: prueba de concepto para el periodo 2027-1.
- c) Requisitos normativos o de auditoría (detalle no especificado; ejemplos mencionados: Ley 1581 de 2012, auditoría de recaudo).
- d) Políticas institucionales que limitan opciones (detalle no especificado; ejemplos mencionados: lineamientos OATI, licenciamiento, alojamiento propio).
Nota: el detalle de c y d queda como pregunta abierta.

### Q10: ¿Qué métricas confirmarán el éxito?
[Answer]: aceptamos todo a exepción de que los Cambio de reglas en cada periodo todo es parametrico o ingresa por la plantilla

| Métrica | Estado actual | Estado objetivo | Cómo se mide |
|---|---|---|---|
| PHP 5 en el servidor del módulo | PHP 5 | Ningún componente en PHP 5 | Inventario del servidor |
| Las solicitudes coinciden con las del sistema actual | — | 100% iguales en cuotas, exenciones y conceptos en los lotes de prueba | Comparar los resultados de ambos sistemas con las mismas plantillas |
| Solicitudes incompletas por fallos en la carga | Pueden ocurrir (sin transacciones) | 0 | Consulta de solicitudes sin cuotas o sin conceptos |
| Vulnerabilidades críticas o altas | Inyección SQL, XSS, permisos manipulables | 0 | Escaneo de seguridad |
| Cambio de reglas en cada periodo | Se edita y se comenta código | 100% de las reglas son paramétricas o ingresan por la plantilla; 0 cambios de código por periodo | Registro de cambios por periodo |

---

## Sección 2 — Cambio solicitado · Q9 (reemplaza el detalle anterior de Q9)
**Registrado**: 2026-11-23T21:30:00Z

### Q9: ¿Qué restricciones fijas aplican?
Respuesta del usuario (verbatim): "q9 - fecha limite 15 de dic

- política de protección de datos ley 1581 del 2012 y reglas de minimos privilegios, logs siempre habilitados, gestión de sesiones seguras, control de dependencias, cabeceras

- lineamientos para aplicativos: https://github.com/udistrital/lineamientos_oas, q10 aprobado"

[Answer]: b + c + d
- b) Fecha límite: 15 de diciembre (año por confirmar; relación con la PoC 2027-1 por confirmar).
- c) Normativa y seguridad: política de protección de datos personales (Ley 1581 de 2012); mínimo privilegio; logs siempre habilitados; gestión segura de sesiones; control de dependencias; cabeceras de seguridad HTTP.
- d) Políticas institucionales: lineamientos para aplicativos de la Universidad Distrital — https://github.com/udistrital/lineamientos_oas (no leído aún; se debe revisar en el rol Técnico).

### Q10
[Answer]: aprobado (sin cambios respecto al registro anterior).

---

## Sección 2 — Cambio solicitado · Q9 (año de la fecha límite)
**Registrado**: 2026-11-23T21:45:00Z

### Q9 — fecha límite
Respuesta del usuario (verbatim): "la fecha es 15 de diciembre de 2026"
[Answer]: b) Fecha límite: **15 de diciembre de 2026** (≈22 días desde 2026-11-23). Se asocia al hito de Q5: PoC para el periodo 2027-1.
Nota: según los lineamientos OAS (`interview/technical/institutional-guidelines-analysis.md` §10), el paso a producción exige comité de modelo, DBA, WSO2, pruebas y revisión de Seguridad; queda por confirmar en qué ambiente se considera cumplida la PoC.

---

## Sección 2 — Cambio solicitado · Q9 (alcance de la fecha límite)
**Registrado**: 2026-11-23T21:55:00Z

Respuesta del usuario (verbatim): "La aprobación del modelo de datos por el comité. ya existe la base por los DBA. ya existe 

El registro en WSO2. ya existe

Pruebas de carga y de usuario. se realizaran una vez este en entorno de desarrollo

La revisión de Seguridad. se realizara una vez este en entorno de pruebas

por lo que al 15 de diciembre debe quedar lo mencionado hasta la fase de pruebas para iniciar las revisiones de seguridad"

[Answer]: Q9 b) Fecha límite 15/12/2026 = solución desplegada en **ambiente de pruebas (test)**, lista para iniciar la revisión de Seguridad (opción b).
Precondiciones ya resueltas según el usuario:
- Modelo de datos aprobado por el comité: ya existe.
- Base de datos creada por DBA: ya existe.
- Registro en WSO2: ya existe.
Secuencia acordada:
1. Desarrollo (dev): pruebas de carga y de usuario.
2. Pruebas (test) al 15/12/2026: inicio de la revisión de Seguridad.
3. Producción: después de la revisión de Seguridad (fecha no definida; se relaciona con la PoC 2027-1 de Q5).
Pendiente para el rol Técnico: ubicación del modelo de datos aprobado, motor y nombre de la base, y datos del registro WSO2 (sin secretos).

---

## ✅ Sección 2 completa — aprobada
**Registrado**: 2026-11-23T22:00:00Z
Aprobación del usuario: "aprobar"

---

## Sección 3 — Visión completa · Q11–Q13
**Registrado**: 2026-11-23T22:05:00Z
Respuesta del usuario (verbatim): "q11 aprobada la sugerencia, q12 aprobamos la sugerencia, q13 b"

### Q11: ¿Cómo se ve el producto cuando esté completo?
[Answer]: "Admisiones, Registro y Control genera las solicitudes de recibo de pago de cualquier proyecto curricular desde una aplicación segura que sigue la arquitectura OAS. Las reglas de cuotas, exenciones y conceptos se ajustan por parámetros o por la plantilla, sin tocar código, y cada carga queda completa y registrada."

### Q12: ¿Cuáles son las grandes áreas funcionales de la visión completa?
[Answer]:
1. Carga y validación de plantillas — subir el archivo, identificar el tipo (pregrado, posgrado por créditos o posgrado en salarios mínimos) y validar el formato.
2. Validación académica del estudiante — estado, carrera y terminación de materias, contra Oracle académico.
3. Generación de solicitudes — cuotas, porcentajes y fechas de pago (ordinaria y extraordinaria, saltando festivos), exenciones (incluido el certificado electoral) y conceptos.
4. Administración de parámetros — conceptos, exenciones, fechas de pago por facultad, porcentajes por defecto, estados permitidos y eventos del calendario.
5. Resultados y trazabilidad — resumen de procesados y rechazados con motivo, historial de lotes y auditoría.
6. Consulta histórica por estudiante — solicitudes y recibos generados (hoy `admin_historicoPorEstudiante` / `admin_generados`).
7. Integración con la generación e impresión del recibo — entregar las solicitudes al módulo que produce el recibo (hoy "Solicitados", fuera del repositorio).

### Q13: ¿Qué capacidades pensaste pero decidiste no comprometer todavía?
[Answer]: b — Ninguna. La visión anterior lo incluye todo.

---

## ✅ Sección 3 completa — aprobada
**Registrado**: 2026-11-23T22:08:00Z
Aprobación del usuario: "aprobar"

---

## Sección 4 — Alcance de la primera versión (IN) · Q14–Q15
**Registrado**: 2026-11-23T22:12:00Z
Respuesta del usuario (verbatim): "q14 ok, q15 a+d+e"

### Q14: ¿Qué funcionalidades entran en la primera versión?
[Answer]: ok (sugerencia aceptada)

| Funcionalidad | Por qué tiene que estar | Usuario |
|---|---|---|
| Carga de las 3 plantillas actuales (pregrado, posgrado por créditos, posgrado en salarios mínimos), con validación de formato | Es por donde empieza el proceso actual | Admisiones, Registro y Control |
| Validación del estudiante contra Oracle académico: estado, carrera y terminación de materias | Sin esto se generan solicitudes inválidas | Admisiones, Registro y Control |
| Generación de solicitudes con cuotas, exenciones y conceptos, igual que el sistema actual | Capacidad principal (Q3) y métrica de coincidencia del 100% (Q10) | Admisiones, Registro y Control |
| Cancelación automática de las solicitudes anteriores sin imprimir del mismo estudiante | Regla vigente del sistema actual | Admisiones, Registro y Control |
| Reglas en tablas de parámetros (conceptos, exenciones, fechas por facultad, porcentajes, estados), sin pantalla de administración | Métrica Q10: ningún cambio de código por periodo | OATI / Admisiones, Registro y Control |
| Cada solicitud se guarda completa o no se guarda | Métrica Q10: ninguna solicitud incompleta | Admisiones, Registro y Control |
| Resumen del lote: procesados y rechazados, con el motivo | Ya existe hoy y se usa para gestionar los rechazos | Admisiones, Registro y Control |
| Historial de lotes y auditoría: quién, cuándo, qué archivo y desde qué IP | Restricción Q9: logs siempre habilitados | Admisiones, Registro y Control / Seguridad |
| Inicio de sesión y rol único con WSO2 y `configuracion_cliente` | Restricción Q9 y lineamientos OAS | Admisiones, Registro y Control |
| Solicitudes entregadas en un formato que el módulo de impresión actual ("Solicitados") pueda seguir usando | Sin esto no se pueden imprimir los recibos | Admisiones, Registro y Control / Estudiante |

Fuera de la primera versión (candidatos para Q16): pantalla de administración de parámetros (área 4) y consulta histórica por estudiante (área 6).

### Q15: ¿Qué propiedades no funcionales importan más en la primera versión?
[Answer]: a + d + e — Tiempo de respuesta; Seguridad y protección de datos; Costos bajos.

---

## ✅ Sección 4 completa — aprobada
**Registrado**: 2026-11-23T22:15:00Z
Aprobación del usuario: "aprobar"

---

## Sección 5 — Qué queda fuera de la primera versión · Q16
**Registrado**: 2026-11-23T22:18:00Z
Respuesta del usuario (verbatim): "q16 b"
Interpretación: "b" responde la pregunta de reingreso (quedan para una fase posterior). La tabla sugerida se toma como aceptada sin cambios (supuesto; se confirma en la aprobación de la sección).

### Q16: ¿Qué NO entra en la primera versión, y por qué?
[Answer]:

| Queda fuera | Motivo | Cuándo se haría |
|---|---|---|
| Pantalla para administrar parámetros (conceptos, exenciones, fechas, porcentajes, estados) | Los parámetros se cargan en tablas; la pantalla no alcanza antes del 15/12/2026 | Fase 2 |
| Consulta histórica por estudiante (`admin_historicoPorEstudiante` / `admin_generados`) | No hace falta para generar las solicitudes de 2027-1 | Fase 2 |
| Generar e imprimir el recibo en el sistema nuevo | Se sigue usando el módulo actual ("Solicitados"); la primera versión solo le entrega las solicitudes | Fase 2 o después |
| Migrar las solicitudes históricas del MySQL actual | La primera versión trabaja solo con solicitudes nuevas | Por definir |
| Código que ya no se usa: `action.php`, `html.php`, "PLANTILLA SIMPLE" | No forman parte del flujo actual | No se migra |
| Consultas de notas del coordinador (`admin_consultasCoordinador`) | No tienen relación con los recibos | Fuera del proyecto |
| Recibos de reingreso (C-045558) | Opción b del usuario; no hay código en el repositorio | Fase posterior |

---

## ✅ Sección 5 completa — aprobada
**Registrado**: 2026-11-23T22:20:00Z
Aprobación del usuario: "aprobar" (incluye la tabla sugerida + reingreso en fase posterior)

---

## Sección 6 — Riesgos y preguntas abiertas · Q17–Q18
**Registrado**: 2026-11-23T22:30:00Z

Respuesta del usuario (verbatim):
"q17 ok, q18 1 indefinido 2 paralelo 3 eliminar regla, ¿Qué tablas, campos y estados necesita el módulo "Solicitados" para seguir imprimiendo los recibos?
Oracle:
acasperi
acest
acestmat
acvlrscs

MySql:
solicitudrecibo10:55 AM


¿Cuáles son las plantillas oficiales vigentes, con su número de columnas y sus encabezados?
PLANTILLA GENERAL PREGRADOS             
DETALLES DEL PAGO CONCEPTOS   EXENCIONES         ESPECIAL
Código del estudiante Seguro Estudiantil Carnet Estudiantil Sistematización 10% votación 2do Hermano 3er Hermano Terminación de Materias Beneficiario Matrícula de Honor Deportista de alto rendimiento Estudiante Distinguido /Cultural-Científico Mérito Académico Reingreso

PLANTILLA GENERAL POSTGRADOS CREDITOS                            
DETALLES DEL PAGO   CONCEPTOS   EXENCIONES           \"Fechas de Pago 
(Solo Pago Ordinario, el sistema calcula de forma automática la fecha de pago extraordinario)\"         Porcentaje de Cada Cuota  
                 Cuota 1   Cuota 2   Cuota 3     
Código del estudiante Créditos Cuotas Seguro Estudiantil Carnet Estudiantil Sistematización 10% votación Monitor Egresado Docente Beneficiario Beca Mejor ECAES Grado de Honor 50% Segundo hermano 70% Secretaria Educación \"90%
Doctorado Interinstitucional\" Día Mes Año Día Mes Año Día Mes Año Cuota 1 Cuota 2 Cuota 3


PLANTILLA GENERAL POSTGRADOS SALARIOS MINIMOS LEGALES                            
DETALLES DEL PAGO   CONCEPTOS   EXENCIONES           \"Fechas de Pago 
(Solo Pago Ordinario, el sistema calcula de forma automática la fecha de pago extraordinario)\"         Porcentaje de Cada Cuota  
                 Cuota 1   Cuota 2   Cuota 3     
Código del estudiante SMLV Cuotas Seguro Estudiantil Carnet Estudiantil Sistematización 10% votación Monitor Egresado Docente Beneficiario Beca Mejor ECAES Grado de Honor 50% Segundo hermano 70% Secretaria Educación \"90%
Doctorado Interinstitucional\" Día Mes Año Día Mes Año Día Mes Año Cuota 1 Cuota 2 Cuota 3



¿Quién de Admisiones, Registro y Control confirma que el sistema nuevo da los mismos resultados, y con qué lotes de prueba?

Coordinador funcional de admisiones y registro y control, lotes de pruebas de periodos anteriores"

### Q17: ¿Cuáles son los riesgos conocidos?
[Answer]: ok (tabla sugerida aceptada)

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Quedan ~22 días para llegar al ambiente de pruebas | Alto | Alcance cerrado (Q14/Q16), parámetros en tablas sin pantalla, usar modelo, BD y WSO2 existentes |
| Malinterpretar reglas que hoy solo están en el código (cuotas, exenciones, conceptos, cuotas al 0% "COVID") | Alto | Validar cada regla con Admisiones, Registro y Control; comparar con lotes reales del sistema actual |
| Repositorio incompleto (núcleo del framework y módulo "Solicitados") | Alto | Conseguir el código o documentar la conexión con "Solicitados" antes de construir |
| Dependencia de Oracle académico y sus funciones PL/SQL | Medio | Acceso de solo lectura acordado con DBA y probado pronto en dev |
| La revisión de Seguridad puede bloquear el paso a producción | Medio | Cumplir el checklist de seguridad desde el inicio (sin secretos, SonarQube, Dependabot, OWASP) |
| Datos personales de estudiantes (Ley 1581) en archivos y logs | Medio | Mínimo privilegio, retención definida de archivos, no registrar datos sensibles en logs |
| Diferencias de formato en las plantillas | Bajo | Usar las plantillas oficiales vigentes como casos de prueba |

### Q18: ¿Qué queda sin resolver?
[Answer]: a — lista, con respuestas parciales del usuario:
1. Fecha de retiro definitivo de PHP 5 y del sistema actual: **indefinida** (sigue abierta).
2. En 2027-1 el sistema nuevo **funciona en paralelo** con el PHP.
3. Regla de diferido de pregrado con cuotas al 0% ("COVID"): **eliminar la regla**. (Por confirmar con qué se reemplaza.)
4. Contrato con "Solicitados": usa en Oracle `acasperi`, `acest`, `acestmat`, `acvlrscs`; en MySQL `solicitudrecibo`. (Campos y estados por detallar en el rol Técnico.)
5. Plantillas oficiales vigentes: encabezados entregados (ver arriba, verbatim).
6. Validación de equivalencia: **Coordinador funcional de Admisiones, Registro y Control**, con **lotes de prueba de periodos anteriores**.

---

## Sección 6 — Aclaraciones sobre plantillas · cambio en Q16
**Registrado**: 2026-11-23T22:40:00Z
Respuesta del usuario (verbatim): "1 reingresos queda excluido y la plantilla tendra modificacione spara no incluirlo,  2 D:\usuarios\OATI\migracion-recibos-ws\documentacion\plantillas-recibos, 3en pregrado no hay numero de cuotas,"

1. Reingreso: **excluido**. La plantilla de pregrado se modificará para quitar la columna 14 "Reingreso". (Actualiza la fila de Q16: ya no es "fase posterior" sino "excluido".)
2. Plantillas oficiales en `documentacion/plantillas-recibos/`. Revisadas (ver `interview/technical/templates-analysis.md`): pregrado 14 columnas; posgrado créditos 29 columnas (coincide con el código; "Beca" y "Mejor ECAES" son columnas separadas). Falta el archivo de posgrado SMLV.
3. En pregrado **no hay número de cuotas** en la plantilla. El código actual lee la columna 2 (Seguro Estudiantil) como cuota: defecto que no se replica.

Pendiente: con qué se reemplaza la regla eliminada de cuotas al 0% ("COVID") para diferido de pregrado.

---

## Sección 6 — Aclaración Q18.3 (diferido de pregrado)
**Registrado**: 2026-11-23T22:45:00Z
Respuesta del usuario (verbatim): "un estudiante de pregrado no tiene pago diferido por lo que esa regla se elimina"

[Answer]: En pregrado **no existe pago diferido**. Se elimina toda la lógica de diferido para pregrado (incluida la variante de cuotas al 0% "COVID").
Consecuencia: en pregrado cada solicitud lleva **una sola cuota al 100%**, con fechas tomadas de las fechas de pago por facultad (equivale a la rama "sin diferido" del código actual en `guardarCuotas`).

---

## ✅ Sección 6 completa — aprobada
**Registrado**: 2026-11-23T22:48:00Z
Aprobación del usuario: "aprobar"

---

## Sección 7 — Sistema existente · QB1–QB2
**Registrado**: 2026-11-23T22:52:00Z
Respuesta del usuario (verbatim): "qb1 ok, qb2 ok a"

### QB1: Describe en un párrafo cómo funciona hoy el sistema.
[Answer]: "Hoy, Admisiones, Registro y Control carga en weboffice (PHP 5 y un framework propio de la Universidad) una plantilla Excel .xls con los códigos de los estudiantes. Hay tres plantillas: pregrado, posgrado por créditos y posgrado SMLV. El módulo registro_lote_recibo revisa cada estudiante en el sistema académico de Oracle: su estado, su carrera y el calendario. Luego cancela las solicitudes anteriores que no se imprimieron y crea en MySQL las solicitudes de recibo, con sus cuotas, exenciones y conceptos. Después, el módulo "Solicitados" lee esas solicitudes junto con tablas de Oracle (acasperi, acest, acestmat, acvlrscs) y genera e imprime los recibos. Las reglas están escritas directamente en el código, y el sistema no tiene pruebas ni API."

### QB2: ¿Qué NO debe cambiar?
[Answer]: ok + a
- Sistema académico en Oracle: solo lectura, sin modificar estructura ni datos.
- Módulo "Solicitados": no se modifica y sigue leyendo las solicitudes como hoy.
- Tabla `solicitudrecibo`: se mantienen su estructura y sus estados (0 = sin imprimir, 2 = cancelada; demás por confirmar).
- Sistema PHP actual: sigue funcionando sin cambios durante el paralelo de 2027-1.
- Lo que ya existe: modelo de datos aprobado, base creada por los DBA y registro en WSO2.
- Reglas de cálculo vigentes (cuotas de posgrado, fecha extraordinaria +8 días sin festivos, exenciones y conceptos), salvo: sin reingreso, sin diferido en pregrado y sin leer "Seguro" como cuota.
- Paralelo 2027-1 (opción a): el sistema nuevo **escribe en la misma tabla MySQL `solicitudrecibo`** que lee "Solicitados".

Notas para la consolidación (open-questions):
- Con ambos sistemas escribiendo en `solicitudrecibo`, la regla "cancelar solicitudes previas sin imprimir" puede cancelar solicitudes creadas por el otro sistema. Hay que acordar cómo se reparte la carga entre sistemas.
- Posible contradicción con los lineamientos OAS (PostgreSQL, convenciones de nombres) y con el "modelo de datos aprobado": ¿el modelo aprobado es el MySQL actual o uno nuevo? → rol Técnico.

---

## Sección 7 — Cambio solicitado · QB2 (paralelo y bases de datos)
**Registrado**: 2026-11-23T22:58:00Z
Respuesta del usuario (verbatim): "1 solo funcionan en paralelo para pruebas luego se reemplazan, 2 los lineamientos son solo para el codigo no para als bases de datos, se mantienen  la conexion a oracle"

1. **Paralelo solo durante las pruebas.** Ambos sistemas conviven únicamente para comparar resultados; después el sistema nuevo **reemplaza** al PHP. (Actualiza Q18.2: "funciona en paralelo" → "en paralelo solo para pruebas; luego reemplaza al PHP".) El riesgo de cancelaciones cruzadas en `solicitudrecibo` queda limitado a la etapa de pruebas.
2. **Los lineamientos OAS aplican solo al código, no a las bases de datos.** Se mantienen las bases actuales: la conexión a **Oracle** académico y la tabla **MySQL** `solicitudrecibo` (y relacionadas) que lee "Solicitados". No se migra a PostgreSQL ni se renombran tablas.
   Consecuencia para el rol Técnico: los hallazgos L22–L29 de `interview/technical/institutional-guidelines-analysis.md` (modelo de datos) se marcan como **no aplicables** a este proyecto.

QB2 actualizada:
- Oracle académico: solo lectura, se mantiene la conexión.
- "Solicitados": no se modifica.
- `solicitudrecibo` (MySQL): se mantienen estructura y estados; el sistema nuevo escribe ahí.
- Sistema PHP: sigue funcionando sin cambios durante las pruebas en paralelo; después se reemplaza.
- Modelo de datos aprobado, base creada por los DBA y registro en WSO2: se usan tal como existen.
- Reglas de cálculo vigentes, salvo: sin reingreso, sin diferido en pregrado, sin leer "Seguro" como cuota.

---

## ✅ Sección 7 completa — aprobada
**Registrado**: 2026-11-23T23:05:00Z
Aprobación del usuario: "aprobar"
Entrevista de Negocio completa (20/20). Se generaron `open-questions.md` (OQ-B-1 a OQ-B-6) y `vision-document.md`, pendientes de la aprobación final del rol.

---

## Corrección por consolidación final (C-1, C-3, C-4, C-6)
**Registrado**: 2026-11-24T00:55:00Z
Respuesta del usuario (verbatim): "para c1 consultara y actualizara a un servicio externo de nopmbre parametros, la sintaxis se explicara despues por ahora debe quedar indicado, c2 dejalo sincrono, c3 debe tomar 13, las pruebas se evaluan independientes, c4 sera posterior, c5 en este caso no importa, c6 el desarrollo es guiado por ia por lo que no aplica el alcance, b"

- Q14 (corrige fila): las reglas parametrizadas se consultan y actualizan en el servicio externo "parametros" (antes: "tablas de parámetros").
- Reglas acordadas (agrega): el sistema nuevo solo acepta la plantilla de pregrado de 13 columnas; las pruebas de cada sistema se evalúan de forma independiente.
- Q10 (precisa método): herramienta de comparación de equivalencia en etapa posterior.
- Riesgo de plazo vs alcance: no aplica (desarrollo guiado por IA).
- `vision-document.md` actualizado con estas decisiones.

---
