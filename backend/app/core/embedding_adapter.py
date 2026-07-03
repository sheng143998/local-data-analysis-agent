from __future__ import annotations

import hashlib
from dataclasses import dataclass
from time import perf_counter, sleep
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field

from backend.app.core.config import settings


class EmbeddingUsage(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingRequest(BaseModel):
    texts: list[str]
    trace_id: str | None = None


class EmbeddingResponse(BaseModel):
    ok: bool
    vectors: list[list[float]] = Field(default_factory=list)
    provider: str
    model: str
    dimension: int
    latency_ms: int
    usage: EmbeddingUsage = Field(default_factory=EmbeddingUsage)
    error_code: str | None = None
    error_message: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingAdapterConfig:
    provider: str = settings.embedding_provider
    base_url: str = settings.embedding_base_url
    model: str = settings.embedding_model
    api_key: str = settings.embedding_api_key
    dimensions: int = settings.embedding_dimensions
    timeout_seconds: float = settings.embedding_timeout_seconds
    max_retries: int = settings.embedding_max_retries


class EmbeddingTransport(Protocol):
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        ...


class HttpxEmbeddingTransport:
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        with httpx.Client(timeout=timeout) as client:
            return client.post(url, headers=headers, json=json)


class EmbeddingAdapter:
    """统一 OpenAI-compatible Embeddings 适配器。"""

    def __init__(
        self,
        config: EmbeddingAdapterConfig | None = None,
        transport: EmbeddingTransport | None = None,
    ) -> None:
        self.config = config or EmbeddingAdapterConfig()
        self.transport = transport or HttpxEmbeddingTransport()

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        started = perf_counter()
        if not request.texts:
            return self._error_response(
                started=started,
                error_code="empty_texts",
                error_message="Embedding 请求 texts 不能为空",
            )
        if any(not text.strip() for text in request.texts):
            return self._error_response(
                started=started,
                error_code="empty_text",
                error_message="Embedding 请求文本不能为空字符串",
            )

        if self.config.provider == "deterministic":
            return self._deterministic_response(started, request.texts)

        payload = self._payload(request)
        headers = self._headers()
        url = self._embeddings_url()
        attempts = max(1, self.config.max_retries + 1)
        last_error: str | None = None

        for attempt in range(attempts):
            try:
                response = self.transport.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout_seconds,
                )
                if response.status_code >= 400:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    if attempt < attempts - 1:
                        sleep(_retry_delay(attempt))
                        continue
                    return self._error_response(
                        started=started,
                        error_code="http_error",
                        error_message=last_error,
                    )
                return self._success_response(started, response.json())
            except Exception as exc:  # noqa: BLE001 - adapter 边界需要结构化所有外部异常
                last_error = str(exc)
                if attempt < attempts - 1:
                    sleep(_retry_delay(attempt))
                    continue

        return self._error_response(
            started=started,
            error_code="transport_error",
            error_message=last_error or "Embedding 请求失败",
        )

    def _payload(self, request: EmbeddingRequest) -> dict[str, Any]:
        return {
            "model": self.config.model,
            "input": request.texts,
            "dimensions": self.config.dimensions,
        }

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key and self.config.api_key != "change_me":
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _embeddings_url(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/embeddings"

    def _success_response(self, started: float, payload: dict[str, Any]) -> EmbeddingResponse:
        vectors = [list(item.get("embedding") or []) for item in payload.get("data", [])]
        usage_payload = payload.get("usage") or {}
        dimension = len(vectors[0]) if vectors else self.config.dimensions
        return EmbeddingResponse(
            ok=True,
            vectors=vectors,
            provider=self.config.provider,
            model=str(payload.get("model") or self.config.model),
            dimension=dimension,
            latency_ms=_latency_ms(started),
            usage=EmbeddingUsage(
                prompt_tokens=int(usage_payload.get("prompt_tokens") or 0),
                total_tokens=int(usage_payload.get("total_tokens") or 0),
            ),
            raw_response=payload,
        )

    def _deterministic_response(self, started: float, texts: list[str]) -> EmbeddingResponse:
        vectors = [_deterministic_vector(text, self.config.dimensions) for text in texts]
        return EmbeddingResponse(
            ok=True,
            vectors=vectors,
            provider=self.config.provider,
            model=self.config.model,
            dimension=self.config.dimensions,
            latency_ms=_latency_ms(started),
            usage=EmbeddingUsage(prompt_tokens=sum(len(text.split()) for text in texts)),
        )

    def _error_response(
        self,
        *,
        started: float,
        error_code: str,
        error_message: str,
    ) -> EmbeddingResponse:
        return EmbeddingResponse(
            ok=False,
            provider=self.config.provider,
            model=self.config.model,
            dimension=self.config.dimensions,
            latency_ms=_latency_ms(started),
            error_code=error_code,
            error_message=error_message,
        )


def _deterministic_vector(text: str, dimensions: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    for index in range(dimensions):
        byte = digest[index % len(digest)]
        values.append(round((byte / 127.5) - 1.0, 6))
    return values


def _latency_ms(started: float) -> int:
    return int((perf_counter() - started) * 1000)


def _retry_delay(attempt: int) -> float:
    return min(0.2 * (attempt + 1), 1.0)
