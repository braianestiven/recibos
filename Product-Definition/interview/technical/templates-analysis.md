# Plantillas oficiales vs. código actual (contexto para la entrevista técnica)

- Fecha: 2026-11-23T22:40:00Z
- Fuente: `documentacion/plantillas-recibos/` (lectura de los registros BIFF8 de los `.xls`: DIMENSIONS, SST y LABELSST; sin abrir Excel, sin modificar los archivos)
- Contrastado con: `codigo-fuente/weboffice/bloque/registro_lote_recibo/bloque.php` y `funcion.class.php`

## Archivos encontrados

| Archivo | Tamaño | Nota |
|---|---|---|
| `plantilla_general_pregrados(1).xls` | 10 240 B | 14 columnas |
| `plantilla_general_postgrados_creditos.xls` | 12 800 B | 29 columnas |
| `plantilla_general_postgrados_creditos (1).xls` | 12 800 B | Mismo contenido de encabezados que el anterior (aparente duplicado) |
| *(falta)* `PLANTILLA GENERAL POSTGRADOS SALARIOS MINIMOS LEGALES` | — | No está en la carpeta |

## Pregrado — `PLANTILLA GENERAL PREGRADOS`

Encabezados en la fila 3; datos desde la fila 4 (coincide con `filaInicio = 4`).

| Col | Grupo | Encabezado | Uso en el código actual |
|---|---|---|---|
| 1 | Detalles del pago | Código del estudiante | Código del estudiante |
| 2 | Conceptos | Seguro Estudiantil | Concepto → `id_concepto 2` **y también se lee como número de cuota** (`cuotaPlantilla`) ⚠ |
| 3 | Conceptos | Carnet Estudiantil | Concepto → `id_concepto 3` |
| 4 | Conceptos | Sistematización | Concepto → `id_concepto 4` |
| 5 | Exenciones | 10% votación | `id_exencion 1` (certificado electoral) |
| 6 | Exenciones | 2do Hermano | `id_exencion 2` |
| 7 | Exenciones | 3er Hermano | `id_exencion 3` |
| 8 | Exenciones | Terminación de Materias | `id_exencion 4`; además activa fechas de la cuota 3 de la facultad |
| 9 | Exenciones | Beneficiario | `id_exencion 5` |
| 10 | Exenciones | Matrícula de Honor | `id_exencion 6` |
| 11 | Exenciones | Deportista de alto rendimiento | `id_exencion 7` |
| 12 | Exenciones | Estudiante Distinguido / Cultural-Científico | `id_exencion 8` |
| 13 | Exenciones | Mérito Académico | `id_exencion 9` |
| 14 | Especial | Reingreso | `id_exencion 18` (cambio C-045558) — **se excluye**; la plantilla se modificará para quitarla |

Decisiones del negocio (2026-11-23):
- **En pregrado no hay número de cuotas en la plantilla.** El código actual lee la columna 2 (Seguro Estudiantil) como cuota: es un defecto que el sistema nuevo no debe replicar.
- **Reingreso queda excluido.** La plantilla de pregrado pasará a 13 columnas. El código actual solo acepta 14 o 29 columnas (`bloque.php`), así que el sistema nuevo debe validar la nueva estructura.

## Posgrado por créditos — `PLANTILLA GENERAL POSTGRADOS CREDITOS`

Encabezados en las filas 2–4; datos desde la fila 5 (coincide con `filaInicio = 5`). **29 columnas, coincide con el código.**

| Col | Encabezado | Uso en el código actual |
|---|---|---|
| 1 | Código del estudiante | Código |
| 2 | Créditos | `unidad` |
| 3 | Cuotas | Número de cuotas (1–3) |
| 4–6 | Seguro Estudiantil, Carnet Estudiantil, Sistematización | Conceptos 2, 3, 4 |
| 7 | 10% votación | `id_exencion 1` |
| 8 | Monitor | `id_exencion 10` |
| 9 | Egresado | `id_exencion 11` |
| 10 | Docente | `id_exencion 12` |
| 11 | Beneficiario | `id_exencion 5` |
| 12 | Beca | `id_exencion 13` |
| 13 | Mejor ECAES | `id_exencion 14` |
| 14 | Grado de Honor | `id_exencion 15` |
| 15 | 50% Segundo hermano | `id_exencion 2` |
| 16 | 70% Secretaria Educación | `id_exencion 16` |
| 17 | 90% Doctorado Interinstitucional | `id_exencion 17` |
| 18–20 | Cuota 1: Día, Mes, Año | Fecha ordinaria cuota 1 (extraordinaria = +8 días sin festivos) |
| 21–23 | Cuota 2: Día, Mes, Año | Fecha ordinaria cuota 2 |
| 24–26 | Cuota 3: Día, Mes, Año | Fecha ordinaria cuota 3 |
| 27–29 | Porcentaje Cuota 1, 2, 3 | Porcentaje por cuota (si vacío: 100 / 60-40 / 40-30-30) |

La diferencia de 28 vs. 29 columnas que vimos en el texto pegado se debía a que "Beca" y "Mejor ECAES" son dos columnas separadas. El comentario de `bloque.php` ("postgrado 26") está desactualizado.

## Posgrado SMLV

No hay archivo. Por el código, tiene la misma estructura que créditos, con "SMLV" en la columna 2 (según los encabezados pegados por el usuario). **Pendiente:** conseguir el archivo oficial para confirmarlo.
