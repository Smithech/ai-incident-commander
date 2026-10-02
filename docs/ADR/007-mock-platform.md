# ADR-007: Mock Platform

- **Fecha:** 
- **Estado:** Aceptada

## Contexto

Como parte del flujo de investigación de un incidente, el sistema debe recolectar datos de diversas fuentes que será la evidencia para generar y validad la hipótesis del incidente. Estas fuentes son externas al sistema. 

## Alternativas consideradas

### 1. Datos simulados
Ventajas:
- Mayor facilidad de implementación
- MVP más ligero para demos
- Los sitemas externos no es el objetivo primordial del MVP

Desventajas:
- No se acerca a la complejidad de un sistema eral. 

### 2. Constriur sistemas externos

Ventajas:
- Entorno cercano al real.
- MVP más completo. 

Desventajas:
- Mayor complejidad y consumo de recursos
- Más variables para considerar en un demo.
- Incremento en el tiempo de desarrollo que no aporta valor al core del MVP.

## Decisión

Los sistemas externos serán simulados mediante `mock-platform`.

## Consecuencias

### Positivas
- Facilidad de implementación del MVP y ejecución de demos.
- La arquitectura se desarrollará de forma que facilita implementar estos sistemas externos. 

### Negativas
- Ninguna para el nivel actual del MVP.

### Riesgos
- Ninguno

## Notas
