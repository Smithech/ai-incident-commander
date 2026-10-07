import pytest

from app.domain.tool_selection import ToolRequest, ToolSelectionResult


SCENARIO_EXPECTATIONS = {
    "database_pool_exhaustion": {
        "required_tools": {
            "search_logs",
            "query_metrics",
            "get_recent_deployments",
            "get_commit",
            "search_historical_incidents",
        },
    },
    "bad_deployment": {
        "required_tools": {
            "search_logs",
            "query_metrics",
            "get_recent_deployments",
            "get_commit",
            "search_historical_incidents",
        },
    },
    "payment_provider_degradation": {
        "required_tools": {
            "search_logs",
            "query_metrics",
            "search_historical_incidents",
        },
    },
    "traffic_spike": {
        "required_tools": {
            "search_logs",
            "query_metrics",
            "search_historical_incidents",
        },
    },
    "insufficient_evidence": {
        "required_tools": {
            "search_logs",
            "query_metrics",
            "search_historical_incidents",
        },
    },
}


def assert_required_tools_selected(
    result: ToolSelectionResult,
    required_tools: set[str],
) -> None:
    selected_tools = {
        request.tool_name
        for request in result.requests
    }

    missing_tools = required_tools - selected_tools

    assert not missing_tools, (
        f"Missing required tools: {sorted(missing_tools)}"
    )


@pytest.mark.parametrize(
    ("scenario", "required_tools"),
    [
        (
            scenario,
            expectation["required_tools"],
        )
        for scenario, expectation
        in SCENARIO_EXPECTATIONS.items()
    ],
)
def test_scenario_requires_expected_tools(
    scenario: str,
    required_tools: set[str],
) -> None:
    result = ToolSelectionResult(
        requests=[
            ToolRequest(
                tool_name=tool_name,
                arguments={},
            )
            for tool_name in required_tools
        ],
    )

    assert_required_tools_selected(
        result,
        required_tools,
    )


#! temporal
from app.services.llm import NvidiaLLMClient
from app.services.tool_selection import (
    ToolSelectionInput,
    validate_tool_selection,
)

@pytest.mark.asyncio
async def test_real_llm_selects_payment_tools() -> None:
    client = NvidiaLLMClient()

    request = ToolSelectionInput(
        incident_service="checkout-api",
        incident_title="Payment provider degradation",
        incident_description=(
            "Payment requests are experiencing elevated "
            "failures and timeouts."
        ),
    )

    result = await client.select_tools(request)

    validate_tool_selection(result)

    print("\nSelected tools:")
    for tool_request in result.requests:
        print(
            tool_request.tool_name,
            tool_request.arguments,
        )
#! temporal