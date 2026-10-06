import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from app.mcp_server import (
    _get_commit,
    _get_recent_deployments,
    _query_metrics,
    _search_historical_incidents,
    mcp,
)
from app.tools.get_commit import CommitResult
from app.tools.get_recent_deployments import Deployment
from app.tools.query_metrics import MetricResult
from app.tools.search_logs import LogEntry
from app.tools.search_historical_incidents import HistoricalIncident


class FakeIncidentPlatformClient:
    async def search_logs(
        self,
        *,
        service: str,
        query: str,
    ) -> list[LogEntry]:
        return []

    async def query_metrics(
        self,
        *,
        service: str,
        metric: str,
        window_minutes: int,
    ) -> MetricResult:
        return MetricResult(
            metric="error_rate",
            service="checkout-api",
            value=18.4,
            baseline=0.8,
            unit="percent",
            window_minutes=window_minutes,
        )

    async def get_recent_deployments(
        self,
        *,
        service: str,
        window_minutes: int,
    ) -> list[Deployment]:
        return [
            Deployment(
                id="deploy-123",
                service="checkout-api",
                commit_sha="abc123",
                deployed_at="2026-10-03T13:55:00Z",
                version="2026.10.03.42",
            )
        ]

    async def get_commit(
        self,
        *,
        commit_sha: str,
    ) -> CommitResult:
        return CommitResult(
            sha="abc123",
            message="Increase database pool size",
            author="alice",
            changed_files=[
                "app/db.py",
                "app/config.py",
            ],
        )

    async def search_historical_incidents(
        self,
        *,
        service: str,
        query: str,
    ) -> list[HistoricalIncident]:
        return [
            HistoricalIncident(
                id="INC-42",
                title="Database connection pool exhaustion",
                root_cause="Database connection pool size was too small",
                resolved_at="2026-09-21T16:30:00Z",
            )
        ]


@pytest.mark.asyncio
async def test_investigation_tools_return_structured_results():
    client = FakeIncidentPlatformClient()

    metrics = await _query_metrics(
        client,
        service="checkout-api",
        metric="error_rate",
        window_minutes=30,
    )
        
    deployments = await _get_recent_deployments(
        client,
        service="checkout-api",
        window_minutes=60,
    )

    commit = await _get_commit(
        client,
        commit_sha="abc123",
    )
    
    historical = await _search_historical_incidents(
        client,
        service="checkout-api",
        query="database",
    )

    assert metrics.metric == "error_rate"
    assert metrics.value == 18.4

    assert len(deployments.deployments) == 1
    assert deployments.deployments[0].commit_sha == "abc123"

    assert commit.sha == "abc123"

    assert len(historical.incidents) == 1
    assert historical.incidents[0].id == "INC-42"


@pytest.mark.asyncio
async def test_query_metrics_rejects_invalid_window():
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "query_metrics",
                {
                    "service": "checkout-api",
                    "metric": "error_rate",
                    "window_minutes": 0,
                },
            )
