# ADR-010: LangGraph workflow state vs domain state

- **Fecha:** 
- **Estado:** Aceptada

## Contexto

Una investigación tiene el siguiente flujo conceptual:

```
Investigation
      │
      ▼
Collect evidence
      │
      ▼
Generate hypotheses
      │
      ▼
Evaluate hypotheses
      │
      ▼
Produce conclusion
```

### Contrato de cada etapa

- Collect evidence
    - Entrada:  `Incident`
    - Salida:   `Evidence[]`

- Generate hypotheses
    - Entrada:  `Incident + Evidence[]`
    - Salida:   `Hypothesis[]`

- Evaluate hypotheses
    - Entrada:  `Hypothesis[] + Evidence[]`
    - Salida:   `EvaluatedHypothesis[]`

- Conclusion
    - Entrada:  `Incident + Evidence + evaluated hypotheses`
    - Salida:   `InvestigationResult`

### Decisión: 

¿Dónde vive esa información?

## Alternativas consideradas

### 1. Todo en LangGraph State

Ventajas:

- Implementación inicial más simple.
- El estado necesario para continuar el workflow está en un único lugar.
- Encaja naturalmente con checkpoints y recuperación de LangGraph.
- Evita introducir entidades y tablas de dominio prematuramente.

Desventajas:

- El estado de la aplicación queda acoplado al mecanismo de ejecución del workflow.
- Consultar el estado de una investigación desde la API requeriría depender de LangGraph.
- Complica separar el ciclo de vida de `Investigation` de la ejecución concreta del workflow.
- Hace menos clara la frontera entre estado durable del negocio y estado temporal de ejecución.
- Cambiar posteriormente de motor de workflow tendría mayor impacto.

### 2. PostgreSQL como dominio

Ventajas:

- El estado durable de la aplicación tiene una fuente de verdad independiente del workflow.
- Investigation puede consultarse directamente desde la API.
- ermite mantener el lifecycle de una investigación independientemente del motor de ejecución.
- Facilita auditoría, testing y evaluación sobre datos persistentes.
- Reduce el acoplamiento entre el dominio y LangGraph.

Desventajas:

- Introduce dos representaciones de estado que deben mantenerse coherentes.
- Requiere decidir qué información pertenece al dominio y cuál solamente al workflow.
- Añade complejidad de sincronización entre ejecución del workflow y persistencia.
- Puede resultar innecesario persistir información que solamente sirve para continuar una ejecución.

## Decisión

LangGraph mantiene el estado de ejecución del workflow; PostgreSQL mantiene el estado durable del dominio de la aplicación.

En el MVP:

```
PostgreSQL
├── Incident
├── Investigation
└── InvestigationEvent
```

Mientras que LangGraph será responsable del estado necesario para ejecutar y continuar el workflow:

```
LangGraph State
├── incident context
├── evidence
├── hypotheses
└── workflow execution state
```

Esta decisión no implica todavía que `Evidence`, `Hypothesis` o `Conclusion` deban convertirse en entidades persistentes de PostgreSQL. Esa decisión se tomará cuando exista un requisito concreto que lo justifique.

## Consecuencias

### Positivas
- Separa claramente estado de dominio y estado de ejecución.
- PostgreSQL continúa siendo la fuente de verdad para el lifecycle de Investigation.
- LangGraph puede evolucionar o reemplazarse sin redefinir necesariamente el dominio de la aplicación.
- Podemos consultar investigaciones sin depender de reconstruir el estado del workflow.
- Evitamos crear tablas prematuramente para cada objeto interno del agente.
- Facilita distinguir entre información durable del sistema y datos necesarios solamente durante una ejecución.

### Negativas
- Tenemos dos lugares donde existe información relacionada con una investigación.
- Debemos definir claramente qué información pertenece a cada estado.
- Algunos cambios de estado del workflow pueden necesitar reflejarse también en PostgreSQL.
- La implementación requiere cuidado para evitar inconsistencias entre el lifecycle persistido y la ejecución real.

### Riesgos
- Duplicación de estado: almacenar la misma información en PostgreSQL y LangGraph podría generar divergencias.
- Frontera mal definida: si no distinguimos domain state de workflow state, podemos terminar persistiendo innecesariamente el estado completo del agente.
- Fallos entre sistemas: un workflow puede avanzar mientras una actualización de PostgreSQL falla, o viceversa.
- Evolución prematura del modelo: podríamos convertir Evidence o Hypothesis en entidades persistentes sin tener todavía un requisito real.

Para el MVP mitigaremos estos riesgos manteniendo una regla simple:

> PostgreSQL responde por el estado durable de la aplicación; LangGraph responde por la ejecución del workflow.

Y evitaremos sincronizar automáticamente todo el LangGraph State con PostgreSQL.

## Notas

En [ADR-003: PostgreSQL como estado persistente](/docs/ADR/003-postgresql-state.md), indica que PostgreSQL es la fuente de verdad del estado durable de la aplicación.

Este ADR indica que LangGraph mantiene workflow state.

```
                    STATE
                      │
          ┌───────────┴───────────┐
          │                       │
      DOMAIN STATE          WORKFLOW STATE
          │                       │
     PostgreSQL                LangGraph
          │                       │
    "qué existe"           "qué paso está
                            la ejecución"
```

Por ejemplo:

```
PostgreSQL:

Investigation
status = running
incident_id = ...


LangGraph:

current_node = analyze_evidence
evidence = [...]
hypotheses = [...]
```