from pydantic import BaseModel, Field

from app.domain.tool_selection import ToolSelectionResult


class ToolSelectionInput(BaseModel):
    incident_service: str = Field(min_length=1, max_length=100)
    incident_title: str = Field(min_length=1, max_length=500)
    incident_description: str = Field(min_length=1, max_length=2_000)


class ToolSelectionClient:
    async def select_tools(
        self,
        request: ToolSelectionInput,
    ) -> ToolSelectionResult:
        raise NotImplementedError


ALLOWED_TOOLS = {
    "search_logs",
    "query_metrics",
    "get_recent_deployments",
    "get_commit",
    "search_historical_incidents",
}


def validate_tool_selection(
    result: ToolSelectionResult,
) -> None:
    for request in result.requests:
        if request.tool_name not in ALLOWED_TOOLS:
            raise ValueError(
                f"Unsupported tool: {request.tool_name}"
            )