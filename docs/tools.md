# Diagnostic Tools

## Overview

AI Incident Commander uses a small set of deterministic diagnostic tools to collect evidence from the systems involved in an incident.

The MVP exposes five tools:

```Text
search_logs
query_metrics
get_recent_deployments
get_commit
search_historical_incidents
```

These tools are intentionally deterministic.

The LLM does not execute tools directly. Instead, it proposes diagnostic actions, application code validates those requests, and the tools are executed through the MCP boundary.

The overall flow is:

```text
LLM
 │
 │ proposes tool requests
 ▼
Tool Selection
 │
 │ deterministic validation
 ▼
Tool Execution
 │
 │ MCP
 ▼
Mock Platform
 │
 │ diagnostic data
 ▼
Evidence
```

This separation is one of the central design decisions of the MVP.


## Tool Responsibilities

Each tool answers a specific diagnostic question.

| Tool | Diagnostic question |
|---|---|
| `search_logs` | What errors or relevant events are occurring? |
| `query_metrics` | How is the service behaving quantitatively? |
| `get_recent_deployments` | Did a recent deployment change the service? |
| `get_commit` | What code change is associated with a deployment? |
| `search_historical_incidents` | Have we seen a similar incident before? |

The tools should provide observations rather than conclusions.

For example:

```text
search_logs
    → "Payment provider request timed out"
```

is appropriate.

```text
search_logs
    → "The payment provider is definitely the root cause"
```

is not.

The latter is an interpretation and belongs to the reasoning layer.


## Tool Contracts

### `search_logs`

Searches logs associated with a service.

#### Purpose

Provides textual evidence about errors, warnings, timeouts, and other operational events.

#### Input

```text
service
query
```

Example:

```json
{
  "service": "checkout-api",
  "query": "database connection"
}
```

#### Output

The tool returns log observations that can be transformed into `Evidence`.

Example:

```Python
Evidence
source: search_logs
summary: "Database connection timeout"
data:
  timestamp: "2026-10-07T12:00:00Z"
  level: "ERROR"
  service: "checkout-api"
  message: "Database connection timeout"
```

#### Diagnostic role

Useful for identifying:

- errors
- timeouts
- dependency failures
- connection problems
- request failures
- other observable runtime symptoms


### `query_metrics`

Queries a supported metric for a service.

#### Purpose

Provides quantitative evidence about service behavior.

#### Supported metrics

The MVP currently supports:

```text
error_rate
request_rate
```

Not every scenario contains every metric.

For example, `request_rate` is available in the traffic-spike scenario but may not exist in other scenarios.

A valid metric request can therefore legitimately return no available data.

This distinction is important:

```text
supported metric
        ≠
metric data available in every scenario
```

#### Input

```text
service
metric
window_minutes
```

Example:

```json
{
  "service": "checkout-api",
  "metric": "error_rate",
  "window_minutes": 30
}
```

#### Output

Example:

```Python
Evidence
source: query_metrics
summary: "error_rate = 18.4%, baseline = 0.8%"
data:
  metric: "error_rate"
  value: 18.4
  baseline: 0.8
  unit: "percent"
  window_minutes: 30
```

#### Diagnostic role

Metrics help establish:

- whether an abnormal condition exists
- magnitude of an anomaly
- comparison against a baseline
- traffic/load changes
- error-rate changes

Metrics generally complement logs rather than replace them.


### `get_recent_deployments`

Returns recent deployments associated with a service.

#### Purpose

Provides evidence about recent changes to the running service.

#### Input

```text
service
```

Example:

```json
{
  "service": "checkout-api"
}
```

#### Output

Example:

```Python
Evidence
source: get_recent_deployments
summary: "Recent deployment deploy-456"
data:
  deployment_id: "deploy-456"
  version: "2026.10.04.17"
  commit_sha: "def456"
```

#### Diagnostic role

Useful when investigating:

- regressions
- sudden errors after a release
- configuration changes
- recently introduced behavior

The existence of a recent deployment does not prove that the deployment caused the incident.

It is evidence that must be correlated with other observations.


### `get_commit`

Retrieves information about a commit.

#### Purpose

Provides context about the code change associated with a deployment.

#### Input

```text 
commit_sha
```

Example:

```json
{
  "commit_sha": "def456"
}
```

#### Output

Example:

```Python
Evidence
source: get_commit
summary: "Commit def456: Refactor checkout validation flow"
data:
  commit_sha: "def456"
  message: "Refactor checkout validation flow"
```

#### Diagnostic role

Useful for connecting:

```text
deployment
    ↓
commit
    ↓
code change
```

This can provide stronger evidence for deployment-related hypotheses.


### `search_historical_incidents`

Searches historical incidents for similar operational patterns.

#### Purpose

Provides historical context that may help identify recurring failure modes.

#### Input

The tool accepts search context associated with the current incident.

Example:

```json
{
  "service": "checkout-api",
  "query": "database connection"
}
```

#### Output

Example:

```Python
Evidence
source: search_historical_incidents
summary: "Historical incident INC-42 had database connection pool exhaustion"
data:
  incident_id: "INC-42"
  summary: "Database connection pool exhaustion"
```

#### Diagnostic role

Historical incidents can help:

- identify recurring problems
- compare current symptoms with previous incidents
- provide additional context for hypotheses

Historical similarity is not proof of causality.


## Tool Selection

The LLM is responsible for proposing which tools should be used.

For example, given:

```text
Service: checkout-api

Incident:
Checkout requests are failing at an elevated rate.
```

the LLM may propose:

```text
search_logs
query_metrics
get_recent_deployments
```

The LLM does not execute these requests.

Instead, the application receives structured tool requests.

Conceptually:

```text
ToolRequest
├── tool_name
└── arguments
```

Example:

```json
{
  "tool_name": "query_metrics",
  "arguments": {
    "service": "checkout-api",
    "metric": "error_rate",
    "window_minutes": 30
  }
}
```


## Deterministic Validation

Tool requests produced by the LLM are treated as untrusted input. Before execution, deterministic application code validates them.

Validation includes:

- supported tool name
- required arguments
- argument types
- supported metric names
- rejection of unknown arguments
- tool-specific constraints

For example:

```text
LLM requests:

query_metrics(
    service="checkout-api",
    metric="cpu_usage"
)

        ↓

Validator

        ↓

Rejected:
Unsupported metric: cpu_usage
```

The LLM cannot expand the application's tool surface simply by generating a new tool name or argument.

This creates an important security and reliability boundary:

```text
LLM
 │
 │ untrusted proposal
 ▼
Deterministic validator
 │
 │ approved request
 ▼
Tool execution
```


## Tool Execution

After validation, the application executes the requested tool.

The workflow does not allow the LLM to directly call arbitrary Python functions or external services.

Instead, execution goes through the defined integration boundary.

The current execution path is:

```text
LangGraph
    │
    ▼
Tool execution service
    │
    ▼
MCP client
    │
    ▼
MCP server
    │
    ▼
Mock Platform
```

This separates:

- reasoning
- validation
- execution
- external-system access


## MCP Boundary

The MVP uses MCP as the boundary between the investigation service and diagnostic tools.

The Mock Platform exposes the diagnostic capabilities through an MCP server.

Conceptually:

```text 
Agent Service
     │
     │ MCP client
     ▼
MCP Server
     │
     ▼
Mock Platform
```

MCP is therefore not the reasoning engine.

It is the tools boundary.

The LLM does not need to know how the Mock Platform is implemented.

The application only needs to work with the defined tool contracts.

This makes the architecture compatible with replacing the simulated platform with real integrations later.


## Mock Platform

The Mock Platform simulates external operational systems.

It provides deterministic scenario data for the five MVP scenarios:

```text
1. database_pool_exhaustion
2. bad_deployment
3. payment_provider_degradation
4. traffic_spike
5. insufficient_evidence
```

The platform provides data for:

```text
Logs
Metrics
Deployments
Commits
Historical incidents
```

The scenario determines which data is available.

For example:

```text 
traffic_spike

logs:
    request queue depth increasing
    request timeout waiting for worker

metrics:
    request_rate
    error_rate

deployments:
    none

commits:
    none

historical incidents:
    traffic saturation incident
```

This deterministic dataset allows the investigation workflow to be tested repeatedly without depending on real infrastructure.


## Tool Data Availability

A valid diagnostic request does not guarantee that data exists.

For example:

```Python
query_metrics(
    metric="request_rate"
)
```

may be a valid request while the current scenario has no `request_rate` data.

The tool execution layer therefore distinguishes between:

```text
Invalid request
        vs.
Valid request with unavailable data
```

An invalid request is a validation or execution error. Unavailable diagnostic data is treated as an expected condition.

For the MVP, the workflow can skip unavailable diagnostic data and continue investigating with the evidence that is available.

This is important because the LLM may request a diagnostically reasonable signal that is simply not present in a particular scenario.


## Evidence Conversion

Tool responses are converted into the domain's `Evidence` representation.

Conceptually:

```text
Tool response
    │
    ▼
Tool execution layer
    │
    ▼
Evidence
```

For example:

```Python
query_metrics
        │
        ▼
{
  metric: "error_rate",
  value: 18.4,
  baseline: 0.8
}
        │
        ▼
Evidence
```

The evidence retains enough structured information to support later reasoning.

The reasoning layer should not need to re-query the original tool merely to understand the observation that was already collected.


## Deterministic vs. Agentic responsibilities

The tools architecture follows a clear responsibility boundary.

### Deterministic components

Responsible for:

- tool definitions
- input validation
- supported tool names
- supported metrics
- tool execution
- external integration
- evidence construction
- error handling

### Agentic components

Responsible for:

- deciding which diagnostic signals may be useful
- generating hypotheses
- evaluating hypotheses against evidence

The boundary can be summarized as:

```text 
                Agentic
                   │
                   ▼
          ┌─────────────────┐
          │  Tool selection │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │   Validation    │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Tool execution  │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │    Evidence     │
          └─────────────────┘
                Deterministic
```

This is intentional. The LLM is allowed to reason, but the application remains responsible for controlling what the system can actually execute.


## Tool Usage in the Investigation Workflow

The current workflow uses tools in the following sequence:

```text
START
  │
  ▼
select_tools
  │
  ▼
validate requests
  │
  ▼
collect_evidence
  │
  ├── search_logs
  ├── query_metrics
  ├── get_recent_deployments
  ├── get_commit
  └── search_historical_incidents
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

The workflow does not currently perform additional tool selection after hypothesis evaluation. Therefore, the reasoning loop is intentionally bounded.


## Tool Selection Is Probabilistic

Because the initial tool selection is LLM-driven, different executions may select different but reasonable combinations of tools.

For example, an investigation may collect:

```text
search_logs
query_metrics
get_recent_deployments
```

in one execution and:

```text
search_logs
query_metrics
search_historical_incidents
```

in another.

This is an expected property of the MVP. The system therefore does not require the LLM to produce one exact sequence of tool calls.

Instead, deterministic code guarantees that:

- requested tools must exist
- arguments must be valid
- unsupported metrics are rejected
- arbitrary tool execution is not possible
- tool failures are handled explicitly

The goal is useful and bounded investigation behavior rather than deterministic LLM output.


## Why Five Tools?

The MVP intentionally starts with five tools because they cover several complementary diagnostic dimensions:

```text
Runtime symptoms
    → search_logs

Quantitative behavior
    → query_metrics

Recent changes
    → get_recent_deployments
    → get_commit

Historical context
    → search_historical_incidents
```

Together they allow the investigation workflow to correlate:

```text
What is happening?
        +
How abnormal is it?
        +
What changed?
        +
What code was involved?
        +
Have we seen this before?
```

Adding more tools before validating this model would increase complexity without necessarily improving the MVP.


## Future Tool Extensions

The current tool boundary leaves room for additional integrations.

Potential future tools could include:

```text
get_service_dependencies
query_traces
get_feature_flags
get_container_status
get_database_status
```

These should only be added when a concrete investigation capability requires them. The architecture does not assume that every future diagnostic capability must become a tool immediately.

The guiding principle is:

> Add a tool when it provides a distinct diagnostic capability that the investigation workflow actually needs.


## Summary

The diagnostic tool architecture establishes four important boundaries:

```text
1. LLM proposes
       ↓
2. Application validates
       ↓
3. MCP executes
       ↓
4. Tools produce evidence
```

The five MVP tools are:

```text
search_logs
query_metrics
get_recent_deployments
get_commit
search_historical_incidents
```

They provide complementary operational signals while remaining deterministic and independently testable. The LLM controls neither tool implementation nor arbitrary execution.

The application remains responsible for validation, execution, error handling, and the conversion of external observations into domain evidence.