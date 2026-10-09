# Domain Model

## Overview

AI Incident Commander models an incident investigation as an asynchronous process that collects diagnostic evidence, generates hypotheses, evaluates those hypotheses, and persists the resulting investigation.

The domain model is intentionally small.

The MVP does not attempt to model every concept that could exist in a production incident-management platform. Instead, it focuses on the minimum concepts required to represent an investigation from creation to completion.

The main domain concepts are:

```text
Incident
   │
   └── Investigation
          │
          ├── InvestigationEvent
          │
          └── InvestigationResult
                 ├── Evidence[]
                 ├── Hypothesis[]
                 └── Evaluation[]
```

The workflow used to produce the result is separate from these persisted domain concepts.


## Core Concepts

### Incident

An `Incident` represents an operational problem that requires investigation.

At the MVP level, an incident contains the context needed by the investigation workflow:

- service
- title
- description
- creation timestamp

Conceptually:

```text
Incident
├── id
├── service
├── title
├── description
└── created_at
```

The incident is the input to an investigation.

The system does not currently model additional incident-management concepts such as:

- severity
- priority
- assigned engineer
- escalation policy
- incident timeline from external systems
- affected customers
- incident status beyond the investigation context

Those concepts could be added later if the product requires them.


### Investigation

An `Investigation` represents an asynchronous attempt to understand an incident.

An incident may have an investigation associated with it, and the investigation has its own lifecycle.

The MVP lifecycle is:

```text
pending
   │
   ▼
running
   │
   ├──► completed
   │
   └──► failed
```

The initial investigation is created with:

```text
status = pending
result = null
```

Once background execution begins:

```text
status = running
```

If the workflow completes successfully:

```text
status = completed
result = InvestigationResult
```

If execution fails:

```text
status = failed
result = null
```

The investigation stores durable information about the execution, including:

- investigation identifier
- incident relationship
- lifecycle status
- creation/update timestamps
- persisted investigation result when successful

The investigation itself does not contain the complete transient workflow state.


### Investigation Events

`InvestigationEvent` records important lifecycle transitions of an investigation.

The MVP records four event types:

```text
investigation.created
investigation.started
investigation.completed
investigation.failed
```

For example:

```text
Investigation
    │
    ├── investigation.created
    ├── investigation.started
    └── investigation.completed
```

Events provide a durable lifecycle history without requiring the system to persist every internal workflow step.

The events are intentionally coarse-grained.

The MVP does not persist events for every:

- LLM invocation
- tool selection decision
- tool execution
- hypothesis generation step
- LangGraph node transition

Those concerns belong to workflow execution and, eventually, observability rather than the current domain event model.


### Evidence

`Evidence` represents an observation obtained from a diagnostic tool.

Evidence is produced by deterministic tools such as:

- `search_logs`
- `query_metrics`
- `get_recent_deployments`
- `get_commit`
- `search_historical_incidents`

Conceptually:

```text
Evidence
├── id
├── source
├── summary
└── data
```

Examples:

```text
Evidence
├── source: search_logs
├── summary: "Database connection timeout"
└── data: {...}
```

or:

```text
Evidence
├── source: query_metrics
├── summary: "error_rate increased to 18.4%"
└── data: {...}
```

The important distinction is that evidence represents **observed information**, not an interpretation.

For example:

```text
Evidence:
"error_rate = 18.4%, baseline = 0.8%"
```

is evidence.

The statement:

```text
"The latest deployment caused the incident."
```

is not evidence. It is a hypothesis or conclusion derived from evidence.

This separation is important because the system should be able to distinguish:

```text
what the system observed
        ↓
what the system believes may explain it
```

During investigation execution, evidence is maintained inside the LangGraph workflow state.

When the workflow completes successfully, evidence becomes part of the persisted `InvestigationResult`.

The MVP does not use a separate PostgreSQL table for every evidence item.


### Hypothesis

A `Hypothesis` represents a possible explanation for the observed evidence.

Hypotheses are generated after evidence has been collected.

Conceptually:

```text
Hypothesis
├── id
├── statement
└── ...
```

For example:

```text
"The recent deployment introduced a defect in
the checkout validation flow."
```

A hypothesis is therefore different from evidence.

```text
Evidence
    ↓
Observation

Hypothesis
    ↓
Possible explanation
```

The system does not treat a generated hypothesis as fact.

A hypothesis must be evaluated against the available evidence.

The MVP intentionally does not introduce a complex hypothesis model with concepts such as:

- confidence score
- probability
- ranking
- causal graph
- hypothesis history
- automatic deduplication

Those capabilities may become useful later, but they are not necessary for the current MVP.


### Evaluation

An `Evaluation` describes how a hypothesis relates to the available evidence.

The MVP supports three verdicts:

```text
supported
contradicted
inconclusive
```

Conceptually:

```text
Evaluation
├── hypothesis_id
├── verdict
├── supporting_evidence_ids[]
├── contradicting_evidence_ids[]
└── reasoning
```

For example:

```text
Hypothesis:
"The recent deployment introduced a checkout defect."

Evaluation:
    verdict = supported
    supporting_evidence_ids = [
        "deployment-1",
        "commit-1",
        "metric-1"
    ]
```

An evaluation must reference identifiers that actually exist in the current investigation state.

This prevents the reasoning layer from creating references to nonexistent evidence or hypotheses.

The evaluation stage does not collect additional evidence.

The workflow boundary is:

```text
Tool selection
      ↓
Evidence collection
      ↓
Hypothesis generation
      ↓
Hypothesis evaluation
```

Once evaluation begins, it reasons over the evidence already collected.

The MVP deliberately does not implement an iterative loop such as:

```text
evaluate
   ↓
need more evidence?
   ↓
select another tool
   ↓
evaluate again
```

That may be introduced later if the investigation workflow needs adaptive reasoning.


### Investigation Result

`InvestigationResult` is the durable business result of a successfully completed investigation.

The current MVP result contains:

```text
InvestigationResult
├── evidence[]
├── hypotheses[]
└── evaluations[]
```

The result is persisted as JSONB associated with the `Investigation`.

Conceptually:

```text
Investigation
    │
    └── result
          │
          ├── evidence[]
          ├── hypotheses[]
          └── evaluations[]
```

The result is only persisted after successful workflow completion.

Therefore:

```text
pending
    result = null

running
    result = null

completed
    result = InvestigationResult

failed
    result = null
```

Partial results are not persisted in the MVP.

This keeps the persistence model simple and establishes a clear contract:

> A persisted investigation result represents a successfully completed investigation.


## Domain State vs. Workflow State

The application deliberately separates durable domain state from transient workflow state.

### Durable domain state

PostgreSQL owns the application state that must survive process restarts:

```text
PostgreSQL
├── Incident
├── Investigation
│   └── InvestigationResult
└── InvestigationEvent
```

This state is the source of truth for the API.

For example, a client querying:

```text
GET /investigations/{investigation_id}
```

reads the investigation lifecycle and persisted result from PostgreSQL.

### Workflow state

LangGraph owns the state required while an investigation is being executed:

```text
InvestigationState
├── incident_id
├── service
├── incident_title
├── incident_description
├── tool_requests
├── evidence
├── hypotheses
└── evaluations
```

This state exists to coordinate workflow execution.

It is not the API's source of truth.

The distinction can be summarized as:

```text
                 ┌──────────────────────┐
                 │     PostgreSQL       │
                 │                      │
                 │ Incident             │
                 │ Investigation        │
                 │ InvestigationEvent   │
                 │ InvestigationResult  │
                 └──────────┬───────────┘
                            │
                     durable state
                            │
                            ▼
                 ┌──────────────────────┐
                 │      LangGraph       │
                 │                      │
                 │ InvestigationState   │
                 │                      │
                 │ tool requests        │
                 │ evidence             │
                 │ hypotheses           │
                 │ evaluations          │
                 └──────────────────────┘
```

This boundary prevents the workflow framework from becoming the domain persistence layer.


## Investigation Lifecycle

The complete lifecycle can be represented as:

```text
POST /incidents
      │
      ▼
Incident created
      │
      │ POST /incidents/{id}/investigations
      ▼
Investigation created
status = pending
      │
      │ background execution
      ▼
status = running
      │
      ▼
LangGraph workflow
      │
      ├── select tools
      ├── collect evidence
      ├── generate hypotheses
      └── evaluate hypotheses
      │
      ▼
InvestigationResult
      │
      ▼
status = completed
```

If an execution error occurs:

```text
pending
   ↓
running
   ↓
failed
```

A failed investigation does not persist a partial `InvestigationResult`.


## Domain Boundaries

The domain model intentionally separates several responsibilities.

### Incident

Provides the context for investigation.

### Investigation

Represents the asynchronous investigation process and its lifecycle.

### InvestigationEvent

Provides durable lifecycle history.

### Evidence

Represents observations obtained from diagnostic systems.

### Hypothesis

Represents possible explanations derived from observations.

### Evaluation

Represents the relationship between a hypothesis and the collected evidence.

### InvestigationResult

Provides the completed, persisted representation of the investigation.

This gives the investigation a clear conceptual pipeline:

```text
Incident
   │
   ▼
Investigation
   │
   ▼
Evidence
   │
   ▼
Hypotheses
   │
   ▼
Evaluations
   │
   ▼
InvestigationResult
```


## What is not yet part of the domain

The MVP deliberately does not model several concepts that may become useful later.

### Recommendation

The current result does not contain a separate recommendation such as:

```text
"Rollback deployment deploy-456."
```

The current workflow focuses on evidence, hypotheses, and evaluations.

A recommendation can be introduced once the system has enough reasoning and evaluation maturity to make that concept useful.

### Root Cause

There is currently no dedicated `RootCause` entity.

A hypothesis can describe a possible root cause, but the system does not currently persist a formally declared root cause.

This avoids prematurely presenting an LLM-generated interpretation as ground truth.

### Confidence

The MVP does not assign numerical confidence to hypotheses or evaluations.

Confidence would require defining semantics that are currently more complex than the MVP needs.

### Human Approval

There is no human-in-the-loop approval state.

An investigation can complete without an engineer explicitly approving its findings.

Human approval may become relevant when the system begins recommending or executing remediation actions.

### Remediation

The MVP does not execute operational changes.

It investigates incidents and produces findings.

Actions such as:

```text
rollback deployment
restart service
increase database capacity
disable feature
```

are outside the current domain boundary.

### Persistent Evidence and Hypothesis Tables

Evidence and hypotheses are not separate PostgreSQL entities in the MVP.

They are part of the persisted `InvestigationResult`.

This avoids introducing additional relational structure before there is a concrete requirement for querying, lifecycle management, or independent relationships between these objects.


## Why the Domain is intentionally small

The MVP is designed around a simple principle:

> Persist concepts that have durable business meaning; keep execution details inside the workflow.

This means the system does not create a domain entity for every internal concept.

For example:

```text
LLM request
LangGraph node
tool invocation
prompt
workflow transition
```

are important implementation or execution concepts, but they are not currently independent domain entities.

The resulting model remains small enough to understand while still representing the complete investigation lifecycle.


## Summary

The MVP domain can be summarized as:

```text
Incident
   │
   │ starts
   ▼
Investigation
   │
   ├── lifecycle → InvestigationEvent[]
   │
   └── successful execution
          │
          ▼
   InvestigationResult
          │
          ├── Evidence[]
          ├── Hypothesis[]
          └── Evaluation[]
```

The central boundary is:

```text
Domain
    = what the application needs to remember

Workflow
    = how the application performs the investigation
```

PostgreSQL is responsible for durable domain state.

LangGraph is responsible for workflow execution state.

The LLM contributes reasoning and proposes diagnostic actions, but it does not define the domain model or directly control persistence and execution.