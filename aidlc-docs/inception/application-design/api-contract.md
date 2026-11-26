# Contrato de la API — recibos_service v1

Base: la URL que publique WSO2 AM para `recibos_service`, con el prefijo `/v1`. Todas las operaciones de `/v1` piden `Authorization: Bearer <token>` y el rol ARC. Este documento es la fuente para `swagger/swagger.yml` (U1, en Swagger 2.0 como el lineamiento) y para los modelos de `recibos_mf` (U2).

## Sobre de respuesta

```json
{
  "Success": true,
  "Status": 200,
  "Message": "Solicitud exitosa",
  "Data": {}
}
```

- `Status` es un entero igual al código HTTP.
- Todas las respuestas llevan la cabecera `X-Request-Id`, con el identificador de la petición que queda en los registros; CORS la expone a `recibos_mf` (AD-33).
- Las respuestas de `/v1/*` llevan `Cache-Control: no-store`, porque el reporte trae códigos de estudiantes (AD-36).
- `POST /v1/lotes` responde en unos 100 s como máximo: el límite propio de 90 s más la sentencia de MySQL que esté en curso. `recibos_mf` espera hasta 150 s (AD-34).
- `Message` es texto en español. Sin mensaje propio, se usa el de `utils_oas` para ese código.
- Los listados agregan `Metadata`.
- En los errores, `Success` es `false` y `Data` es `null`, salvo en el 422 de formato.

## `POST /v1/lotes` — cargar y procesar un lote

Petición: `multipart/form-data` con un campo `archivo` (plantilla `.xls` de 2 MB como máximo).

Respuesta **201**: el lote se procesó, aunque tenga estudiantes rechazados.

```json
{
  "Success": true,
  "Status": 201,
  "Message": "Recurso creado con éxito",
  "Data": {
    "id_lote": 1532,
    "tipo_plantilla": "PREGRADO",
    "total_filas": 3,
    "procesados": [
      { "fila": 4, "codigo": "20231020001" },
      { "fila": 5, "codigo": "20231020017" }
    ],
    "rechazados": [
      {
        "fila": 6,
        "codigo": "20231020045",
        "motivo": "ESTADO_NO_PERMITIDO",
        "mensaje": "El estado del estudiante (E) no permite generar el recibo"
      }
    ]
  }
}
```

Respuesta **422**: el lote quedó registrado, pero la plantilla no tiene el formato esperado.

```json
{
  "Success": false,
  "Status": 422,
  "Message": "La plantilla de pregrado no es la vigente: trae la columna Reingreso",
  "Data": { "id_lote": 1533 }
}
```

| Código | Cuándo |
|---|---|
| 201 | Lote procesado |
| 400 | Falta el campo `archivo` |
| 401 | Falta el token o no es válido |
| 403 | El usuario no tiene el rol ARC |
| 413 | El archivo supera el tamaño máximo (2 MB) |
| 415 | El archivo no es `.xls` (extensión o contenido real) |
| 422 | Formato de plantilla inválido |
| 502 | Una dependencia respondió con datos inválidos |
| 503 | WSO2 IS, "parametros", Oracle, MySQL o S3 no responden, o no alcanzan en los 30 s que tiene la fase previa a las filas |
| 500 | Error inesperado |

Valores de `motivo` y un texto de referencia de `mensaje`. Los textos finales, con sus variantes, están en `aidlc-docs/construction/recibos_service/functional-design/business-rules.md` §10:

| `motivo` | `mensaje` |
|---|---|
| `CODIGO_INVALIDO` | Código de estudiante inválido, o "Falta el código del estudiante" si la fila tiene datos y no tiene código (F3) |
| `CODIGO_REPETIDO` | El código ya está en la fila N; solo se procesa la primera aparición (F2) |
| `ESTUDIANTE_NO_ENCONTRADO` | El código no está registrado |
| `SIN_VALOR_MATRICULA` | Sin información de matrícula; solicitar por oficio |
| `ESTADO_NO_PERMITIDO` | El estado del estudiante no permite generar el recibo |
| `CARRERA_INACTIVA` | El proyecto curricular del estudiante no está activo |
| `NO_TERMINACION_MATERIAS` | El estado del estudiante es diferente de terminación de materias |
| `SIN_PERIODO_VIGENTE` | No hay periodo vigente para el proyecto curricular del estudiante. Repórtelo al área de sistemas (RE-05) |
| `CUOTAS_INVALIDAS` | El número de cuotas es obligatorio y debe estar entre 1 y 3 (RE-03, RE-04) |
| `FECHA_INVALIDA` | Falta la fecha, es inválida, es anterior al día de la carga o vence antes que la cuota anterior, en la cuota indicada (RE-06, F7) |
| `UNIDAD_INVALIDA` | Los créditos o SMLV son obligatorios y deben ser mayores que 0 (F6) |
| `NIVEL_NO_CORRESPONDE` | El nivel del proyecto curricular del estudiante no corresponde a la plantilla (F5) |
| `PORCENTAJE_INVALIDO` | El porcentaje debe estar entre 0 y 100 |
| `DESCUENTOS_NO_ACUMULABLES` | Solo se puede marcar un descuento además de la votación (C2); en posgrado, además de la votación y de la Secretaría de Educación (F12) |
| `PORCENTAJES_NO_SUMAN_100` | Los porcentajes de las cuotas deben sumar 100 |
| `TIEMPO_AGOTADO` | No se alcanzó a procesar en el tiempo del lote; vuelva a cargar esta fila (N3) |
| `ERROR_GUARDADO` | Error al guardar la solicitud |

## `GET /v1/lotes` — historial de lotes

Parámetros de consulta: `limit` (1–100, por defecto 20) y `offset` (≥ 0, por defecto 0). Orden: del más reciente al más antiguo.

Respuesta **200**:

```json
{
  "Success": true,
  "Status": 200,
  "Message": "Solicitud exitosa",
  "Data": [
    {
      "id": 1533,
      "usuario": "79123456",
      "fecha": "2026-12-01T10:15:00-05:00",
      "nombre_archivo": "pregrado_2027_1.xls",
      "ip": "10.20.30.40"
    }
  ],
  "Metadata": { "total": 57, "limit": 20, "offset": 0 }
}
```

Si no hay lotes, la respuesta es 200 con `Data: []`. Errores: 400 (parámetros), 401, 403, 503.

## Health checks (sin token, sin prefijo, no se auditan)

| Ruta | Respuesta |
|---|---|
| `GET /` | `{"status": "ok"}` |
| `GET /health` | `{"status": "UP"}` |

## Modelos TypeScript para `recibos_mf`

```ts
export interface RespuestaApi<T> {
  Success: boolean;
  Status: number;
  Message: string;
  Data: T | null;
  Metadata?: MetadataPagina;
}

export interface MetadataPagina {
  total: number;
  limit: number;
  offset: number;
}

export type TipoPlantilla = 'PREGRADO' | 'POSGRADO_CREDITOS' | 'POSGRADO_SMLV';

export interface Rechazo {
  fila: number;
  codigo: string | null;
  motivo: string;
  mensaje: string;
}

export interface Procesado {
  fila: number;
  codigo: string;
}

export interface ResumenLote {
  id_lote: number;
  tipo_plantilla: TipoPlantilla;
  total_filas: number;
  procesados: Procesado[];   // los que se subieron (RF-11 CA3)
  rechazados: Rechazo[];     // los que no se subieron, con el motivo
}

export interface Lote {
  id: number;
  usuario: string;
  fecha: string;
  nombre_archivo: string;
  ip: string;
}
```

Notas para el microcliente:
- La carga puede tardar mientras se procesa todo el lote. La pantalla muestra que está procesando y no permite un segundo envío.
- WSO2 AM puede responder 429 si se pasa el límite de tráfico (AD-23). La pantalla muestra un mensaje para intentar más tarde.
- Los códigos de estudiante solo se muestran en pantalla; no se guardan en el navegador.
