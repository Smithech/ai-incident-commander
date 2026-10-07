import pytest

from app.domain.tool_selection import (
    ToolRequest,
    ToolSelectionResult,
)
from app.services.tool_selection import ToolSelectionInput, validate_tool_selection


def test_tool_selection_result_contains_requested_tools():
    request = ToolSelectionInput(
        incident_service="checkout-api",
        incident_title="Payment provider degradation",
        incident_description=(
            "Payment requests are experiencing elevated "
            "failures and timeouts."
        ),
    )

    result = ToolSelectionResult(
        requests=[
            ToolRequest(
                tool_name="search_logs",
                arguments={
                    "service": request.incident_service,
                    "query": "payment provider",
                },
            ),
            ToolRequest(
                tool_name="query_metrics",
                arguments={
                    "service": request.incident_service,
                    "metric": "error_rate",
                    "window_minutes": 30,
                },
            ),
            ToolRequest(
                tool_name="search_historical_incidents",
                arguments={
                    "service": request.incident_service,
                    "query": "payment provider",
                },
            ),
        ],
    )

    assert len(result.requests) == 3

    assert result.requests[0].tool_name == "search_logs"
    assert result.requests[1].tool_name == "query_metrics"
    assert (
        result.requests[2].tool_name
        == "search_historical_incidents"
    )


def test_tool_request_requires_tool_name():
    with pytest.raises(ValueError):
        ToolRequest(
            tool_name="",
            arguments={},
        )


def test_tool_selection_input_requires_service():
    with pytest.raises(ValueError):
        ToolSelectionInput(
            incident_service="",
            incident_title="Payment provider degradation",
            incident_description="Payment failures",
        )


def test_validate_tool_selection_accepts_allowed_tools():
    result = ToolSelectionResult(
        requests=[
            ToolRequest(
                tool_name="search_logs",
                arguments={
                    "service": "checkout-api",
                    "query": "payment provider",
                },
            ),
            ToolRequest(
                tool_name="query_metrics",
                arguments={
                    "service": "checkout-api",
                    "metric": "error_rate",
                    "window_minutes": 30,
                },
            ),
        ],
    )

    validate_tool_selection(result)


def test_validate_tool_selection_rejects_unknown_tool():
    result = ToolSelectionResult(
        requests=[
            ToolRequest(
                tool_name="delete_database",
                arguments={},
            ),
        ],
    )

    with pytest.raises(ValueError, match="Unsupported tool"):
        validate_tool_selection(result)