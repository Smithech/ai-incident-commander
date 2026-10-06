from app.models import (
    Commit,
    Deployment,
    HistoricalIncident,
    LogEntry,
    MetricResult,
)


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