# Entrevista de Negocio — Sección 7 de 7: Sistema existente

Progreso: █████████░ 18/20 preguntas · ~3 min restantes

Las preguntas anteriores (Q1–Q18) ✅ están guardadas en `vision-answers-history.md`; no se pierde nada.
Este archivo muestra solo las preguntas activas.

---

### QB1: Describe en un párrafo el estado actual.

**Sugerencia:** "Hoy, Admisiones, Registro y Control carga en weboffice (PHP 5, framework propio de la Universidad) una plantilla Excel .xls de pregrado, posgrado por créditos o posgrado SMLV con los códigos de los estudiantes. El módulo `registro_lote_recibo` valida cada estudiante contra el sistema académico en Oracle (estado, carrera, calendario), cancela solicitudes previas sin imprimir y crea en MySQL las solicitudes de recibo con sus cuotas, exenciones y conceptos. Después, el módulo "Solicitados" lee esas solicitudes junto con tablas de Oracle (`acasperi`, `acest`, `acestmat`, `acvlrscs`) para generar e imprimir los recibos. Las reglas están escritas en el código y el sistema no tiene pruebas ni API."

[Answer]:

---

### QB2: ¿Qué NO debe cambiar?

Es un límite estricto para AI-DLC.

**Sugerencia:**
- Esquema y datos del sistema académico Oracle: acceso de **solo lectura** (`ACEST`, `ACCRA`, `ACASPERI`, `ACASPERIEVENTOS`, `V_ACESTMATBRUTO`, `ACCERELECTORAL`, `ACESTMAT`, `ACVLRSCS`, funciones `fua_verifica_evento` y `mntac.fua_verifica_diferido`).
- El módulo "Solicitados" y su forma de leer las solicitudes: el sistema nuevo no lo modifica.
- La estructura y los estados de `solicitudrecibo` que usa "Solicitados" (0 = sin imprimir, 2 = cancelada; otros por confirmar).
- El sistema PHP actual sigue funcionando sin cambios mientras se ejecutan en paralelo (2027-1).
- El modelo de datos aprobado por el comité, la base creada por los DBA y el registro existente en WSO2.
- Las reglas de cálculo vigentes (cuotas de posgrado, fechas extraordinarias +8 días sin festivos, exenciones y conceptos), salvo los cambios ya acordados: sin reingreso, sin diferido en pregrado y sin leer la columna "Seguro" como cuota.

**Pregunta clave sobre el funcionamiento en paralelo:** en 2027-1, ¿el sistema nuevo escribe en la misma tabla MySQL `solicitudrecibo` que lee "Solicitados", o escribe en la base nueva aprobada y algo sincroniza hacia "Solicitados"?

a) Escribe en el mismo `solicitudrecibo` de MySQL
b) Escribe en la base nueva y se sincroniza
c) Solo se comparan resultados; los recibos reales los sigue generando el PHP
x) Otro

[Answer]:
