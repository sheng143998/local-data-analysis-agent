from typing import Any

import httpx

from backend.app.core.model_adapter import (
    ModelAdapter,
    ModelAdapterConfig,
    ModelMessage,
    ModelRequest,
)


class FakeTransport:
    def __init__(self, responses: list[httpx.Response] | None = None, error: Exception | None = None):
        self.responses = responses or []
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        self.calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        if self.error:
            raise self.error
        return self.responses.pop(0)


def test_model_adapter_sends_openai_compatible_chat_payload() -> None:
    transport = FakeTransport(
        responses=[
            httpx.Response(
                200,
                json={
                    "model": "qwen-local",
                    "choices": [{"message": {"content": "SELECT 1"}}],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 2,
                        "total_tokens": 12,
                    },
                },
            )
        ]
    )
    adapter = ModelAdapter(
        config=ModelAdapterConfig(
            provider="local",
            base_url="http://localhost:8001/v1",
            model="qwen-local",
            api_key="change_me",
            timeout_seconds=5,
            max_retries=0,
        ),
        transport=transport,
    )

    response = adapter.chat(
        ModelRequest(messages=[ModelMessage(role="user", content="生成 SQL")], max_tokens=128)
    )

    assert response.ok is True
    assert response.content == "SELECT 1"
    assert response.provider == "local"
    assert response.model == "qwen-local"
    assert response.usage.total_tokens == 12
    assert transport.calls[0]["url"] == "http://localhost:8001/v1/chat/completions"
    assert transport.calls[0]["json"]["messages"] == [{"role": "user", "content": "生成 SQL"}]
    assert "Authorization" not in transport.calls[0]["headers"]


def test_model_adapter_adds_authorization_for_real_api_key() -> None:
    transport = FakeTransport(
        responses=[httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})]
    )
    adapter = ModelAdapter(
        config=ModelAdapterConfig(
            provider="openai-compatible",
            base_url="https://example.test/v1",
            model="test-model",
            api_key="real-key",
            timeout_seconds=5,
            max_retries=0,
        ),
        transport=transport,
    )

    adapter.chat(ModelRequest(messages=[ModelMessage(role="user", content="ping")]))

    assert transport.calls[0]["headers"]["Authorization"] == "Bearer real-key"


def test_model_adapter_returns_structured_error_for_empty_messages() -> None:
    adapter = ModelAdapter(
        config=ModelAdapterConfig(model="test-model"),
        transport=FakeTransport(),
    )

    response = adapter.chat(ModelRequest(messages=[]))

    assert response.ok is False
    assert response.error_code == "empty_messages"
    assert "不能为空" in (response.error_message or "")


def test_model_adapter_retries_http_errors_then_succeeds() -> None:
    transport = FakeTransport(
        responses=[
            httpx.Response(429, text="rate limited"),
            httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}),
        ]
    )
    adapter = ModelAdapter(
        config=ModelAdapterConfig(
            base_url="http://localhost:8001/v1",
            model="test-model",
            timeout_seconds=5,
            max_retries=1,
        ),
        transport=transport,
    )

    response = adapter.chat(ModelRequest(messages=[ModelMessage(role="user", content="ping")]))

    assert response.ok is True
    assert response.content == "ok"
    assert len(transport.calls) == 2


def test_model_adapter_returns_structured_transport_error() -> None:
    adapter = ModelAdapter(
        config=ModelAdapterConfig(model="test-model", max_retries=0),
        transport=FakeTransport(error=TimeoutError("timeout")),
    )

    response = adapter.chat(ModelRequest(messages=[ModelMessage(role="user", content="ping")]))

    assert response.ok is False
    assert response.error_code == "transport_error"
    assert "timeout" in (response.error_message or "")
