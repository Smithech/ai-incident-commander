from typing import TypedDict
from uuid import UUID

from fastmcp import Client
from langgraph.graph import END, START, StateGraph

from app.domain.evidence import Evidence
from app.mcp_server import mcp
from app.tools.search_logs import (
    SearchLogsResult,
    search_logs_result_to_evidence,
)


class InvestigationState(TypedDict):
    incident_id: UUID
    service: str
    evidence: list[Evidence]


async def collect_evidence(
    state: InvestigationState,
) -> dict:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_logs",
            {
                "service": state["service"],
                "query": "error",
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

    tool_result = SearchLogsResult.model_validate(
        result.structured_content
    )

    evidence = search_logs_result_to_evidence(
        tool_result
    )

    return {
        "evidence": evidence,
    }


builder = StateGraph(InvestigationState)

builder.add_node(
    "collect_evidence",
    collect_evidence,
)

builder.add_edge(
    START,
    "collect_evidence",
)

builder.add_edge(
    "collect_evidence",
    END,
)

investigation_graph = builder.compile() 