# Architecture

## Overview

AI Incident Commander is an asynchronous incident investigation system. The system combines a conventional backend architecture with an LLM-driven investigation workflow.

The main architectural principle is:

> **The LLM is responsible for reasoning and proposing diagnostic actions, while deterministic application code controls validation, execution, persistence, and workflow boundaries.**

The MVP is intentionally implemented as a small number of services:

```text
┌──────────────────────┐
│      Client          │
└──────────┬───────────┘
           │ HTTP
           ▼
┌──────────────────────┐
│    Agent Service     │
│                      │
│ FastAPI              │
│ Investigation API    │
│ LangGraph Workflow   │
│ Tool Execution       │
│ LLM Integration      │
└───────┬───────┬──────┘
        │       │
        │       └──────────────────┐
        │                          │
        ▼                          ▼
┌───────────────┐          ┌────────────────┐
│  PostgreSQL   │          │ Mock Platform  │
│               │          │                │
│ Incidents     │          │ Logs           │
│ Investigations│          │ Metrics        │
│ Events        │          │ Deployments    │
│ Results       │          │ Commits        │
└───────────────┘          │ Past incidents │
                           └────────────────┘
```


## Services

### Agent Service

The Agent Service is the main application. It exposes the HTTP API and coordinates investigation execution.

Responsibilities include:
- incident management
- investigation lifecycle
- persistence
- LangGraph workflow execution
- LLM integration
- deterministic tool validation
- MCP tool execution
- investigation result persistence

The service is implemented as a single Python application rather than multiple independently deployed services.

This keeps the MVP simple while maintaining clear internal boundaries.



### Mock Platform

The Mock Platform simulates the external systems that an incident investigation would normally query.

It provides deterministic data for:

- logs
- metrics
- deployments
- commits
- historical incidents

The platform supports several predefined incident scenarios.

The purpose is to provide a reproducible environment for development, testing, and demonstrations without requiring integrations with real production systems.


### PostgreSQL

PostgreSQL is the durable source of truth for application state.

The MVP persists:

```text
Incident
Investigation
InvestigationEvent
InvestigationResult
```

PostgreSQL does not act as LangGraph's internal workflow state store. That distinction is intentional.


## Domain State vs Workflow State

The system separates durable application state from workflow execution state.

### PostgreSQL

PostgreSQL owns domain state:

```text
Incident
Investigation
InvestigationEvent
InvestigationResult
```

This state must survive process restarts and be queryable independently of the workflow implementation.

### LangGraph

LangGraph owns workflow execution state:

```text
incident context
tool requests
evidence
hypotheses
evaluations
```

This state exists to execute the investigation workflow.

The boundary can be summarized as:

```text
PostgreSQL
├── Incident
├── Investigation
│   └── InvestigationResult
└── InvestigationEvent

LangGraph
└── InvestigationState
    ├── incident context
    ├── tool requests
    ├── evidence
    ├── hypotheses
    └── evaluations
```

LangGraph state should not automatically become a database entity.

Likewise, PostgreSQL domain entities should not be introduced merely because a value exists in workflow state.


## Asynchronous Investigation Execution

Creating an investigation does not block the HTTP request until the investigation finishes.

The API contract is:

```text
POST /incidents/{incident_id}/investigations
        │
        ▼
     202 Accepted
        │
        ▼
 investigation created
        │
        ▼
 background execution
```

The investigation lifecycle is:

```text
pending
   │
   ▼
running
   │
   ├──────────────► failed
   │
   ▼
completed
```

PostgreSQL is the source of truth for the lifecycle.

For the MVP, execution uses FastAPI `BackgroundTasks`.

This was chosen because the project needs asynchronous behavior without introducing a distributed task infrastructure before there is a concrete requirement for it.

The trade-off is explicit:

- simple deployment
- no additional queue infrastructure
- easy local development

but:

- work is in-process
- a process crash can interrupt an investigation
- it is not a durable job queue
- it does not provide exactly-once execution

A future implementation could replace the execution mechanism without changing the external asynchronous API contract.


## Investigation Workflow

LangGraph orchestrates the investigation.

The current workflow is:

```text
START
  │
  ▼
select_tools
  │
  ▼
collect_evidence
  │
  ├── no evidence ─────────────► END
  │
  ▼
generate_hypotheses
  │
  ▼
evaluate_hypotheses
  │
  ▼
END
```

### `select_tools`

The LLM analyzes the incident context and proposes diagnostic tool requests.

The model does not directly execute tools.

The output is represented as structured `ToolRequest` objects.


### `collect_evidence`

Each requested tool is validated and executed through the deterministic tool execution layer.

The resulting data is normalized into `Evidence`.

The workflow can continue when an individual diagnostic signal is unavailable.

For example:

```text
LLM requests request_rate
        │
        ▼
Mock Platform
        │
        ▼
404 — metric unavailable
        │
        ▼
ToolDataUnavailableError
        │
        ▼
skip this signal
        │
        ▼
continue investigation
```

Unexpected failures are not silently ignored.

This distinction allows the workflow to tolerate incomplete diagnostic data without hiding actual application or infrastructure failures.


### `generate_hypotheses`

The LLM generates hypotheses using the collected evidence.

The hypothesis must reference evidence that actually exists in the workflow state.

The system does not allow the reasoning layer to invent evidence.


### `evaluate_hypotheses`

The evaluator analyzes each hypothesis against the existing evidence.

Possible results are:

```text
supported
contradicted
inconclusive
```

The evaluator cannot request additional tools at this stage.

This creates a clear boundary:

```text
Tool selection
      ↓
Evidence collection
      ↓
Hypothesis generation
      ↓
Hypothesis evaluation
```

The current MVP deliberately does not implement an open-ended reasoning loop.


## End-to-end MVP flow

```text
Client
  │
  │ POST /incidents
  ▼
Incident persisted
  │
  │ POST /incidents/{id}/investigations
  ▼
Investigation created
status = pending
  │
  │ 202 Accepted
  ▼
Background execution
  │
  ▼
status = running
  │
  ▼
LangGraph
  │
  ├── Select tools
  │       ↓
  │   Validate requests
  │       ↓
  │   Execute via MCP
  │       ↓
  │   Mock Platform
  │       ↓
  │   Evidence
  │
  ├── Generate hypotheses
  │
  └── Evaluate hypotheses
  │
  ▼
InvestigationResult
  │
  ▼
PostgreSQL
  │
  ▼
GET /investigations/{id}
  │
  ▼
completed
```


## LLM Boundary

The LLM is used for reasoning-heavy tasks:

```text
LLM
├── select diagnostic tools
├── generate hypotheses
└── evaluate hypotheses
```

Deterministic application code handles:

```text
Application
├── validate tool requests
├── execute tools
├── normalize external data
├── persist domain state
├── control workflow transitions
└── validate evidence references
```

This boundary is one of the central architectural decisions of the project.

The system does not give the model unrestricted access to external systems.


## MCP Boundary

MCP provides the boundary between agentic reasoning and diagnostic capabilities.

Conceptually:

```text
LangGraph / Agent
        │
        ▼
ToolRequest
        │
        ▼
Deterministic validation
        │
        ▼
MCP
        │
        ▼
Mock Platform
```

The MCP layer exposes diagnostic capabilities without allowing the LLM to directly manipulate the underlying platform.

Current tools are:

```text
search_logs
query_metrics
get_recent_deployments
get_commit
search_historical_incidents
```

The detailed contracts are documented in `docs/tools.md`.


## Persistence Model

An investigation result is persisted after successful workflow completion.

The current result contains:

```text
InvestigationResult
├── evidence[]
├── hypotheses[]
└── evaluations[]
```

The result is stored as JSONB associated with the `Investigation`.

The MVP does not create separate database tables for Evidence or Hypothesis.

This is intentional because the current application does not require independent querying, lifecycle management, or relationships for those objects.

The persistence boundary is:

```text
LangGraph
    │
    │ successful completion
    ▼
InvestigationResult
    │
    ▼
PostgreSQL JSONB
```

Partial investigation results are not persisted as business results.


## Error Handling

The system distinguishes between recoverable diagnostic incompleteness and actual execution failures.

### Recoverable

Example:

```text
metric does not exist in current scenario
```

Behavior:

```text
skip unavailable signal
continue investigation
```

### Non-recoverable

Examples:

- MCP connection failure
- malformed tool response
- invalid application state
- unexpected runtime exception

Behavior:

```text
investigation → failed
```

The application intentionally does not catch broad exceptions merely to make investigations appear successful.


## Database Migrations

PostgreSQL schema evolution is managed with Alembic.

The initial MVP used SQLAlchemy metadata creation during early development.

Once the schema required a real evolution, versioned migrations were introduced.

The Docker Compose startup sequence is:

```text
PostgreSQL
    │
    ▼
migration service
    │
    │ alembic upgrade head
    ▼
agent-service
```

This ensures that the application starts only after the required schema version has been applied.


## Configuration

LLM configuration is externalized through environment variables.

The application currently uses an OpenAI-compatible API interface.

Configuration includes:

```text
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
```

The workflow depends on an application-level LLM abstraction rather than directly coupling workflow code to a specific provider.

The initial provider choice is documented in ADR-010.


## Deployment Model

The MVP runs using Docker Compose:

```text
docker compose up --build
```

Containers:

```text
agent-service
mock-platform
postgres
migration
```

The migration service is a short-lived initialization container.

No distributed message broker or external task queue is required for the current MVP.


## Design Principles

The architecture follows several principles:

### Build vertically

Features are implemented end-to-end before introducing additional infrastructure.

### Prefer deterministic boundaries

LLM output is treated as untrusted input that must be validated before execution.

### Keep domain state separate from workflow state

Not every workflow value needs to become a database entity.

### Introduce infrastructure only when justified

The MVP intentionally avoids Kafka, Redis, Celery, Kubernetes, and similar infrastructure because the current requirements do not justify their operational complexity.

### Preserve evolution paths

The current architecture leaves room for future improvements such as durable workers, richer evaluation, observability, retries, and human-in-the-loop workflows without requiring those components in the MVP.