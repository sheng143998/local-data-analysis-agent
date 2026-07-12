from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.api import conversations, routes
from backend.app.core.config import settings
from backend.app.schemas.analysis import AnalyzeResponse
from backend.app.services import agent_service
from backend.app.services.agent_service import AgentService
from backend.app.services.conversation_store import InMemoryConversationStore
from backend.app.main import app


def _graph_response(question: str, **_kwargs) -> AnalyzeResponse:
    return AnalyzeResponse(
        question=question,
        path="cold_path",
        summary="查询完成",
        sql="SELECT 1",
        metrics=[],
        rows=[],
        source={"dataset": "test", "tables": [], "fields": [], "metricDefinition": "test", "range": "2017年", "returnedRows": 0, "queryTime": "0ms", "security": "只读 SELECT，已通过 SQL Guard"},
        trace={"toolCalls": 0, "modelCalls": 0, "memoryCandidates": 0, "totalTime": "0ms"},
        steps=[],
    )


def test_followup_merges_pending_slots_before_graph_execution(monkeypatch) -> None:
    monkeypatch.setattr(settings, "intent_parser_enabled", False)
    calls = []

    def fake_graph(question, **kwargs):
        calls.append((question, kwargs["parsed_intent"]))
        return _graph_response(question)

    monkeypatch.setattr(agent_service, "run_analysis_graph", fake_graph)
    service = AgentService(conversation_store=InMemoryConversationStore())

    first = service.analyze(type("Payload", (), {"question": "看看最近情况", "conversation_id": None})())

    assert first.pending_clarification is True
    assert first.conversation_id is not None
    second = service.analyze(type("Payload", (), {"question": "销售额，2017年", "conversation_id": first.conversation_id})())

    assert second.pending_clarification is False
    assert second.sql == "SELECT 1"
    assert len(calls) == 1
    assert calls[0][1].query_spec.metrics == ["sales_amount"]
    assert calls[0][1].query_spec.time_start == "2017-01-01"
    assert calls[0][1].query_spec.time_end == "2018-01-01"


def test_conversations_are_scoped_to_authenticated_owner(monkeypatch) -> None:
    monkeypatch.setattr(settings, "intent_parser_enabled", False)
    monkeypatch.setattr(agent_service, "run_analysis_graph", _graph_response)
    service = AgentService(conversation_store=InMemoryConversationStore())
    owner = uuid4()
    other_owner = uuid4()
    response = service.analyze(type("Payload", (), {"question": "销售额是多少", "conversation_id": None})(), app_user_id=owner)

    assert len(service.list_conversations(owner)) == 1
    assert service.list_conversations(other_owner) == []
    with pytest.raises(HTTPException) as error:
        service.get_conversation(response.conversation_id, other_owner)
    assert error.value.status_code == 404


def test_conversation_api_continues_clarification_and_exposes_history(monkeypatch) -> None:
    monkeypatch.setattr(settings, "intent_parser_enabled", False)
    monkeypatch.setattr(agent_service, "run_analysis_graph", _graph_response)
    store = InMemoryConversationStore()
    monkeypatch.setattr(routes.agent_service, "conversation_store", store)
    monkeypatch.setattr(conversations.conversation_service, "conversation_store", store)
    client = TestClient(app)

    first = client.post("/api/analyze", json={"question": "看看最近情况"})
    assert first.status_code == 200
    conversation_id = first.json()["conversation_id"]
    assert first.json()["pending_clarification"] is True

    second = client.post("/api/analyze", json={"question": "销售额，2017年", "conversation_id": conversation_id})
    assert second.status_code == 200
    assert second.json()["pending_clarification"] is False
    history = client.get(f"/api/conversations/{conversation_id}")
    assert history.status_code == 200
    assert [item["role"] for item in history.json()["messages"]] == ["user", "assistant", "user", "assistant"]


def test_authenticated_users_cannot_read_each_others_conversations(monkeypatch) -> None:
    monkeypatch.setattr(settings, "intent_parser_enabled", False)
    monkeypatch.setattr(settings, "auth_required", True)
    monkeypatch.setattr(settings, "auth_allow_self_registration", True)
    store = InMemoryConversationStore()
    monkeypatch.setattr(routes.agent_service, "conversation_store", store)
    monkeypatch.setattr(conversations.conversation_service, "conversation_store", store)
    owner_client = TestClient(app)
    other_client = TestClient(app)
    owner_email = f"owner-{uuid4().hex}@example.com"
    other_email = f"other-{uuid4().hex}@example.com"
    for client, email in ((owner_client, owner_email), (other_client, other_email)):
        assert client.post("/api/auth/register", json={"email": email, "display_name": "Test User", "password": "correct horse battery staple"}).status_code == 200

    created = owner_client.post("/api/analyze", json={"question": "看看最近情况"})
    assert created.status_code == 200
    conversation_id = created.json()["conversation_id"]
    assert other_client.get(f"/api/conversations/{conversation_id}").status_code == 404
