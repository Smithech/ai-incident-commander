from fastmcp import Client

from app.domain.evidence import Evidence
from app.domain.tool_selection import ToolRequest
from app.mcp_server import mcp
from app.tools.search_logs import (
    SearchLogsResult,
    search_logs_result_to_evidence,
)


async def execute_tool_request(
    request: ToolRequest,
) -> list[Evidence]:
    if request.tool_name != "search_logs":
        raise ValueError(
            f"Unsupported tool: {request.tool_name}"
        )

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

    evidence = search_logs_result_to_evidence(logs)

    return evidence
