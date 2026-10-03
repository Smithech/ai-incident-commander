from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from app.integrations.mock_platform import create_mock_platform_client
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