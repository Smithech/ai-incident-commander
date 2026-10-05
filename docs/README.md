# Documentation

La documetación de este repositorio se estructura de la siguiente forma:

- `architecture.md`.  Explica cómo está construido el sistema y cómo se comunican sus partes.

- `domain.md`. Es la referencia conceptual del proyecto.

- `tools.md`. Explica qué capacidades externas puede utilizar el agente y cuáles son sus contratos.

- `evaluation.md`. Su pregunta es: ¿Cómo sabemos que el agente realmente funciona?

- `demo.md`. Guía paso a paso de cómo ejecutar el proyecto y algunos ejemplos de respuestas.

- `engineering-notes.md`. Es mi registro de aprendizaje y decisiones tomadas.

- `ADR/`. Documenta y explica las decisiones arquitectónicas tomadas durante el desarrollo.

Lista de ADR:

- ADR-001: Incident Investigation como único bounded context
- ADR-002: Tecnologías core del proyecto
- ADR-003: PostgreSQL como estado persistente
- ADR-004: Deterministic tools vs agentic reasoning
- ADR-005: MCP como tools boundary
- ADR-006: Workflow controlado por LangGraph
- ADR-007: Mock Platform
- ADR-008: Deterministic evaluation
- ADR-009: Ejecución asíncrona de investigaciones
- ADR-010: LangGraph workflow state vs domain state
- ADR-011: LLM provider and model configuration
- ADR-012: Persistencia del resultado de una investigación