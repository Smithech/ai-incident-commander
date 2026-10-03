from typing import Any

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    id: str
    source: str
    summary: str = Field(min_length=1, max_length=1_000)
    data: dict[str, Any]