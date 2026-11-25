# Análisis del sistema existente (contexto para la entrevista técnica)

- Fecha: 2026-11-23T20:35:00Z
- Fuente: `codigo-fuente/` (clon local de https://github.com/braianestiven/recibos.git, rama `main`, 1 commit: `a247a67 Commit inicial del proyecto`)
- Alcance del análisis: lectura estática únicamente. No se modificó, ejecutó ni desplegó nada.
- Uso: este archivo alimenta las respuestas sugeridas de la entrevista técnica (TB1–TB3 y T5, T8, T13, T14, T17, T20). No es un entregable final.

---

## 1. Acceso y estructura

El repositorio contiene **13 archivos PHP (~143 KB)**. Todos están en `codigo-fuente/weboffice/`:

```
weboffice/
├── clase/
│   └── funcionGeneral.class.php          (clase base: SQL, sesión, conexión, carga de archivos)
└── bloque/
    ├── registro_lote_recibo/             ← núcleo de "recibos"
    │   ├── bloque.php                    (controlador: html() / action())
    │   ├── funcion.class.php             (lógica de negocio + HTML, 41 KB)
    │   ├── sql.class.php                 (constructor de sentencias SQL)
    │   ├── action.php                    (versión 2008, procedural; no la incluye bloque.php)
    │   ├── html.php                      (formulario antiguo; no lo incluye bloque.php)
    │   └── index.php                     (redirección a ../index.php)
    ├── admin_consultasCoordinador/       (consultas académicas: control de notas, histórico)
    │   ├── bloque.php · funcion.class.php · sql.class.php · index.php
    └── admin_historicoPorEstudiante/     (solo un formulario que envía a "admin_generados")
        ├── bloque.php · index.php
```

**El repositorio es un extracto parcial.** El código depende de archivos del framework que **no están** en el repo:

- Núcleo: `index.php` raíz (enrutador), `bloque.class.php`, `sql.class.php` (base), `dbConexion.class.php`, `sesion.class.php`, `datosGenerales.class.php`, `datosSolicitud.class.php`
- Utilidades: `subir_archivo.class.php`, `reader.class.php` (Spreadsheet_Excel_Reader), `encriptar.class.php`, `validacion_usu_wo.class.php`, `calendario.class.php`, `alerta.class.php`, `html.class.php`, `navegacion.class.php`
- Presentación: `estilo/basico/tema.php`, `estilo.php`, `funciones.js`
- El arreglo de configuración `$configuracion` (rutas, host, prefijo de tablas, credenciales)
- Los módulos relacionados `admin_generados` y la impresión del recibo. "Solicitados" (`admin_solicitudCoordinador`) se agregó al workspace el 2026-11-25 y se analizó en Reverse Engineering (RE-20 a RE-26 en `aidlc-docs/inception/reverse-engineering/story-code-traceability.md`)

No hay `composer.json`, pruebas, configuración, esquema de BD, documentación ni historial de cambios.

## 2. Lenguajes, frameworks y dependencias

| Elemento | Hallazgo |
|---|---|
| Lenguaje | PHP mixto (procedural + clases), con HTML embebido y `echo` directo |
| Versión PHP probable | 5.x – 7.x. Usa etiquetas cortas `<?`, `utf8_encode/utf8_decode` (obsoletas en 8.2) y parámetros opcionales antes de obligatorios (obsoleto en 8.0) |
| Framework | Framework propio de la Universidad Distrital ("weboffice" / patrón de *bloques*, autor Paulo César Coronado, 2005–2009) |
| Lectura de Excel | `Spreadsheet_Excel_Reader` (php-excel-reader): solo `.xls` binario (BIFF), sin mantenimiento |
| Front-end | HTML con tablas, CSS del tema `basico` y JavaScript (`funciones.js`, `control_vacio`) |
| Gestor de dependencias | Ninguno |

## 3. Arquitectura actual

- **Monolito web con renderizado en el servidor.** Las páginas se enrutan con `index.php?pagina=...` y los parámetros van cifrados en la URL (`encriptar::codificar_url`).
- **Patrón "bloque":** cada módulo tiene `bloque.php` (controlador que despacha a `html()` o `action()` según `$_REQUEST`), `funcion.class.php` (lógica + vista) y `sql.class.php` (un `switch` que arma cadenas SQL).
- **Protección de inclusión:** `if(!isset($GLOBALS["autorizado"]))` impide el acceso directo a los archivos.
- **Sesión** guardada en la BD MySQL del framework (`rescatarValorSesion`: `id_usuario`, `identificacion`, `nivelUsuario`).
- **Autorización por nivel**, con una cuenta de Oracle distinta para cada perfil:

| Nivel | Perfil | Conexión Oracle | Alcance |
|---|---|---|---|
| 4 | Coordinador | `coordinador` | Carreras donde es coordinador (`ACCRA.CRA_EMP_NRO_IDEN`) |
| 110 | Asistente | `asistente` | Proyectos asignados (`validarUsu::consultarProyectosAsistente`) |
| 114 | Secretario | `secretario` | Proyectos asignados |
| 132 | Admisiones, Registro y Control ("ORC" en el código; confirmado por el usuario el 2026-11-25) | `coordinador` | Todas las carreras activas |

### Componente principal: `registro_lote_recibo` (carga masiva de solicitudes de recibo de pago)

Flujo:
1. El usuario sube un `.xls` y el archivo se guarda en `documento/solicitudes/`. Se registra en `solicitudLote` con el usuario, el nombre, la IP y la fecha.
2. Se valida el número de columnas (14 o 29) y se identifica la plantilla por el texto de la celda A1:
   - `PLANTILLA GENERAL PREGRADOS` → tipo 1, datos desde la fila 4
   - `PLANTILLA GENERAL POSTGRADOS CREDITOS` → tipo 2, datos desde la fila 5
   - `PLANTILLA GENERAL POSTGRADOS SALARIOS MINIMOS LEGALES` → tipo 3, datos desde la fila 5
3. Por cada código de estudiante:
   - Se valida el estado (`V, J, T, A, Q, B`) y que la carrera pertenezca al usuario.
   - Si el evento 82 (terminación de materias) está activo, solo se aceptan estudiantes en estado `T` o `H`.
   - Se cancelan las solicitudes anteriores sin imprimir (`estado 0 → 2`).
   - Se insertan registros en `solicitudRecibo`, `solicitudCuota`, `solicitudExencion` y `solicitudConcepto`.
4. Reglas de cuotas:
   - **Pregrado:** si el estudiante tiene diferido aprobado, se generan 3 cuotas con porcentaje fijado en 0% (comentario "No se cobra segunda cuota por COVID"). Si no, 1 cuota al 100%. Las fechas salen de `fechaPagoFacultad` (MySQL) según la facultad.
   - **Posgrado:** fechas y porcentajes vienen en la plantilla. Los porcentajes por defecto son 100 / 60-40 / 40-30-30. La fecha extraordinaria es la ordinaria + 8 días, saltando festivos.
5. Exenciones: hay un mapeo fijo de columna de plantilla → `id_exencion`. El certificado electoral se agrega automáticamente desde `ACCERELECTORAL` si la suma de exenciones es ≤ 90%.
6. Conceptos: siempre se graba el concepto 1 (matrícula), el 19 solo en pregrado, y los conceptos 2, 3 y 4 según las columnas de la plantilla.
7. El resultado se muestra en HTML (códigos procesados y rechazados). **La generación o impresión del recibo ocurre en otro módulo** ("Solicitados") que no está en el repo.

### Otros componentes

- `admin_consultasCoordinador`: listado de proyectos, control de notas parciales, histórico de notas y selección de periodo (solo Oracle). **No está relacionado con recibos.** *Corrección del 2026-11-25:* es el módulo de notas de Admisiones, Registro y Control (nivel 132, "ORC"); el nombre dice "coordinador" por error. Detalle en `aidlc-docs/inception/reverse-engineering/story-code-traceability.md` (RE-18, RE-19).
- `admin_historicoPorEstudiante`: formulario que consulta los recibos generados por estudiante a través del módulo `admin_generados`, que no está en el repo.

## 4. Bases de datos, servicios e integraciones

**Bases de datos (dos motores):**

| Motor | Uso | Objetos identificados |
|---|---|---|
| **MySQL** (BD del framework, tablas con `$configuracion["prefijo"]`) | Sesión, solicitudes, parámetros | `solicitudLote`, `solicitudRecibo`, `solicitudCuota`, `solicitudExencion`, `solicitudConcepto`, `exencion`, `fechaPagoFacultad` (vía `datosSolicitud`), tabla de sesiones |
| **Oracle** (sistema académico, esquema `mntac`) | Datos académicos y financieros de solo lectura | Tablas: `ACEST`, `ACCRA`, `ACASPERI`, `ACASPERIEVENTOS`, `ACCALEVENTOS`, `ACCERELECTORAL`, `ACRANGOSPAGO`, `GEDEP`, `PEEMP`, `ACDOCENTE`, `ACASI`, `ACCARGAS`, `ACCURSOS`, `ACHORARIOS`, `GEUSUCRA`. Vistas: `V_ACESTMATBRUTO`, `V_ACINSNOTPAR`, `V_ACINSNOTPAR_ANTERIOR`. Funciones: `fua_verifica_evento`, `mntac.fua_verifica_diferido` |

**Servicios web e integraciones:** el código **no tiene** llamadas HTTP, SOAP, REST, colas ni correo. Las integraciones que se ven son:
- La BD Oracle académica (integración a nivel de datos, con funciones PL/SQL).
- El sistema de archivos del servidor (`documento/solicitudes/`).
- El portal Cóndor (`condor.udistrital.edu.co`), al que el código solo enlaza; la sesión probablemente viene de ahí.
- Los módulos posteriores de generación e impresión del recibo, y posiblemente la integración con bancos o recaudo, que no están en el repo.

## 5. Riesgos y restricciones técnicas para la migración

**Seguridad**
- R1. **Inyección SQL:** todas las sentencias se arman concatenando texto, y los valores numéricos van sin comillas (`est_cod=` + celda de Excel). No se sabe qué hace `verificar_variables`.
- R2. **XSS:** valores de `$_REQUEST` (`tipoUser`, `nivel`, `nomcra`) se escriben en el HTML sin escaparlos.
- R3. **Autorización controlable por el cliente:** en `admin_consultasCoordinador`, `tipoUser=132` viene de `$_REQUEST` y da acceso a todas las carreras. Como 132 es el nivel de Admisiones, Registro y Control (2026-11-25), cualquier usuario que envíe ese valor obtiene los permisos de ARC en ese módulo.
- R4. **Carga de archivos:** permisos `0777`, solo se valida la extensión y se usa `set_time_limit(0)`.
- R5. Se usan cuatro cuentas Oracle distintas; no se sabe dónde están las credenciales.

**Integridad de datos**
- R6. **No hay transacciones.** Las inserciones de solicitud, cuotas, exenciones y conceptos son independientes, así que un fallo a mitad de camino deja datos inconsistentes. `guardarCuotas` siempre devuelve `true`, y los resultados se acumulan con `.=`, que concatena texto en lugar de evaluar éxito o fallo.
- R7. Las fechas se guardan como timestamps Unix en texto y se interpretan con `strtotime(m/d/Y)`.
- R8. La lógica de negocio cruza dos motores (Oracle + MySQL) sin consistencia transaccional.

**Reglas de negocio implícitas**
- R9. Hay muchas reglas fijadas en el código: IDs de conceptos (1, 2, 3, 4, 19), el mapa columna → exención, eventos (80, 82), niveles de usuario, estados de estudiante y porcentajes por defecto.
- R10. Hay cambios temporales que se activan o desactivan comentando código ("2020-1", "COVID", "2014-3"). Hoy, el diferido de pregrado genera cuotas al 0%, y no está claro si eso es intencional.
- R11. Las plantillas Excel tienen un formato posicional rígido. El comentario dice "postgrado 26 columnas" pero el código valida 29.
- R12. El encabezado de `funcion.class.php` menciona "2025-12-17 … recibos de reingreso por plantilla C-045558", pero **no hay código de reingreso** en el repo. Puede faltar código o haber otra rama.

**Deuda técnica y plataforma**
- R13. Partes de PHP obsoletas o incompatibles con PHP 8: etiquetas cortas, `utf8_encode`, firmas inválidas, `$this` usado fuera de una clase en `html.php`, y `verificarLote` declarada con 4 parámetros pero llamada con 5.
- R14. `Spreadsheet_Excel_Reader` solo lee `.xls`; los `.xlsx` no son compatibles.
- R15. El código muerto o duplicado (`action.php`, `html.php`) tiene reglas distintas: año 2008 fijo y conceptos 42/43.
- R16. **El repo no se puede ejecutar ni probar** porque falta el núcleo del framework. No hay pruebas, esquema ni datos de ejemplo. Eso limita la ingeniería inversa y la validación de equivalencia funcional.
- R17. La lógica está mezclada con la presentación en `funcion.class.php` (echo de HTML).
- R18. Probable codificación ISO-8859-1 y uso de entidades HTML (`&aacute;`).

## 6. Respuestas técnicas sugeridas a partir del código (por confirmar)

| Pregunta | Borrador desde el código |
|---|---|
| TB1 Inventario actual | PHP 5/7 + framework propio "weboffice" (bloques), MySQL (framework) + Oracle (académico, `mntac`), php-excel-reader (.xls), HTML/CSS/JS en el servidor, sesión en BD, carga de archivos local |
| TB2 Lo que no debe cambiar | Por confirmar: esquema Oracle académico (solo lectura), tablas `solicitud*` si otros módulos las consumen (impresión de recibos), formato de las 3 plantillas, reglas de cuotas, exenciones y conceptos |
| TB3 Patrones prohibidos | Por confirmar: SQL concatenado, autorización por parámetros del cliente, archivos con 0777, lógica mezclada con HTML |
| T5 / T8 Lenguaje y framework | Origen: PHP. Destino: **pendiente** |
| T13 Estilo de API | Hoy no hay API (solo formularios POST). Destino: **pendiente** |
| T14 Datos | Hoy: relacional, dos motores. Destino: **pendiente** |
| T17 Autenticación | Hoy: sesión del framework en MySQL con niveles 4/110/114/132. Destino: **pendiente** |
| T20 Secretos | Hoy: desconocido (probablemente en `$configuracion`). Destino: **pendiente** |
| T22 Pruebas | Hoy: ninguna |
