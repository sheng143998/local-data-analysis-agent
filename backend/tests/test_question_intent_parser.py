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


def test_parse_question_intent_normalizes_natural_language_model_candidates() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content=(
                '{"normalized_question":"查询已支付订单总量",'
                '"metrics":[],"metric_candidates":["已支付订单"],'
                '"dimensions":[],"filters":[],"time_range":"",'
                '"confidence":0.9,"needs_clarification":false}'
            ),
            provider="cloud",
            model="fine-tuned-intent-model",
            latency_ms=1,
        )
    )

    intent = parse_question_intent("当前订单总数是多少？", adapter=adapter, model_enabled=True)

    assert intent.needs_clarification is False
    assert intent.metrics == ["order_count"]
    assert intent.query_spec.required_tables == ["orders", "payments"]


def test_parse_question_intent_heuristic_fallback_recognizes_order_total() -> None:
    intent = parse_question_intent("当前订单总数是多少？", model_enabled=False)

    assert intent.needs_clarification is False
    assert intent.metrics == ["order_count"]


def test_parse_question_intent_clarifies_unknown_model_metric_candidate() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content=(
                '{"normalized_question":"查询物流及时率",'
                '"metrics":[],"metric_candidates":["物流及时率"],'
                '"dimensions":[],"filters":[],"time_range":"",'
                '"confidence":0.91,"needs_clarification":false}'
            ),
            provider="cloud",
            model="fine-tuned-intent-model",
            latency_ms=1,
        )
    )

    intent = parse_question_intent("物流及时率是多少？", adapter=adapter, model_enabled=True)

    assert intent.needs_clarification is True
    assert "尚未定义" in intent.clarification
    assert "未映射的指标候选：物流及时率" in intent.warnings


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


def test_parse_question_intent_heuristic_fallback_maps_average_sold_phrase() -> None:
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
        "2017年卖了多少钱，平均卖了多少钱",
        adapter=adapter,
        model_enabled=True,
    )

    assert intent.needs_clarification is False
    assert intent.metrics == ["avg_order_value", "sales_amount"]
    assert intent.time_range == "2017年"
    assert intent.query_spec.time_start == "2017-01-01"
    assert intent.query_spec.time_end == "2018-01-01"


def test_parse_question_intent_recognizes_user_funnel_and_coupon_metrics() -> None:
    cases = [
        ("过去 6 个月每月新增用户数是多少？", "new_user_count", "users"),
        ("最近 30 天访问到下单转化率是多少？", "visit_to_order_conversion_rate", "traffic_events"),
        ("哪些优惠券核销率最高？", "coupon_redemption_rate", "coupon_usages"),
    ]

    for question, metric, required_table in cases:
        intent = parse_question_intent(question, model_enabled=False)

        assert intent.needs_clarification is False
        assert metric in intent.metrics
        assert required_table in intent.query_spec.required_tables
