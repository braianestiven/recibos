# Entrevista Técnica — Sección 9 de 9: Sistema existente

Progreso: ████████░░ 29/33 preguntas · ~4 min restantes

Las preguntas anteriores (T1–T29) ✅ están guardadas en `tech-env-answers-history.md`; no se pierde nada.
Este archivo muestra solo las preguntas activas.

---

### TB1: ¿Qué hay hoy en el stack existente?

**Sugerencia:**

| Lenguaje / framework | Uso actual | Dirección |
|---|---|---|
| PHP 5 + framework propio "weboffice" (bloques) | Módulo `registro_lote_recibo` y consultas | Retirar (reemplazo tras las pruebas en paralelo) |
| php-excel-reader (`Spreadsheet_Excel_Reader`) | Lectura de plantillas `.xls` | Retirar → xlrd |
| HTML con tablas + `funciones.js` | Interfaz del módulo | Retirar → Angular / single-spa (`recibos_mf`) |
| Sesión del framework en MySQL, niveles 4/110/114/132 | Autenticación y permisos | Retirar → WSO2 + rol único |
| Oracle académico (esquema `mntac`) | Datos académicos y funciones PL/SQL | **Mantener** (solo lectura) |
| MySQL (`solicitudRecibo`, `solicitudCuota`, `solicitudExencion`, `solicitudConcepto`, `solicitudLote`, `exencion`, `fechaPagoFacultad`) | Solicitudes y parámetros | **Mantener** |
| Módulo "Solicitados" (fuera del repo) | Generación e impresión de recibos | **Mantener** sin cambios |
| Carpeta local `documento/solicitudes/` | Archivos cargados | Retirar → S3 privado |

[Answer]:

---

### TB2: ¿Qué servicios, esquemas, contratos o configuraciones NO se tocan?

**Sugerencia (detalle técnico de QB2):**
- Esquema y datos de Oracle académico: `ACEST`, `ACCRA`, `ACASPERI`, `ACASPERIEVENTOS`, `ACCALEVENTOS`, `ACCERELECTORAL`, `ACRANGOSPAGO`, `V_ACESTMATBRUTO`, `ACESTMAT`, `ACVLRSCS` y funciones `fua_verifica_evento`, `mntac.fua_verifica_diferido`. Solo lectura.
- Estructura de las tablas MySQL `solicitud*`, `exencion` y `fechaPagoFacultad`, **incluidos los formatos que lee "Solicitados"**: fechas como timestamp Unix, porcentajes 0–100, `estado` (0 = sin imprimir, 2 = cancelada) y los IDs actuales de conceptos y exenciones.
- El módulo "Solicitados" y el sistema PHP actual durante las pruebas en paralelo.
- Registro existente en WSO2 y modelo de datos aprobado.

[Answer]:

---

### TB3: ¿Qué patrones del sistema actual NO deben repetirse?

a) Escribiré una lista · b) Ninguno además de T7/T10 · x) Otro

**Sugerencia:** a
- SQL armado por concatenación (`sql.class.php`).
- Permisos o roles tomados de parámetros del cliente (`$_REQUEST['tipoUser']`).
- Lógica de negocio mezclada con HTML (`echo` en `funcion.class.php`).
- Reglas que se activan o desactivan comentando código (cuotas "COVID", "2020-1").
- IDs de conceptos, exenciones, eventos y estados fijos en el código (deben ir en parámetros).
- Varias escrituras relacionadas sin transacción.
- Archivos con permisos `0777` en disco local.
- Configuración global con credenciales (`$configuracion`).
- Parámetros cifrados en la URL como mecanismo de seguridad (`encriptar::codificar_url`).
- Copias duplicadas de la lógica (`action.php` vs `funcion.class.php`).

Excepción: los **formatos de datos** de las tablas existentes (timestamp Unix, porcentaje 0–100) se mantienen porque los lee "Solicitados" (TB2).

[Answer]:

---

### TB4: ¿De dónde salen los ejemplos de código?

a) Archivos reales del repositorio · b) Fragmentos pegados · c) Mezcla · x) Otro

**Sugerencia:** a — Rutas reales de `codigo-fuente/lineamientos_oas/` y `codigo-fuente/utils_oas/` (T26, T27, T29). El código PHP de `codigo-fuente/weboffice/` sirve como **referencia de reglas de negocio**, no de estilo.

[Answer]:
