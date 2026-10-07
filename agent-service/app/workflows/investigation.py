from collections.abc import Awaitable, Callable
from typing import TypedDict
from uuid import UUID, uuid4

from fastmcp import Client
from langgraph.graph import END, START, StateGraph

from app.domain.evidence import Evidence
from app.domain.hypothesis import Hypothesis
from app.domain.tool_selection import ToolRequest
from app.mcp_server import mcp
from app.services.hypothesis_generation import (
    HypothesisGenerationInput,
    validate_evidence_references,
)
from app.services.llm import LLMClient
from app.services.tool_execution import execute_tool_request
from app.services.tool_selection import (
    ToolSelectionInput,
    validate_tool_selection,
)


ToolExecutor = Callable[
    [ToolRequest],
    Awaitable[list[Evidence]],
]


class InvestigationState(TypedDict):
    incident_id: UUID
    service: str
    incident_title: str
    incident_description: str
    tool_requests: list[ToolRequest]
    evidence: list[Evidence]
    hypotheses: list[Hypothesis]


async def select_tools(
    state: InvestigationState,
    llm_client: LLMClient,
) -> dict:
    request = ToolSelectionInput(
        incident_service=state["service"],
        incident_title=state["incident_title"],
        incident_description=state["incident_description"],
    )

    result = await llm_client.select_tools(request)

    validate_tool_selection(result)

    return {
        "tool_requests": result.requests,
    }


async def collect_evidence(
    state: InvestigationState,
    execute_tool: ToolExecutor = execute_tool_request,
) -> dict:
    evidence: list[Evidence] = []

    for request in state["tool_requests"]:
        tool_evidence = await execute_tool(request)
        evidence.extend(tool_evidence)

    return {
        "evidence": evidence,
    }


async def generate_hypotheses(
    state: InvestigationState,
    llm_client: LLMClient
) -> dict:
    """Generate hypotheses from collected evidence using the LLM."""

    request = HypothesisGenerationInput(
        incident_service=state["service"],
        incident_title=state["incident_title"],
        incident_description=state["incident_description"],
        evidence=state["evidence"],
    )

    result = await llm_client.generate_hypotheses(request)

    validate_evidence_references(
        result=result,
        evidence=state["evidence"],
    )

    hypotheses = [
        Hypothesis(
            id=str(uuid4()),
            statement=candidate.statement,
            supporting_evidence_ids=candidate.supporting_evidence_ids,
            contradicting_evidence_ids=candidate.contradicting_evidence_ids,
        )
        for candidate in result.hypotheses
    ]

    return {"hypotheses": hypotheses}


def build_investigation_graph(
    llm_client: LLMClient,
    execute_tool: ToolExecutor = execute_tool_request,
):
    async def generate_hypotheses_node(
        state: InvestigationState,
    ) -> dict:
        return await generate_hypotheses(
            state,
            llm_client=llm_client,
        )

    async def collect_evidence_node(
        state: InvestigationState,
    ) -> dict:
        return await collect_evidence(
            state,
            execute_tool=execute_tool,
        )
    
    builder = StateGraph(InvestigationState)

    async def select_tools_node(
        state: InvestigationState,
    ) -> dict:
        return await select_tools(
            state,
            llm_client,
        )
    
    builder.add_node("select_tools", select_tools_node)
    builder.add_node("collect_evidence", collect_evidence_node)
    builder.add_node("generate_hypotheses", generate_hypotheses_node)

    builder.add_edge(START, "select_tools")
    builder.add_edge("select_tools", "collect_evidence")

    builder.add_conditional_edges(
        "collect_evidence",
        should_generate_hypotheses,
        {
            "end": END,
            "generate_hypotheses": "generate_hypotheses",
        },
    )

    builder.add_edge("generate_hypotheses", END)

    return builder.compile()


def should_generate_hypotheses(
    state: InvestigationState,
) -> str:
    if not state["evidence"]:
        return "end"

    return "generate_hypotheses"