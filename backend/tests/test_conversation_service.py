from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.api import conversations, routes
from backend.app.core.config import settings
from backend.app.schemas.analysis import AnalyzeResponse
from backend.app.schemas.conversation import PendingClarification
from backend.app.schemas.query_spec import QuerySpec
from backend.app.services import agent_service
from backend.app.services.agent_service import AgentService, AnalysisUnavailableError
from backend.app.services.conversation_store import InMemoryConversationStore
from backend.app.services import followup_resolver
from backend.app.tools.question_intent_parser import ParsedQuestionIntent
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


def test_rejecting_a_clarification_reparses_the_original_question(monkeypatch) -> None:
    pending = PendingClarification(
        original_question="当前用户总数是多少？",
        parsed_intent={},
        query_spec=QuerySpec(),
        missing_slots=["metrics"],
        clarification="你想重点分析哪项业务数据？",
        created_at=datetime.now(timezone.utc),
    )
    calls = []

    def fake_parse(question, **kwargs):
        calls.append((question, kwargs.get("conversation_context", "")))
        return ParsedQuestionIntent(
            original_question=question,
            normalized_question="查询当前用户总数",
            semantic_metrics=["当前用户总数"],
            confidence=0.4,
            needs_clarification=False,
            source="llm",
        )

    monkeypatch.setattr(followup_resolver, "parse_question_intent", fake_parse)

    resolution = followup_resolver.resolve_followup("我不想查询这些", pending)

    assert resolution.decision == "new_question"
    assert resolution.intent is not None
    assert resolution.intent.semantic_metrics == ["当前用户总数"]
    assert calls[0][0] == "当前用户总数是多少？"
    assert "拒绝了此前建议" in calls[0][1]


def test_complete_semantic_candidate_enters_analysis_graph_without_clarification(monkeypatch) -> None:
    graph_calls = []

    def fake_parse(question, **_kwargs):
        return ParsedQuestionIntent(
            original_question=question,
            normalized_question="查询当前用户总数",
            semantic_metrics=["当前用户总数"],
            confidence=0.35,
            needs_clarification=False,
            source="llm",
        )

    def fake_graph(question, **kwargs):
        graph_calls.append((question, kwargs["parsed_intent"]))
        return _graph_response(question)

    monkeypatch.setattr(agent_service, "parse_question_intent", fake_parse)
    monkeypatch.setattr(agent_service, "run_analysis_graph", fake_graph)
    service = AgentService(conversation_store=InMemoryConversationStore())

    response = service.analyze(type("Payload", (), {"question": "当前用户总数是多少？", "conversation_id": None})())

    assert response.pending_clarification is False
    assert response.sql == "SELECT 1"
    assert len(graph_calls) == 1
    assert graph_calls[0][1].semantic_metrics == ["当前用户总数"]


def test_modification_followup_uses_model_generated_clarification(monkeypatch) -> None:
    pending = PendingClarification(
        original_question="看看最近情况",
        parsed_intent={},
        query_spec=QuerySpec(),
        missing_slots=["metrics"],
        clarification="旧澄清问题",
        created_at=datetime.now(timezone.utc),
    )

    def fake_parse(question, **_kwargs):
        return ParsedQuestionIntent(
            original_question=question,
            normalized_question=question,
            confidence=0.2,
            needs_clarification=True,
            clarification="你希望把问题修改为分析哪个业务指标或对象？",
            source="llm",
        )

    monkeypatch.setattr(followup_resolver, "parse_question_intent", fake_parse)

    resolution = followup_resolver.resolve_followup("我想修改", pending)

    assert resolution.decision == "still_pending"
    assert resolution.pending is not None
    assert resolution.pending.clarification == "你希望把问题修改为分析哪个业务指标或对象？"


def test_conversations_are_scoped_to_authenticated_owner(monkeypatch) -> None:
    monkeypatch.setattr(settings, "intent_parser_enabled", False)
    monkeypatch.setattr(agent_service, "run_analysis_graph", _graph_response)
    service = AgentService(conversation_store=InMemoryConversationStore())
    owner = uuid4()
    other_owner = uuid4()
    response = service.analyze(type("Payload", (), {"question": "销售额是多少", "conversation_id": None})(), app_user_id=owner)

    assert len(service.list_conversations(owner).items) == 1
    assert service.list_conversations(other_owner).items == []
    with pytest.raises(HTTPException) as error:
        service.get_conversation(response.conversation_id, other_owner)
        assert error.value.status_code == 404


def test_failed_analysis_is_saved_to_conversation_history(monkeypatch) -> None:
    def unavailable_response(question, **_kwargs):
        return AnalyzeResponse(
            question=question,
            path="cold_path",
            summary="没有可执行 SQL",
            sql="",
            metrics=[],
            rows=[],
            source={"dataset": "test", "tables": [], "fields": [], "metricDefinition": "test", "range": "", "returnedRows": 0, "queryTime": "0ms", "security": "模型 SQL 失败"},
            trace={"toolCalls": 0, "modelCalls": 0, "memoryCandidates": 0, "totalTime": "0ms"},
            steps=[],
        )

    monkeypatch.setattr(agent_service, "run_analysis_graph", unavailable_response)
    store = InMemoryConversationStore()
    service = AgentService(conversation_store=store)

    with pytest.raises(AnalysisUnavailableError):
        service.analyze(type("Payload", (), {"question": "当前订单总数是多少？", "conversation_id": None})())

    history = service.list_conversations(None)
    assert len(history.items) == 1
    detail = service.get_conversation(history.items[0].id, None)
    assert [message.role for message in detail.messages] == ["user", "assistant"]
    assert detail.messages[-1].response["failure"] is True


def test_explicit_claim_moves_development_history_to_authenticated_owner(monkeypatch) -> None:
    monkeypatch.setattr(agent_service, "run_analysis_graph", _graph_response)
    store = InMemoryConversationStore()
    service = AgentService(conversation_store=store)
    service.analyze(type("Payload", (), {"question": "匿名历史", "conversation_id": None})())
    owner = uuid4()

    assert service.claim_development_conversations(owner) == 1
    assert service.list_conversations(None).items == []
    assert len(service.list_conversations(owner).items) == 1


def test_conversation_list_cursor_is_stable_and_has_no_duplicates(monkeypatch) -> None:
    monkeypatch.setattr(agent_service, "run_analysis_graph", _graph_response)
    store = InMemoryConversationStore()
    service = AgentService(conversation_store=store)

    for question in ("第一个会话", "第二个会话", "第三个会话"):
        service.analyze(type("Payload", (), {"question": question, "conversation_id": None})())

    first_page = service.list_conversations(None, limit=2)
    assert len(first_page.items) == 2
    assert first_page.next_cursor

    second_page = service.list_conversations(None, limit=2, cursor=first_page.next_cursor)
    assert len(second_page.items) == 1
    assert second_page.next_cursor is None
    assert {item.id for item in first_page.items}.isdisjoint({item.id for item in second_page.items})

    with pytest.raises(HTTPException) as error:
        service.list_conversations(None, cursor="not-a-valid-cursor")
    assert error.value.status_code == 422


def test_conversation_message_window_loads_older_messages_without_overlap(monkeypatch) -> None:
    monkeypatch.setattr(agent_service, "run_analysis_graph", _graph_response)
    store = InMemoryConversationStore()
    service = AgentService(conversation_store=store)

    first = service.analyze(type("Payload", (), {"question": "第一轮", "conversation_id": None})())
    for question in ("第二轮", "第三轮"):
        service.analyze(type("Payload", (), {"question": question, "conversation_id": first.conversation_id})())

    latest = service.get_conversation(first.conversation_id, None, limit=3)
    assert len(latest.messages) == 3
    assert latest.has_more is True
    assert latest.next_before == latest.messages[0].id

    older = service.get_conversation(first.conversation_id, None, limit=3, before=latest.next_before)
    assert len(older.messages) == 3
    assert older.has_more is False
    assert {message.id for message in latest.messages}.isdisjoint({message.id for message in older.messages})

    with pytest.raises(HTTPException) as error:
        service.get_conversation(first.conversation_id, None, before=uuid4())
    assert error.value.status_code == 422


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


def test_conversation_api_returns_page_and_message_window_contract(monkeypatch) -> None:
    monkeypatch.setattr(settings, "intent_parser_enabled", False)
    store = InMemoryConversationStore()
    monkeypatch.setattr(routes.agent_service, "conversation_store", store)
    monkeypatch.setattr(conversations.conversation_service, "conversation_store", store)
    client = TestClient(app)

    first = client.post("/api/analyze", json={"question": "看看最近情况"})
    second = client.post("/api/analyze", json={"question": "另一个问题"})
    assert first.status_code == 200
    assert second.status_code == 200

    page = client.get("/api/conversations?limit=1")
    assert page.status_code == 200
    assert len(page.json()["items"]) == 1
    assert page.json()["next_cursor"]

    older_page = client.get(f"/api/conversations?limit=1&cursor={page.json()['next_cursor']}")
    assert older_page.status_code == 200
    assert older_page.json()["items"][0]["id"] != page.json()["items"][0]["id"]

    detail = client.get(f"/api/conversations/{first.json()['conversation_id']}?limit=1")
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 1
    assert detail.json()["has_more"] is True
    assert detail.json()["next_before"]

    older_messages = client.get(
        f"/api/conversations/{first.json()['conversation_id']}?limit=1&before={detail.json()['next_before']}"
    )
    assert older_messages.status_code == 200
    assert older_messages.json()["messages"][0]["id"] != detail.json()["messages"][0]["id"]


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
