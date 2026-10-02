# ADR-006: Workflow controlado por LangGraph

- **Fecha:** 
- **Estado:** Aceptada

## Contexto

El sistema de investigación de incidentes utiliza un componente de razonamiento basado en un LLM para analizar evidencia, generar hipótesis y apoyar la investigación.

Un enfoque completamente agentic permitiría que el LLM decidiera libremente qué acción ejecutar a continuación:

```
Incident
   ↓
LLM
   ├── query_logs
   ├── query_metrics
   ├── inspect_deployment
   ├── query_traces
   └── ...
```

Aunque este modelo proporciona flexibilidad, introduce dificultades para controlar, probar y evaluar el comportamiento del agente.

En particular, un LLM no debería tener control arbitrario sobre el flujo de ejecución del sistema. La investigación de un incidente requiere un proceso predecible, observable y reproducible, especialmente cuando las conclusiones deben estar respaldadas por evidencia.

Se busca, por tanto, separar:

- Control del workflow: responsabilidad de la aplicación y LangGraph.
- Razonamiento: responsabilidad del LLM dentro de los puntos definidos por el workflow.
- Ejecución de herramientas: responsabilidad de tools deterministas y controladas.

El proceso conceptual de investigación será:

```
Create Incident
      ↓
Start Investigation
      ↓
Collect Evidence
      ↓
Analyze Evidence
      ↓
Generate Hypotheses
      ↓
Validate Hypotheses
      ↓
Generate Recommendation
```

El LLM puede participar en determinados nodos, pero no controla arbitrariamente la totalidad del workflow.

## Alternativas consideradas

### 1. Workflow completamente determinista

El proceso de investigación se implementaría como una secuencia fija de pasos sin razonamiento agentic significativo.

```
Start
  ↓
Collect evidence
  ↓
Generate hypotheses
  ↓
Evaluate hypotheses
  ↓
Determine confidence
  ↓
Produce recommendation
  ↓
Finish
```

Cada paso tendría un comportamiento predeterminado.

Ventajas: 

- Alta predictibilidad.
- Fácil de probar.
- Fácil de observar y depurar.
- Comportamiento altamente reproducible.
- Costos y número de operaciones más predecibles.

Desventajas:

- Menor capacidad para adaptarse a incidentes inesperados.
- Requiere codificar explícitamente más casos de investigación.
- Puede resultar rígido ante diferentes tipos de incidentes.
- Reduce la capacidad del LLM para explorar hipótesis basadas en la evidencia disponible.

### 2. Agente completamente abierto controlado por el LLM

El LLM tendría libertad para decidir qué herramienta ejecutar y qué paso realizar a continuación.

```
              ┌─────────┐
              │   LLM   │
              └────┬────┘
                   │
          ┌────────┼─────────┐
          ▼        ▼         ▼
        Logs    Metrics     Git
          │        │         │
          └────────┼─────────┘
                   │
                   ▼
                  LLM
                   │
                  ...
```

Ventajas: 

- Alta flexibilidad.
- Puede adaptar la investigación dinámicamente.
- Puede explorar diferentes caminos según la evidencia encontrada.
- Requiere menos lógica explícita para representar cada posible estrategia.

Desventajas:

- Menor determinismo.
- Difícil de probar exhaustivamente.
- Mayor dificultad para reproducir una investigación.
- Riesgo de loops o ejecución innecesaria de herramientas.
- Mayor dificultad para controlar costos y tiempos.
- Mayor superficie de seguridad.
- Más difícil determinar por qué el agente tomó un determinado camino.
- Puede producir comportamientos diferentes ante investigaciones similares.
- La evaluación de calidad se vuelve más compleja.

### 3. Workflow controlado con razonamiento agentic

LangGraph controla la estructura y las transiciones principales del proceso, mientras que el LLM participa en nodos específicos que requieren razonamiento.

```
                         Start
                           │
                           ▼
                  ┌─────────────────┐
                  │ Collect evidence│
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │Generate          │
                  │hypotheses       │
                  │     LLM         │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │Evaluate          │
                  │hypotheses       │
                  │     LLM         │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │Determine         │
                  │confidence       │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │Produce           │
                  │recommendation   │
                  │     LLM         │
                  └────────┬────────┘
                           │
                           ▼
                         Finish
```

Esta alternativa combina control estructural con capacidad de razonamiento.

## Decisión

Se utilizará LangGraph como mecanismo de control del workflow de investigación.

El workflow definirá los estados, nodos y transiciones permitidos durante una investigación.

El LLM podrá participar en nodos específicos que requieran razonamiento, pero no tendrá control arbitrario sobre el flujo de ejecución del sistema.

Los nodos podrán utilizar herramientas deterministas para obtener información de sistemas externos.

El LLM podrá decidir aspectos relacionados con el razonamiento dentro de los límites establecidos por el workflow, pero no podrá introducir arbitrariamente nuevas etapas o ejecutar cualquier herramienta fuera de las capacidades autorizadas por el workflow.

En consecuencia, la responsabilidad se divide de la siguiente manera:

```
┌─────────────────────────────────────────┐
│              LangGraph                  │
│                                         │
│  - Workflow                             │
│  - Estados                              │
│  - Transiciones                         │
│  - Control de ejecución                 │
│  - Checkpoints                          │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│                  LLM                    │
│                                         │
│  - Análisis                             │
│  - Generación de hipótesis              │
│  - Evaluación de evidencia               │
│  - Razonamiento                         │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│              Tools                      │
│                                         │
│  - Logs                                 │
│  - Metrics                              │
│  - Traces                               │
│  - Git                                  │
│  - Kubernetes                           │
└─────────────────────────────────────────┘
```

Esta decisión no implica que el workflow deba ser completamente lineal. Puede contener ramas, ciclos controlados y condiciones determinadas por el estado de la investigación.

Por ejemplo:

```
             Evaluate hypotheses
                     │
              ┌──────┴──────┐
              ▼             ▼
        Enough evidence?   No
              │             │
             Yes            ▼
              │       Collect more evidence
              │             │
              │             └──────┐
              ▼                    │
       Determine confidence ◄──────┘
              │
              ▼
       Produce recommendation
```

La diferencia fundamental es que los posibles caminos forman parte del workflow definido por la aplicación, en lugar de quedar completamente bajo el control del LLM.

## Consecuencias

### Positivas
- Determinismo: la estructura de la investigación está definida por el workflow y no depende completamente de las decisiones del LLM.
- Testabilidad: cada nodo y transición puede probarse individualmente.
- Observabilidad: es posible registrar el estado y el paso actual de cada investigación.
- Evaluación reproducible: las investigaciones pueden evaluarse utilizando workflows y estados conocidos.
- Control de costos: pueden establecerse límites sobre iteraciones, llamadas a herramientas y duración del workflow.
- Mayor seguridad: el LLM solamente puede operar dentro de las capacidades proporcionadas por el workflow.
- Razonamiento flexible: el LLM conserva capacidad para analizar evidencia y generar hipótesis sin controlar arbitrariamente el sistema.
- Evolución controlada: nuevas capacidades pueden incorporarse como nodos, tools o transiciones explícitas.
- Mejor auditabilidad: una investigación puede representar claramente qué etapas fueron ejecutadas y qué resultados produjo cada una.

### Negativas
- Mayor complejidad inicial: es necesario diseñar estados, nodos y transiciones del workflow.
- Menor libertad para el agente: algunas investigaciones pueden requerir caminos que todavía no estén representados por el workflow.
- Mantenimiento del workflow: a medida que aumenten los tipos de incidentes, puede crecer el número de nodos y transiciones.
- Acoplamiento con LangGraph: la implementación del workflow dependerá de las abstracciones proporcionadas por LangGraph.
- Diseño adicional de estados: será necesario definir cuidadosamente qué información pertenece al estado de ejecución y qué información pertenece al dominio de la investigación.

### Riesgos
- Workflow demasiado rígido: si se modelan pocos caminos posibles, el agente podría no disponer de una estrategia adecuada para incidentes desconocidos.
- Workflow excesivamente complejo: agregar demasiadas ramas y excepciones puede convertir el grafo en un sistema difícil de mantener.
- Confusión entre workflow y razonamiento: el LLM no debe convertirse indirectamente en el controlador del workflow mediante instrucciones que permitan ejecutar cualquier herramienta o modificar arbitrariamente el
estado.
- Loops no controlados: los ciclos utilizados para recopilar evidencia adicional deberán tener límites explícitos de iteraciones, tiempo y recursos.
- Dependencia excesiva del LLM: aunque LangGraph controle el workflow, los nodos que utilicen LLM seguirán siendo probabilísticos. Se deberán definir mecanismos de evaluación y validación de sus resultados.

## Notas
