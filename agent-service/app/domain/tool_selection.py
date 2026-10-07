from typing import Any

from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    tool_name: str = Field(min_length=1, max_length=100)
    arguments: dict[str, Any]


class ToolSelectionResult(BaseModel):
    requests: list[ToolRequest] = Field(max_length=10)