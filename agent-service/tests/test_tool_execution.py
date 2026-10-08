import pytest

from app.domain.evidence import Evidence
from app.domain.tool_selection import ToolRequest
from app.domain.tool_selection import ToolRequest
from app.services.tool_execution import execute_tool_request, ToolDataUnavailableError
from app.workflows.investigation import collect_evidence

async def fake_execute_tool(request):
    if request.tool_name == "query_metrics":
        raise ToolDataUnavailableError(
            "Metric not available: request_rate"
        )

    return [
        Evidence(
            id="evidence-1",
            source="search_logs",
            summary="Database connection timeout",
            data={},
        )
    ]


@pytest.mark.asyncio
async def test_collect_evidence_ignores_unavailable_tool_data():
    state = {
        "tool_requests": [
            ToolRequest(
                tool_name="query_metrics",
                arguments={
                    "service": "checkout-api",
                    "metric": "request_rate",
                },
            ),
            ToolRequest(
                tool_name="search_logs",
                arguments={
                    "service": "checkout-api",
                    "query": "database connection",
                },
            ),
        ],
        "evidence": [],
    }

    result = await collect_evidence(
        state,
        execute_tool=fake_execute_tool,
    )

    assert len(result["evidence"]) == 1
    assert result["evidence"][0].id == "evidence-1"
    assert result["evidence"][0].source == "search_logs"


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
async def test_execute_query_metrics_returns_evidence() -> None:
    request = ToolRequest(
        tool_name="query_metrics",
        arguments={
            "service": "checkout-api",
            "metric": "error_rate",
            "window_minutes": 30,
        },
    )

    evidence = await execute_tool_request(request)

    assert len(evidence) == 1
    assert evidence[0].source == "query_metrics"
    assert "error_rate" in evidence[0].summary


@pytest.mark.asyncio
async def test_execute_recent_deployments_returns_evidence() -> None:
    request = ToolRequest(
        tool_name="get_recent_deployments",
        arguments={
            "service": "checkout-api",
            "window_minutes": 60,
        },
    )

    evidence = await execute_tool_request(request)

    assert evidence
    assert all(
        item.source == "get_recent_deployments"
        for item in evidence
    )


@pytest.mark.asyncio
async def test_execute_get_commit_returns_evidence() -> None:
    request = ToolRequest(
        tool_name="get_commit",
        arguments={
            "commit_sha": "abc123",
        },
    )

    evidence = await execute_tool_request(request)

    assert len(evidence) == 1
    assert evidence[0].source == "get_commit"
    assert "abc123" in evidence[0].summary


@pytest.mark.asyncio
async def test_execute_historical_incidents_returns_evidence() -> None:
    request = ToolRequest(
        tool_name="search_historical_incidents",
        arguments={
            "service": "checkout-api",
            "query": "database",
        },
    )

    evidence = await execute_tool_request(request)

    assert evidence
    assert all(
        item.source == "search_historical_incidents"
        for item in evidence
    )


@pytest.mark.asyncio
async def test_execute_unknown_tool_fails() -> None:
    request = ToolRequest(
        tool_name="unknown_tool",
        arguments={},
    )

    with pytest.raises(
        ValueError,
        match="Unsupported tool: unknown_tool",
    ):
        await execute_tool_request(request)


@pytest.mark.asyncio
async def test_execute_search_logs_requires_service() -> None:
    request = ToolRequest(
        tool_name="search_logs",
        arguments={
            "query": "database",
        },
    )

    with pytest.raises(
        ValueError,
        match="search_logs requires a non-empty service",
    ):
        await execute_tool_request(request)


@pytest.mark.asyncio
async def test_execute_query_metrics_requires_metric() -> None:
    request = ToolRequest(
        tool_name="query_metrics",
        arguments={
            "service": "checkout-api",
        },
    )

    with pytest.raises(
        ValueError,
        match="query_metrics requires a non-empty metric",
    ):
        await execute_tool_request(request)


@pytest.mark.asyncio
async def test_execute_get_commit_requires_sha() -> None:
    request = ToolRequest(
        tool_name="get_commit",
        arguments={},
    )

    with pytest.raises(
        ValueError,
        match="get_commit requires a non-empty commit_sha",
    ):
        await execute_tool_request(request)
