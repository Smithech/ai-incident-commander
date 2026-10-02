# ADR-004: Deterministic tools vs agentic reasoning

- **Fecha:** 
- **Estado:** Aceptada

## Contexto

La integración de un LLM requiere definir su rol en el sistema. Puede integrarse a un modo agente, donde el LLM razona y determina los pasos a seguir, qué herramientas usar, e interpreta resultado para evaluar si alcanzó el objetivo dado; o es parte un workflow, con pasos, estados y salidas más deterministas, y el LLM interviene en los que el workflow decida. 

## Alternativas consideradas

### 1. Workflow 

Ventajas:

- Predectible
- Fácil de probar
- Mayor control de ejecución. 
- Costos más predecibles
- Seguridad más sencilla

Desventajas:

- Menor capacidad de adaptación a incidentes nuevos
- A mayor requerimientos, mayor complejidad del workflow.
- Menos capacidad de exploración

### 2. Razonamiento agéntico

Ventajas:

- Solución más flexible para donde el objetivo o tarea a realizar es más diverso, y modelar cada paso posible sería más complejo. 
- Hay LLM con capacidades de razonamiento potentes que permiten analizar y planificar la solución de tareas complejas. 
- Los modelos pueden realizar tareas a través de tools o el uso de MCP.

Desventajas:

- El flujo no es determinista
- Dificultar de testear el comportamiento
- Mayor de consumo de tokens y Costos impredecibles. 
- Alucinaciones o razonamiento incorrecto
- Mayores consideraciones de seguridad al darte tanta capacidades al modelo. 

### 3. Razonamiento agéntico con Tools deterministas

Ventajas:

- Combina flexibilidad y control
- Las herramientas son fáciles d
- Permite investigar incidentes desconocidos
- Mejor trazabilidad
- Permite introducir controles de seguridad
- Facilita la evolución
- Puedes cambiar el LLM sin cambiar las herramientas

Desventajas:

- Mayor complejidad arquitectónica
- El comportamiento del agente sigue siendo no determinista
- Testing más complejo
- Mayor costo computacional
- Posibilidad de razonamiento incorrecto
- El diseño de las herramientas se vuelve crítico

## Decisión

Razonamiento agéntico con Tools deterministas

Las herramientas de investigación serán deterministas y el proceso de selección de herramientas podrá utilizar razonamiento agentic. El agente no tendrá acceso directo a sistemas externos; toda interacción deberá realizarse mediante herramientas explícitamente registradas, tipadas y con límites de ejecución.

```
Tools
   ↓
deterministic evidence retrieval

Agent
   ↓
reasoning / correlation / hypotheses
```

## Consecuencias

### Positivas
- Equilibro entre adaptabildad y control
- Las herramientas pueden suministrarse al modelo a través de un MCP, perminitiendo controlar acciones permitidas y denegadas, contratos explícitos. 
- Las herramientas entregaran envidencia determinista al modelo, este razona, correlaciona, genera hipótesis y recomendaciones. 
- Mejora la evaluación y observabilidad.

### Negativas
- Hay que controlar y evaluar las salidas no deterministas del agente. 
- Evaluar las capacidades de diveross modelos para encontrar un punto de equilibro entre rendimiento y costos. 

### Riesgos
- Controlar la ejecución del modelo será clave para garantizar mejor rendimiento, coste y salidas que ahorren tiempo en la resolución de incidentes de software. 

## Notas

Ninguna. 
