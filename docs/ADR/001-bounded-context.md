# ADR-001: Incident Investigation como único bounded context

- **Fecha:** 
- **Estado:** Aceptada

## Context

AI Incident Commander necesita investigar incidentes de producción consultando múltiples fuentes externas:

- logs
- métricas
- deployments
- commits
- incidentes históricos

Se puede modelar cada fuente como un servicio o bounded context independiente, pero el objetivo del MVP es construir un sistema de investigación de incidentes, no reproducir la arquitectura completa de una plataforma de observabilidad.

Separar estas fuentes prematuramente introduciría múltiples servicios, comunicación entre servicios, contratos adicionales, complejidad operacional y problemas de deployment sin aportar valor al objetivo principal del MVP.

## Decisión

El MVP tendrá un único bounded context: `Incident Investigation`

Dentro de este contexto estarán los conceptos relacionados con la investigación:

- Incident
- Investigation
- InvestigationEvent
- Evidence
- Hypothesis
- Recommendation

Las fuentes externas de información no serán bounded contexts propios del sistema. Serán tratadas como external systems y se accederá a ellas mediante interfaces/tools.

Para el MVP se utilizará un `mock-platform` separado para simular estos sistemas externos.

### Architecture

```text
                    Incident Investigation
                    ┌─────────────────────┐
                    │                     │
                    │ Incident            │
                    │ Investigation       │
                    │ Evidence            │
                    │ Hypothesis          │
                    │ Recommendation      │
                    │                     │
                    └──────────┬──────────┘
                               │
                         tool contracts
                               │
                    ┌──────────▼──────────┐
                    │   External Systems  │
                    │                     │
                    │ Logs                │
                    │ Metrics             │
                    │ Deployments         │
                    │ Commits             │
                    │ Historical Incidents│
                    └─────────────────────┘
```

## Why
El principal problema de negocio es investigar un incidente y producir una conclusión respaldada por evidencia.

Las fuentes externas son mecanismos para obtener información necesaria para resolver ese problema, no el dominio principal del sistema.

Esto permite mantener el MVP pequeño mientras conservamos un boundary claro para introducir posteriormente integraciones reales.

## Consecuencias

### Positivas
- Menor complejidad operacional.
- Un único modelo de dominio.
- Desarrollo más rápido.
- Las fuentes externas pueden reemplazarse sin modificar el dominio de investigación.
- El mock-platform permite reproducir escenarios deterministas.
- Facilita evolucionar posteriormente hacia integraciones reales.

### Negativas
- El MVP no representa toda la separación de servicios que podría existir en una plataforma de producción.
- Algunas responsabilidades permanecen dentro del mismo servicio.
- Si el dominio crece significativamente, habrá que reevaluar los boundaries.

### Riesgos
- Ninguno

## Notas

Ninguna