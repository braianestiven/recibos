# Activación de las extensiones de AI-DLC

Estas preguntas pertenecen a Requirements Analysis (paso 5.1 de `aws-aidlc-rule-details/inception/requirements-analysis.md`). No se hicieron en ese momento porque las reglas de AI-DLC no estaban en el workspace; aparecieron el 2026-11-24, durante Units Generation.

Mientras no se decidan, el workflow aplica las tres extensiones por defecto (`.kiro/steering/core-workflow.md`, "Default to enforced if no configuration exists"). Se deciden antes de cerrar Units Generation. Las respuestas se registran en `aidlc-docs/aidlc-state.md`, sección `## Extension Configuration`, y solo entonces se cargan las reglas completas de las extensiones activadas.

Las preguntas se hacen en el chat y se registran aquí.

## Question 1 — Extensión de seguridad
¿Se aplican las reglas de la extensión de seguridad como restricciones bloqueantes?

A) Sí — aplicar todas las reglas SECURITY como restricciones bloqueantes (recomendado para aplicaciones de producción)

B) No — omitir todas las reglas SECURITY (para pruebas de concepto, prototipos y proyectos experimentales)

X) Other (please describe after [Answer]: tag below)

**Recomendación:** A. La revisión de Seguridad en test puede bloquear el paso a producción, y la mayoría de estas reglas ya están en los requisitos: cabeceras, validación de entradas, mínimo privilegio, registros, cadena de suministro y manejo de excepciones. Las reglas de red y de intermediarios (por ejemplo SECURITY-02 y SECURITY-07) recaen en el grupo de infraestructura; se le entregan como requisitos en Infrastructure Design.

[Answer]: A (usuario, 2026-11-24)

## Question 2 — Extensión de resiliencia
¿Se aplica la línea base de resiliencia a este proyecto?

**Qué es.** Un conjunto de buenas prácticas de diseño para sistemas resilientes, tomadas del pilar de confiabilidad del AWS Well-Architected Framework y de guías de revisión de resiliencia. Orienta requisitos, diseño y código hacia tolerancia a fallos, alta disponibilidad, observabilidad y recuperación, en 15 áreas. Incluye decisiones que el usuario debe tomar, como los objetivos de RTO y RPO, la gestión de cambios, el despliegue y la reversión.

**Qué no es.** No deja la carga lista para producción ni certifica o garantiza disponibilidad, RTO o RPO. Es un primer borrador de la postura de resiliencia, que se valida y se refuerza; no reemplaza una revisión formal de AWS Well-Architected del sistema construido.

A) Sí — aplicar la línea base como buenas prácticas y guía de diseño (recomendado para cargas críticas del negocio, como punto de partida que se valida y se refuerza antes de salir a producción)

B) No — omitir la línea base (para pruebas de concepto, prototipos y proyectos experimentales donde importa más iterar rápido que la confiabilidad)

X) Other (please describe after [Answer]: tag below)

**Recomendación:** B. Esta versión es una prueba de concepto para 2027-1 que se despliega en test. La infraestructura (ECS, balanceador, alta disponibilidad, recuperación) la administra el grupo de infraestructura, y no hay CDK ni Terraform en el alcance. Lo que depende del código ya está en el diseño: transacción por estudiante, health checks y errores claros cuando una dependencia falla. Se puede activar más adelante, antes del paso a producción.

[Answer]: B (usuario, 2026-11-24)

## Question 3 — Pruebas basadas en propiedades
¿Se aplican las reglas de pruebas basadas en propiedades (PBT)?

A) Sí — aplicar todas las reglas PBT como restricciones bloqueantes (recomendado para proyectos con lógica de negocio, transformaciones de datos, serialización o componentes con estado)

B) Parcial — aplicar las reglas PBT solo a funciones puras y a conversiones de ida y vuelta (para proyectos con complejidad algorítmica limitada)

C) No — omitir todas las reglas PBT (para aplicaciones CRUD simples, proyectos solo de interfaz o capas delgadas de integración sin lógica de negocio significativa)

X) Other (please describe after [Answer]: tag below)

**Recomendación:** B. Las reglas de cálculo de `app/domain/` son funciones puras con propiedades claras: los porcentajes de las cuotas suman 100, la fecha extraordinaria nunca cae en festivo, y se registra un solo descuento, el de mayor porcentaje. Siguen siendo pruebas unitarias automatizadas, así que respetan la decisión de hacer solo pruebas unitarias; agregan `hypothesis` como dependencia de pruebas. La opción A exigiría además pruebas con estado y con modelos de referencia, que aquí aportan poco.

[Answer]: B (usuario, 2026-11-24)
