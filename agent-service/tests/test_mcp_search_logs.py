import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from app.mcp_server import mcp, _search_logs
from app.tools.search_logs import LogEntry


class FakeIncidentPlatformClient:
    async def search_logs(
        self,
        *,
        service: str,
        query: str,
    ) -> list[LogEntry]:
        return [
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


@pytest.mark.asyncio
async def test_search_logs_returns_matching_logs():
    client = FakeIncidentPlatformClient()

    result = await _search_logs(
        client,
        service="checkout-api",
        query="database connection",
    )

    assert len(result.matches) == 2

    assert all(
        match.service == "checkout-api"
        for match in result.matches
    )

    assert all(
        "database connection" in match.message.lower()
        for match in result.matches
    )


@pytest.mark.asyncio
async def test_search_logs_rejects_empty_service():
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "search_logs",
                {
                    "service": "",
                    "query": "database",
                },
            )


@pytest.mark.asyncio
async def test_search_logs_rejects_empty_query():
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "search_logs",
                {
                    "service": "checkout-api",
                    "query": "",
                },
            )


@pytest.mark.asyncio
async def test_search_logs_rejects_service_that_is_too_long():
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "search_logs",
                {
                    "service": "x" * 101,
                    "query": "database",
                },
            )


@pytest.mark.asyncio
async def test_search_logs_rejects_query_that_is_too_long():
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "search_logs",
                {
                    "service": "checkout-api",
                    "query": "x" * 201,
                },
            )