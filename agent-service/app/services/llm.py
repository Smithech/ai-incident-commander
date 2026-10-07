import os
from typing import Protocol

from openai import AsyncOpenAI

from app.domain.hypothesis import HypothesisGenerationResult
from app.domain.tool_selection import ToolSelectionResult
from app.services.hypothesis_generation import HypothesisGenerationInput
from app.services.tool_selection import ToolSelectionInput


class LLMClient(Protocol):
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        ...

    async def select_tools(
        self,
        request: ToolSelectionInput,
    ) -> ToolSelectionResult:
        ...


class NvidiaLLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.model = model or os.environ["LLM_MODEL"]

        self.client = AsyncOpenAI(
            api_key=api_key or os.environ["LLM_API_KEY"],
            base_url=base_url or os.environ["LLM_BASE_URL"],
        )

    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        response = await self.client.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an incident investigation assistant. "
                        "Generate hypotheses only from the provided incident and evidence. "
                        "\n\n"
                        "Evidence grounding rules: "
                        "1. Every factual claim in a hypothesis must be supported by "
                        "the provided evidence. "
                        "2. A hypothesis may infer a causal relationship from evidence, "
                        "but must not introduce concrete facts that are not supported. "
                        "3. Every evidence ID must be copied EXACTLY from the provided "
                        "evidence list. "
                        "4. Never invent, modify, shorten, or infer an evidence ID. "
                        "5. If no available evidence supports a hypothesis, do not "
                        "generate that hypothesis. "
                        "6. If the evidence is insufficient, return no hypotheses. "
                        "\n\n"
                        "Evidence IDs are opaque identifiers. Treat them as exact strings."
                    ),
                },
                {
                    "role": "user",
                    "content": request.model_dump_json(),
                },
            ],
            response_format=HypothesisGenerationResult,
        )

        parsed = response.choices[0].message.parsed

        if parsed is None:
            raise ValueError("LLM returned no structured result")

        return parsed

    async def select_tools(
        self,
        request: ToolSelectionInput,
    ) -> ToolSelectionResult:
        response = await self.client.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": request.model_dump_json(),
                },
            ],
            response_format=ToolSelectionResult,
        )

        parsed = response.choices[0].message.parsed

        if parsed is None:
            raise ValueError("LLM returned no structured tool selection")

        return parsed


system_prompt = """
You are an incident investigation assistant.

Your task is to select the tools that should be executed to gather
sufficient evidence for investigating the incident.

Available tools:

1. search_logs

Purpose:
Search application logs for relevant errors and events.

Arguments:
- service: string, REQUIRED
- query: string, REQUIRED

Example:
{
  "tool_name": "search_logs",
  "arguments": {
    "service": "checkout-api",
    "query": "payment"
  }
}


2. query_metrics

Purpose:
Query a service metric and compare it with its baseline.

Arguments:
- service: string, REQUIRED
- metric: string, REQUIRED
- window_minutes: integer, OPTIONAL

Example:
{
  "tool_name": "query_metrics",
  "arguments": {
    "service": "checkout-api",
    "metric": "error_rate",
    "window_minutes": 30
  }
}


3. get_recent_deployments

Purpose:
Find recent deployments for a service.

Arguments:
- service: string, REQUIRED
- window_minutes: integer, OPTIONAL


4. get_commit

Purpose:
Retrieve information about a specific commit.

Arguments:
- commit_sha: string, REQUIRED


5. search_historical_incidents

Purpose:
Search previous incidents for similar symptoms or causes.

Arguments:
- service: string, REQUIRED
- query: string, REQUIRED

Selection guidelines:

- Select all tools that can provide materially useful evidence.
- Prefer gathering complementary evidence from different sources.
- Do not select a tool merely because it exists.
- Do not assume facts that have not been established.
- Base tool selection only on the information available in the incident.
- Do not invent tool names.
- Do not execute tools.
- Return only valid tool requests.
- Every selected tool MUST include all required arguments.
- Never return an empty arguments object.
- Use the incident service when the tool requires a service.
- Do not invent values that are not available from the incident context.

Investigation heuristics:

- For incidents involving errors, failures, exceptions, or timeouts,
  search_logs is usually useful because logs can reveal the concrete
  failure mechanism and external dependency errors.
- For incidents involving elevated or abnormal behavior, query_metrics
  is useful to quantify the deviation from baseline.
- For incidents that may be related to a recent change, get_recent_deployments
  is useful.
- Use get_commit when a specific commit SHA is already available.
- For incidents involving a known symptom, dependency, or failure mode,
  search_historical_incidents can provide useful comparison evidence.
- Prefer multiple complementary sources when the incident description
  indicates that they may reveal different aspects of the failure.
"""