from typing import TypedDict
from uuid import UUID, uuid4

from fastmcp import Client
from langgraph.graph import END, START, StateGraph

from app.domain.evidence import Evidence
from app.domain.hypothesis import Hypothesis
from app.mcp_server import mcp
from app.services.hypothesis_generation import (
    HypothesisGenerationInput,
    validate_evidence_references,
)
from app.services.llm import LLMClient
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


class InvestigationState(TypedDict):
    incident_id: UUID
    service: str
    incident_title: str
    incident_description: str
    evidence: list[Evidence]
    hypotheses: list[Hypothesis]


async def collect_evidence(
    state: InvestigationState,
) -> dict:
    async with Client(mcp) as client:

        # 1. Logs
        logs_result = await client.call_tool(
            "search_logs",
            {
                "service": state["service"],
                "query": "database",
            },
        )

        if logs_result.is_error:
            raise RuntimeError(
                "search_logs MCP tool failed"
            )

        if logs_result.structured_content is None:
            raise RuntimeError(
                "search_logs returned no structured content"
            )

        logs = SearchLogsResult.model_validate(
            logs_result.structured_content
        )

        evidence = search_logs_result_to_evidence(logs)

        # 2. Metrics
        metrics_result = await client.call_tool(
            "query_metrics",
            {
                "service": state["service"],
                "metric": "error_rate",
                "window_minutes": 30,
            },
        )

        if metrics_result.is_error:
            raise RuntimeError(
                "query_metrics MCP tool failed"
            )

        if metrics_result.structured_content is None:
            raise RuntimeError(
                "query_metrics returned no structured content"
            )

        metrics = MetricResult.model_validate(
            metrics_result.structured_content
        )

        evidence.append(
            metric_result_to_evidence(metrics)
        )

        # 3. Recent deployments
        deployments_result = await client.call_tool(
            "get_recent_deployments",
            {
                "service": state["service"],
                "window_minutes": 60,
            },
        )

        if deployments_result.is_error:
            raise RuntimeError(
                "get_recent_deployments MCP tool failed"
            )

        if deployments_result.structured_content is None:
            raise RuntimeError(
                "get_recent_deployments returned no structured content"
            )

        deployments = RecentDeploymentsResult.model_validate(
            deployments_result.structured_content
        )

        evidence.extend(
            deployment_result_to_evidence(deployments)
        )

        # 4. Commits associated with recent deployments
        for deployment in deployments.deployments:
            commit_result = await client.call_tool(
                "get_commit",
                {
                    "commit_sha": deployment.commit_sha,
                },
            )

            if commit_result.is_error:
                raise RuntimeError(
                    f"get_commit MCP tool failed for "
                    f"{deployment.commit_sha}"
                )

            if commit_result.structured_content is None:
                raise RuntimeError(
                    "get_commit returned no structured content"
                )

            commit = CommitResult.model_validate(
                commit_result.structured_content
            )

            evidence.append(
                commit_result_to_evidence(commit)
            )

        # 5. Historical incidents
        historical_result = await client.call_tool(
            "search_historical_incidents",
            {
                "service": state["service"],
                "query": "database",
            },
        )

        if historical_result.is_error:
            raise RuntimeError(
                "search_historical_incidents MCP tool failed"
            )

        if historical_result.structured_content is None:
            raise RuntimeError(
                "search_historical_incidents "
                "returned no structured content"
            )

        historical = HistoricalIncidentsResult.model_validate(
            historical_result.structured_content
        )

        evidence.extend(
            historical_incidents_to_evidence(
                historical
            )
        )

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
):
    async def generate_hypotheses_node(
        state: InvestigationState,
    ) -> dict:
        return await generate_hypotheses(
            state,
            llm_client=llm_client,
        )

    builder = StateGraph(InvestigationState)

    builder.add_node("collect_evidence", collect_evidence)
    builder.add_node("generate_hypotheses", generate_hypotheses_node)

    builder.add_edge(START, "collect_evidence")

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