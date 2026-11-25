# Boceto visual — Historial de respuestas

## Lote 1 (V1 a V5) — 2026-11-25

Respuesta del usuario: "v1 a,  v4, v5, para las demás mira el ejemplo de este cliente de otro sistema en la oficina para que lo tomes de guia visual: https://github.com/udistrital/sga_cliente_admisiones_mf"

| Pregunta | Respuesta | Cómo se aplica |
|---|---|---|
| V1 Persona | A | Profesional de Admisiones, Registro y Control (ARC) |
| V2 Profundidad | Sin letra; se usa la recomendada (B) | Camino feliz más dos caminos alternos: plantilla con formato inválido y archivo no permitido. Seis pantallas |
| V3 Estilo | Guía visual: `sga_cliente_admisiones_mf` (equivale a C, con marca) | Colores, tipografía y componentes del cliente de referencia (ver abajo) |
| V4 Datos de ejemplo | "v4" sin letra; se toma la recomendada (A) | Datos realistas de la Visión, las historias y `api-contract.md`, con códigos de estudiante y documentos inventados |
| V5 Pantalla | "v5" sin letra; se toma la recomendada (A) | Escritorio, 1280 × 800 |

Supuesto: en "v1 a, v4, v5" se leyó que V4 y V5 toman la opción recomendada. Si no era así, se corrige en la compuerta del boceto.

## Guía visual tomada de `sga_cliente_admisiones_mf`

Fuente: clon de solo lectura de https://github.com/udistrital/sga_cliente_admisiones_mf, rama `develop`, commit `5a4dc4f` (2026-11-23). Solo se tomaron estilos y patrones de pantalla, no funciones.

| Elemento | Valor en el cliente de referencia | Archivo |
|---|---|---|
| Color primario | `#03678f` (escala de `#e1edf2` a `#013960`) | `src/assets/styles/sga-theme-angular-material.scss` |
| Color de acento | `#145a95` | ídem; también es el botón de confirmación de las alertas |
| Color de advertencia | `#d9c53a` | ídem |
| Tipografía | "Open Sans" | ídem |
| Botón principal | Fondo `#03678f`, texto blanco, borde redondeado de 5 px, relleno 10 × 20 px | `listado-oficializados.component.scss` (`.boton-primary`) |
| Procesos en pasos | `mat-stepper` vertical | `cargue-snp.component.html`, `listado-historico.component.html` |
| Resumen | Fila de título en `#03678f` con texto blanco y tres casillas blancas con totales | `cargue-snp.component.html` y `.ts` (`tiles`) |
| Tablas | `mat-table` con filas alternas `#f7f9fc`, fila resaltada `#edf1f7`, bordes `#edf1f7`, filtro arriba y paginador `5, 10, 25, 100` | `cargue-snp.component.scss` |
| Estado por fila | Íconos `done` en verde y `close` en rojo | `cargue-snp.component.html` |
| Espera | Capa gris semitransparente con `mat-spinner` | `.loader-div` en varios componentes |
| Mensajes | SweetAlert2 con fondo `#f0f4f8`, título `#282828` y botón `#145a95` | `src/assets/styles/sga-sweetalert2/sga-sweetalert2.scss` |
| Textos | En español, con `ngx-translate`: "Cargar archivo", "Consultar", "Filtro", "Cargando..." | `src/assets/i18n/es.json` |

Ajustes para las maquetas:
- La fuente no se descarga (regla de maquetas autocontenidas). Se pide "Open Sans" y, si no está instalada, se usa la del sistema.
- El rojo de los textos se oscurece a `#b91c1c` para cumplir el contraste AA.
- El microcliente real se muestra dentro del root y el core institucionales, que ponen el encabezado y el menú; el repositorio de referencia no los trae. Las maquetas dibujan un encabezado y un menú genéricos con el nombre de la Universidad.

Dato para U2 NFR Requirements (OQ-T-1): el `package.json` del cliente de referencia usa Angular y Angular Material 21.2, TypeScript 5.9, single-spa 6.0.3 y single-spa-angular 9. El README del mismo repositorio dice Angular 16, así que está desactualizado.

## Lote 2 — Correcciones y aprobación (2026-11-25)

Respuesta del usuario:

```text
V2 b: el camino normal y dos alternos.  
V4 a: datos realistas, con códigos, documentos e IP inventados.  
V5 c: escritorio y movil., aprobar y continuar, pero hazlos mas bonitos
```

| Pregunta | Antes | Ahora |
|---|---|---|
| V2 | B (recomendada, sin letra) | B, confirmada |
| V4 | A (recomendada, sin letra) | A, confirmada |
| V5 | A (recomendada, sin letra) | **C**: escritorio y móvil |

Cambios pedidos: "hazlos más bonitos". Se rehicieron las maquetas con la misma guía visual (`sga_cliente_admisiones_mf`):
- Encabezado con degradado institucional, insignia "UD" y chip del usuario; menú lateral con íconos y opción activa marcada.
- Tarjetas redondeadas con sombra suave; íconos SVG dentro del archivo (sin imágenes remotas).
- Carga con zona para arrastrar la plantilla, botón "Seleccionar archivo", archivo seleccionado de ejemplo, plantillas vigentes y recomendaciones "Antes de cargar".
- Reporte con indicadores (total, se subieron, no se subieron), barra de proporción, etiquetas de motivo y tablas con filas alternas.
- Avisos de error como diálogos en escritorio y como hojas inferiores en móvil.
- Versión móvil dentro de un marco de teléfono de 390 × 844, con menú inferior y listas en lugar de tablas.

Estructura: `mockups/index.html` enlaza a `mockups/desktop/index.html` y a `mockups/mobile/index.html`; cada carpeta tiene las 6 pantallas. Se borraron las maquetas anteriores de `mockups/` (las de un solo tamaño).

Aprobación: "aprobar y continuar" con estos cambios. El boceto queda aprobado al aplicarlos.

