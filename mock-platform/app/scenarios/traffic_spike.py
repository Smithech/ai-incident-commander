from app.models import (
    HistoricalIncident,
    LogEntry,
    MetricResult,
)


LOGS = [
    LogEntry(
        timestamp="2026-10-06T11:00:00Z",
        level="INFO",
        service="checkout-api",
        message="Request completed successfully",
    ),
    LogEntry(
        timestamp="2026-10-06T11:04:00Z",
        level="WARN",
        service="checkout-api",
        message="Request queue depth is increasing",
    ),
    LogEntry(
        timestamp="2026-10-06T11:05:00Z",
        level="ERROR",
        service="checkout-api",
        message="Request timed out while waiting for available worker",
    ),
]


METRICS = [
    MetricResult(
        metric="request_rate",
        service="checkout-api",
        value=4200,
        baseline=1200,
        unit="requests_per_minute",
        window_minutes=30,
    ),
    MetricResult(
        metric="error_rate",
        service="checkout-api",
        value=12.6,
        baseline=0.8,
        unit="percent",
        window_minutes=30,
    ),
]


DEPLOYMENTS = []


COMMITS = []


HISTORICAL_INCIDENTS = [
    HistoricalIncident(
        id="INC-71",
        title="Traffic spike caused service saturation",
        root_cause="A sudden increase in incoming traffic saturated available service capacity",
        resolved_at="2026-09-25T14:10:00Z",
    ),
]