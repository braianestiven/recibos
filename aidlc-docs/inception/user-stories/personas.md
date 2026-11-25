# Personas — Migración del módulo de recibos por lote

Fuente: `vision-document.md` (Usuarios y partes interesadas), `requirements.md` §3.
Decisión de planificación Q4-a: una persona principal y actores secundarios.
Actualizado el 2026-11-25: ARC corresponde al nivel 132 de weboffice (RE-19).

---

## Persona principal: Profesional de Admisiones, Registro y Control (ARC)

| Atributo | Detalle |
|---|---|
| Rol en el sistema | Rol único **Admisiones, Registro y Control**, registrado en `configuracion_cliente` |
| Corresponde a | El nivel 132 de weboffice ("ORC" en el código; confirmado el 2026-11-25, RE-19). Además absorbe los perfiles coordinador (4), asistente (110) y secretario (114), cuyas tareas ya hace hoy ARC |
| Alcance de datos | Todos los proyectos curriculares (pregrado y posgrado); sin filtro por carrera asignada |
| Frecuencia de uso | Concentrada al inicio de cada periodo académico, cuando se generan las solicitudes de matrícula; cargas puntuales de corrección durante el periodo |
| Herramientas actuales | weboffice (PHP 5): carga de lotes (`registro_lote_recibo`) y consultas de notas (`admin_consultasCoordinador`, mal nombrado "coordinador" y fuera del alcance de este proyecto); plantillas Excel `.xls` oficiales |
| Objetivo | Generar en una sola carga las solicitudes de recibo correctas para un grupo de estudiantes (hasta 1000 por lote) |
| Necesidades | Saber de inmediato qué estudiantes se procesaron y cuáles se rechazaron, y por qué; corregir y volver a cargar solo los rechazados; confiar en que una carga fallida no deja solicitudes a medias |
| Dolores actuales | Las reglas cambian editando código; cada periodo depende de las personas que conocen el código; cargas interrumpidas dejan solicitudes incompletas |
| Criterio de éxito personal | Las solicitudes que genera el sistema nuevo coinciden con las que generaría el actual (salvo las tres reglas acordadas) y "Solicitados" las imprime sin ajustes |

---

## Actores secundarios (no son usuarios del sistema nuevo)

### Estudiante (usuario indirecto)
- No usa `recibos_service` ni `recibos_mf`.
- Recibe el recibo que produce el módulo actual "Solicitados" a partir de las solicitudes que escribe este sistema.
- Le importa que valor, cuotas, exenciones y fechas sean correctos. Sus datos personales están protegidos por la Ley 1581 de 2012.

### Seguridad
- No opera el módulo. Consume los logs de auditoría y ejecuta la revisión de Seguridad en el ambiente de pruebas (test), fuera del ciclo de desarrollo.
- Le importa poder responder quién cargó qué archivo, cuándo y desde qué IP, sin que los logs contengan datos personales.

### Sistemas externos
Oracle académico (solo lectura), MySQL `solicitud*` (lectura y escritura), S3 privado, WSO2 IS/AM, servicio "parametros" y módulo "Solicitados". Aparecen en los criterios de aceptación, no como personas.
