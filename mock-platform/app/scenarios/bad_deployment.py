from app.models import (
    Commit,
    Deployment,
    HistoricalIncident,
    LogEntry,
    MetricResult,
)


LOGS = [
    LogEntry(
        timestamp="2026-10-04T10:00:00Z",
        level="INFO",
        service="checkout-api",
        message="Request completed successfully",
    ),
    LogEntry(
        timestamp="2026-10-04T10:06:00Z",
        level="INFO",
        service="checkout-api",
        message="Deployment deploy-456 started",
    ),
    LogEntry(
        timestamp="2026-10-04T10:07:00Z",
        level="ERROR",
        service="checkout-api",
        message="Checkout request failed with HTTP 500",
    ),
    LogEntry(
        timestamp="2026-10-04T10:08:00Z",
        level="ERROR",
        service="checkout-api",
        message="Unexpected error while processing checkout",
    ),
]


METRICS = [
    MetricResult(
        metric="error_rate",
        service="checkout-api",
        value=22.7,
        baseline=0.9,
        unit="percent",
        window_minutes=30,
    ),
]


DEPLOYMENTS = [
    Deployment(
        id="deploy-456",
        service="checkout-api",
        commit_sha="def456",
        deployed_at="2026-10-04T10:06:00Z",
        version="2026.10.04.17",
    ),
]


COMMITS = [
    Commit(
        sha="def456",
        message="Refactor checkout validation flow",
        author="bob",
        changed_files=[
            "app/checkout.py",
            "app/validation.py",
        ],
    ),
]


HISTORICAL_INCIDENTS = [
    HistoricalIncident(
        id="INC-57",
        title="Checkout failures after deployment",
        root_cause="A production deployment introduced a regression in checkout validation",
        resolved_at="2026-09-28T15:20:00Z",
    ),
]