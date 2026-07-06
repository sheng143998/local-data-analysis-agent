from backend.app.core.model_adapter import ModelResponse
from backend.app.tools.question_intent_parser import parse_question_intent


class FakeAdapter:
    def __init__(self, response: ModelResponse):
        self.response = response
        self.calls = 0

    def chat(self, request):
        self.calls += 1
        return self.response


def test_parse_question_intent_maps_colloquial_metrics_from_llm() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content=(
                '{"normalized_question":"查询总销售额和客单价",'
                '"metrics":["sales_amount","avg_order_value"],'
                '"dimensions":[],"filters":[],"time_range":"",'
                '"confidence":0.88,"needs_clarification":false}'
            ),
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    intent = parse_question_intent(
        "现在卖了多少钱，平均每单大概多少？",
        adapter=adapter,
        model_enabled=True,
    )

    assert intent.needs_clarification is False
    assert intent.metrics == ["avg_order_value", "sales_amount"]
    assert "销售额" in intent.normalized_question
    assert "客单价" in intent.normalized_question
    assert adapter.calls == 1


def test_parse_question_intent_asks_for_clarification_when_uncertain() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content=(
                '{"normalized_question":"查看最近业务情况",'
                '"metrics":[],"dimensions":[],"filters":[],"time_range":"",'
                '"confidence":0.3,"needs_clarification":true,'
                '"clarification":"我理解你想查看最近的核心经营概览。是否查询销售额、订单数和客单价，还是需要修改？"}'
            ),
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    intent = parse_question_intent("看看最近情况", adapter=adapter, model_enabled=True)

    assert intent.needs_clarification is True
    assert "是否查询" in intent.clarification


def test_parse_question_intent_keeps_dimensions_from_intent_model() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content=(
                '{"normalized_question":"查询2017年总销售额和平均每单金额",'
                '"metrics":["sales_amount","avg_order_value"],'
                '"dimensions":["date"],"filters":[],"time_range":"2017年",'
                '"confidence":0.83,"needs_clarification":false}'
            ),
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    intent = parse_question_intent(
        "2017年卖了多少钱，平均每单大概多少",
        adapter=adapter,
        model_enabled=True,
    )

    assert intent.needs_clarification is False
    assert intent.time_range == "2017年"
    assert "date" in intent.dimensions


def test_parse_question_intent_heuristic_fallback_when_model_fails() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=False,
            provider="local",
            model="test",
            latency_ms=1,
            error_message="timeout",
        )
    )

    intent = parse_question_intent(
        "卖了多少钱，平均每单是多少？",
        adapter=adapter,
        model_enabled=True,
    )

    assert intent.needs_clarification is False
    assert intent.metrics == ["avg_order_value", "sales_amount"]
    assert "timeout" in intent.warnings
