from fastmcp import Client
from fastmcp.exceptions import ToolError

from app.domain.evidence import Evidence
from app.domain.tool_selection import ToolRequest
from app.mcp_server import mcp
from app.tools.get_commit import (
    CommitResult,
    commit_result_to_evidence,
)
from app.tools.get_recent_deployments import (
    RecentDeploymentsResult,
    deployment_result_to_evidence,
)
from app.tools.query_metrics import (
    MetricResult,
    metric_result_to_evidence,
)
from app.tools.search_historical_incidents import (
    HistoricalIncidentsResult,
    historical_incidents_to_evidence,
)
from app.tools.search_logs import (
    SearchLogsResult,
    search_logs_result_to_evidence,
)


class ToolDataUnavailableError(Exception):
    """Raised when a tool has no data available for the request."""


async def execute_tool_request(
    request: ToolRequest,
) -> list[Evidence]:
    if request.tool_name == "search_logs":
        return await _execute_search_logs(request)

    if request.tool_name == "query_metrics":
        return await _execute_query_metrics(request)

    if request.tool_name == "get_recent_deployments":
        return await _execute_recent_deployments(request)

    if request.tool_name == "get_commit":
        return await _execute_get_commit(request)

    if request.tool_name == "search_historical_incidents":
        return await _execute_historical_incidents(request)

    raise ValueError(
        f"Unsupported tool: {request.tool_name}"
    )


async def _execute_search_logs(
    request: ToolRequest,
) -> list[Evidence]:
    service = request.arguments.get("service")
    query = request.arguments.get("query")

    if not isinstance(service, str) or not service:
        raise ValueError(
            "search_logs requires a non-empty service"
        )

    if not isinstance(query, str) or not query:
        raise ValueError(
            "search_logs requires a non-empty query"
        )

    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_logs",
            {
                "service": service,
                "query": query,
            },
        )

    if result.is_error:
        raise RuntimeError(
            "search_logs MCP tool failed"
        )

    if result.structured_content is None:
        raise RuntimeError(
            "search_logs returned no structured content"
        )

    logs = SearchLogsResult.model_validate(
        result.structured_content
    )

    return search_logs_result_to_evidence(logs)


async def _execute_query_metrics(
    request: ToolRequest,
) -> list[Evidence]:
    service = request.arguments.get("service")
    metric = request.arguments.get("metric")
    window_minutes = request.arguments.get(
        "window_minutes",
        30,
    )

    if not isinstance(service, str) or not service:
        raise ValueError(
            "query_metrics requires a non-empty service"
        )

    if not isinstance(metric, str) or not metric:
        raise ValueError(
            "query_metrics requires a non-empty metric"
        )

    if (
        isinstance(window_minutes, bool)
        or not isinstance(window_minutes, int)
        or window_minutes <= 0
    ):
        raise ValueError(
            "query_metrics requires a positive integer "
            "window_minutes"
        )

    try:
        async with Client(mcp) as client:
            result = await client.call_tool(
                "query_metrics",
                {
                    "service": service,
                    "metric": metric,
                    "window_minutes": window_minutes,
                },
            )
    except ToolError as exc:
        if "404 Not Found" in str(exc):
            raise ToolDataUnavailableError(
                f"Metric not available: {metric}"
            ) from exc

        raise

    if result.is_error:
        raise RuntimeError(
            "query_metrics MCP tool failed"
        )

    if result.structured_content is None:
        raise RuntimeError(
            "query_metrics returned no structured content"
        )

    metric_result = MetricResult.model_validate(
        result.structured_content
    )

    return [
        metric_result_to_evidence(metric_result)
    ]


async def _execute_recent_deployments(
    request: ToolRequest,
) -> list[Evidence]:
    service = request.arguments.get("service")
    window_minutes = request.arguments.get(
        "window_minutes",
        60,
    )

    if not isinstance(service, str) or not service:
        raise ValueError(
            "get_recent_deployments requires "
            "a non-empty service"
        )

    if (
        isinstance(window_minutes, bool)
        or not isinstance(window_minutes, int)
        or window_minutes <= 0
    ):
        raise ValueError(
            "get_recent_deployments requires a positive "
            "integer window_minutes"
        )

    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_recent_deployments",
            {
                "service": service,
                "window_minutes": window_minutes,
            },
        )

    if result.is_error:
        raise RuntimeError(
            "get_recent_deployments MCP tool failed"
        )

    if result.structured_content is None:
        raise RuntimeError(
            "get_recent_deployments returned no "
            "structured content"
        )

    deployments = RecentDeploymentsResult.model_validate(
        result.structured_content
    )

    return deployment_result_to_evidence(deployments)


async def _execute_get_commit(
    request: ToolRequest,
) -> list[Evidence]:
    commit_sha = request.arguments.get("commit_sha")

    if not isinstance(commit_sha, str) or not commit_sha:
        raise ValueError(
            "get_commit requires a non-empty commit_sha"
        )

    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_commit",
            {
                "commit_sha": commit_sha,
            },
        )

    if result.is_error:
        raise RuntimeError(
            "get_commit MCP tool failed"
        )

    if result.structured_content is None:
        raise RuntimeError(
            "get_commit returned no structured content"
        )

    commit = CommitResult.model_validate(
        result.structured_content
    )

    return [
        commit_result_to_evidence(commit)
    ]


async def _execute_historical_incidents(
    request: ToolRequest,
) -> list[Evidence]:
    service = request.arguments.get("service")
    query = request.arguments.get("query")

    if not isinstance(service, str) or not service:
        raise ValueError(
            "search_historical_incidents requires "
            "a non-empty service"
        )

    if not isinstance(query, str) or not query:
        raise ValueError(
            "search_historical_incidents requires "
            "a non-empty query"
        )

    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_historical_incidents",
            {
                "service": service,
                "query": query,
            },
        )

    if result.is_error:
        raise RuntimeError(
            "search_historical_incidents MCP tool failed"
        )

    if result.structured_content is None:
        raise RuntimeError(
            "search_historical_incidents returned no "
            "structured content"
        )

    incidents = HistoricalIncidentsResult.model_validate(
        result.structured_content
    )

    return historical_incidents_to_evidence(incidents)