from typing import Any

import httpx

from backend.app.core.embedding_adapter import (
    EmbeddingAdapter,
    EmbeddingAdapterConfig,
    EmbeddingRequest,
)


class FakeEmbeddingTransport:
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


def test_embedding_adapter_sends_openai_compatible_payload() -> None:
    transport = FakeEmbeddingTransport(
        responses=[
            httpx.Response(
                200,
                json={
                    "model": "text-embedding-v4",
                    "data": [{"embedding": [0.1, 0.2, 0.3]}],
                    "usage": {"prompt_tokens": 8, "total_tokens": 8},
                },
            )
        ]
    )
    adapter = EmbeddingAdapter(
        config=EmbeddingAdapterConfig(
            provider="openai-compatible",
            base_url="http://localhost:8001/v1",
            model="text-embedding-v4",
            api_key="change_me",
            dimensions=3,
            timeout_seconds=5,
            max_retries=0,
        ),
        transport=transport,
    )

    response = adapter.embed(EmbeddingRequest(texts=["orders total_amount"]))

    assert response.ok is True
    assert response.vectors == [[0.1, 0.2, 0.3]]
    assert response.dimension == 3
    assert response.usage.total_tokens == 8
    assert transport.calls[0]["url"] == "http://localhost:8001/v1/embeddings"
    assert transport.calls[0]["json"] == {
        "model": "text-embedding-v4",
        "input": ["orders total_amount"],
        "dimensions": 3,
    }
    assert "Authorization" not in transport.calls[0]["headers"]


def test_embedding_adapter_adds_authorization_for_real_api_key() -> None:
    transport = FakeEmbeddingTransport(
        responses=[httpx.Response(200, json={"data": [{"embedding": [0.1]}]})]
    )
    adapter = EmbeddingAdapter(
        config=EmbeddingAdapterConfig(
            provider="openai-compatible",
            base_url="https://example.test/v1",
            model="embedding-model",
            api_key="real-key",
            dimensions=1,
            timeout_seconds=5,
            max_retries=0,
        ),
        transport=transport,
    )

    adapter.embed(EmbeddingRequest(texts=["schema document"]))

    assert transport.calls[0]["headers"]["Authorization"] == "Bearer real-key"


def test_embedding_adapter_returns_structured_error_for_empty_texts() -> None:
    adapter = EmbeddingAdapter(
        config=EmbeddingAdapterConfig(provider="deterministic", dimensions=4),
        transport=FakeEmbeddingTransport(),
    )

    response = adapter.embed(EmbeddingRequest(texts=[]))

    assert response.ok is False
    assert response.error_code == "empty_texts"
    assert "不能为空" in (response.error_message or "")


def test_embedding_adapter_returns_structured_error_for_blank_text() -> None:
    adapter = EmbeddingAdapter(
        config=EmbeddingAdapterConfig(provider="deterministic", dimensions=4),
        transport=FakeEmbeddingTransport(),
    )

    response = adapter.embed(EmbeddingRequest(texts=[" "]))

    assert response.ok is False
    assert response.error_code == "empty_text"


def test_embedding_adapter_deterministic_provider_returns_stable_vectors() -> None:
    adapter = EmbeddingAdapter(
        config=EmbeddingAdapterConfig(provider="deterministic", model="local", dimensions=6),
        transport=FakeEmbeddingTransport(),
    )

    first = adapter.embed(EmbeddingRequest(texts=["orders total_amount"]))
    second = adapter.embed(EmbeddingRequest(texts=["orders total_amount"]))

    assert first.ok is True
    assert first.vectors == second.vectors
    assert first.dimension == 6
    assert len(first.vectors[0]) == 6


def test_embedding_adapter_retries_http_errors_then_succeeds() -> None:
    transport = FakeEmbeddingTransport(
        responses=[
            httpx.Response(503, text="busy"),
            httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2]}]}),
        ]
    )
    adapter = EmbeddingAdapter(
        config=EmbeddingAdapterConfig(
            provider="openai-compatible",
            base_url="http://localhost:8001/v1",
            model="embedding-model",
            dimensions=2,
            timeout_seconds=5,
            max_retries=1,
        ),
        transport=transport,
    )

    response = adapter.embed(EmbeddingRequest(texts=["schema document"]))

    assert response.ok is True
    assert len(transport.calls) == 2


def test_embedding_adapter_returns_structured_transport_error() -> None:
    adapter = EmbeddingAdapter(
        config=EmbeddingAdapterConfig(
            provider="openai-compatible",
            model="embedding-model",
            max_retries=0,
        ),
        transport=FakeEmbeddingTransport(error=TimeoutError("timeout")),
    )

    response = adapter.embed(EmbeddingRequest(texts=["schema document"]))

    assert response.ok is False
    assert response.error_code == "transport_error"
    assert "timeout" in (response.error_message or "")
