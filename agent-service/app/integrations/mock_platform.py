import os

import httpx

from app.tools.search_logs import LogEntry


class MockPlatformClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def search_logs(
        self,
        *,
        service: str,
        query: str,
    ) -> list[LogEntry]:
        async with httpx.AsyncClient(
            timeout=5.0,
        ) as client:
            response = await client.get(
                f"{self.base_url}/logs",
                params={
                    "service": service,
                    "query": query,
                },
            )

        response.raise_for_status()

        return [
            LogEntry.model_validate(item)
            for item in response.json()
        ]


def create_mock_platform_client() -> MockPlatformClient:
    base_url = os.environ["MOCK_PLATFORM_URL"]
    return MockPlatformClient(base_url)