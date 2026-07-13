from backend.app.services import agent_service
from backend.app.core.config import settings
from backend.app.services.agent_service import AgentService
from backend.app.services.conversation_store import InMemoryConversationStore


def test_general_chat_does_not_call_analysis_graph(monkeypatch) -> None:
    def graph_should_not_run(*_args, **_kwargs):
        raise AssertionError("通用聊天不能进入 SQL Agent")

    monkeypatch.setattr(agent_service, "run_analysis_graph", graph_should_not_run)
    service = AgentService(conversation_store=InMemoryConversationStore())

    response = service.analyze(type("Payload", (), {"question": "你好，介绍一下你能做什么", "conversation_id": None})())

    assert response.sql == ""
    assert response.source.security == "未访问数据库，未生成 SQL"
    assert response.conversation_id is not None


def test_explicit_data_question_enters_existing_analysis_graph(monkeypatch) -> None:
    monkeypatch.setattr(settings, "intent_parser_enabled", False)
    called = []

    def fake_graph(question, **_kwargs):
        called.append(question)
        return agent_service._dialogue_response(question, "数据查询完成").model_copy(update={"sql": "SELECT 1"})

    monkeypatch.setattr(agent_service, "run_analysis_graph", fake_graph)
    service = AgentService(conversation_store=InMemoryConversationStore())

    response = service.analyze(type("Payload", (), {"question": "当前订单数是多少", "conversation_id": None})())

    assert called == ["当前订单数是多少"]
    assert response.sql == "SELECT 1"


def test_result_explanation_uses_saved_summary_without_graph(monkeypatch) -> None:
    monkeypatch.setattr(agent_service, "run_analysis_graph", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不应查询")))
    service = AgentService(conversation_store=InMemoryConversationStore())
    first = service.analyze(type("Payload", (), {"question": "你好", "conversation_id": None})())

    response = service.analyze(type("Payload", (), {"question": "解释刚才的结论", "conversation_id": first.conversation_id})())

    assert response.sql == ""
    assert response.source.dataset == "通用对话"
