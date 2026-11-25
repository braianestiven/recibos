# Evaluación de la calidad del código

- Etapa: INCEPTION → Reverse Engineering (2026-11-25)
- Complementa los riesgos R1–R18 de `existing-system-analysis.md` §5 con ubicaciones exactas y con lo que encontró esta etapa. Los números de línea son de `bloque/registro_lote_recibo/funcion.class.php`, salvo que se indique otro archivo
- Ninguna prueba se ejecutó: el sistema PHP no corre sin el núcleo del framework y en la máquina no hay PHP. `utils_oas` pide Go 1.26 y la máquina tiene 1.17

## Cobertura de pruebas

- **General**: ninguna en `weboffice`. En `utils_oas`, 2 de 21 paquetes tienen pruebas (`apiStatusLib`, `xray`); la cobertura no se midió.
- **Pruebas unitarias**: no hay en `weboffice`.
- **Pruebas de integración**: no hay.
- **Efecto en la migración**: la equivalencia no se puede comprobar ejecutando el sistema actual desde el repositorio. Se apoya en esta lectura del código, en los lotes de prueba de periodos anteriores que valida ARC y en la comparación que define C-4.

## Indicadores de calidad

- **Análisis estático (linting)**: no configurado. No hay `phpcs`, `golangci-lint` ni `sonar-project.properties` en el código actual.
- **Estilo**: inconsistente. Se mezclan etiquetas `<?` y `<?php`, tabuladores y espacios, nombres en español e inglés, `camelCase` y `snake_case`, y comentarios con fechas de cambios ("2020-1", "COVID", "2014-3").
- **Documentación**: pobre. Los bloques de comentario dicen `@param unknown`; no hay README ni esquema de datos. `utils_oas` sí tiene README.
- **CI/CD**: no hay en el repositorio del sistema actual.

## Deuda técnica

| ID | Problema | Ubicación | Relación |
|---|---|---|---|
| TD-01 | SQL armado concatenando valores, sin parámetros | `sql.class.php`, las 22 opciones (por ejemplo 103, 141, 154) | R1 |
| TD-02 | Escrituras sin transacción; los resultados se concatenan con `.=` y nunca dan falso; `guardarCuotas` devuelve siempre verdadero; `verificarSolicitudCodigo` no revisa el `UPDATE` | 630, 645, 681, 686, 711; 1027–1031; 391–402 | R6 |
| TD-03 | Cancelación de las solicitudes anteriores antes de terminar de validar | 414 | RE-02 |
| TD-04 | Estado compartido entre filas: `errorProceso` solo se limpia en `procesarRegistro`, así que un rechazo puede mostrar el motivo de otra fila | 413, 530–541 | RE-14 |
| TD-05 | Validación débil de las filas: cuotas, fechas y porcentajes de posgrado | 436–451, 805–810, 971, 999–1020 | RE-04, RE-17 |
| TD-06 | Valores vacíos que se guardan sin aviso: periodo y fechas de la facultad | 293–294, 858–877 | RE-05, RE-06 |
| TD-07 | Reglas fijas en el código y cambios que se activan comentando líneas | Mapa de exenciones 552–605; conceptos 676–708; estados 512–517; eventos 417 y `sql.class.php` 37; diferido "COVID" 909–964; porcentajes por defecto 1001–1020 | R9, R10 |
| TD-08 | Código muerto | `action.php`, `html.php`; 6 opciones de SQL sin uso (`code-structure.md`); métodos vacíos 144–149; `isUTF8` sin uso (202); ramas iguales del `if` de 866–877; columnas leídas y no usadas (`est_nro_iden`, `est_nombre`, `emb_valor_matricula`, `cra_abrev`, `cer_fecha`); `facultadCarrera` se consulta también en posgrado sin usarse (829) | R15 |
| TD-09 | Lógica de negocio mezclada con HTML (`echo`) | 79–142, 310–379, 1089–1136 | R17 |
| TD-10 | La IP del lote sale de cabeceras que el cliente controla | `funcionGeneral.class.php` 141–162 | RE-13 |
| TD-11 | Carga de archivos sin límite de tamaño, con permisos `0777` y sin límite de tiempo | `funcionGeneral.class.php` 102, 115, 120 | R4 |
| TD-12 | Firmas incoherentes: `verificarLote` declara 4 parámetros y se llama con 5; parámetros opcionales antes de obligatorios | `bloque.php` 65; 148, 213 | R13 |
| TD-13 | `error_log` con el texto SQL de cada consulta de porcentaje | `sql.class.php` 227 | — |
| TD-14 | Periodo calculado dos veces: `datosGenerales` lo lee para el lote y `periodoActual` lo reemplaza en cada fila | 251–252, 292–294 | — |
| TD-15 | Comentarios desactualizados: "postgrado 26" (son 29) y "recibos de reingreso" sin código | `bloque.php` 61–63; encabezado de `funcion.class.php` | R11, R12 |
| TD-16 | En `utils_oas`, `errorctrlPrueba` es copia idéntica de `errorctrl`, y `request.ExtractData` hace `panic` cuando `Success` es falso | `errorctrlPrueba/errorctrl.go`; `request/transaction_tools.go` 78–95 | No se replica |
| TD-17 | Módulo de notas de ARC: el nivel llega en `tipoUser` (44, 148, 531) y el usuario en `$_REQUEST['usuario']` cuando la sesión no lo trae (62, 217, 399, 513). Con `tipoUser=132` cualquier usuario obtiene los permisos de ARC | `admin_consultasCoordinador/funcion.class.php` | R3, RE-19 |
| TD-18 | Datos personales de los docentes (identificación, teléfono, celular y correos) en el HTML del control de notas | `admin_consultasCoordinador/funcion.class.php` 354, 626 | Ley 1581 |
| TD-19 | Código roto o sin uso en el módulo de notas: `registrarEstudiantes` no existe (189); `datosUsuario` no está en el catálogo SQL (698, 707); 3 consultas sin uso; una consulta escrita dentro de la vista (449–456); todos los usuarios usan la cuenta de Oracle `coordinador` (36) | `admin_consultasCoordinador/funcion.class.php` y `sql.class.php` | — |

| TD-20 | "Solicitados": SQL armado con valores de la petición (`carrera`, `estudiante`, `codGenerar_*`, `recGenerar_*`). Antes de generar no vuelve a comprobar que la solicitud sea de un proyecto del usuario; el propio código lo deja como pendiente (178). Usa `each()` y `money_format()`, que no existen desde PHP 8 | `admin_solicitudCoordinador/sql.class.php`; `admin_solicitudCoordinador/funcion.class.php` 125–163, 178, 898, 917 | R1, R3 |
| TD-21 | "Solicitados": calcula si el estudiante tiene deudas (`acdeudores`) pero no usa el resultado; `ema_imp_recibo` va siempre en 1 | `admin_solicitudCoordinador/funcion.class.php` 373–381; `sql.class.php` 409 | — |
| TD-22 | "Solicitados": en las cuotas 2 y 3, los conceptos distintos de la matrícula vuelven a ejecutar la última sentencia, porque `$cadena_sql` no se limpia; eso repite el `INSERT` anterior en Oracle. El total con otros conceptos solo suma el concepto de la segunda posición | `admin_solicitudCoordinador/funcion.class.php` 455, 462–474 | — |
| TD-23 | "Solicitados": la exención de la Secretaría de Educación se aplica dentro del ciclo de cuotas de posgrado, así que se acumula: la cuota 2 la recibe dos veces y la 3, tres | `admin_solicitudCoordinador/funcion.class.php` 236–238 | — |
| TD-24 | "Solicitados": valor bruto 0 en posgrado por créditos si la facultad no es 23, 24, 32, 33, 41, 42 o 101, si el nivel no es uno de los cuatro previstos o si `unidad` está vacía; valor negativo si las exenciones suman más de 100% | `admin_solicitudCoordinador/funcion.class.php` 196, 1260–1322 | RE-22, RE-23 |
| TD-25 | "Solicitados": 9 de sus 34 consultas no se usan; la búsqueda por estudiante usa las exenciones de la primera solicitud para todas (1138) y solo mira `est_diferido` para el número de cuotas (1162); la observación "EXONERACION 100% MATRICULA CERO" sale en los recibos de pregrado sin otra exención especial (393) | `admin_solicitudCoordinador/*` | RE-21, RE-25 |
## Patrones y antipatrones

- **Patrones que conviene conservar**:
  - El lote se registra antes de procesarlo, así que todo archivo cargado deja rastro (se conserva, P-9).
  - Las sentencias SQL están en un solo archivo, lo que facilitó este inventario.
  - El mapa columna → exención es explícito y fácil de pasar a parámetros (RF-09).
  - En `utils_oas`: filtros transversales para auditoría, cabeceras y trazas; sobre de respuesta único; credenciales en SSM.
- **Antipatrones**:
  - SQL concatenado (TD-01).
  - Escrituras relacionadas sin transacción y errores ignorados (TD-02).
  - Reglas en el código y cambios por comentarios (TD-07).
  - Estado mutable compartido entre filas (TD-04).
  - Lógica y presentación en la misma clase (TD-09).
  - Confiar en cabeceras del cliente para datos de auditoría (TD-10).
  - Permisos que llegan en la petición: `tipoUser` de `$_REQUEST` en `admin_consultasCoordinador/funcion.class.php` 44 (R3). Ese módulo es de ARC, así que el valor 132 da los permisos de ARC a quien lo envíe (TD-17, RE-19).

## Relación con la extensión de seguridad

Estos problemas son del sistema que se retira; esta etapa no lo modifica ni diseña nada nuevo, así que no son hallazgos bloqueantes de Reverse Engineering. Se listan para que Seguridad y las etapas de Construction verifiquen que el sistema nuevo no los repite.

| Regla | Problema en el sistema actual | Dónde lo resuelve el diseño aprobado |
|---|---|---|
| SECURITY-03 | Sin registro de aplicación; un `error_log` con SQL (TD-13) | AD-24 |
| SECURITY-04 | Sin cabeceras de seguridad; valores de `$_REQUEST` sin escapar en HTML (R2) | `middlewares/cabeceras_seguridad`; escape de Angular |
| SECURITY-05 | SQL concatenado; solo se revisa la extensión del archivo (TD-01, TD-11) | RNF-2; UC-01 paso 2 |
| SECURITY-08 | Autorización por nivel de sesión y por `tipoUser` del cliente (R3). En el módulo de notas de ARC, `tipoUser=132` da los permisos de ARC a cualquier usuario (TD-17); el módulo queda para la Fase 2 (C5) y sigue en producción mientras corra el PHP | AD-09; UC-03. El riesgo del PHP se informa a Seguridad |
| SECURITY-09 | Archivos con `0777`; PHP sin soporte (TD-11, R13) | S3 privado (RF-01); AD-27 |
| SECURITY-10 | Sin manifiesto de dependencias; lector de Excel sin mantenimiento (R14) | AD-26 |
| SECURITY-12 | Credenciales en `$configuracion`, fuera del repositorio (R5) | SSM (RNF-2) |
| SECURITY-13 | Cancelaciones sin registro de quién ni cuándo | AD-25 |
| SECURITY-15 | Errores ignorados: una solicitud puede quedar incompleta y contarse como procesada (TD-02) | RF-10; `middlewares/errores` |
| SECURITY-03 y SECURITY-13 | IP falseable en `solicitudLote` (TD-10) | AD-29 (2026-11-25): `X-Forwarded-For` con la entrada del último proxy de confianza; falta D13 |
