# Runbook

## Overview

This document explains how to run, verify, test, and troubleshoot the AI Incident Commander MVP.

The system is composed of:

- `agent-service`
- `mock-platform`
- `postgres`

The recommended development environment is Docker Compose.


## Prerequisites

Install:

- Docker
- Docker Compose

No local Python installation is required for the application.


## Configuration

Configuration is provided through environment variables.

The main variables are:

```Text
DATABASE_URL
MOCK_PLATFORM_URL
MOCK_PLATFORM_SCENARIO
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
```

For local development, copy `.env.example` to `.env` and configure the required values.

The default Mock Platform scenario is:

```text
database_pool_exhaustion
```


## Start the application

Build and start all services:

```Bash
docker compose up --build
```

The expected services are:

```text
postgres
migration
mock-platform
agent-service
```

The `migration` service runs:

```bash
uv run alembic upgrade head
```

before `agent-service` starts.

A successful startup should show:

```text
migration exited with code 0
agent-service ... Uvicorn running on http://0.0.0.0:8000
mock-platform ... Uvicorn running on http://0.0.0.0:8001
```


## Verify containers

Check service status:

```bash
docker compose ps
```

Expected state:

- `postgres` → healthy
- `migration` → exited with code 0
- `mock-platform` → running
- `agent-service` → running


## Verify the API

The Agent Service is available at:

```text
http://localhost:8000
```

The Mock Platform is available at:

```text
http://localhost:8001
```

Create an incident through the API and then start an investigation using the investigation endpoint.

The investigation API is asynchronous.

Creation returns:

```json
{
  "investigation_id": "...",
  "status": "pending"
}
```

The client should then poll:

```text
GET /investigations/{investigation_id}
```

until the investigation reaches:

```text
completed
```

or:

```text
failed
```


## Test environment

### Test database

The test suite uses a separate PostgreSQL database:

```text
incident_commander_test
```

The test configuration points to:

```text
postgresql+asyncpg://incident_commander:incident_commander@postgres:5432/incident_commander_test
```

The test database must have the current Alembic schema before running the suite.

Apply migrations with:

```bash
docker compose exec \
  -e DATABASE_URL="postgresql+asyncpg://incident_commander:incident_commander@postgres:5432/incident_commander_test" \
  agent-service \
  uv run alembic upgrade head
```


## Test scenario

The current test suite includes tests that exercise the real Mock Platform.

Because the Mock Platform exposes one scenario at a time, the **full test suite currently expects the `database_pool_exhaustion` scenario**.

Before running the complete test suite, make sure the environment uses:

```text
MOCK_PLATFORM_SCENARIO=database_pool_exhaustion
```

This is also the default value configured by Docker Compose.

If `.env` contains another scenario, change it back to:

```text
MOCK_PLATFORM_SCENARIO=database_pool_exhaustion
```

Then recreate the Mock Platform:

```bash
docker compose up -d --force-recreate mock-platform
```

### Important

Do not switch the Mock Platform to another scenario before running the complete test suite.

For example, using:

```text
bad_deployment
```

or:

```text
traffic_spike
```

may cause tests that depend on the default dataset to fail.

This is a current MVP limitation of the test setup: some integration tests depend on the globally configured Mock Platform scenario.

The five scenarios are still useful for **scenario-specific E2E testing and demonstrations**, but they should not currently be treated as interchangeable configurations for the complete `pytest` suite.


## Run tests

Once the test database has been migrated and the Mock Platform is configured with `database_pool_exhaustion`, run:

```bash
docker compose exec agent-service uv run pytest
```

The expected result is the complete test suite passing.

The test suite currently covers:

- incident API
- investigation API
- investigation lifecycle
- MCP tools
- evidence collection
- LangGraph workflow
- hypothesis generation
- hypothesis evaluation
- tool selection
- tool execution
- resilience to unavailable diagnostic data
- scenario-specific behavior


## Running individual tests

A specific test file can be executed with:

```bash
docker compose exec agent-service uv run pytest tests/test_investigations.py
```

A specific test can be executed with:

```bash
docker compose exec agent-service uv run pytest tests/test_investigation_graph.py -k test_name
```

When running tests that depend on the Mock Platform, keep the expected scenario configured.


## Database migrations

The application database is managed through Alembic.

Check the current migration:

```bash
docker compose exec agent-service uv run alembic current
```

Apply pending migrations:

```bash
docker compose exec agent-service uv run alembic upgrade head
```

Create a new migration after a schema change:

```bash
docker compose exec agent-service \
  uv run alembic revision --autogenerate -m "describe change"
```

Then review the generated migration before applying it.

Do not use:

```python
Base.metadata.create_all()
```

as a replacement for versioned migrations once schema evolution is being managed by Alembic.


## Reset local environment

To stop the application:

```bash
docker compose down
```

To remove containers and the PostgreSQL volume:

```bash
docker compose down -v
```

The `-v` option deletes local PostgreSQL data.

After resetting the database, start again with:

```bash
docker compose up --build
```

The migration service will recreate the schema through Alembic.


## Selecting a Mock Platform scenario

The Mock Platform supports five deterministic scenarios:

```text
database_pool_exhaustion
bad_deployment
payment_provider_degradation
traffic_spike
insufficient_evidence
```

The scenario is configured with:

```text
MOCK_PLATFORM_SCENARIO
```

For example:

```text
MOCK_PLATFORM_SCENARIO=traffic_spike
```

After changing the value, recreate the Mock Platform:

```bash
docker compose up -d --force-recreate mock-platform
```

These scenarios are primarily used for E2E demonstrations and scenario-specific investigation testing.

Remember to restore:

```text
MOCK_PLATFORM_SCENARIO=database_pool_exhaustion
```

before running the complete test suite.


## Debugging logs

View Agent Service logs:

```bash
docker compose logs -f agent-service
```

View Mock Platform logs:

```bash
docker compose logs -f mock-platform
```

View PostgreSQL logs:

```bash
docker compose logs -f postgres
```

View migration logs:

```bash
docker compose logs migration
```


## Common startup problems

### Migration fails

Inspect:

```bash
docker compose logs migration
```

Verify:

- PostgreSQL is healthy
- `DATABASE_URL` is correct
- the migration files are present
- the database credentials are correct


### Test database has no tables

If tests fail with errors such as:

```text
relation "incidents" does not exist
```

or:

```text
relation "investigations" does not exist
```

run:

```bash
docker compose exec \
  -e DATABASE_URL="postgresql+asyncpg://incident_commander:incident_commander@postgres:5432/incident_commander_test" \
  agent-service \
  uv run alembic upgrade head
```


### Tests fail because of Mock Platform data

First verify:

```text
MOCK_PLATFORM_SCENARIO=database_pool_exhaustion
```

The full suite currently assumes this scenario for tests that interact with the real Mock Platform.

If another scenario is configured, restore the default and recreate the service:

```bash
docker compose up -d --force-recreate mock-platform
```


### Investigation remains pending

Check:

```bash
docker compose logs -f agent-service
```

The expected lifecycle is:

```text
pending
  ↓
running
  ↓
completed
```

or:

```text
pending
  ↓
running
  ↓
failed
```

The application uses FastAPI `BackgroundTasks` for MVP asynchronous execution.

Because this is an in-process mechanism, a process restart can interrupt an investigation.


### Investigation produces different evidence between runs

Tool selection is LLM-driven.

Therefore, two investigations of the same scenario may select different diagnostic tools.

This is expected behavior.

The deterministic parts of the system still enforce:

- valid tool names
- valid arguments
- supported metrics
- MCP tool execution
- workflow structure
- evidence validation
- hypothesis validation
- persistence boundaries

The MVP does not guarantee identical tool selection on every run.


### Diagnostic data is unavailable

A valid tool request may refer to diagnostic data that is not available in the current scenario.

For example, the model may request:

```text
request_rate
```

while the selected scenario only exposes:

```text
error_rate
```

The Mock Platform returns the appropriate unavailable-data response.

The investigation workflow treats this as unavailable diagnostic data and continues with the evidence that is available.

This is intentionally different from swallowing unexpected application errors.


## LLM configuration

The LLM provider is configured through environment variables:

```text
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
```

The application depends on the generic `LLMClient` interface.

Provider-specific configuration is encapsulated by the LLM service.

For local development, verify that the configured provider supports the selected model and API format.


## Stop the application

Stop containers:

```bash
docker compose down
```

Stop containers and remove PostgreSQL data:

```bash
docker compose down -v
```

Use the second command only when intentionally resetting the local database.


## Operational boundaries

The MVP intentionally uses:

- Docker Compose
- PostgreSQL
- FastAPI `BackgroundTasks`
- LangGraph
- MCP
- deterministic mock scenarios

It does not currently use:

- Kafka
- Redis
- Celery
- Kubernetes
- Temporal

The asynchronous API contract is intentionally independent of the execution mechanism.

A future durable worker architecture could replace `BackgroundTasks` without changing the external investigation API.


## Recommended development workflow

For normal development:

1. Start the stack:

```bash
docker compose up --build
```

2. Verify migrations completed successfully.

3. Verify the Mock Platform is using:

```text
database_pool_exhaustion
```

4. Ensure the test database is migrated.

5. Run the full test suite:

```bash
docker compose exec agent-service uv run pytest
```

6. Change the Mock Platform scenario only when performing scenario-specific E2E testing.

7. Restore `database_pool_exhaustion` before running the full suite again.

8. Review logs when investigating failures.

9. Update documentation when an operational behavior changes.


## Operational checklist

Before considering the local environment healthy:

- [ ] PostgreSQL is healthy
- [ ] Alembic migrations completed successfully
- [ ] Agent Service is running
- [ ] Mock Platform is running
- [ ] `MOCK_PLATFORM_SCENARIO=database_pool_exhaustion` for the full test suite
- [ ] Test database has the current schema
- [ ] `pytest` passes
- [ ] API can create an incident
- [ ] API can start an investigation
- [ ] Investigation reaches `completed` or `failed`
- [ ] Investigation result can be retrieved
- [ ] Scenario-specific E2E behavior can be demonstrated


## Summary

The MVP is designed to be reproducible with Docker Compose.

The main operational sequence is:

```text
docker compose up --build
        ↓
PostgreSQL healthy
        ↓
Alembic migrations
        ↓
Mock Platform
        ↓
Agent Service
        ↓
API available
        ↓
Tests
```

For the **complete test suite**, the current supported configuration is:

```text
MOCK_PLATFORM_SCENARIO=database_pool_exhaustion
```

The other four scenarios are used for scenario-specific investigation testing and demonstrations.

The test-suite dependency on a globally selected Mock Platform scenario is a known MVP limitation. It can be improved later by making integration tests explicitly control their scenario or by providing isolated scenario fixtures.