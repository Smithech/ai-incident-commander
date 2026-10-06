import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.models import (
    Commit,
    Deployment,
    HistoricalIncident,
    LogEntry,
    MetricResult,
)

from app.scenarios.bad_deployment import (
    COMMITS as BAD_DEPLOYMENT_COMMITS,
    DEPLOYMENTS as BAD_DEPLOYMENT_DEPLOYMENTS,
    HISTORICAL_INCIDENTS as BAD_DEPLOYMENT_HISTORICAL_INCIDENTS,
    LOGS as BAD_DEPLOYMENT_LOGS,
    METRICS as BAD_DEPLOYMENT_METRICS,
)
from app.scenarios.database_pool_exhaustion import (
    COMMITS as SCENARIO_COMMITS,
    DEPLOYMENTS as SCENARIO_DEPLOYMENTS,
    HISTORICAL_INCIDENTS as SCENARIO_HISTORICAL_INCIDENTS,
    LOGS as SCENARIO_LOGS,
    METRICS as SCENARIO_METRICS,
)


SCENARIO = os.getenv(
    "MOCK_PLATFORM_SCENARIO",
    "database_pool_exhaustion",
)

SCENARIOS = {
    "database_pool_exhaustion": (
        SCENARIO_LOGS,
        SCENARIO_METRICS,
        SCENARIO_DEPLOYMENTS,
        SCENARIO_COMMITS,
        SCENARIO_HISTORICAL_INCIDENTS,
    ),
    "bad_deployment": (
        BAD_DEPLOYMENT_LOGS,
        BAD_DEPLOYMENT_METRICS,
        BAD_DEPLOYMENT_DEPLOYMENTS,
        BAD_DEPLOYMENT_COMMITS,
        BAD_DEPLOYMENT_HISTORICAL_INCIDENTS,
    ),
}

if SCENARIO not in SCENARIOS:
    raise ValueError(
        f"Unsupported mock platform scenario: {SCENARIO}"
    )


app = FastAPI(title="Mock Platform")


(
    LOGS,
    METRICS,
    DEPLOYMENTS,
    COMMITS,
    HISTORICAL_INCIDENTS,
) = SCENARIOS[SCENARIO]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/logs", response_model=list[LogEntry])
async def search_logs(
    service: str,
    query: str,
):
    return [
        log
        for log in LOGS
        if log.service == service
        and query.lower() in log.message.lower()
    ]


@app.get("/metrics", response_model=MetricResult)
async def query_metrics(
    service: str,
    metric: str,
    window_minutes: int = 30,
) -> MetricResult:
    for item in METRICS:
        if item.service == service and item.metric == metric:
            return item.model_copy(update={"window_minutes": window_minutes})

    raise HTTPException(status_code=404, detail="Metric not found")


@app.get("/deployments", response_model=list[Deployment])
async def get_recent_deployments(
    service: str,
    window_minutes: int = 60,
) -> list[Deployment]:
    return [deployment for deployment in DEPLOYMENTS if deployment.service == service]


@app.get("/commits/{commit_sha}", response_model=Commit)
async def get_commit(commit_sha: str) -> Commit:
    for commit in COMMITS:
        if commit.sha == commit_sha:
            return commit

    raise HTTPException(status_code=404, detail="Commit not found")


@app.get(
    "/historical-incidents",
    response_model=list[HistoricalIncident],
)
async def search_historical_incidents(
    service: str,
    query: str,
) -> list[HistoricalIncident]:
    if service != "checkout-api":
        return []

    return [
        incident
        for incident in HISTORICAL_INCIDENTS
        if query.lower() in incident.title.lower()
        or query.lower() in incident.root_cause.lower()
    ]
