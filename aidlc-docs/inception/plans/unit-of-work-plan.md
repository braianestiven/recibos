# Plan — Units Generation

- Etapa: INCEPTION → Units Generation (profundidad mínima)
- Reglas: `aws-aidlc-rule-details/inception/units-generation.md`
- Entradas: `plans/execution-plan.md` (U1 → U2), `application-design/*`, `user-stories/stories.md` (todos aprobados)
- Preguntas: se hacen en el chat (modo conversacional pedido por el usuario) y se registran aquí con `[Answer]:`
- Preguntas de las extensiones de AI-DLC: `inception/requirements/extension-opt-in-questions.md`

## Parte 1 — Planificación
- [x] Analizar requisitos, historias y diseño aprobados
- [x] Evaluar las categorías de preguntas (tabla de abajo)
- [x] Respuesta del usuario a Q1 y a las preguntas de las extensiones (2026-11-24): Q1 = A; seguridad = A; resiliencia = B; pruebas basadas en propiedades = B
- [x] Analizar las respuestas: sin ambigüedades ni contradicciones. La activación de seguridad obligó a revisar el diseño aprobado (ver `application-design.md` §10)
- [x] Aprobación del plan: el usuario respondió después de que se le anunció que con sus respuestas se generarían los artefactos

## Parte 2 — Generación
- [x] Generar `application-design/unit-of-work.md`: definición de U1 y U2, responsabilidades y organización del código
- [x] Generar `application-design/unit-of-work-dependency.md`: matriz de dependencias entre unidades, con sistemas externos e insumos pendientes
- [x] Generar `application-design/unit-of-work-story-map.md`: historias → unidades
- [x] Validar límites y dependencias de las unidades: U1 no depende de U2; U2 depende solo del contrato y del despliegue de U1
- [x] Verificar que todas las historias tengan unidad: 15 de 15
- [x] Resumen de cumplimiento de las extensiones activadas (seguridad y pruebas basadas en propiedades)
- [ ] Aprobación del usuario

## Unidades (fijadas por C-5 y el plan aprobado)

| Unidad | Tipo | Repositorio | Contenido |
|---|---|---|---|
| U1 | Servicio desplegable | `recibos_service` | API Flask: dominio, casos de uso, adaptadores, interfaces |
| U2 | Servicio desplegable (microcliente) | `recibos_mf` | Angular con single-spa: carga, resumen e historial |

Orden: U1 y después U2. U2 se construye contra `application-design/api-contract.md`.

## Evaluación de las categorías de preguntas

| Categoría | ¿Se pregunta? | Justificación |
|---|---|---|
| Agrupación de historias | No | Cada historia va a la unidad del componente que la implementa (Application Design). US-01, US-02, US-12 y US-13 tienen parte en las dos unidades |
| Dependencias | No | U2 depende solo del contrato de la API, ya aprobado; la comunicación es HTTPS síncrona a través de WSO2 AM |
| Equipo | No | Un solo equipo de 3 desarrolladores, con desarrollo guiado por IA (C-6); no hay fronteras de propiedad entre unidades |
| Consideraciones técnicas | No | Las dos unidades van en contenedores en ECS con Drone (L43). La diferencia que importa, los tiempos de espera del lote síncrono, ya está en el plan para NFR de U1 |
| Dominio de negocio | No | Un solo contexto: solicitudes de recibo por lote |
| Organización del código | **Sí (Q1)** | El código nuevo no tiene una estructura existente donde vivir: `codigo-fuente/` contiene el sistema PHP, los lineamientos y `utils_oas`, y no se modifica |

## Preguntas

## Question 1
¿Dónde se crea el código de las dos unidades?

A) En dos carpetas en la raíz de este workspace, `recibos_service/` y `recibos_mf/`. Cada una se arma como la raíz de su futuro repositorio (README, Dockerfile, docker-compose.yml, .drone.yml, sonar-project.properties) y queda dentro del repositorio actual (`braianestiven/recibos`) hasta pasarla a su repositorio institucional

B) En las mismas dos carpetas, pero cada una como un repositorio git propio, ignorado por el repositorio actual y listo para publicar en `udistrital/recibos_service` y `udistrital/recibos_mf`

C) Fuera de este workspace, en una ruta que indique el usuario

X) Other (please describe after [Answer]: tag below)

**Recomendación:** A. Deja documentación y código en un solo workspace y un solo historial, que es lo más simple para el desarrollo guiado por IA. Pasar cada carpeta a su repositorio institucional al final es copiarla, o usar `git subtree split` si se quiere conservar el historial. Con B cada carpeta tiene su historial desde el inicio, pero los repositorios anidados complican las herramientas.

[Answer]: A (usuario, 2026-11-24)
