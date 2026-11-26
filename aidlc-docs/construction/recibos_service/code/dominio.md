# Código del dominio — U1 `recibos_service`

- Paso 3 y 4 del plan de generación (`construction/plans/recibos_service-code-generation-plan.md`)
- Ubicación: `recibos_service/app/domain/` y `recibos_service/tests/domain/`
- Verificado el 2026-11-25 en `python:3.15.2-slim`: ruff sin errores, mypy estricto sin errores, 159 pruebas bien y 100% de cobertura de líneas y ramas (605 sentencias, 144 ramas)

## Módulos

| Módulo | Qué hace | Reglas |
|---|---|---|
| `modelos.py` | Entidades y objetos de valor inmutables; `crear_hoja` descarta celdas vacías o con solo espacios | `domain-entities.md` §2, F4 |
| `errores.py` | `FormatoInvalido` (422), `ReglaInvalida` y `ExencionSinPorcentaje` (502) | BR-L04, BR-L05, BR-L08 a BR-L11 |
| `mensajes.py` | Textos para ARC y armado de cada `Rechazo` | `business-rules.md` §10, DF-08, BR-T02 |
| `reglas.py` | `ReglasLiquidacion`: valida los porcentajes por defecto, los días y los estados; exige el porcentaje de cada exención de los mapas y de la votación | BR-L04, BR-L05, F11 |
| `plantillas.py` | Las tres especificaciones, identificación por A1, formato con el mensaje propio de "Reingreso" y extracción de filas | BR-L08 a BR-L11, C-3 |
| `validacion_filas.py` | Lectura de enteros, unidad, fechas y porcentajes; código; datos de posgrado | BR-F01, BR-D01 a BR-D04, DF-02, DF-03 |
| `validacion_estudiante.py` | Reglas del estudiante en el orden de hoy y después las nuevas | BR-E02 a BR-E07 |
| `fechas.py` | Fecha extraordinaria, timestamps de America/Bogota y rango de festivos | BR-Q04, BR-S04, BR-L13 |
| `cuotas.py` | Cuota de pregrado; cuotas de posgrado con porcentajes por defecto y suma de 100 | BR-Q01 a BR-Q03, BR-D05 |
| `exenciones.py` | Votación, descuento y Secretaría, con el tope de 100% | BR-X01 a BR-X07 |
| `conceptos.py` | Matrícula, exclusivo de pregrado y marcados | BR-C01, BR-C02 |
| `generador_solicitud.py` | Arma la `Solicitud` o devuelve la falla, en el orden de las reglas | BR-S01 a BR-S03 |

## Pruebas
- De ejemplo: `test_*_ejemplos.py` y `test_generador_solicitud.py`, con los escenarios de US-03 a US-08 y US-11 y la tabla de decisión de `business-logic-model.md` §4.6.
- De propiedades (Hypothesis): `test_*_propiedades.py`, con las propiedades del dominio de `business-logic-model.md` §9: ida y vuelta de la unidad SMLV y del timestamp (PBT-02); invariantes de filas, formato, fechas, cuotas, exenciones, conceptos y solicitud (PBT-03); idempotencia de la lectura (PBT-04); oráculos de las validaciones del estudiante y de la tabla de exenciones (PBT-05).
- Generadores centralizados en `tests/estrategias.py` (PBT-07) y perfiles `dev` y `ci` en `tests/conftest.py` (PBT-08).
- `tests/test_arquitectura.py` revisa que `app/domain` solo importe la biblioteca estándar (NFR-M01).

## Valores provisionales
- Pregrado (D1): la fecha ordinaria en las columnas 14, 15 y 16 y 16 columnas en total (`plantillas.PREGRADO`).
- Posgrado SMLV (D2): la estructura de créditos con "SMLV" en el encabezado de la columna 2 (`plantillas.POSGRADO_SMLV`).
- Los encabezados se comparan por una palabra clave de cada columna, normalizada (sin tildes, en mayúsculas). Se revisan contra los archivos oficiales de `documentacion/plantillas-recibos/` en el paso 13.
