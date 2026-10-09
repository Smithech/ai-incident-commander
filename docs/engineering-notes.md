# Engineering Notes

This document captures the main engineering lessons learned while building **AI Incident Commander**.

Unlike the Architecture Decision Records (ADRs), which document explicit architectural decisions, these notes focus on **implementation lessons, trade-offs, debugging discoveries, and practical engineering insights** that emerged during development.

The goal is not to document every implementation detail, but to preserve the reasoning that would otherwise be easy to forget.

## Engineering Principles

1. Build vertically before expanding horizontally.
2. Keep domain state separate from workflow state.
3. Design asynchronous APIs independently from their execution mechanism.
4. Use deterministic validation around probabilistic components.
5. Treat prompts as guidance, not enforcement.
6. Distinguish invalid requests from unavailable diagnostic data.
7. Allow investigations to abstain when evidence is insufficient.
8. Represent uncertainty explicitly instead of forcing certainty.
9. Use integration tests where system boundaries matter.
10. Use deterministic scenarios as executable specifications.
11. Introduce infrastructure only when a concrete problem justifies it.
12. Prefer stable boundaries over speculative implementations.
13. Keep the MVP small enough to actually finish and publish.
14. Document trade-offs, not just final decisions.
15. Let the LLM reason, but keep the system in control.

The most important lesson is probably the last one:

> **AI does not remove the need for software engineering. It makes software boundaries, validation, observability, testing, and failure handling even more important.**

## Engineering Learnings


### 1. Build vertically, not horizontally

One of the most important lessons from the project was the value of building a **vertical slice** before implementing individual layers completely.

The first useful slice was intentionally small:

```text
Create Incident
      ↓
Create Investigation
      ↓
pending
      ↓
running
      ↓
completed / failed
      ↓
Investigation Events
```

Only after that lifecycle worked did the project add:

- LangGraph
- MCP
- Deterministic tools
- Eevidence
- Hypothesis generation
- Hypothesis evaluation
- LLM provider integration
- Result persistence
- Docker
- Migrations

This approach made each new layer build on something already working.

### Lesson

A project like this can easily become a collection of disconnected infrastructure components: `FastAPI`, `LangGraph`, `MCP`, `PostgreSQL`, `LLM`, `OpenTelemetry`, `Docker`. 
Having all of them present does not mean the system works.

A better progression is: 

> First make one complete path work. Then make that path intelligent. Then make it resilient. Then make it observable.

This reduced debugging complexity significantly.


### 2. Separate Domain State From Workflow State

One of the most important architectural distinctions was between **application state** and **workflow execution state**.

PostgreSQL owns durable application state: `Incident`, `Investigation`, `InvestigationEvent`, `InvestigationResult`.

LangGraph owns temporary workflow state: `incident context`, `tool requests`, `evidence`, `hypotheses`, `evaluations`, `workflow execution state`.

This distinction prevented the workflow implementation from dictating the domain model.

The key question became: **Does the application need to remember this after the workflow finishes?**. If yes, it belongs to durable domain state. If it only exists to execute the investigation, it can remain workflow state.

#### Why this matters

Without this distinction, it would have been tempting to create PostgreSQL tables for every intermediate object. That would have increased persistence complexity without providing a concrete MVP benefit. For the MVP, the final `InvestigationResult` is persisted as JSONB instead.


### 3. Async APIs do not require a distributed job queue

The investigation API was designed asynchronously from the beginning:

```text
POST /investigations
        ↓
202 Accepted
        ↓
investigation_id
        ↓
background execution
        ↓
GET /investigations/{id}
```

The first instinct in an asynchronous architecture can be to introduce a queue immediately. That would have been premature here.

The MVP uses: `FastAPI BackgroundTasks` + `PostgreSQL`. PostgreSQL is the source of truth for investigation lifecycle.

#### Trade-off

This provides a simple architecture:

```text
API
 ↓
BackgroundTasks
 ↓
Investigation
 ↓
PostgreSQL
```

But it does not provide durable background execution. If the process dies while an investigation is running, the in-process task can be lost. That limitation is explicitly accepted for the MVP.

#### Lesson

The important architectural decision was not: **Use BackgroundTasks forever**. It was: **Design the API contract so execution is asynchronous and independent from the HTTP request**.

That leaves room for a future durable worker without changing the public API contract.


### 4. `202 Accepted` is an architectural boundary

Returning: `202 Accepted` instead of blocking the request until the investigation finishes was more than an API implementation detail.

It establishes a clean boundary between: `request lifecycle` and `investigation lifecycle`

The client does not need to know whether the investigation is executed by:

- FastAPI BackgroundTasks
- a worker
- a queue
- another process
- a future distributed execution system

The API only exposes the durable investigation state.

This is an important distributed-systems principle: **The external contract should not depend on the internal execution mechanism**.


### 5. Database migrations should become explicit once schema evolves

Initially, the project used `Base.metadata.create_all()`. This was intentionally acceptable while the schema was still experimental.

Once `Investigation.result` was introduced, the schema had a real evolution history. At that point, `create_all()` was no longer sufficient as the schema management mechanism.

The project moved to:

```text
Alembic
    ↓
versioned migrations
    ↓
PostgreSQL
```

#### Lesson

Using migrations too early can add friction during rapid prototyping. Using `create_all()` forever creates a different problem.

A useful rule is: **Use the simplest schema mechanism while the schema is disposable. Introduce versioned migrations when schema evolution becomes part of the application**. The important part is recognizing that transition point.


### 6. The LLM should propose actions, not control the system

One of the central lessons of the project was the importance of separating **reasoning** from **execution**.

The LLM can propose:

```text
search_logs(...)
query_metrics(...)
get_recent_deployments(...)
```

But it does not directly execute those operations.

The control flow is:

```text
LLM
 ↓
tool request
 ↓
deterministic validation
 ↓
MCP
 ↓
tool execution
 ↓
evidence
```

This means the application remains responsible for:

- supported tool names
- required arguments
- argument validation
- supported metrics
- execution
- error handling
- persistence
- workflow transitions

#### Why this matters

An LLM is probabilistic. Application control flow should be deterministic wherever possible. The architecture therefore follows: **Let the LLM reason, but keep the system in control**. This became one of the strongest architectural principles of the project.


### 7. Deterministic validation is more Important than prompt instructions

The tool-selection prompt tells the model:

```text
Use supported tools.
Use valid arguments.
Do not invent metric names.
```

But prompt instructions are not enforcement. The application still validates the generated request. For example, the system explicitly restricts metrics to:

```text
error_rate
request_rate
```

If the model proposes an unsupported metric, the request is rejected before execution.

The same principle applies to:

- tool names
- required arguments
- unknown arguments
- argument types
- tool execution

#### Lesson

A useful mental model is:

```text
Prompt = guidance
Validation = enforcement
```

Never rely on the LLM prompt as the only security or correctness boundary.


### 8. Valid tool arguments do not guarantee available data

A subtle problem appeared while testing the traffic-spike scenario. `request_rate` is a valid metric. However, not every scenario contains `request_rate`.

For example:

```text
database_pool_exhaustion
    error_rate
    no request_rate
```

while:

```text
traffic_spike
    error_rate
    request_rate
```

Therefore these are two different concepts: `Is the request valid?` versus `Is data available for this request?`

The validator answers the first question. The Mock Platform answers the second. This distinction prevented the system from incorrectly treating missing scenario data as an invalid tool request.


### 9. Missing diagnostic data should not automatically fail an investigation

The LLM may request a valid diagnostic signal that is unavailable in the current scenario. For example: `query_metrics(request_rate)` may return `404 Not Found ` because that metric does not exist for the scenario.

The first implementation treated this as a general tool failure. That made the workflow too fragile. 

The final behavior distinguishes `invalid request / unexpected infrastructure failure` from `valid diagnostic request, but data unavailable`.

The latter is represented internally by `ToolDataUnavailableError` and the workflow skips that piece of evidence while continuing the investigation.

#### Lesson

In diagnostic systems, absence of one signal does not necessarily mean failure of the investigation.

A useful distinction is `Tool execution failed ≠ Requested diagnostic data does not exist`. Only the latter should be tolerated automatically.

### 10. The Mock Platform is part of the test architecture

The `Mock Platform` is not simply fake data for the demo. It provides a deterministic environment for:

- integration tests
- workflow tests
- scenario reproduction
- tool execution
- evaluation
- demos

Each scenario represents a known operational condition.

For example:

```text
database_pool_exhaustion
bad_deployment
payment_provider_degradation
traffic_spike
insufficient_evidence
```

This allows the project to ask **given this known environment, did the investigation produce reasonable evidence and hypotheses**. Without deterministic scenarios, evaluating an LLM-driven investigation would be significantly harder.


### 11. LLM-Based Tool Selection is probabilistic

A key discovery was that the same scenario does not necessarily produce exactly the same tool sequence every time.

For example, one run may select:

```text
search_logs
query_metrics
get_recent_deployments
```

while another may select:

```text
query_metrics
search_historical_incidents
```

This is expected because tool selection is model-driven. 

The important architectural question is therefore not: **Can we force the LLM to always select exactly these tools?"** but **can the system remain correct when the model chooses different reasonable diagnostic paths?**

This led to an important evaluation principle: **Evaluate evidence sufficiency and relevance, not only exact tool sequences**. Exact tool matching can be too strict for an agentic diagnostic system.


### 12. Prompt Engineering should not Replace architecture

Several prompts were adjusted during development. This was useful, but it also exposed a common trap. When an LLM produces an unexpected result, it is tempting to keep modifying the prompt until the output matches one desired example. That can create brittle behavior.

The better hierarchy is:

```text
1. architecture
2. deterministic validation
3. workflow constraints
4. data quality
5. prompt design
6. model behavior
```

Prompts should guide the model. They should not compensate for missing system boundaries. This became particularly clear with the insufficient-evidence scenario.


### 13. "Insufficient Evidence" is a real successful outcome

An investigation does not always need to produce a root cause. The `insufficient_evidence` scenario was intentionally designed to test whether the system could avoid inventing one.

The desired result is:

```text
evidence:
    available

hypotheses:
    []
```

rather than:

```text
hypothesis:
    "The internal error caused the incident."
```

The latter is circular reasoning rather than diagnosis.

#### Lesson

For AI systems, abstention is an important capability. A good investigation system should be able to say: **There is not enough evidence to support a meaningful hypothesis**. That is often more valuable than producing a confident but unsupported explanation.


### 14. Hypothesis Generation and Hypothesis Evaluation are different problems

The workflow separates:

```text
Evidence
   ↓
Hypothesis generation
   ↓
Hypothesis evaluation
```

Hypothesis generation asks: **What explanations could account for this evidence?**

Evaluation asks: **Does the existing evidence support or contradict these hypotheses?**

The evaluator does not perform new tool calls.

Its input is:

```text
existing evidence
+
existing hypotheses
```

and its output is:

```text
supported
contradicted
inconclusive
```

This separation keeps the reasoning stages understandable and testable.


### 15. "Inconclusive" is better than false certainty

The database-pool scenario exposed an important reasoning issue.

The evidence showed:

```text
database connection timeout
failed connection acquisition
high error rate
recent deployment
```

It did not prove the exact mechanism.

Possible explanations included:

```text
pool size reduction
connection leak
```

Both were plausible, but neither was directly established.

Therefore the evaluator correctly returned: `inconclusive`

This is a useful pattern for AI-assisted diagnosis: `Evidence → plausible hypothesis`,  does not automatically mean: `Evidence → proven root cause`. The system should preserve uncertainty rather than hide it.


### 16. JSONB was a deliberate MVP trade-off

`InvestigationResult` contains structured data such as:

```text
evidence
hypotheses
evaluations
```

Rather than creating separate relational tables for each concept, the MVP persists the completed result as JSONB. This keeps the persistence model small. The trade-off is that querying individual evidence or hypotheses relationally is less convenient.

That is acceptable because the current application primarily needs to `retrieve investigation result` rather than perform complex analytics across individual evidence records.

#### Lesson

A normalized schema is not automatically better. The right question is *what queries and invariants does the application actually need today?**. If future requirements demand analytics, filtering, or cross-investigation queries over evidence, the model can evolve.


### 17. Domain models should reflect real requirements

The project deliberately avoided prematurely introducing concepts such as:

- Recommendation
- RootCause
- Confidence
- Remediation
- HumanApproval
- persistent Evidence tables
- persistent Hypothesis tables

These are all plausible future features. But creating them before the application needs them would increase complexity without improving the current MVP. This reinforced a broader principle **Model the domain around current behavior, not imagined future features**. Future requirements can justify future schema changes.


### 18. Testing revealed infrastructure assumptions

The test suite initially failed with errors such as relation "incidents" does not exist. The problem was not application logic. The test database existed, but its schema had not been migrated. The production database had already been migrated by the Docker migration service. The test database had not. 

This was a useful reminder: A test suite is only as reproducible as its environment setup. For the MVP, the test database migration is documented in the runbook rather than introducing additional infrastructure. This is intentionally a known operational limitation.


### 19. Integration tests should use real boundaries selectively

The project does not mock every dependency.

Some tests exercise real boundaries:

```text
FastAPI
 ↓
PostgreSQL
 ↓
MCP
 ↓
Mock Platform
```

This is valuable because many failures occur between components rather than inside individual functions.

Unit tests remain useful for deterministic logic such as:

- tool validation
- hypothesis generation
- hypothesis evaluation
- tool execution behavior

But integration tests validate that the pieces actually work together.

#### Lesson

A healthy test strategy is not:

```text
mock everything
```

nor:

```text
integration test everything
```

Instead:

> Use unit tests for local logic and integration tests where the boundary itself is important.


### 20. The five scenarios became an executable specification

The scenarios are more than demo data. They define expected system behavior.

#### Database pool exhaustion

Expected signals include:

```text
database timeout
connection acquisition failures
elevated error rate
recent deployment
```

#### Bad deployment

Expected signals include:

```text
checkout errors
elevated error rate
recent deployment
related commit
```

#### Payment provider degradation

Expected signals include:

```text
provider timeout
provider 503
elevated error rate
historical provider incident
```

#### Traffic spike

Expected signals include:

```text
high request rate
queue growth
worker saturation/timeouts
historical traffic incident
```

#### Insufficient evidence

Expected behavior:

```text
limited evidence
no credible hypothesis
```

These scenarios form a small executable specification for the agent.


### 21. Scenario tests should not assume identical LLM behavior

One testing lesson was particularly important:

If integration tests use a real LLM, tests should avoid depending too heavily on one exact tool-selection sequence.

For example, this is brittle:

```text
assert selected_tools == [
    "search_logs",
    "query_metrics",
    "get_recent_deployments",
]
```

A better test can verify properties such as:

```text
tool names are valid
arguments are valid
investigation completes
relevant evidence is produced
no unsupported claims are introduced
```

This distinction is important when testing probabilistic systems. Deterministic application logic should have deterministic tests. LLM behavior should be evaluated with criteria appropriate to probabilistic outputs.


### 22. Migration as a separate Compose Service is simple and explicit

The migration process is modeled as:

```text
PostgreSQL
    ↓
migration service
    ↓
agent-service
```

The agent service waits for:

```text
migration completed successfully
```

This avoids putting migration logic inside application startup.

The application can therefore assume that its expected schema exists once it starts.

This separation also makes the deployment sequence visible:

```text
database available
        ↓
schema migrated
        ↓
application starts
```


### 23. Observability Became Easier to Reason About After the Boundaries Were Clear

Even though the full observability phase is deferred, the architecture already identifies useful boundaries:

```text
HTTP request
    ↓
Investigation
    ↓
Workflow
    ↓
Tool execution
    ↓
MCP
    ↓
Mock Platform

and:

Investigation
    ↓
LLM invocation
```

These boundaries naturally suggest future OpenTelemetry spans. The lesson is that good observability usually follows good architecture. If responsibilities are unclear, telemetry becomes unclear too.


### 24. Keep Advanced Infrastructure for When It Is Justified

Several technologies were deliberately not introduced:

- Kafka
- Redis
- Celery
- Temporal
- Kubernetes
- Elasticsearch
- vector databases

The project could have used them to appear more "production-like", but doing so would not solve a concrete MVP problem.

For example:

```text
Need durable distributed job execution?
→ consider a queue/worker.

Need semantic retrieval across a large corpus?
→ consider a vector database.

Need distributed deployment orchestration?
→ consider Kubernetes.
```

Without those requirements, the additional infrastructure would mostly increase operational complexity.

#### Lesson

A senior engineering decision is not always:

> "Which technology can I add?"

Often it is:

> "Which technology can I deliberately avoid?"


### 25. Architecture Should Leave Room for Evolution Without Implementing It Prematurely

The MVP intentionally has extension points.

For example:

```text
Current:
FastAPI BackgroundTasks
```

could later become:

```text
API
 ↓
durable job mechanism
 ↓
worker
 ↓
investigation
```

without changing:

```text
POST /investigations → 202
GET /investigations/{id}
```

Similarly:

```text
JSONB InvestigationResult
```

could later evolve into normalized tables if query requirements justify it.

And:

```text
Mock Platform
```

could eventually be replaced or supplemented by real integrations.

The important principle is:

> Design stable boundaries, not speculative implementations.


### 26. The MVP scope became more valuable than additional features

During development, it was easy to identify interesting next steps:

- more sophisticated agent loops
- human-in-the-loop
- confidence scoring
- automated evaluation
- OpenTelemetry
- durable workers
- retry policies
- more tools
- more providers
- multi-agent workflows

All of these are technically interesting. But implementing them before publishing the MVP would delay the actual goal. The project therefore separates:

#### MVP

```text
domain
scenarios
reasoning
Docker
documentation
demo
portfolio polish
```

#### Post-MVP

```text
evaluation framework
observability
resilience
advanced LangGraph features
durable execution
```

This is an important engineering lesson:

> A technically interesting feature is not necessarily the next highest-value feature.

### 27. Current system mental model

The implementation can now be understood through five boundaries:

```text
                 ┌─────────────────────┐
                 │       Client        │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     FastAPI API     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    Investigation    │
                 │      Service        │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     LangGraph       │
                 │      Workflow       │
                 └──────────┬──────────┘
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
       ┌───────────────┐        ┌────────────────┐
       │      LLM      │        │   PostgreSQL   │
       │   reasoning   │        │ durable state  │
       └───────┬───────┘        └────────────────┘
               │
               ▼
       ┌───────────────┐
       │ MCP boundary  │
       └───────┬───────┘
               │
               ▼
       ┌────────────────┐
       │ Mock Platform  │
       │ diagnostic data│
       └────────────────┘
```

The key control boundary remains:

```text
LLM proposes
    ↓
Application validates
    ↓
MCP executes
    ↓
Evidence enters workflow
```


## Closing Perspective

The project started as an exercise in combining FastAPI, LangGraph, MCP, PostgreSQL, and an LLM. It became more valuable as an engineering exercise by forcing explicit decisions about boundaries, determinism, asynchronous execution, failure handling, testing, and uncertainty.

The main takeaway is that building an AI-enabled backend is still fundamentally a software engineering problem. The LLM adds probabilistic reasoning, but the surrounding system must provide the contracts, controls, persistence, observability, and failure semantics that make that reasoning useful.