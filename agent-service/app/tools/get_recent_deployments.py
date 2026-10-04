from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from app.domain.evidence import Evidence


class Deployment(BaseModel):
    id: str
    service: str
    commit_sha: str
    deployed_at: datetime
    version: str


class RecentDeploymentsResult(BaseModel):
    deployments: list[Deployment] = Field(max_length=20)


def deployment_result_to_evidence(
    result: RecentDeploymentsResult,
) -> list[Evidence]:
    return [
        Evidence(
            id=str(uuid4()),
            source="get_recent_deployments",
            summary=(
                f"Deployment {deployment.id} of "
                f"{deployment.service} version "
                f"{deployment.version} was deployed at "
                f"{deployment.deployed_at.isoformat()}."
            ),
            data=deployment.model_dump(mode="json"),
        )
        for deployment in result.deployments
    ]