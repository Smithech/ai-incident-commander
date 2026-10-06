from typing import Annotated, Protocol

from fastmcp import FastMCP
from pydantic import Field

from app.integrations.mock_platform import create_mock_platform_client
from app.tools.get_commit import CommitResult
from app.tools.get_recent_deployments import Deployment, RecentDeploymentsResult
from app.tools.query_metrics import MetricResult
from app.tools.search_historical_incidents import (
    HistoricalIncident,
    HistoricalIncidentsResult,
)
from app.tools.search_logs import LogEntry, SearchLogsResult


mcp = FastMCP("AI Incident Commander Tools")


class IncidentPlatformClient(Protocol):
    async def search_logs(
        self,
        *,
        service: str,
        query: str,
    ) -> list[LogEntry]:
        ...

    async def query_metrics(
        self,
        *,
        service: str,
        metric: str,
        window_minutes: int,
    ) -> MetricResult:
        ...

    async def get_recent_deployments(
        self,
        *,
        service: str,
        window_minutes: int,
    ) -> list[Deployment]:
        ...

    async def get_commit(
        self,
        *,
        commit_sha: str,
    ) -> CommitResult:
        ...

    async def search_historical_incidents(
        self,
        *,
        service: str,
        query: str,
    ) -> list[HistoricalIncident]:
        ...


async def _search_logs(
    client: IncidentPlatformClient,
    *,
    service: str,
    query: str,
) -> SearchLogsResult:
    logs = await client.search_logs(
        service=service,
        query=query,
    )

    return SearchLogsResult(
        matches=logs[:100],
    )


async def _query_metrics(
    client: IncidentPlatformClient,
    *,
    service: str,
    metric: str,
    window_minutes: int,
) -> MetricResult:
    return await client.query_metrics(
        service=service,
        metric=metric,
        window_minutes=window_minutes,
    )


async def _get_recent_deployments(
    client: IncidentPlatformClient,
    *,
    service: str,
    window_minutes: int,
) -> RecentDeploymentsResult:
    deployments = await client.get_recent_deployments(
        service=service,
        window_minutes=window_minutes,
    )

    return RecentDeploymentsResult(
        deployments=deployments[:20],
    )


async def _get_commit(
    client: IncidentPlatformClient,
    *,
    commit_sha: str,
) -> CommitResult:
    return await client.get_commit(
        commit_sha=commit_sha,
    )


async def _search_historical_incidents(
    client: IncidentPlatformClient,
    *,
    service: str,
    query: str,
) -> HistoricalIncidentsResult:
    incidents = await client.search_historical_incidents(
        service=service,
        query=query,
    )

    return HistoricalIncidentsResult(
        incidents=incidents[:20],
    )


@mcp.tool
async def search_logs(
    service: Annotated[
        str,
        Field(min_length=1, max_length=100),
    ],
    query: Annotated[
        str,
        Field(min_length=1, max_length=200),
    ],
) -> SearchLogsResult:
    """Search logs for a service using the incident platform."""
    client = create_mock_platform_client()

    return await _search_logs(
        client,
        service=service,
        query=query,
    )


@mcp.tool
async def query_metrics(
    service: Annotated[
        str,
        Field(min_length=1, max_length=100),
    ],
    metric: Annotated[
        str,
        Field(min_length=1, max_length=200),
    ],
    window_minutes: Annotated[
        int,
        Field(gt=0, le=1440),
    ] = 30,
) -> MetricResult:
    """Query a metric for a service."""
    client = create_mock_platform_client()

    return await _query_metrics(
        client,
        service=service,
        metric=metric,
        window_minutes=window_minutes,
    )



@mcp.tool
async def get_recent_deployments(
    service: Annotated[
        str,
        Field(min_length=1, max_length=100),
    ],
    window_minutes: Annotated[
        int,
        Field(gt=0, le=1440),
    ] = 60,
) -> RecentDeploymentsResult:
    """Get recent deployments for a service."""
    client = create_mock_platform_client()

    return await _get_recent_deployments(
        client,
        service=service,
        window_minutes=window_minutes,
    )


@mcp.tool
async def get_commit(
    commit_sha: Annotated[
        str,
        Field(min_length=1, max_length=100),
    ],
) -> CommitResult:
    """Get details for a commit."""
    client = create_mock_platform_client()

    return await _get_commit(
        client,
        commit_sha=commit_sha,
    )


@mcp.tool
async def search_historical_incidents(
    service: Annotated[
        str,
        Field(min_length=1, max_length=100),
    ],
    query: Annotated[
        str,
        Field(min_length=1, max_length=200),
    ],
) -> HistoricalIncidentsResult:
    """Search historical incidents for a service."""
    client = create_mock_platform_client()

    return await _search_historical_incidents(
        client,
        service=service,
        query=query,
    )