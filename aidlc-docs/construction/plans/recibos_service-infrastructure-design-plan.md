# Plan del diseño de infraestructura — U1 `recibos_service`

- Etapa: CONSTRUCTION → U1 `recibos_service` → Infrastructure Design, profundidad mínima (`inception/plans/execution-plan.md`)
- Inicio: 2026-11-25T19:37:56Z
- Fuentes: el diseño funcional de U1; `nfr-design/nfr-design-patterns.md` y `nfr-design/logical-components.md` (aprobados el 2026-11-25T19:31:30Z); `nfr-requirements/`; `firma-electronica-mid-analysis.md` (pipeline institucional); lineamientos L41 a L48
- Alcance: la infraestructura de AWS la administra el grupo de infraestructura y no hay CDK ni Terraform en el proyecto (`technical-environment.md`). Esta etapa entrega la especificación que infraestructura aplica; `Dockerfile`, `docker-compose.yml`, `.drone.yml` y `gunicorn.conf.py` se escriben en Code Generation
- Extensiones: seguridad, con todas sus reglas bloqueantes; aquí aplican sobre todo SECURITY-02, 06, 07, 09, 10 y 14. PBT parcial: la extensión no asigna reglas a esta etapa. Resiliencia desactivada (N17 = b)
- Cómo responder: después de cada `[Answer]:` de este archivo, o en el chat con el formato "i1 a, i2 a, i3 a, i4 a, i5 a"

## Pasos
- [x] 1. Analizar el diseño funcional y el diseño de NFR de U1
- [x] 2. Escribir este plan con las preguntas I1 a I5
- [ ] 3. Recibir las respuestas y revisar que ninguna quede ambigua
- [ ] 4. `infrastructure-design.md`: el servicio de AWS de cada componente lógico, con su configuración (ECS, balanceador, ECR, S3, SSM, CloudWatch, SNS, IAM y red)
- [ ] 5. `deployment-architecture.md`: ambientes, topología, pipeline de Drone, despliegue y vuelta atrás
- [ ] 6. `construction/shared-infrastructure.md`: lo que U1 y U2 comparten de la plataforma de la OAS
- [ ] 7. Llevar los cambios a los documentos anteriores e insumos (D7, D11 a D16 y uno nuevo para la red)
- [ ] 8. Validar los diagramas y las tablas, revisar el cumplimiento de seguridad y presentar la compuerta

## Categorías revisadas
| Categoría | ¿Hay pregunta? | Por qué |
|---|---|---|
| Ambiente de despliegue | I1 e I5 | Falta decidir si hay un ambiente dev en AWS (L41 y L44 lo mencionan, pero el pipeline solo despliega test y producción) y cómo se fija la imagen que corre en producción (SECURITY-10) |
| Cómputo | I2 | El tamaño y el escalado ya salen de NFR-C02 y NFR-C06 (decisiones de abajo); falta saber si los clusters `test` y `oas` corren en Fargate o en EC2 |
| Almacenamiento | No | Bases existentes (Discovery), un bucket de S3 por ambiente y parámetros de SSM; las decisiones están abajo |
| Mensajería | No | No hay colas ni eventos: el procesamiento es síncrono (C-2) |
| Red | I3 e I4 | El balanceador necesita 120 s de inactividad y ese valor es de todo el balanceador; falta saber si el tramo entre el balanceador y la tarea va cifrado (NFR-S01) |
| Monitoreo | No | Las alarmas y sus fuentes salen de `nfr-design-patterns.md` §8.2; los umbrales están abajo y el canal es el insumo D15 |
| Infraestructura compartida | I3 | Los clusters, WSO2, Drone y ECR son de la plataforma de la OAS; I3 decide si el balanceador también se comparte |

## Decisiones que no necesitan pregunta
Se aplican salvo que digas otra cosa.
- **Tareas:** 0,5 vCPU y 1 GB de memoria por tarea, en test y en producción. Producción con 2 tareas en zonas de disponibilidad distintas; test con 1 (NFR-A02). Sin autoescalado (NFR-C06). Los valores se revisan con las métricas de uso de test.
- **Servicio de ECS:** despliegue con 100% de tareas sanas como mínimo y 200% como máximo; reversa automática si las tareas nuevas no quedan sanas (deployment circuit breaker); 60 s de gracia para el primer health check; 120 s de parada (`stopTimeout`).
- **Contenedor:** usuario sin privilegios; sistema de archivos de solo lectura, con `/tmp` escribible porque Werkzeug guarda en disco los archivos de más de 500 KB mientras los lee; `initProcessEnabled` para reenviar las señales; puerto 8080; registros con el driver `awslogs`.
- **Grupo de destino:** health check a `/health` cada 15 s, con 5 s de espera, 2 respuestas buenas para entrar y 3 fallas para salir; desregistro de 110 s (`nfr-design-patterns.md` §3.1).
- **S3:** un bucket por ambiente, solo para este servicio; acceso público bloqueado; cifrado SSE-S3; una política que rechaza las peticiones sin TLS y solo deja escribir al rol de la tarea; versionado activo, para que un archivo sobrescrito no se pierda; borrado automático a los 365 días, también de las versiones anteriores (NFR-S09); acceso por el endpoint de puerta de enlace de S3 en la VPC, que no tiene costo.
- **SSM:** parámetros `SecureString` bajo `/{parameterStore}/recibos_service/` (rutas exactas en D7); el rol de la tarea solo lee esa ruta.
- **ECR:** repositorio `recibos_service` creado por infraestructura (el pipeline no lo crea), con escaneo de vulnerabilidades al subir cada imagen y retención de las últimas 30.
- **Registros:** grupo de CloudWatch Logs por ambiente (`/ecs/recibos_service_test` y `/ecs/recibos_service_prod`) con 365 días; el rol de la tarea no puede borrar registros (NFR-S09). Registros de acceso del balanceador y de WSO2 AM con la misma retención (SECURITY-02).
- **Alarmas:** un tema de SNS por ambiente, al que infraestructura suscribe su canal (D15). Umbrales en producción: ninguna tarea sana durante 1 minuto; 1 error 500 en 5 minutos; 1 error 502, 503 o 504 generado por el balanceador en 5 minutos; p95 de `duracion_ms` por encima de 60 s en una hora; 10 respuestas 401 o 403 en 5 minutos; 1 lote con `TIEMPO_AGOTADO`; 1 lote cortado por MySQL; una tarea que se detiene sin que haya un despliegue. En test, las mismas alarmas van a un tema de SNS aparte, sin turnos de atención. Un tablero de CloudWatch para producción (NFR-O06).
- **IAM:** rol de ejecución y rol de tarea con políticas administradas por el cliente y sin comodines, salvo `ecr:GetAuthorizationToken`, que AWS no deja limitar a un recurso (excepción documentada, SECURITY-06). El usuario de Drone solo puede subir imágenes a `recibos_service` y actualizar los servicios `recibos_service_test` y `recibos_service_prod`.
- **Red:** tareas en subredes privadas de dos zonas, sin IP pública. El grupo de seguridad de la tarea solo recibe del balanceador en el puerto 8080 y solo sale a los puertos de las bases, a 443 y a la lista de prefijos de S3. El balanceador solo acepta tráfico de WSO2 AM.
- **WSO2 AM:** 130 s de tiempo de espera hacia el servicio (NFR-P05); política de throttling por usuario de 5 cargas por minuto, propuesta para D12.
- **Pipeline:** los pasos institucionales (revisión de la rama y de los commits, SonarQube, ECR, ECS y aviso por Telegram) más pruebas con cobertura, ruff, mypy, pip-audit y la SBOM; todas las imágenes del pipeline con versión fija (SECURITY-10).

## Preguntas

### Pregunta I1 — Ambiente dev
El lineamiento L41 habla de tres ambientes (dev, test y producción) y L44 dice que dev usa Jenkins. El pipeline de Drone, como el de `firma_electronica_mid`, solo despliega `release/*` en test y `master` en producción.

A) Sin ambiente dev en AWS: dev es la máquina de cada desarrollador, con `docker-compose`; la rama `develop` solo pasa las revisiones del pipeline. Recomendada: es lo que hace el pipeline institucional y no suma costos

B) También un ambiente dev en AWS, desplegado desde `develop`, con una tarea y sus propios recursos (bucket, parámetros y registros)

C) Other (please describe after [Answer]: tag below)

[Answer]: 

### Pregunta I2 — Tipo de cómputo de los clusters `test` y `oas`
El diseño necesita una interfaz de red por tarea, para darle su propio grupo de seguridad, y 120 s para detener una tarea.

A) Fargate: no hay servidores que mantener, cada tarea tiene su interfaz de red y 120 s es el máximo de parada que permite. Recomendada si los clusters ya lo usan o lo admiten

B) EC2: las instancias del cluster usan el modo de red `awsvpc` para tener un grupo de seguridad por tarea, y la definición de tarea fija los 120 s de parada, porque el agente de ECS usa 30 s si no se indica

C) Other (please describe after [Answer]: tag below). Si no lo sabes, escribe "no sé": queda como insumo para infraestructura y el diseño sirve para los dos casos

[Answer]: 

### Pregunta I3 — Balanceador
El servicio necesita que el balanceador espere 120 s sin datos (NFR-P05), pero ese tiempo de inactividad es de todo el balanceador, no de cada servicio. El valor por defecto de AWS es 60 s.

A) Usar el balanceador que ya comparten los servicios de la OAS, con un grupo de destino y una regla para `recibos_service`. Infraestructura sube el tiempo de inactividad a 120 s y revisa que los demás servicios sigan bien: un servicio cuyo keep-alive quede entre 60 y 120 s puede empezar a dar errores 502. Recomendada si ese balanceador existe, porque no suma costos

B) Un balanceador solo para `recibos_service`, con 120 s de inactividad. No toca a los demás servicios y cuesta unos USD 16 a 25 al mes más, según la región

C) Other (please describe after [Answer]: tag below)

[Answer]: 

### Pregunta I4 — Tramo entre el balanceador y la tarea
NFR-S01 pide TLS "en todo el tráfico". El balanceador recibe HTTPS de WSO2 AM; falta decidir cómo le habla a la tarea dentro de la red privada.

A) HTTP en el puerto 8080: el balanceador termina TLS y el grupo de seguridad de la tarea solo deja entrar al balanceador. Es la práctica usual de AWS y no hay certificados dentro del contenedor. Se precisa NFR-S01: TLS en todo el tráfico, salvo este tramo dentro de la VPC. SECURITY-01 no lo exige, porque solo cubre los almacenes de datos. Recomendada

B) HTTPS también en este tramo: gunicorn sirve TLS con un certificado que infraestructura guarda en SSM. El balanceador cifra, pero no valida ese certificado, así que solo protege contra alguien que lea el tráfico dentro de la VPC; hay que renovar y rotar ese certificado

C) Other (please describe after [Answer]: tag below)

[Answer]: 

### Pregunta I5 — Imagen que corre en producción (SECURITY-10)
Hoy el pipeline institucional sube la imagen con las etiquetas `release` (test) y `latest` (producción) y redespliega el servicio con `--force-new-deployment`. SECURITY-10 no permite la etiqueta `latest` en producción.

A) Imagen por commit: Drone sube la imagen solo con la etiqueta del commit, toma la definición de tarea vigente, cambia solo la imagen y registra una revisión nueva; el servicio se actualiza a esa revisión. Volver atrás es elegir la revisión anterior, y las etiquetas de ECR quedan inmutables. El usuario de Drone necesita, además, registrar definiciones de tarea y pasar los dos roles de la tarea. Recomendada: cumple SECURITY-10 y deja saber qué commit corre en cada ambiente

B) Como el pipeline institucional, con `latest` y `--force-new-deployment`. Incumple SECURITY-10; con la extensión de seguridad activa es un hallazgo bloqueante y la etapa no se puede aprobar así

C) Other (please describe after [Answer]: tag below)

[Answer]: 

## Estado (2026-11-25T19:48:59Z)
Aplazada por el usuario el 2026-11-25T19:39:46Z: "omitir la infraestructura,  dejarlo para después, pasa al paso de generar el codigo". Las preguntas I1 a I5 y las decisiones de este plan siguen sin responder ni aprobar. Se retoma antes del primer despliegue en test; lo que Code Generation deja pendiente por esto está en `recibos_service-code-generation-plan.md` §5.
