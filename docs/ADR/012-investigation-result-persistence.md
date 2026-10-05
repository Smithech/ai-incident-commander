# ADR-012: Persistencia del resultado de una investigación

- **Fecha:** 
- **Estado:** Aceptada

## Contexto

El workflow de investigación ejecutado mediante LangGraph actualmente produce información útil durante su ejecución, principalmente Evidence y Hypothesis.

LangGraph mantiene esta información como parte de su estado de ejecución, pero el resultado actualmente no se persiste como parte del estado durable de la aplicación.

Esto genera una limitación importante: una vez finalizada la investigación, PostgreSQL solamente conserva el lifecycle de Investigation y sus eventos, pero no el resultado que produjo el workflow.

La investigación necesita conservar un resultado durable que pueda ser consultado posteriormente por la API y utilizado por los tests de evaluación.

Al mismo tiempo, no queremos acoplar el estado de ejecución de LangGraph con el modelo de persistencia de la aplicación ni introducir prematuramente tablas independientes para Evidence y Hypothesis.

Por lo tanto, es necesario definir qué parte del resultado de una investigación pertenece al estado durable de la aplicación y cómo debe persistirse.

## Alternativas consideradas

### 1. No persistir el resultado

Mantener `Evidence` e `Hypothesis` únicamente dentro del estado de ejecución de LangGraph.

Ventajas:

- Implementación mínima.
- No requiere cambios en el modelo de persistencia.
- Mantiene toda la información temporal dentro de LangGraph.

Desventajas:

- El resultado de una investigación se pierde al finalizar el workflow.
- La API no puede devolver las evidencias ni hipótesis generadas.
- Dificulta la evaluación posterior de las investigaciones.
- Hace que el resultado dependa de que el estado de ejecución de LangGraph permanezca disponible.

### 2.Persistir `Evidence` e `Hypothesis` como entidades independientes

Crear tablas independientes relacionadas con Investigation:

```
Investigation
├── Evidence[]
└── Hypothesis[]
```

Ventajas:

- Modelo relacional explícito.
- Permite consultar y relacionar Evidence e Hypotheses individualmente.
- Facilita futuras consultas analíticas sobre estos elementos.

Desventajas:

- Introduce nuevas tablas, repositories y relaciones.
- Aumenta la complejidad del modelo de persistencia.
- Requiere definir lifecycle y reglas de persistencia para cada entidad.
- No existe todavía una necesidad concreta de realizar consultas independientes sobre Evidence o Hypotheses.
- Puede llevar a diseñar prematuramente un modelo de datos que todavía puede evolucionar.

### 3. Persistir un `InvestigationResult` como documento JSONB

Representar el resultado final de una investigación mediante un objeto compuesto por Evidence e Hypothesis y almacenarlo como JSONB asociado a Investigation.

Conceptualmente:

```
Investigation
└── result
    ├── evidence[]
    └── hypotheses[]
```

Ventajas:

- Mantiene el modelo de persistencia simple.
- Permite conservar el resultado completo de una investigación.
- Evita introducir tablas adicionales prematuramente.
- Permite que la API consulte y devuelva el resultado directamente.
- Facilita la evaluación posterior de las investigaciones.
- Mantiene separada la persistencia del dominio del estado interno de LangGraph.
- Permite evolucionar el resultado posteriormente con nuevos componentes.

Desventajas:

- No permite consultar Evidence o Hypotheses individualmente mediante relaciones SQL sin procesar el documento.
- El esquema del documento JSONB debe mantenerse compatible a medida que evolucione.
- Existe menos validación relacional que con tablas independientes.

## Decisión

Una investigación completada producirá un `InvestigationResult` compuesto inicialmente por:

```
Evidence[]
Hypothesis[]
```

El `InvestigationResult` se persistirá como un documento JSONB asociado a la entidad `Investigation` en PostgreSQL.

La frontera entre estado de aplicación y estado de workflow será:

```
PostgreSQL
├── Incident
├── Investigation
│   └── InvestigationResult
└── InvestigationEvent

LangGraph
└── InvestigationState
    ├── incident context
    ├── evidence
    ├── hypotheses
    └── workflow execution state
```

Durante la ejecución, `Evidence` e `Hypothesis` pertenecen al estado de LangGraph. Cuando el workflow finaliza correctamente, su resultado se transforma en `InvestigationResult` y se persiste en PostgreSQL.

Los resultados parciales no se persistirán en esta etapa.

La semántica será:

```
pending   → result = null
running   → result = null
completed → result = InvestigationResult
failed    → result = null
```

La persistencia del resultado no implica que LangGraph se convierta en la fuente de verdad del dominio ni que se utilice su mecanismo de checkpointing como mecanismo de persistencia de resultados de negocio.

Tampoco se crearán inicialmente tablas independientes para `Evidence` o `Hypothesis`.

## Consecuencias

### Positivas

- La investigación conserva un resultado durable después de finalizar.
- La API puede consultar y devolver Evidence e Hypotheses.
- Los evaluation tests pueden trabajar sobre resultados persistidos.
- PostgreSQL continúa siendo la fuente de verdad del estado durable de la aplicación.
- LangGraph mantiene una responsabilidad clara sobre el estado de ejecución del workflow.
- Se evita introducir tablas y repositories adicionales antes de necesitarlos.
- El modelo puede evolucionar posteriormente hacia Conclusion y Recommendation si el workflow los incorpora.

### Negativas

- Evidence e Hypotheses no pueden consultarse como entidades relacionales independientes de forma directa.
- El documento JSONB requiere mantener un contrato de datos estable.
- La evolución futura del resultado puede requerir migraciones o compatibilidad entre versiones del documento.
- Existen dos representaciones durante la ejecución: el estado de LangGraph y el resultado persistido en PostgreSQL.

## Notas

Esta decisión no determina que Evidence o Hypothesis deban permanecer siempre dentro de JSONB.

Si en el futuro aparecen necesidades concretas de consulta, filtrado, análisis o relaciones sobre estos elementos, podrá reconsiderarse su persistencia como entidades independientes.

Esta decisión tampoco introduce todavía Conclusion, Recommendation, confidence scores, ranking de hipótesis ni persistencia de resultados parciales.

### ADR relacionada

[ADR-010: LangGraph workflow state vs domain state](/docs/ADR/010-langgraph-state-boundary.md)