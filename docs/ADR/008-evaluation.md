# ADR-008: Deterministic evaluation

- **Fecha:** 
- **Estado:** Aceptada

## Contexto

El sistema de investigación de incidentes utiliza razonamiento basado en LLM, por lo que su comportamiento no es completamente determinista.

Esto introduce una dificultad fundamental: no basta con verificar que el agente pueda ejecutar el workflow o producir una respuesta. Necesitamos determinar si sus investigaciones son correctas, relevantes y respaldadas por evidencia.

Si la estrategia de evaluación se define después de implementar el agente, existe el riesgo de optimizar el sistema para producir respuestas plausibles sin disponer de una forma objetiva de determinar si las investigaciones son correctas.

Por esta razón, la evaluación debe formar parte de la arquitectura del sistema desde el inicio.

Se utilizarán escenarios de incidentes con ground truth conocido. Cada escenario representará un caso de investigación con evidencia relevante, información irrelevante y un resultado esperado.

Conceptualmente:

```
Scenario
   │
   ├── Incident
   ├── Evidence
   ├── Ground truth
   └── Expected outcome
          │
          ▼
       Agent
          │
          ▼
     Investigation
          │
          ▼
      Evaluation
```

El objetivo no es exigir que el agente reproduzca exactamente un único camino de investigación, sino evaluar si llega a conclusiones correctas utilizando evidencia suficiente y evitando afirmaciones no respaldadas.

## Alternativas consideradas

### 1. Evaluación determinista con ground truth

Cada escenario tendrá un resultado esperado conocido y se comparará la investigación producida por el agente contra ese ground truth.

Los escenarios contendrán:

```
scenario
expected root cause
required evidence
expected recommendation
irrelevant signals
```

Se medirán posteriormente diferentes dimensiones de la investigación.

Ventajas: 

- Permite medir objetivamente el comportamiento del agente.
- Permite detectar regresiones entre versiones.
- Hace posible comparar diferentes implementaciones o modelos.
- Permite construir un conjunto de evaluación reproducible.
- Facilita evaluar por separado causa raíz, evidencia y recomendación.
- Permite identificar cuando el agente llega a una conclusión correcta por razones incorrectas.
- Puede ejecutarse automáticamente en CI/CD.
- Permite evaluar el comportamiento antes de introducir nuevos incidentes en producción.

Desventajas:

- Crear escenarios representativos requiere esfuerzo.
- El ground truth puede ser difícil de establecer para incidentes complejos.
- Los escenarios pueden no representar toda la diversidad de incidentes reales.
- Requiere definir criterios claros para determinar qué constituye evidencia suficiente o una recomendación correcta.

### 2. Evaluación manual/ad hoc

El agente sería desarrollado primero y posteriormente evaluado mediante revisión manual de investigaciones.

Los resultados podrían ser revisados por un ingeniero para determinar si la respuesta parece correcta.

Ventajas:

- Baja inversión inicial.
- Permite evaluar rápidamente prototipos.
- Puede utilizar casos reales de forma exploratoria.
- Es flexible ante comportamientos inesperados.

Desventajas:

- Resultados difíciles de reproducir.
- Evaluaciones subjetivas.
- Difícil detectar regresiones automáticamente.
- No permite comparar fácilmente diferentes versiones del agente.
- No proporciona una métrica consistente de calidad.
- Puede ocultar errores cuando la respuesta parece plausible.
- La evaluación termina dependiendo excesivamente del criterio del evaluador.

### 3. Evaluación exclusivamente mediante LLM-as-a-Judge

También existe la utilizar un segundo LLM evaluaría las investigaciones producidas por el agente, pero para este MVP no se considera este tipo de evaluación.

## Decisión
 
La evaluación del agente se realizará mediante escenarios deterministas con ground truth conocido.

## Consecuencias

### Positivas
- La evaluación se diseña antes de que el agente esté completamente implementado.
-  Existe una definición explícita de qué significa que una investigación sea correcta.
- Se pueden detectar regresiones automáticamente.
- Las diferentes versiones del agente pueden compararse utilizando los mismos escenarios.
- Es posible comparar diferentes modelos LLM o estrategias de prompting.
- Permite separar calidad de la conclusión de calidad del razonamiento.
- Los escenarios pueden ejecutarse de forma reproducible.
- La evaluación puede integrarse posteriormente en CI/CD.
- Se puede medir el progreso del agente de forma objetiva.
- Los casos difíciles pueden convertirse en nuevos escenarios de evaluación.

### Negativas

- Crear y mantener escenarios requiere esfuerzo.
- Los escenarios deben mantenerse sincronizados con la evolución del dominio.
- Determinar el ground truth puede ser complejo en incidentes ambiguos.
- Las métricas pueden incentivar la optimización hacia los escenarios conocidos.
- Una buena puntuación en escenarios controlados no garantiza por sí misma un buen comportamiento frente a incidentes completamente nuevos.
- Será necesario definir criterios de comparación para resultados generados por LLM que pueden utilizar diferentes formulaciones.

### Riesgos

- Ground truth incorrecto: si la causa raíz esperada es incorrecta, la evaluación puede penalizar una respuesta correcta.
- Dataset poco representativo: un conjunto pequeño o demasiado homogéneo de escenarios puede dar una percepción exageradamente positiva del desempeño.
- Overfitting a escenarios: el agente podría aprender patrones específicos de los escenarios en lugar de desarrollar una capacidad de investigación general.
- Evaluación superficial: medir únicamente si la causa raíz coincide puede ocultar que el agente llegó a ella utilizando evidencia incorrecta.
- Falsos positivos: una recomendación correcta acompañada de claims no respaldados podría considerarse incorrectamente como una investigación exitosa si no se evalúan las diferentes dimensiones por separado.
- Métricas de herramientas mal definidas: penalizar excesivamente el número de llamadas podría desincentivar investigaciones legítimas que requieren explorar evidencia adicional.

## Notas
