import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from app.mcp_server import mcp


@pytest.mark.asyncio
async def test_investigation_tools_return_structured_results():
    async with Client(mcp) as client:
        metrics = await client.call_tool(
            "query_metrics",
            {
                "service": "checkout-api",
                "metric": "error_rate",
                "window_minutes": 30,
            },
        )
        deployments = await client.call_tool(
            "get_recent_deployments",
            {
                "service": "checkout-api",
                "window_minutes": 60,
            },
        )
        commit = await client.call_tool(
            "get_commit",
            {"commit_sha": "abc123"},
        )
        historical = await client.call_tool(
            "search_historical_incidents",
            {
                "service": "checkout-api",
                "query": "database",
            },
        )

    assert not metrics.is_error
    assert metrics.structured_content["metric"] == "error_rate"
    assert metrics.structured_content["value"] == 18.4

    assert not deployments.is_error
    assert len(deployments.structured_content["deployments"]) == 1
    assert deployments.structured_content["deployments"][0]["commit_sha"] == "abc123"

    assert not commit.is_error
    assert commit.structured_content["sha"] == "abc123"

    assert not historical.is_error
    assert len(historical.structured_content["incidents"]) == 1
    assert historical.structured_content["incidents"][0]["id"] == "INC-42"


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
