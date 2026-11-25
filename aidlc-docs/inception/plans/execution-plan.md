# Plan de ejecución — Workflow Planning

- Etapa: INCEPTION → Workflow Planning
- Fecha: 2026-11-24
- Entradas: `requirements.md` (aprobado), `user-stories/stories.md` (aprobadas), `Product-Definition/*`
- Estado: **pendiente de aprobación del usuario**
- Hito fijo: desplegado en el ambiente de pruebas (test) el 15/12/2026, listo para la revisión de Seguridad

Notas de método:
- Este plan sigue `.kiro/steering/core-workflow.md`. Hasta Application Design las reglas de detalle no estaban en el workspace; desde Units Generation se siguen las de `aws-aidlc-rule-details/`.
- Extensiones (decididas el 2026-11-24): seguridad activa y bloqueante; pruebas basadas en propiedades en modo parcial (bloqueantes PBT-02, 03, 07, 08 y 09); resiliencia no activa. Cada etapa incluye su resumen de cumplimiento.
- Modo de preguntas: conversacional. Las preguntas se hacen en el chat cuando la etapa las necesita (§4).

## 1. Etapas

| Etapa | Decisión | Profundidad | Motivo |
|---|---|---|---|
| Workspace Detection | Completada | — | Brownfield; Discovery completo |
| Reverse Engineering | Ejecutada (agregada el 2026-11-25 a pedido del usuario) | Estándar | Primero se omitió porque Discovery ya había analizado el sistema actual (`existing-system-analysis.md`, `templates-analysis.md`, `utils-oas-analysis.md`, `institutional-guidelines-analysis.md`). El 2026-11-25 el usuario pidió hacerla con base en las historias, los casos de uso y el código. Artefactos en `inception/reverse-engineering/`; los análisis de Discovery se referencian. Aprobada el 2026-11-25 |
| Requirements Analysis | Completada | Completa | Aprobada 2026-11-24 |
| User Stories | Completada | Estándar | Aprobadas 2026-11-24 |
| Workflow Planning | En revisión | — | Este documento |
| Application Design | Ejecutar | Estándar | Componentes nuevos en dos repositorios; puertos y adaptadores (Oracle, MySQL, S3, WSO2, "parametros", lector xlrd); contrato OpenAPI que necesita `recibos_mf` |
| Units Generation | Ejecutar | Mínima | Las unidades ya están fijadas por C-5; solo se documentan su alcance, la asignación de historias y la dependencia por el contrato de la API |
| **U1 `recibos_service`** | | | |
| Functional Design | Ejecutar | Completa | Reglas de cuotas, exenciones, conceptos, fechas y validaciones; mapeo a las tablas MySQL. Concentra la mayoría de las preguntas pendientes |
| NFR Requirements | Ejecutar | Estándar | Lote síncrono de 1000 estudiantes (tiempos de espera), seguridad OAS, Ley 1581. El stack ya está fijado |
| NFR Design | Ejecutar | Estándar | Middlewares de autenticación, cabeceras y auditoría; transacción por solicitud; caché del token |
| Infrastructure Design | Ejecutar | Mínima | Especificación para el grupo de infraestructura: ECS, S3, SSM, CloudWatch Logs, X-Ray y tiempos de espera; `Dockerfile`, `docker-compose.yml`, `.drone.yml`. Sin CDK ni Terraform (fuera de alcance) |
| Code Generation | Ejecutar | — | Siempre. Incluye pruebas unitarias (≥80%; 100% en `app/domain/`) |
| **U2 `recibos_mf`** | | | |
| Functional Design | Ejecutar | Mínima | Tres vistas: carga, resumen e historial; estados de la pantalla |
| NFR Requirements | Ejecutar | Mínima | Fijar versiones de Angular, TypeScript y Node (OQ-T-1) |
| NFR Design | Omitir | — | Las reglas del frontend (sin `localStorage` para tokens, escape de Angular, sesión por el microcliente core) se aplican directamente con la plantilla `oas_cliente` |
| Infrastructure Design | Ejecutar | Mínima | `Dockerfile` y `.drone.yml` según `oas_cliente` y el lineamiento L43 |
| Code Generation | Ejecutar | — | Siempre. Incluye pruebas `*.spec.ts` |
| Build and Test | Ejecutar (ajustada) | — | Solo compilación, pruebas unitarias y controles de CI (SonarQube, escaneo de dependencias). No se planean pruebas de integración, carga, funcionales, de usuario, de equivalencia ni de seguridad: las hacen otros grupos (`technical-environment.md`, "Pruebas") |
| Operations | No aplica | — | Etapa reservada del workflow; el despliegue en test lo hacen Drone y el grupo de infraestructura |

## 2. Unidades y orden

| Orden | Unidad | Repositorio | Historias | Depende de |
|---|---|---|---|---|
| 1 | U1 | `recibos_service` (Flask, Clean Architecture) | US-01 a US-15 (lado servidor) | Insumos D1–D7 y P-n según §4 |
| 2 | U2 | `recibos_mf` (Angular, single-spa) | US-01, US-02, US-12, US-13 (interfaz) | Contrato OpenAPI de U1 (sale de Application Design) |

U1 va primero porque U2 consume su API. Con el contrato OpenAPI definido en Application Design, U2 puede construirse contra la especificación sin esperar a que U1 esté desplegado.

## 3. Diagramas

Flujo general (texto equivalente: tabla de §1):

```mermaid
flowchart TD
    WD["Workspace Detection: completada"] --> RA["Requirements Analysis: aprobada"]
    RE["Reverse Engineering: agregada el 2026-11-25"] -.-> RA
    RA --> USS["User Stories: aprobadas"]
    USS --> WP["Workflow Planning: en revisión"]
    WP --> AD["Application Design: estándar"]
    AD --> UG["Units Generation: mínima"]
    UG --> U1["U1 recibos_service"]
    U1 --> U2["U2 recibos_mf"]
    U2 --> BT["Build and Test: solo unitarias y CI"]
    BT --> DEP["Ambiente test: 15/12/2026"]
```

Etapas por unidad (texto equivalente: filas U1 y U2 de §1):

```mermaid
flowchart LR
    subgraph S1["U1 recibos_service"]
        FD1["Functional Design: completa"] --> NR1["NFR Requirements: estándar"]
        NR1 --> ND1["NFR Design: estándar"]
        ND1 --> ID1["Infrastructure Design: mínima"]
        ID1 --> CG1["Code Generation"]
    end
    subgraph S2["U2 recibos_mf"]
        FD2["Functional Design: mínima"] --> NR2["NFR Requirements: mínima"]
        NR2 --> ID2["Infrastructure Design: mínima"]
        ID2 --> CG2["Code Generation"]
    end
    CG1 --> FD2
```

## 4. Cuándo se pregunta cada pendiente (en el chat)

| Momento | Pregunta o insumo | Desbloquea | Quién puede responder |
|---|---|---|---|
| Workflow Planning (resuelto 2026-11-24) | P-12 → mayor porcentaje; P-13 → regla actual de la votación | US-07 desbloqueada; US-08 sigue bloqueada por D5 y D2 | Usuario |
| Reverse Engineering (resuelto 2026-11-25) | C1 a C5: C1 a (sin votación automática en filas sin exenciones marcadas), C2 b (más de un descuento: la fila no se sube; votación marcada con cualquier descuento), C3 b (fechas de pregrado desde la plantilla), C4 a (versiones actualizadas), C5 b (módulo de notas de ARC en la Fase 2) | US-08 sin C1 ni C2; US-07 pasa a depender de D1 | Usuario / ARC |
| U1 Functional Design | D5: origen de los festivos y si sábados y domingos cuentan | US-08 | DBA / OATI |
| U1 Functional Design | D1: plantilla de pregrado sin Reingreso y con las fechas de pago (A1, fila inicial, encabezados, columnas y formato de las fechas, y si trae la fecha extraordinaria) | US-03, US-07 | ARC |
| U1 Functional Design | D2: plantilla de posgrado SMLV | US-05 y variante SMLV de US-08 | ARC |
| U1 Functional Design | ~~D3~~ resuelta el 2026-11-25 con el código de "Solicitados" (RE-21, A15). C6, C7 y C8: respuesta sobre A14, suma mayor que 100% y cancelación de periodos anteriores | US-07, US-08, US-09 | Usuario |
| U1 Functional Design | P-1, P-2, P-6, P-10 (P-14 ya no aplica desde C2) | US-02, US-06, US-08, US-12 | Usuario / ARC |
| U1 Functional Design (entrega) | D10: lista de parámetros de las reglas para crear en "parametros" (dev y test) | US-15 | OATI / ARC los crean |
| U1 NFR Requirements | Tiempo de respuesta objetivo para un lote de 1000 estudiantes (RNF-1) | — | Usuario |
| U1 Infrastructure Design | D7: rutas SSM, destino y retención de logs (mínimo 90 días), tamaño máximo y retención en S3; D11: orígenes de CORS; D12: throttling en WSO2 AM; D13: número de proxies de confianza para la IP (AD-29); requisitos de AD-28 | — | Infraestructura / Seguridad / Arquitectura |
| Antes de U1 Code Generation | Herramientas de la máquina: el usuario pidió usar las versiones vigentes (2026-11-25). Ya hay Docker 29 y Python 3.14; Node 18 se cambia por una LTS con soporte antes de U2. C4 = a: el proyecto usa la última versión estable de cada lenguaje | Build and Test | Usuario |
| U1 Code Generation | D4: DDL real, prefijo de las tablas y llaves primarias; D6 (acotada): campo del valor de cada regla, ids por ambiente, URL y autenticación; D8: identificador del rol ARC | US-09 a US-11 | DBA; usuario / OATI; Arquitectura |
| U2 NFR Requirements | OQ-T-1: versiones de Angular, TypeScript y Node | — | Se verifican en `oas_cliente` (`feature/clientes_nuevos`) |

Regla: si un insumo no llega en su momento, la historia sigue bloqueada y el trabajo continúa con lo demás. No se inventan valores.

## 5. Riesgos del plan

| Riesgo | Impacto | Mitigación |
|---|---|---|
| D6 y D10 siguen en la ruta crítica: ya se conocen la consulta por id y el formato del sobre, pero falta el campo del valor de cada regla, sus ids y que los parámetros se creen en el servicio | Sin eso no se puede terminar el adaptador de reglas de U1 | El puerto aísla el dominio; el adaptador es lo último de U1. Si el formato no llega a tiempo, se decide en ese momento contigo cómo seguir |
| D4 (DBA) llega tarde | No se puede cerrar el adaptador de escritura MySQL | Las columnas, el valor de `cuota` y los estados ya se conocen por el código del lote y de "Solicitados" (RE-21); solo faltan los tipos exactos, el prefijo y las llaves |
| Los tiempos de espera de gunicorn, el balanceador y WSO2 AM no permiten 1000 estudiantes en una petición | El lote falla aunque el código esté bien | Se fija el objetivo en U1 NFR Requirements y se entrega a infraestructura en Infrastructure Design |
| Festivos sin origen conocido (D5) | No se puede cerrar la fecha extraordinaria de posgrado | Se pregunta al inicio de U1 Functional Design |
| Herramientas de la máquina de desarrollo (verificado el 2026-11-25: Docker 29, Python 3.14, Node 18 sin soporte) | Probar con versiones distintas de las del despliegue | El usuario pidió usar las versiones vigentes; con C4 = a el proyecto también usa las versiones vigentes. Las pruebas pueden correr en contenedores con la misma imagen del despliegue |
| `oas_cliente` trae una versión de Angular sin soporte (SECURITY-09) | Hay que actualizar la plantilla en U2 | Se revisa en U2 NFR Requirements |
