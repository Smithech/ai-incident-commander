# AI Incident Commander

AI-assisted incident investigation system built with Python, FastAPI, LangGraph, MCP, PostgreSQL, and Docker Compose.

The project explores how LLM-based reasoning can be integrated into a backend workflow while keeping **tool execution, validation, persistence, and workflow control deterministic**.

## What it does

Given an incident affecting a service, the system:

1. creates and persists the incident
2. starts an asynchronous investigation
3. uses an LLM to select relevant diagnostic tools
4. validates the requested tools and arguments
5. executes tools through an MCP boundary
6. collects evidence from a deterministic Mock Platform
7. generates hypotheses from the collected evidence
8. evaluates hypotheses against that evidence
9. persists the final investigation result

The core workflow is:

```text
Incident
   ↓
Async Investigation
   ↓
LLM tool selection
   ↓
Deterministic validation
   ↓
MCP tool execution
   ↓
Evidence
   ↓
Hypotheses
   ↓
Hypothesis evaluation
   ↓
InvestigationResult
   ↓
PostgreSQL
```

## Why this project?

The project is designed around a practical AI engineering question:

> How can an LLM participate in incident investigation without giving it unrestricted control over the system?

The architecture therefore separates:

```text
LLM
  → reasoning and proposed actions

Application
  → validation, workflow control and persistence

MCP / Tools
  → controlled access to diagnostic systems

PostgreSQL
  → durable application state
```

This makes the system easier to reason about, test, and evolve than an architecture where the LLM directly controls external systems.

## Architecture

The MVP consists of three main services:

```text
                    ┌─────────────────┐
                    │     Client      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Agent Service  │
                    │                 │
                    │ FastAPI         │
                    │ LangGraph       │
                    │ MCP             │
                    │ LLM             │
                    └───────┬─────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
        ┌─────────────────┐    ┌─────────────────┐
        │    PostgreSQL   │    │ Mock Platform   │
        │                 │    │                 │
        │ Domain state    │    │ Logs            │
        │ Investigations  │    │ Metrics         │
        │ Results         │    │ Deployments     │
        │ Events          │    │ Commits         │
        └─────────────────┘    │ Incidents       │
                               └─────────────────┘
```

The Mock Platform provides deterministic incident scenarios so the investigation workflow can be tested and demonstrated without depending on real production systems.

## Scenarios

The Mock Platform currently provides five deterministic scenarios:

- `database_pool_exhaustion`
- `bad_deployment`
- `payment_provider_degradation`
- `traffic_spike`
- `insufficient_evidence`

The first four provide different forms of diagnostic evidence.

`insufficient_evidence` is specifically designed to demonstrate that the system can recognize when the available evidence is not sufficient to establish a concrete cause.

## Example investigation

A typical investigation is asynchronous:

```text
POST /incidents
       ↓
Incident persisted
       ↓
POST /incidents/{id}/investigations
       ↓
202 Accepted
       ↓
pending
       ↓
running
       ↓
completed
       ↓
GET /investigations/{id}
```

The final result contains:

```text
InvestigationResult
├── evidence
├── hypotheses
└── evaluations
```

Because tool selection and hypothesis generation are LLM-driven, exact evidence and hypothesis output may vary between runs.

The workflow and application boundaries remain deterministic.

## Technology

- Python 3.12
- FastAPI
- LangGraph
- FastMCP
- PostgreSQL
- SQLAlchemy 2.x async API
- Pydantic
- OpenTelemetry-ready architecture
- pytest
- Docker Compose
- uv

## Running locally

The application is designed to run through Docker Compose without requiring a local Python installation.

Start the stack:

```bash
docker compose up --build
```

The main services are:

```text
Agent Service   → http://localhost:8000
Mock Platform   → http://localhost:8001
PostgreSQL      → localhost:5432
```

For the complete operational instructions, see:

- [`docs/runbook.md`](docs/runbook.md)

For a step-by-step product demonstration, see:

- [`docs/demo.md`](docs/demo.md)

## Documentation

### Architecture

Detailed system architecture, state boundaries, workflow, persistence, error handling, and design principles:

- [`docs/architecture.md`](docs/architecture.md)

### Domain

Domain entities, lifecycle, boundaries, and the distinction between domain state and workflow state:

- [`docs/domain.md`](docs/domain.md)

### Tools

Tool contracts, MCP boundary, deterministic validation, execution, and evidence generation:

- [`docs/tools.md`](docs/tools.md)

### Evaluation

Scenario ground truth, evaluation dimensions, and how investigation correctness is defined:

- [`docs/evaluation.md`](docs/evaluation.md)

### Runbook

How to start, test, operate, troubleshoot, and reset the local environment:

- [`docs/runbook.md`](docs/runbook.md)

### Demo

Step-by-step instructions for demonstrating the MVP and its insufficient-evidence behavior:

- [`docs/demo.md`](docs/demo.md)

### Engineering notes

Implementation notes and lessons learned during development:

- [`docs/engineering-notes.md`](docs/engineering-notes.md)

### Architecture Decision Records

Important architectural decisions are documented in:

- [`docs/decisions/`](docs/decisions/)

Key decisions include:

- Python + LangGraph
- PostgreSQL as durable application state
- deterministic tools vs agentic reasoning
- MCP as the tools boundary
- LangGraph workflow control
- Mock Platform
- evaluation strategy
- asynchronous investigations
- workflow state vs domain state
- LLM provider/model configuration
- investigation result persistence

## Project status

This repository represents the MVP implementation.

Currently implemented:

- asynchronous investigation API
- PostgreSQL persistence
- Alembic migrations
- LangGraph investigation workflow
- LLM-driven tool selection
- deterministic tool validation
- MCP tool execution
- five deterministic incident scenarios
- evidence collection
- hypothesis generation
- hypothesis evaluation
- persisted investigation results
- Docker Compose environment
- automated tests

The following areas are intentionally deferred for future iterations:

- formal automated evaluation framework
- advanced OpenTelemetry instrumentation and dashboards
- durable background workers
- advanced LangGraph checkpointing and resilience
- human-in-the-loop investigation
- remediation execution
- multi-agent workflows

The MVP intentionally avoids infrastructure such as Kafka, Redis, Celery, Kubernetes, or other distributed components that are not yet justified by the project's requirements.

## Engineering principles

The project follows a few core principles:

- **Build vertically, not horizontally**
- Prefer simplicity over premature infrastructure
- Keep deterministic responsibilities outside the LLM
- Validate model-generated actions before execution
- Keep domain state separate from workflow state
- Prefer real integrations where they provide useful confidence
- Make asynchronous APIs explicit
- Keep the Mock Platform deterministic and reproducible
- Introduce infrastructure complexity only when a concrete requirement justifies it

## Portfolio / interview focus

This project demonstrates practical experience with:

- backend API design
- asynchronous workflows
- PostgreSQL persistence
- distributed-system boundaries
- deterministic tool execution
- MCP integration
- LangGraph orchestration
- LLM integration
- AI-assisted reasoning
- resilience to incomplete diagnostic data
- testing AI-driven workflows
- Docker-based development environments

The central engineering idea is:

> **Let the LLM reason, but keep the system in control.**