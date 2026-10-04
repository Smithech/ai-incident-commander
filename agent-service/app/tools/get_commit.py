from uuid import uuid4

from pydantic import BaseModel, Field

from app.domain.evidence import Evidence


class CommitResult(BaseModel):
    sha: str
    message: str
    author: str
    changed_files: list[str] = Field(max_length=100)


def commit_result_to_evidence(
    result: CommitResult,
) -> Evidence:
    return Evidence(
        id=str(uuid4()),
        source="get_commit",
        summary=(
            f"Commit {result.sha} by {result.author}: "
            f"{result.message}"
        ),
        data=result.model_dump(),
    )