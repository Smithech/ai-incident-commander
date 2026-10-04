from uuid import uuid4

import pytest

from app.workflows.investigation import investigation_graph


@pytest.mark.asyncio
async def test_investigation_graph_collects_evidence_through_mcp():
    state = {
        "incident_id": uuid4(),
        "service": "checkout-api",
        "evidence": [],
    }

    result = await investigation_graph.ainvoke(state)

    assert result["incident_id"] == state["incident_id"]
    assert result["service"] == "checkout-api"

    assert len(result["evidence"]) == 6

    sources = [evidence.source for evidence in result["evidence"]]

    assert sources.count("search_logs") == 2
    assert sources.count("query_metrics") == 1
    assert sources.count("get_recent_deployments") == 1
    assert sources.count("get_commit") == 1
    assert sources.count("search_historical_incidents") == 1

    assert any(
        "Database connection timeout" in evidence.summary
        for evidence in result["evidence"]
    )