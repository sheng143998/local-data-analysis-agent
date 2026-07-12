from uuid import uuid4

from backend.app.core.security import hash_password
from backend.app.db.repositories.auth_repository import AuthRepository
from backend.app.services.long_term_memory_service import LongTermMemoryService
from backend.app.services.agent_service import AgentService
from backend.app.services.conversation_store import InMemoryConversationStore


def test_explicit_preferences_are_versioned_and_can_be_forgotten() -> None:
    user = AuthRepository().create_user(
        email=f"memory-{uuid4().hex}@example.com",
        display_name="Memory Test",
        password_hash=hash_password("correct horse battery staple"),
    )
    service = LongTermMemoryService()

    assert service.handle_explicit_preference(user.id, "记住以后默认用人民币")
    first = service.list_memories(user.id)
    assert len(first) == 1
    assert first[0].memory_key == "currency"
    assert first[0].value["value"] == "CNY"

    assert service.handle_explicit_preference(user.id, "记住以后默认用美元")
    second = service.list_memories(user.id)
    assert len(second) == 1
    assert second[0].value["value"] == "USD"
    assert second[0].version == 2
    assert "currency=USD" in service.context_for(user.id, "销售额")

    assert service.handle_explicit_preference(user.id, "忘记货币偏好")
    assert service.list_memories(user.id) == []


def test_explicit_preference_command_does_not_execute_analysis_graph() -> None:
    user = AuthRepository().create_user(
        email=f"memory-command-{uuid4().hex}@example.com",
        display_name="Memory Command Test",
        password_hash=hash_password("correct horse battery staple"),
    )
    service = AgentService(conversation_store=InMemoryConversationStore())
    response = service.analyze(type("Payload", (), {"question": "记住以后默认按月汇总", "conversation_id": None})(), app_user_id=user.id)

    assert response.sql == ""
    assert response.source.security == "未生成 SQL，已更新用户偏好"
    assert LongTermMemoryService().list_memories(user.id)[0].memory_key == "default_granularity"
