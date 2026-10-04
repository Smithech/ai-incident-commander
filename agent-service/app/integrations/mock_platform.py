import os

import httpx

from app.tools.get_commit import CommitResult
from app.tools.get_recent_deployments import Deployment
from app.tools.query_metrics import MetricResult
from app.tools.search_historical_incidents import HistoricalIncident
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

    async def query_metrics(
        self,
        *,
        service: str,
        metric: str,
        window_minutes: int,
    ) -> MetricResult:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{self.base_url}/metrics",
                params={
                    "service": service,
                    "metric": metric,
                    "window_minutes": window_minutes,
                },
            )

        response.raise_for_status()
        return MetricResult.model_validate(response.json())

    async def get_recent_deployments(
        self,
        *,
        service: str,
        window_minutes: int,
    ) -> list[Deployment]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{self.base_url}/deployments",
                params={
                    "service": service,
                    "window_minutes": window_minutes,
                },
            )

        response.raise_for_status()
        return [
            Deployment.model_validate(item)
            for item in response.json()
        ]

    async def get_commit(
        self,
        *,
        commit_sha: str,
    ) -> CommitResult:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{self.base_url}/commits/{commit_sha}",
            )

        response.raise_for_status()
        return CommitResult.model_validate(response.json())

    async def search_historical_incidents(
        self,
        *,
        service: str,
        query: str,
    ) -> list[HistoricalIncident]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{self.base_url}/historical-incidents",
                params={"service": service, "query": query},
            )

        response.raise_for_status()
        return [
            HistoricalIncident.model_validate(item)
            for item in response.json()
        ]


def create_mock_platform_client() -> MockPlatformClient:
    base_url = os.environ["MOCK_PLATFORM_URL"]
    return MockPlatformClient(base_url)