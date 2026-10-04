from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str


class MetricResult(BaseModel):
    metric: str
    service: str
    value: float
    baseline: float
    unit: str
    window_minutes: int


class Deployment(BaseModel):
    id: str
    service: str
    commit_sha: str
    deployed_at: datetime
    version: str


class Commit(BaseModel):
    sha: str
    message: str
    author: str
    changed_files: list[str]


class HistoricalIncident(BaseModel):
    id: str
    title: str
    root_cause: str
    resolved_at: datetime


app = FastAPI(title="Mock Platform")


LOGS = [
    LogEntry(
        timestamp="2026-10-03T13:59:00Z",
        level="INFO",
        service="checkout-api",
        message="Request completed successfully",
    ),
    LogEntry(
        timestamp="2026-10-03T14:01:00Z",
        level="ERROR",
        service="checkout-api",
        message="Database connection timeout",
    ),
    LogEntry(
        timestamp="2026-10-03T14:02:00Z",
        level="ERROR",
        service="checkout-api",
        message="Failed to acquire database connection",
    ),
]


METRICS = [
    MetricResult(
        metric="error_rate",
        service="checkout-api",
        value=18.4,
        baseline=0.8,
        unit="percent",
        window_minutes=30,
    ),
]


DEPLOYMENTS = [
    Deployment(
        id="deploy-123",
        service="checkout-api",
        commit_sha="abc123",
        deployed_at="2026-10-03T13:55:00Z",
        version="2026.10.03.42",
    ),
]


COMMITS = [
    Commit(
        sha="abc123",
        message="Increase database pool size",
        author="alice",
        changed_files=[
            "app/db.py",
            "app/config.py",
        ],
    ),
]


HISTORICAL_INCIDENTS = [
    HistoricalIncident(
        id="INC-42",
        title="Database connection pool exhaustion",
        root_cause="Database connection pool size was too small",
        resolved_at="2026-09-21T16:30:00Z",
    ),
]


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
