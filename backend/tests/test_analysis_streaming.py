import json

from fastapi.testclient import TestClient

from backend.app.api import routes
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.schemas.analysis import AnalyzeResponse
from backend.app.services.agent_service import AnalysisUnavailableError


def _response(question: str) -> AnalyzeResponse:
    return AnalyzeResponse(
        question=question,
        path="cold_path",
        summary="查询完成",
        sql="SELECT 1",
        metrics=[],
        rows=[],
        source={
            "dataset": "test",
            "tables": [],
            "fields": [],
            "metricDefinition": "test",
            "range": "test",
            "returnedRows": 0,
            "queryTime": "0ms",
            "security": "只读 SELECT，已通过 SQL Guard",
        },
        trace={"toolCalls": 0, "modelCalls": 0, "memoryCandidates": 0, "totalTime": "0ms"},
        steps=[],
    )


def _events(body: str) -> list[tuple[str, dict]]:
    result: list[tuple[str, dict]] = []
    for block in body.replace("\r\n", "\n").split("\n\n"):
        if not block:
            continue
        fields = dict(line.split(": ", 1) for line in block.split("\n") if ": " in line)
        result.append((fields["event"], json.loads(fields["data"])))
    return result


def test_analysis_stream_sends_real_stages_then_result_and_done(monkeypatch) -> None:
    def fake_analyze(payload, app_user_id=None, on_stage=None):
        assert app_user_id is None
        assert on_stage is not None
        on_stage({"name": "加载会话", "status": "running"})
        on_stage({"name": "执行受控数据分析", "status": "running"})
        return _response(payload.question)

    monkeypatch.setattr(routes.agent_service, "analyze", fake_analyze)
    response = TestClient(app).post("/api/analyze/stream", json={"question": "当前订单数是多少"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    events = _events(response.text)
    assert [event for event, _data in events] == ["stage", "stage", "result", "done"]
    assert events[0][1]["name"] == "加载会话"
    assert events[2][1]["summary"] == "查询完成"
    assert "text_delta" not in response.text


def test_analysis_stream_serializes_service_failure_as_error_event(monkeypatch) -> None:
    def unavailable(*_args, **_kwargs):
        raise AnalysisUnavailableError("没有可执行 SQL")

    monkeypatch.setattr(routes.agent_service, "analyze", unavailable)
    response = TestClient(app).post("/api/analyze/stream", json={"question": "当前订单数是多少"})

    events = _events(response.text)
    assert [event for event, _data in events] == ["error", "done"]
    assert events[0][1] == {"status": 503, "detail": "没有可执行 SQL"}


def test_analysis_stream_requires_login_when_auth_is_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "auth_required", True)

    response = TestClient(app).post("/api/analyze/stream", json={"question": "当前订单数是多少"})

    assert response.status_code == 401
