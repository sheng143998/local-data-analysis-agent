from backend.app.services import agent_service
from backend.app.core.config import settings
from backend.app.schemas.conversation import ConversationState
from backend.app.services.agent_service import AgentService
from backend.app.services.conversation_store import InMemoryConversationStore
from backend.app.tools.dialogue_router import route_dialogue
from backend.app.core.model_adapter import ModelResponse
from datetime import datetime, timezone
from uuid import uuid4


def test_general_chat_does_not_call_analysis_graph(monkeypatch) -> None:
    def graph_should_not_run(*_args, **_kwargs):
        raise AssertionError("通用聊天不能进入 SQL Agent")

    monkeypatch.setattr(agent_service, "run_analysis_graph", graph_should_not_run)
    service = AgentService(conversation_store=InMemoryConversationStore())

    monkeypatch.setattr(settings, "router_model_enabled", False)
    response = service.analyze(type("Payload", (), {"question": "你好，介绍一下你能做什么", "conversation_id": None})())

    assert response.sql == ""
    assert response.source.security == "未访问数据库，未生成 SQL"
    assert response.conversation_id is not None


def test_ambiguous_business_overview_enters_analysis_for_clarification() -> None:
    state = ConversationState(id=uuid4(), title="测试", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))

    decision = route_dialogue("看看最近情况", state, model_enabled=False)

    assert decision.role == "data_analysis"


def test_explicit_data_question_enters_existing_analysis_graph(monkeypatch) -> None:
    monkeypatch.setattr(settings, "intent_parser_enabled", False)
    monkeypatch.setattr(settings, "router_model_enabled", False)
    called = []

    def fake_graph(question, **_kwargs):
        called.append(question)
        return agent_service._dialogue_response(question, "数据查询完成").model_copy(update={"sql": "SELECT 1"})

    monkeypatch.setattr(agent_service, "run_analysis_graph", fake_graph)
    service = AgentService(conversation_store=InMemoryConversationStore())

    response = service.analyze(type("Payload", (), {"question": "当前订单数是多少", "conversation_id": None})())

    assert called == ["当前订单数是多少"]
    assert response.sql == "SELECT 1"


def test_explicit_data_question_bypasses_router_model() -> None:
    state = ConversationState(id=uuid4(), title="测试", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    adapter = FakeRouterAdapter('{"role":"general_chat","confidence":0.99,"reason":"不应调用"}')

    decision = route_dialogue("2017 年已支付订单数是多少？", state, adapter=adapter)

    assert decision.role == "data_analysis"
    assert decision.source == "deterministic"
    assert adapter.requests == []


def test_result_explanation_uses_saved_summary_without_graph(monkeypatch) -> None:
    monkeypatch.setattr(settings, "router_model_enabled", False)
    monkeypatch.setattr(agent_service, "run_analysis_graph", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不应查询")))
    service = AgentService(conversation_store=InMemoryConversationStore())
    first = service.analyze(type("Payload", (), {"question": "你好", "conversation_id": None})())

    response = service.analyze(type("Payload", (), {"question": "解释刚才的结论", "conversation_id": first.conversation_id})())

    assert response.sql == ""
    assert response.source.dataset == "通用对话"


class FakeRouterAdapter:
    def __init__(self, content: str) -> None:
        self.content = content
        self.requests = []

    def chat(self, request):
        self.requests.append(request)
        return ModelResponse(ok=True, content=self.content, provider="test", model="router", latency_ms=1)


def test_semantic_router_keeps_product_user_experience_in_general_chat() -> None:
    state = ConversationState(id=uuid4(), title="测试", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    decision = route_dialogue(
        "如何提升用户体验？",
        state,
        adapter=FakeRouterAdapter('{"role":"general_chat","confidence":0.96,"reason":"产品建议"}'),
    )

    assert decision.role == "general_chat"
    assert decision.source == "model"


def test_semantic_router_requires_data_evidence_before_database_analysis() -> None:
    state = ConversationState(id=uuid4(), title="测试", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    decision = route_dialogue(
        "用户体验有什么常见问题？",
        state,
        adapter=FakeRouterAdapter('{"role":"data_analysis","confidence":0.98,"reason":"包含用户"}'),
    )

    assert decision.role == "general_chat"
    assert decision.source == "fallback"


def test_semantic_router_allows_model_confirmed_view_request_for_data_object() -> None:
    state = ConversationState(id=uuid4(), title="测试", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    decision = route_dialogue(
        "帮我看一下退款情况",
        state,
        adapter=FakeRouterAdapter('{"role":"data_analysis","confidence":0.91,"reason":"请求业务数据"}'),
    )

    assert decision.role == "data_analysis"
    assert decision.source == "model"


def test_router_model_failure_only_allows_explicit_data_request() -> None:
    state = ConversationState(id=uuid4(), title="测试", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))

    assert route_dialogue("当前订单数是多少？", state, model_enabled=False).role == "data_analysis"
    assert route_dialogue("帮我看一下退款情况", state, model_enabled=False).role == "data_analysis"
    assert route_dialogue("用户体验如何优化？", state, model_enabled=False).role == "general_chat"
