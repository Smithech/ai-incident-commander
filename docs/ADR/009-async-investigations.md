# ADR-009: Ejecución asíncrona de investigaciones

- **Fecha:** 
- **Estado:** Aceptada

## Contexto

Se necesita definir la forma en que una investigación se va a ejecutar. Por su complejidad, se decidió una ejecución asincrónica. 

Queremos que `POST /incidents/{incident_id}/investigations` no ejecute la investigación durante la request.

La API debe responder rápidamente:

```
202 Accepted
{
  "investigation_id": "...",
  "status": "pending"
}
```

y el trabajo continúa en segundo plano.

Después:

```
GET /investigations/{investigation_id}
```

permite consultar el estado.

## Alternativas consideradas

### 1. `FastAPI BackgroundTasks`

Ventajas:
- Fácil implementacion
- No requerimos otras tecnologías a las del core del MVP. 

Desventajas:
- Parte del proceso de FastAPI, si el proceso muere, el trabajo se pierde.

### 2. `asyncio.create_task()`

Ventajas:
- Fácil implementacion
- Más explícito que FastAPI BackgroundTasks

Desventajas:
- Mismas limitaciones de proceso

### 3. Worker separado

Ventajas:
- Más robusto

Desventajas:
- Intruduce otra pieza desplegable
- Probablemente innecesario para nuestro MVP

### 4. Celery / Redis / etc.

Ventajas:
- Solución más robuta, tipo empresarial. 

Desventajas:
- Mas complejidad de implementacion
- Demasiado complejo para el problema del MVP

## Decisión

Para el MVP, las investigaciones se ejecutan mediante `FastAPI BackgroundTasks`, mientras `PostgreSQL` mantiene el estado durable de su ciclo de vida.

```
                   ┌───────────────┐
                   │   FastAPI     │
                   └───────┬───────┘
                           │
                POST /investigations
                           │
                           ▼
                ┌────────────────────┐
                │ Investigation      │
                │ status = pending   │
                └─────────┬──────────┘
                          │
                       COMMIT
                          │
                          ├──────────────► 202 Accepted
                          │
                          ▼
                 BackgroundTasks
                          │
                          ▼
                status = running
                          │
                          ▼
                   execute()
                     /      \
                    /        \
                   ▼          ▼
             completed       failed
                   │            │
                   └──────┬─────┘
                          ▼
                InvestigationEvent
```
Se persiste `pending` antes de lanzar el trabajo.

### `InvestigationService`

El responsable del lifecycle será `InvestigationService`, el cual ejecuta la investigación:

Conceptualmente:

```
create_investigation()
    → pending

run_investigation()
    → running
    → completed
    → failed
```
Estados:

```
investigation.created
investigation.started
investigation.completed
investigation.failed
```

## Consecuencias

### Positivas
- Fácil implementación para probar concepto. 
- El diseño elegido, permitirá en un futuro cambiar qué componente dispara el proceso. Ahora `BackgroundTasks` ejecuta `run_investigation()`, mañana puede ser `worker`.

### Negativas


### Riesgos
- Si el proceso FastAPI falla, el proceso puede fallar. Riesgo aceptado para el MVP. 

## Notas

- [ADR-003: PostgreSQL como estado persistente](/docs/ADR/003-postgresql-state.md)
