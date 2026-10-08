import os
from typing import Protocol

from openai import AsyncOpenAI

from app.domain.hypothesis import HypothesisEvaluationResult, HypothesisGenerationResult
from app.domain.tool_selection import ToolSelectionResult
from app.services.hypothesis_evaluation import HypothesisEvaluationInput
from app.services.hypothesis_generation import HypothesisGenerationInput
from app.services.tool_selection import ToolSelectionInput


class LLMClient(Protocol):
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        ...

    async def evaluate_hypotheses(
        self,
        request: HypothesisEvaluationInput,
    ) -> HypothesisEvaluationResult:
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
                    "content": HYPOTHESIS_GENERATION_SYSTEM_PROMPT,
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

    async def evaluate_hypotheses(
        self,
        request: HypothesisEvaluationInput,
    ) -> HypothesisEvaluationResult:
        response = await self.client.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": HYPOTHESIS_EVALUATION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": request.model_dump_json(),
                },
            ],
            response_format=HypothesisEvaluationResult,
        )

        parsed = response.choices[0].message.parsed

        if parsed is None:
            raise ValueError(
                "LLM returned no hypothesis evaluation result"
            )

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
                    "content": TOOL_SELECTION_SYSTEM_PROMPT,
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


HYPOTHESIS_GENERATION_SYSTEM_PROMPT = """
You are an incident investigation assistant.

Generate hypotheses only from the provided evidence.

Important distinction:
- Evidence may establish that a symptom exists without explaining its cause.
- Do not treat an error message, elevated metric, or other symptom as the cause of itself.
- A hypothesis must explain the incident using evidence that provides
  meaningful support for that explanation.
- If the evidence only confirms that the service is experiencing a problem
  but does not identify or support a plausible cause, return no hypotheses.

Do not invent evidence.
Every factual claim must be supported by the provided evidence.
Causal inference is allowed only when the available evidence provides
meaningful support for the causal relationship.

Every evidence ID you reference must come from the provided evidence.
Copy evidence IDs exactly.
Never invent, modify, shorten, or infer evidence IDs.

If no evidence supports a causal explanation, return no hypotheses.
If the evidence is insufficient to identify a plausible cause, return no hypotheses.
"""


HYPOTHESIS_EVALUATION_SYSTEM_PROMPT = """
You are an incident investigation assistant. Evaluate each hypothesis only against the provided evidence.

Verdicts:
- supported: the evidence provides meaningful support for the hypothesis.
- contradicted: the evidence provides meaningful evidence against the hypothesis.
- inconclusive: the evidence is insufficient to support or contradict the hypothesis.

Important rules:
- Do not invent evidence or facts.
- Do not treat a symptom as its own cause.
- Causal relationships must be meaningfully supported by the provided evidence.
- Every evidence ID must come exactly from the provided evidence.
- Never invent, modify, shorten, or infer evidence IDs.
- Every hypothesis ID must come exactly from the provided hypotheses.
- Never invent or modify hypothesis IDs.
- If the evidence is insufficient to determine whether a hypothesis is supported or contradicted, use 'inconclusive'.
- If there are no hypotheses, return an empty evaluations list.
"""


TOOL_SELECTION_SYSTEM_PROMPT = """
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
- For incidents involving elevated or abnormal behavior, use query_metrics
  to quantify the abnormal behavior and, when relevant, its impact on
  service health.
- For incidents that may be related to a recent change, get_recent_deployments
  is useful.
- Use get_commit when a specific commit SHA is already available.
- For incidents involving a known symptom, dependency, or failure mode,
  search_historical_incidents can provide useful comparison evidence.
- Prefer multiple complementary sources when the incident description
  indicates that they may reveal different aspects of the failure.
- When an incident involves abnormal traffic, load, latency, errors,
  saturation, or capacity, consider complementary evidence:
  - a metric measuring the abnormal behavior,
  - a metric measuring service impact such as error rate or latency,
  - and logs that may reveal the mechanism or symptom.
- When multiple metrics can describe different aspects of the same
  incident, prefer complementary metrics rather than relying on a
  single metric.
- For traffic or load-related incidents, search_logs can help determine
  whether the increased load is associated with timeouts, queueing,
  worker exhaustion, or other service symptoms.
- When an incident involves abnormal traffic or load and the service
  shows elevated error rates, consider search_logs to identify the
  operational mechanism behind the impact, such as timeouts, queueing,
  worker exhaustion, or resource saturation.
- Prefer evidence that explains not only that a metric is abnormal,
  but also how the abnormal condition may be affecting the service.
- When an incident involves abnormal traffic or load and the service
  shows elevated error rates, consider search_logs to identify the
  operational mechanism behind the impact, such as timeouts, queueing,
  worker exhaustion, or resource saturation.
- Prefer evidence that explains not only that a metric is abnormal,
  but also how the abnormal condition may be affecting the service.
"""