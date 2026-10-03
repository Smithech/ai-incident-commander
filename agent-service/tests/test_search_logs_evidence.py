from datetime import datetime, timezone

from app.domain.evidence import Evidence
from app.tools.search_logs import (
    LogEntry,
    SearchLogsResult,
    search_logs_result_to_evidence,
)


def test_search_logs_result_is_converted_to_evidence():
    result = SearchLogsResult(
        matches=[
            LogEntry(
                timestamp=datetime(
                    2026,
                    10,
                    3,
                    14,
                    1,
                    tzinfo=timezone.utc,
                ),
                level="ERROR",
                service="checkout-api",
                message="Database connection timeout",
            ),
        ]
    )

    evidence = search_logs_result_to_evidence(result)

    assert len(evidence) == 1

    item = evidence[0]

    assert isinstance(item, Evidence)

    assert item.source == "search_logs"

    assert item.summary == (
        "ERROR log from checkout-api: "
        "Database connection timeout"
    )

    assert item.data == {
        "timestamp": "2026-10-03T14:01:00+00:00",
        "level": "ERROR",
        "service": "checkout-api",
        "message": "Database connection timeout",
    }