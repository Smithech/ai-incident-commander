import pytest

from app.domain.tool_selection import ToolRequest
from app.services.tool_execution import execute_tool_request


@pytest.mark.asyncio
async def test_execute_search_logs_returns_evidence():
    request = ToolRequest(
        tool_name="search_logs",
        arguments={
            "service": "checkout-api",
            "query": "database",
        },
    )

    evidence = await execute_tool_request(request)

    assert len(evidence) == 2
    assert all(
        item.source == "search_logs"
        for item in evidence
    )


@pytest.mark.asyncio
async def test_execute_unknown_tool_is_rejected():
    request = ToolRequest(
        tool_name="delete_database",
        arguments={},
    )

    with pytest.raises(ValueError, match="Unsupported tool"):
        await execute_tool_request(request)