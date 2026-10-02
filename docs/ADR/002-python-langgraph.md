# ADR-002: Tecnologías core del proyecto

- **Fecha:** 
- **Estado:** Aceptada

## Contexto

Como parte de elegir las tecnologías para le desarrollo de MVP, el primer paso será elegir el lenguaje de programación. Para el workflow, se decidió por LangGraph por interés para el desarrollo. No se busca comparar orquestadores, sino construir sobre esta tecnología. 

## Alternativas consideradas

### 1. Usar Python para desarrollar toda la aplicación

Ventajas:
- Fácil implementacion en tareas de IA/LLM
- Mayor documentación 
- Facil creación de API con FastAPI

Desventajas:
- Mayor consumo de memoria
- Concurrencia menos sencilla.

### 2. Usar Python orquestación y backend + Go para tareas críticas

Ventajas:
- Mayor rendimiento para tareas críticas con Go
- Se aprovecha mejor los dos ecosistemas y bondades de los lenguajes

Desventajas:
- Se debe implementar microservicios, no relevante para el MVP. 

## Decisión

El proyecto será Python-first y utilizará LangGraph para modelar el workflow de investigación. 

El ecosistema se compone de las siguientes tecnologías:

- FastAPI
- Pytest
- Pydantic
- FastMCP
- UV para gestión de dependencias

## Consecuencias

### Positivas
- Ecosistema de IA/LLM muy amplio.
- Herramientas de IA actualizan características primero a SDK y librerías python.
- Velocidad de propotipado

### Negativas
- Al llevarse a producción, debe evaluarse cuellos de botella y extraer componentes criticos.

### Riesgos
- Ninguno relevaten para este MVP.  

## Notas
Ninguna. 