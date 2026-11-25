# Boceto visual — Preguntas (5)

Progreso: [□□□□□] 0/5  (~12 min restantes)

Etapa opcional de Discovery que se había omitido. Se hace el 2026-11-25 a pedido del usuario. Produce un recorrido del usuario (diagrama Mermaid) y maquetas HTML de las pantallas principales de `recibos_mf`. Las maquetas no funcionan: solo sirven para revisar la idea antes de construir. Se toman de la Visión y de las historias aprobadas, con los cambios hasta el 2026-11-25 (por ejemplo, el reporte de los estudiantes que se subieron y los que no).

## V1) ¿Qué persona sigue el recorrido?

A) Profesional de Admisiones, Registro y Control (ARC), la única persona que usa el sistema. Recomendada

B) Estudiante. No usa el sistema; solo recibe el recibo que genera "Solicitados"

X) Otra (descríbela después de [Answer]:)

[Answer]:

## V2) ¿Qué tan completo debe ser el recorrido?

A) Solo el camino feliz, hasta 5 pantallas: entrar al módulo, cargar el lote, ver el reporte y consultar el historial (~10 min)

B) Camino feliz más 1 o 2 caminos alternos, hasta 8 pantallas: por ejemplo, lote rechazado por formato y archivo no permitido (~14 min). Recomendada, porque el reporte de los que no se subieron es central para ARC

X) Personalizado (descríbelo después de [Answer]:)

[Answer]:

## V3) ¿Qué estilo visual deben tener las maquetas?

A) Wireframe: cajas y etiquetas en escala de grises; es el que menos se presta a malentendidos

B) Lo-fi con estilos neutros: estilos por defecto de Tailwind, sin colores de marca. Recomendada: la aplicación real toma el tema del root institucional, cuyos colores no están en el workspace

C) Con marca: indica 2 o 3 colores (hex) y, si quieres, la ruta o URL del logo

[Answer]:

## V4) ¿Qué datos de ejemplo deben aparecer?

A) Realistas, tomados de la Visión y las historias (nombres de plantillas, motivos de rechazo, rol ARC), con códigos de estudiante y documentos inventados. Ningún dato real de estudiantes (Ley 1581). Recomendada

B) Marcadores genéricos (lorem ipsum); es lo más seguro si algo de la Visión es sensible

[Answer]:

## V5) ¿Para qué pantalla se diseñan las maquetas?

A) Escritorio (1280×800). Recomendada: ARC trabaja desde la oficina

B) Móvil (390×844)

C) Ambas: se generan las mismas pantallas dos veces, una por tamaño

[Answer]:

---

Responde en el chat con el formato "v1 a, v2 b, v3 b, v4 a, v5 a", o llena los `[Answer]:` de este archivo y escribe `listo`.
