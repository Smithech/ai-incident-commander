from app.models import (
    Commit,
    Deployment,
    HistoricalIncident,
    LogEntry,
    MetricResult,
)


LOGS = [
    LogEntry(
        timestamp="2026-10-05T16:00:00Z",
        level="INFO",
        service="checkout-api",
        message="Checkout request started",
    ),
    LogEntry(
        timestamp="2026-10-05T16:02:00Z",
        level="ERROR",
        service="checkout-api",
        message="Payment provider request timed out",
    ),
    LogEntry(
        timestamp="2026-10-05T16:03:00Z",
        level="ERROR",
        service="checkout-api",
        message="Payment provider returned HTTP 503",
    ),
]


METRICS = [
    MetricResult(
        metric="error_rate",
        service="checkout-api",
        value=15.8,
        baseline=0.7,
        unit="percent",
        window_minutes=30,
    ),
]


DEPLOYMENTS = []


COMMITS = []


HISTORICAL_INCIDENTS = [
    HistoricalIncident(
        id="INC-63",
        title="Payment provider degradation",
        root_cause="External payment provider experienced elevated error rates",
        resolved_at="2026-09-30T18:45:00Z",
    ),
]