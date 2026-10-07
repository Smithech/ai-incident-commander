from app.models import (
    HistoricalIncident,
    LogEntry,
    MetricResult,
)


LOGS = [
    LogEntry(
        timestamp="2026-10-07T12:00:00Z",
        level="ERROR",
        service="checkout-api",
        message="Request failed with an unexpected internal error",
    ),
]


METRICS = [
    MetricResult(
        metric="error_rate",
        service="checkout-api",
        value=4.2,
        baseline=0.8,
        unit="percent",
        window_minutes=30,
    ),
]


DEPLOYMENTS = []


COMMITS = []


HISTORICAL_INCIDENTS = []