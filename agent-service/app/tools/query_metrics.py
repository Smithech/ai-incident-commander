from uuid import uuid4

from pydantic import BaseModel, Field

from app.domain.evidence import Evidence


class MetricResult(BaseModel):
    metric: str
    service: str
    value: float
    baseline: float
    unit: str
    window_minutes: int = Field(gt=0)


def metric_result_to_evidence(
    result: MetricResult,
) -> Evidence:
    return Evidence(
        id=str(uuid4()),
        source="query_metrics",
        summary=(
            f"{result.metric} for {result.service} is "
            f"{result.value}{result.unit}, "
            f"baseline {result.baseline}{result.unit}."
        ),
        data=result.model_dump(),
    )