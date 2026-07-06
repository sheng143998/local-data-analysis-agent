import json
import logging

from backend.app.tools.run_logger import _log_event


def test_log_event_writes_structured_json(caplog) -> None:
    caplog.set_level(logging.INFO, logger="backend.observability")

    _log_event(
        {
            "event": "tool_call",
            "run_id": "run-1",
            "tool_name": "sql_validation_tools.guard_sql",
            "status": "success",
            "latency_ms": 12,
        }
    )

    payload = json.loads(caplog.records[-1].message)
    assert payload == {
        "event": "tool_call",
        "latency_ms": 12,
        "run_id": "run-1",
        "status": "success",
        "tool_name": "sql_validation_tools.guard_sql",
    }
