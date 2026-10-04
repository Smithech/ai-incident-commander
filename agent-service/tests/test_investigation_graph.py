import pytest
from uuid import uuid4

from app.workflows.investigation import investigation_graph


@pytest.mark.asyncio
async def test_investigation_graph_collects_evidence():
    incident_id = uuid4()

    result = await investigation_graph.ainvoke(
        {
            "incident_id": incident_id,
            "service": "checkout-api",
            "evidence": [],
        }
    )

    assert result["incident_id"] == incident_id
    assert result["service"] == "checkout-api"

    evidence = result["evidence"]

    assert len(evidence) == 6

    sources = [item.source for item in evidence]

    assert sources.count("search_logs") == 2
    assert sources.count("query_metrics") == 1
    assert sources.count("get_recent_deployments") == 1
    assert sources.count("get_commit") == 1
    assert sources.count("search_historical_incidents") == 1

    assert any(
        "Database connection timeout" in item.summary
        for item in evidence
    )

    metric_evidence = next(
        item for item in evidence
        if item.source == "query_metrics"
    )

    assert metric_evidence.data["value"] == 18.4
    assert metric_evidence.data["baseline"] == 0.8

    deployment_evidence = next(
        item for item in evidence
        if item.source == "get_recent_deployments"
    )

    assert deployment_evidence.data["commit_sha"] == "abc123"

    commit_evidence = next(
        item for item in evidence
        if item.source == "get_commit"
    )

    assert commit_evidence.data["sha"] == "abc123"

    historical_evidence = next(
        item for item in evidence
        if item.source == "search_historical_incidents"
    )

    assert historical_evidence.data["id"] == "INC-42"