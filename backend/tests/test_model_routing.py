from backend.app.core.model_routing import route_model


def test_model_routing_uses_dedicated_intent_configuration() -> None:
    route = route_model("intent")
    assert route.role == "intent"
    assert route.provider
    assert route.model


def test_model_routing_uses_sql_model_for_generation() -> None:
    route = route_model("sql_generation")
    assert route.role == "sql_generation"
    assert route.provider
    assert route.model
