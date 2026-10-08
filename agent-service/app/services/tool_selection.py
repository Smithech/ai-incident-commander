from typing import Any

from pydantic import BaseModel, Field

from app.domain.tool_selection import ToolRequest, ToolSelectionResult


class ToolSelectionInput(BaseModel):
    incident_service: str = Field(min_length=1, max_length=100)
    incident_title: str = Field(min_length=1, max_length=500)
    incident_description: str = Field(min_length=1, max_length=2_000)


class ToolSelectionClient:
    async def select_tools(
        self,
        request: ToolSelectionInput,
    ) -> ToolSelectionResult:
        raise NotImplementedError


ALLOWED_TOOLS = {
    "search_logs",
    "query_metrics",
    "get_recent_deployments",
    "get_commit",
    "search_historical_incidents",
}


def validate_tool_selection(
    result: ToolSelectionResult,
) -> None:
    for request in result.requests:
        if request.tool_name not in ALLOWED_TOOLS:
            raise ValueError(
                f"Unsupported tool: {request.tool_name}"
            )


def validate_tool_request(
    request: ToolRequest,
) -> None:
    if request.tool_name not in ALLOWED_TOOLS:
        raise ValueError(
            f"Unsupported tool: {request.tool_name}"
        )

    validators = {
        "search_logs": _validate_search_logs,
        "query_metrics": _validate_query_metrics,
        "get_recent_deployments": _validate_recent_deployments,
        "get_commit": _validate_get_commit,
        "search_historical_incidents": _validate_historical_incidents,
    }

    validators[request.tool_name](request.arguments)


def _require_string(
    arguments: dict[str, Any],
    name: str,
) -> str:
    value = arguments.get(name)

    if not isinstance(value, str) or not value:
        raise ValueError(
            f"{name} must be a non-empty string"
        )

    return value


def _require_optional_int(
    arguments: dict[str, Any],
    name: str,
) -> int | None:
    value = arguments.get(name)

    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"{name} must be an integer"
        )

    return value


def _validate_search_logs(
    arguments: dict[str, Any],
) -> None:
    _require_string(arguments, "service")
    _require_string(arguments, "query")

    _reject_unknown_arguments(
        arguments,
        {"service", "query"},
    )


def _validate_query_metrics(
    arguments: dict[str, Any],
) -> None:
    _require_string(arguments, "service")

    metric = _require_string(arguments, "metric")

    if metric not in {"error_rate", "request_rate"}:
        raise ValueError(
            f"Unsupported metric: {metric}"
        )

    _require_optional_int(arguments, "window_minutes")

    _reject_unknown_arguments(
        arguments,
        {
            "service",
            "metric",
            "window_minutes",
        },
    )


def _validate_recent_deployments(
    arguments: dict[str, Any],
) -> None:
    _require_string(arguments, "service")
    _require_optional_int(arguments, "window_minutes")

    _reject_unknown_arguments(
        arguments,
        {
            "service",
            "window_minutes",
        },
    )


def _validate_get_commit(
    arguments: dict[str, Any],
) -> None:
    _require_string(arguments, "commit_sha")

    _reject_unknown_arguments(
        arguments,
        {"commit_sha"},
    )


def _validate_historical_incidents(
    arguments: dict[str, Any],
) -> None:
    _require_string(arguments, "service")
    _require_string(arguments, "query")

    _reject_unknown_arguments(
        arguments,
        {"service", "query"},
    )


def _reject_unknown_arguments(
    arguments: dict[str, Any],
    allowed: set[str],
) -> None:
    unknown = set(arguments) - allowed

    if unknown:
        raise ValueError(
            f"Unknown arguments: {sorted(unknown)}"
        )