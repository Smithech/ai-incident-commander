# Demo

## Overview

This document explains how to demonstrate the AI Incident Commander MVP end to end.

The demo focuses on two scenarios:

1. `database_pool_exhaustion` — demonstrates an investigation with meaningful diagnostic evidence and generated hypotheses.
2. `insufficient_evidence` — demonstrates that the system can complete an investigation without inventing a root cause when the available evidence is insufficient.

The goal is not to demonstrate every implementation detail.

The goal is to show the core behavior of the system:

```text
Incident
   ↓
Investigation
   ↓
LLM selects diagnostic tools
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
```


## 1. Start the system

From the repository root:

```bash
docker compose up --build
```

Wait until:

- PostgreSQL is healthy
- migrations complete successfully
- Mock Platform is running
- Agent Service is running

The Agent Service is available on:

```text
http://localhost:8000
```

The Mock Platform is available on:

```text
http://localhost:8001
```


## 2. Verify the active scenario

The first demo uses:

```text
MOCK_PLATFORM_SCENARIO=database_pool_exhaustion
```

This is also the scenario expected by the complete test suite.

First, verify which scenario is currently active:

```bash
docker compose exec mock-platform printenv MOCK_PLATFORM_SCENARIO
```

Expected output:

```text
database_pool_exhaustion
```

If a different scenario is active, update the environment and recreate the Mock Platform:

```bash
MOCK_PLATFORM_SCENARIO=database_pool_exhaustion \
docker compose up -d --force-recreate mock-platform
```

Verify again:

```bash
docker compose exec mock-platform printenv MOCK_PLATFORM_SCENARIO
```

Expected:

```text
database_pool_exhaustion
```

This verification is important because the complete test suite currently depends on this scenario.


## 3. Create an incident

Create an incident through the Agent Service:

```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Checkout API elevated error rate",
    "description": "Checkout API is returning a significantly higher number of errors than normal.",
    "service": "checkout-api",
    "severity": "high"
  }'
```

The API returns the created incident, including its `id`.

Copy the returned `id`. It will be used in the next request as `<INCIDENT_ID>`.

### Example output

```json
{
   "id":"1f47e59d-371a-4844-99a1-91e92f5dcb2c",
   "title":"Checkout API elevated error rate",
   "description":"Checkout API is returning a significantly higher number of errors than normal.",
   "service":"checkout-api",
   "severity":"high",
   "created_at":"2026-10-09T04:32:08.095523Z"
}
```


## 4. Start an investigation

Start an investigation for the incident using the ID returned by the previous request:

```bash
curl -X POST http://localhost:8000/incidents/<INCIDENT_ID>/investigations
```

The API is asynchronous and should return:

```json
{
  "investigation_id": "...",
  "status": "pending"
}
```

Copy the returned `investigation_id`. It will be used in the following requests as `<INVESTIGATION_ID>`.

The HTTP request does not wait for the investigation to finish.

This demonstrates the MVP's asynchronous investigation contract.

### Example output

```json
{
   "id":"df2635ee-e5c7-453d-a6e8-07c08ac6fb4b",
   "incident_id":"eee74a1d-12b8-499a-a2e7-4a5c83c81298",
   "status":"pending",
   "created_at":"2026-10-09T04:35:12.073782Z",
   "result":null
}
```


## 5. Poll the investigation

Use the returned investigation ID:

```bash
curl http://localhost:8000/investigations/<INVESTIGATION_ID>
```

Initially the investigation may be:

```json
{
  "status": "pending"
}
```

Then:

```json
{
  "status": "running"
}
```

Eventually:

```json
{
  "status": "completed"
}
```

The normal lifecycle is:

```text
pending
   ↓
running
   ↓
completed
```

If an unexpected error occurs:

```text
pending
   ↓
running
   ↓
failed
```

Because execution is asynchronous, repeat the `GET` request until the investigation reaches `completed` or `failed`.

### Example output — pending

```json
{
   "id":"df2635ee-e5c7-453d-a6e8-07c08ac6fb4b",
   "incident_id":"eee74a1d-12b8-499a-a2e7-4a5c83c81298",
   "status":"pending",
   "created_at":"2026-10-09T04:35:12.073782Z",
   "result":null
}
```

### Example output — running

```json
{
   "id":"df2635ee-e5c7-453d-a6e8-07c08ac6fb4b",
   "incident_id":"eee74a1d-12b8-499a-a2e7-4a5c83c81298",
   "status":"running",
   "created_at":"2026-10-09T04:35:12.073782Z",
   "result":null
}
```

### Example output — completed

```json
{
  "id": "df2635ee-e5c7-453d-a6e8-07c08ac6fb4b",
  "incident_id": "eee74a1d-12b8-499a-a2e7-4a5c83c81298",
  "status": "completed",
  "created_at": "2026-10-09T04:35:12.073782Z",
  "result": {
    "evidence": [
      {
        "id": "d50ee441-14f1-439f-9691-b2f658871b9c",
        "source": "query_metrics",
        "summary": "error_rate for checkout-api is 18.4percent, baseline 0.8percent.",
        "data": {
          "metric": "error_rate",
          "service": "checkout-api",
          "value": 18.4,
          "unit": "percent",
          "baseline": 0.8,
          "window_minutes": 30
        }
      },
      {
        "id": "d785b998-4d7f-453b-a027-13c76e22a7a9",
        "source": "get_recent_deployments",
        "summary": "Deployment deploy-123 of checkout-api version 2026.10.03.42 was deployed at 2026-10-03T13:55:00+00:00.",
        "data": {
          "id": "deploy-123",
          "service": "checkout-api",
          "version": "2026.10.03.42",
          "commit_sha": "abc123",
          "deployed_at": "2026-10-03T13:55:00Z"
        }
      }
    ],
    "hypotheses": [
      {
        "id": "47c70594-c84e-4b0b-be92-19bf9541cf8a",
        "statement": "The deployment deploy-123 of checkout-api version 2026.10.03.42 introduced a defect that caused the error rate to increase.",
        "supporting_evidence_ids": [
          "d50ee441-14f1-439f-9691-b2f658871b9c",
          "d785b998-4d7f-453b-a027-13c76e22a7a9"
        ],
        "contradicting_evidence_ids": []
      }
    ],
    "evaluations": [
      {
        "hypothesis_id": "47c70594-c84e-4b0b-be92-19bf9541cf8a",
        "verdict": "inconclusive",
        "supporting_evidence_ids": [],
        "contradicting_evidence_ids": [],
        "reasoning": "The evidence shows an elevated error rate and a recent deployment, but does not provide direct evidence that the deployment introduced a defect causing the error increase. Temporal proximity alone is insufficient to establish causation."
      }
    ]
  }
}
```


## 6. Observe the investigation result

Once the investigation is completed, retrieve it again:

```bash
curl http://localhost:8000/investigations/<INVESTIGATION_ID>
```

The response contains the persisted investigation result.

Conceptually, the result contains:

```text
InvestigationResult
├── evidence
├── hypotheses
└── evaluations
```

The exact number of evidence items and hypotheses may vary between runs because tool selection and hypothesis generation are LLM-driven.

This is expected.


## 7. What to look for

For `database_pool_exhaustion`, the Mock Platform contains evidence related to:

- database connection timeouts
- failed connection acquisition
- elevated error rate
- a recent deployment
- a related commit
- a historical incident

A successful investigation should identify evidence that is relevant to the database failure.

The generated hypotheses should connect the available evidence rather than simply repeating individual observations.

For example, a hypothesis may relate the recent deployment to a database connection problem.

The important point is not that every run produces exactly the same wording.

The important behavior is:

```text
LLM
 ↓
proposes diagnostic actions
 ↓
application validates them
 ↓
MCP executes them
 ↓
tools return evidence
 ↓
LLM reasons over that evidence
```


## 8. Demonstrate unavailable diagnostic data

The investigation workflow can request a valid diagnostic operation even when the requested data is not available in the current scenario.

For example, a model may request:

```text
request_rate
```

while the selected scenario only exposes:

```text
error_rate
```

The Mock Platform returns an unavailable-data response.

The workflow does not fail the entire investigation because of this.

Instead, the unavailable diagnostic request is ignored and the investigation continues with the evidence that is available.

This demonstrates an important resilience property:

```text
One unavailable diagnostic signal
            ↓
does not necessarily fail
            ↓
the entire investigation
```

If this behavior occurs during the demo, the relevant evidence can be seen in the Agent Service logs:

```bash
docker compose logs agent-service
```

This behavior is not guaranteed to occur on every run because tool selection is LLM-driven.


## 9. Demonstrate insufficient evidence

The second demo is intentionally different.

Change the Mock Platform scenario to:

```text
MOCK_PLATFORM_SCENARIO=insufficient_evidence
```

Update `.env` or otherwise configure the environment accordingly.

Then recreate the Mock Platform:

```bash
MOCK_PLATFORM_SCENARIO=insufficient_evidence \
docker compose up -d --force-recreate mock-platform
```

Verify the active scenario:

```bash
docker compose exec mock-platform printenv MOCK_PLATFORM_SCENARIO
```

Expected:

```text
insufficient_evidence
```

Do not run the full test suite while this scenario is selected. The current test suite expects `database_pool_exhaustion`.


## 10. Create a second incident

Create another incident:

```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Unexpected checkout errors",
    "description": "Checkout API is reporting unexpected internal errors.",
    "service": "checkout-api",
    "severity": "high"
  }'
```

Copy the returned incident `id`.

### Example output

```json
{
   "id":"f54aef30-cc1e-4e62-a05b-f4886026160f",
   "title":"Unexpected checkout errors",
   "description":"Checkout API is reporting unexpected internal errors.",
   "service":"checkout-api",
   "severity":"high",
   "created_at":"2026-10-09T04:46:54.043194Z"
   }
```

Start the investigation:

```bash
curl -X POST http://localhost:8000/incidents/<INCIDENT_ID>/investigations
```

Copy the returned `investigation_id`.

### Example output

```json
{
   "id":"3c3cca90-177c-4bcd-b023-adce46fdf294",
   "incident_id":"f54aef30-cc1e-4e62-a05b-f4886026160f",
   "status":"pending",
   "created_at":"2026-10-09T04:47:05.459055Z",
   "result":null
}  
```

Poll the investigation:

```bash
curl http://localhost:8000/investigations/<INVESTIGATION_ID>
```

Wait until:

```text
status = completed
```

### Example output

```json
{
  "id": "3c3cca90-177c-4bcd-b023-adce46fdf294",
  "incident_id": "f54aef30-cc1e-4e62-a05b-f4886026160f",
  "status": "completed",
  "created_at": "2026-10-09T04:47:05.459055Z",
  "result": {
    "evidence": [
      {
        "id": "5c7e4ddc-63b1-4c44-a1a0-b8b06769fb5d",
        "source": "search_logs",
        "summary": "ERROR log from checkout-api: Request failed with an unexpected internal error",
        "data": {
          "level": "ERROR",
          "message": "Request failed with an unexpected internal error",
          "service": "checkout-api",
          "timestamp": "2026-10-07T12:00:00+00:00"
        }
      },
      {
        "id": "b8709f21-0c41-4bd5-8922-4f9332cf7de4",
        "source": "query_metrics",
        "summary": "error_rate for checkout-api is 4.2 percent, baseline 0.8 percent.",
        "data": {
          "metric": "error_rate",
          "service": "checkout-api",
          "value": 4.2,
          "unit": "percent",
          "baseline": 0.8,
          "window_minutes": 30
        }
      }
    ],
    "hypotheses": [],
    "evaluations": []
  }
}
```


## 11. Observe the insufficient-evidence result

The `insufficient_evidence` scenario contains only limited information:

- an unexpected internal error log
- an elevated error rate
- no deployment
- no commit
- no historical incident

The expected behavior is:

```text
evidence
   ↓
insufficient to establish a concrete cause
   ↓
hypotheses = []
```

The investigation should complete successfully without inventing a specific root cause.

This is one of the most important behaviors to demonstrate.

A good incident investigation system should be able to say, in effect:

> There is evidence of a problem, but there is not enough evidence to establish the cause.

Rather than:

> The root cause is X.

when X is not supported by the available evidence.

When adding the real output, make sure the absence of hypotheses is visible.

For example, the important part should show:

```json
"hypotheses": []
```

if that is the actual response structure.


## 12. Why this scenario matters

The `insufficient_evidence` scenario demonstrates that the system distinguishes between:

```text
Observed problem
```

and:

```text
Established explanation
```

For example:

```text
error_rate = 4.2%
```

is an observation.

It does not prove:

```text
database failure
deployment failure
provider degradation
traffic saturation
```

The workflow should therefore avoid creating a concrete hypothesis when the evidence does not support one.

This behavior is particularly important for AI-assisted incident response because unsupported conclusions can be more dangerous than incomplete conclusions.


## 13. Restore the default scenario

After the demo, restore:

```text
MOCK_PLATFORM_SCENARIO=database_pool_exhaustion
```

Recreate the Mock Platform:

```bash
MOCK_PLATFORM_SCENARIO=database_pool_exhaustion \
docker compose up -d --force-recreate mock-platform
```

Verify:

```bash
docker compose exec mock-platform printenv MOCK_PLATFORM_SCENARIO
```

Expected:

```text
database_pool_exhaustion
```

This returns the environment to the configuration expected by the complete test suite.


## 14. Optional: run the tests after the demo

Once the default scenario has been restored, run:

```bash
docker compose exec agent-service uv run pytest
```

The expected result is the complete test suite passing.


## 15. What the demo demonstrates

The MVP demo covers the main vertical slice:

```text
HTTP API
   ↓
PostgreSQL
   ↓
Async investigation
   ↓
LangGraph workflow
   ↓
LLM tool selection
   ↓
Deterministic validation
   ↓
MCP
   ↓
Mock Platform
   ↓
Evidence
   ↓
Hypotheses
   ↓
Evaluations
   ↓
InvestigationResult
   ↓
PostgreSQL
   ↓
HTTP API
```

It also demonstrates two important AI-engineering properties.

### 1. Controlled tool use

The LLM does not directly execute arbitrary operations.

Instead:

```text
LLM proposes
   ↓
application validates
   ↓
MCP executes
```

### 2. Evidence-aware reasoning

The system should reason from collected evidence and avoid creating unsupported conclusions.

The `insufficient_evidence` scenario provides a deterministic demonstration of this behavior.


## 16. Recommended portfolio demo

For a short portfolio or interview demonstration, use this sequence.

### Demo 1 — Successful investigation

Use:

```text
database_pool_exhaustion
```

Show:

1. active scenario verification
2. incident creation
3. asynchronous investigation creation
4. `pending → running → completed`
5. collected evidence
6. generated hypotheses
7. hypothesis evaluations
8. persisted investigation result

### Demo 2 — Insufficient evidence

Switch to:

```text
insufficient_evidence
```

Show:

1. active scenario verification
2. incident creation
3. investigation execution
4. available evidence
5. absence of hypotheses
6. successful completion without an invented root cause

This second example is particularly useful when explaining why the system is not simply an LLM wrapper.


## 17. What not to promise during the demo

Tool selection and hypothesis generation are model-driven.

Therefore, do not promise:

- identical tool selection on every run
- identical evidence ordering
- identical hypothesis wording
- identical number of hypotheses

Instead, describe the system as:

> A controlled investigation workflow in which the LLM proposes diagnostic actions and hypotheses, while deterministic application code validates tool requests, executes tools through MCP, manages workflow state, and persists the final result.

The examples included in this document are real execution outputs captured from the MVP. Exact outputs may differ in future runs because parts of the investigation are LLM-driven.


## 18. Short interview explanation

A concise explanation of the demo is:

> The system receives an incident and starts an asynchronous investigation. A LangGraph workflow asks the LLM which diagnostic tools would be useful. The application validates those requests before executing them through an MCP boundary against a deterministic Mock Platform. The resulting evidence is passed back to the reasoning stage, which generates and evaluates hypotheses. The final investigation result is persisted in PostgreSQL. I also included an insufficient-evidence scenario to demonstrate that the system can complete an investigation without inventing a root cause when the available evidence is not sufficient.


## Demo checklist

Before a portfolio demo:

- [ ] Docker Compose is running
- [ ] PostgreSQL is healthy
- [ ] migrations completed
- [ ] Mock Platform is running
- [ ] active scenario verified
- [ ] `database_pool_exhaustion` is selected
- [ ] Agent Service is running
- [ ] successful investigation demonstrated
- [ ] persisted result demonstrated
- [ ] `insufficient_evidence` scenario demonstrated
- [ ] no unsupported root cause is generated in the insufficient-evidence scenario
- [ ] default scenario restored afterward
- [ ] complete test suite passes after restoring the default scenario


## Demo scope

The demo intentionally does not attempt to showcase every planned capability.

The following are outside the current MVP demo:

- automated evaluation framework
- OpenTelemetry dashboards
- durable background workers
- advanced LangGraph checkpointing
- human-in-the-loop approval
- remediation execution
- multi-agent workflows

These capabilities can be added after the MVP is published.

The demo should remain focused on the core vertical slice:

```text
Incident
  ↓
Async Investigation
  ↓
Controlled AI Reasoning
  ↓
Tools / MCP
  ↓
Evidence
  ↓
Hypotheses
  ↓
Evaluation
  ↓
Persisted Result
```