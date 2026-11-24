# Application Design — Historial de respuestas (solo se agrega)

## Lote 1 — sintaxis de "parametros" — 2026-11-24T02:00:00Z

Respuesta literal del usuario: "para consultar un parametro usa el id y lo pasa en un get usando una estructura como esta /v1/parametro/9"

| Tema | Respuesta | Aplicado en |
|---|---|---|
| Consulta a "parametros" | `GET /v1/parametro/{id}`, un id por parámetro | AD-20, RF-09 CA2, US-15 |

---

## Lote 2 — P-15 y ejemplo de respuesta — 2026-11-24T02:30:00Z

Respuesta del usuario: "p 15 a" y un ejemplo de respuesta de `GET /v1/parametro/9` (texto literal en `aidlc-docs/audit.md`).

| Tema | Respuesta | Aplicado en |
|---|---|---|
| P-15 | a) Todas las reglas se leen de "parametros", incluidos los porcentajes de las exenciones y las fechas por facultad | AD-16, `ReglasLiquidacion`, RF-09, US-07, US-15 |
| Formato de la respuesta | Sobre CRUD: `Success`, `Status` como texto (`"200"`), `Message`, `Data`. `Data` es un objeto `Parametro`: `Id`, `Nombre`, `Descripcion`, `CodigoAbreviacion`, `Activo`, `NumeroOrden`, `FechaCreacion`, `FechaModificacion`, `TipoParametroId` (solo `Id`), `ParametroPadreId` | AD-20, AD-21, AD-22, `ParametroDTO` |

Interpretaciones:
- El objeto `Parametro` no tiene un campo de valor. El valor de cada regla tiene que ir en uno de sus campos. El adaptador lee el campo que diga la configuración (AD-21), así que esa decisión no cambia el código.
- Los ids que se escriben en MySQL (exenciones, conceptos) no pueden salir del `Id` del parámetro, que es del servicio y cambia entre ambientes. Tienen que venir en un campo del parámetro. El ejemplo sugiere `CodigoAbreviacion` ("41").
- `Activo: false` es el borrado lógico de los servicios OAS. Una regla inactiva no se usa: el lote no se procesa (AD-22, escenario 5 de US-15).
- Las reglas no existen hoy en "parametros": están en el código PHP y en las tablas `exencion` y `fechaPagoFacultad`. Hay que crearlas (D10).
- Consecuencia de P-15 (a): si un porcentaje de exención cambia, se cambia en "parametros" y en la tabla `exencion`, que probablemente usa "Solicitados".
- El servicio es `parametros_crud` (citado en `lineamientos_oas/generacion_de_apis/endpoint_validacions.md`).

---
