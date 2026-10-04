from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from app.integrations.mock_platform import create_mock_platform_client
from app.tools.get_commit import CommitResult
from app.tools.get_recent_deployments import RecentDeploymentsResult
from app.tools.query_metrics import MetricResult
from app.tools.search_historical_incidents import (
    HistoricalIncidentsResult,
)
from app.tools.search_logs import SearchLogsResult

mcp = FastMCP("AI Incident Commander Tools")


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

    logs = await client.search_logs(
        service=service,
        query=query,
    )

    return SearchLogsResult(
        matches=logs[:100],
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

    return await client.query_metrics(
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

    return await client.get_recent_deployments(
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

    return await client.get_commit(
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

    return await client.search_historical_incidents(
        service=service,
        query=query,
    )