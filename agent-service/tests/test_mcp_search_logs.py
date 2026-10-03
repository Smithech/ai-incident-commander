import pytest
from fastmcp import Client

from app.mcp_server import mcp


@pytest.mark.asyncio
async def test_search_logs_returns_matching_logs_from_mock_platform():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_logs",
            {
                "service": "checkout-api",
                "query": "database connection",
            },
        )

    assert not result.is_error
    assert result.structured_content is not None

    matches = result.structured_content["matches"]

    assert len(matches) == 2

    assert all(
        match["service"] == "checkout-api"
        for match in matches
    )

    assert all(
        "database connection" in match["message"].lower()
        for match in matches
    )


@pytest.mark.asyncio
async def test_search_logs_rejects_empty_service():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_logs",
            {
                "service": "",
                "query": "database",
            },
        )

    assert result.is_error


@pytest.mark.asyncio
async def test_search_logs_rejects_empty_query():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_logs",
            {
                "service": "checkout-api",
                "query": "",
            },
        )

    assert result.is_error


@pytest.mark.asyncio
async def test_search_logs_rejects_service_that_is_too_long():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_logs",
            {
                "service": "x" * 101,
                "query": "database",
            },
        )

    assert result.is_error


@pytest.mark.asyncio
async def test_search_logs_rejects_query_that_is_too_long():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_logs",
            {
                "service": "checkout-api",
                "query": "x" * 201,
            },
        )

    assert result.is_error