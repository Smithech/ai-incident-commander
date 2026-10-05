import os
from typing import Protocol

from openai import AsyncOpenAI

from app.domain.hypothesis import HypothesisGenerationResult
from app.services.hypothesis_generation import HypothesisGenerationInput


class LLMClient(Protocol):
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
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
                        "Generate hypotheses only from the provided evidence. "
                        "Do not invent evidence. "
                        "Every evidence ID you reference must come from the "
                        "provided evidence. "
                        "If the evidence is insufficient, return no hypotheses."
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