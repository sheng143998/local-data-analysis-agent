from dataclasses import dataclass

from backend.app.core.config import settings


@dataclass(frozen=True)
class ModelRoute:
    role: str
    provider: str
    model: str
    base_url: str


def route_model(role: str) -> ModelRoute:
    """集中模型角色路由，避免业务节点各自读取配置造成不可审计漂移。"""
    if role in {"intent", "clarification"}:
        return ModelRoute(role, settings.intent_model_provider, settings.intent_model_name, settings.intent_model_base_url)
    if role in {"sql_generation", "sql_repair"}:
        return ModelRoute(role, settings.model_provider, settings.model_name, settings.model_base_url)
    return ModelRoute(role, settings.model_provider, settings.model_name, settings.model_base_url)
