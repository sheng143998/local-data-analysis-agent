from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter, sleep
from typing import Any, Literal, Protocol

import httpx
from pydantic import BaseModel, Field

from backend.app.core.config import settings


ModelRole = Literal["system", "user", "assistant"]


class ModelMessage(BaseModel):
    role: ModelRole
    content: str


class ModelUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float | None = None


class ModelRequest(BaseModel):
    messages: list[ModelMessage]
    temperature: float = 0
    max_tokens: int = 1024
    response_format: dict[str, Any] | None = None
    trace_id: str | None = None


class ModelResponse(BaseModel):
    ok: bool
    content: str = ""
    provider: str
    model: str
    latency_ms: int
    usage: ModelUsage = Field(default_factory=ModelUsage)
    error_code: str | None = None
    error_message: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class ModelAdapterConfig:
    provider: str = settings.model_provider
    base_url: str = settings.model_base_url
    model: str = settings.model_name
    api_key: str = settings.model_api_key
    timeout_seconds: float = settings.model_timeout_seconds
    max_retries: int = settings.model_max_retries


class ChatTransport(Protocol):
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        ...


class HttpxChatTransport:
    def __init__(self, *, trust_env: bool = True) -> None:
        self.trust_env = trust_env

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        with httpx.Client(timeout=timeout, trust_env=self.trust_env) as client:
            return client.post(url, headers=headers, json=json)


class ModelAdapter:
    """统一 OpenAI-compatible Chat Completions 适配器。"""

    def __init__(
        self,
        config: ModelAdapterConfig | None = None,
        transport: ChatTransport | None = None,
    ) -> None:
        self.config = config or ModelAdapterConfig()
        self.transport = transport or HttpxChatTransport(
            trust_env=self.config.provider not in {"local", "ollama"}
        )

    def chat(self, request: ModelRequest) -> ModelResponse:
        started = perf_counter()
        if not request.messages:
            return self._error_response(
                started=started,
                error_code="empty_messages",
                error_message="模型请求 messages 不能为空",
            )

        payload = self._payload(request)
        headers = self._headers()
        url = self._chat_url()
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
            error_message=last_error or "模型请求失败",
        )

    def _payload(self, request: ModelRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.response_format:
            payload["response_format"] = request.response_format
        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key and self.config.api_key != "change_me":
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _chat_url(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/chat/completions"

    def _success_response(self, started: float, payload: dict[str, Any]) -> ModelResponse:
        choice = (payload.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        usage_payload = payload.get("usage") or {}
        return ModelResponse(
            ok=True,
            content=str(message.get("content") or ""),
            provider=self.config.provider,
            model=str(payload.get("model") or self.config.model),
            latency_ms=_latency_ms(started),
            usage=ModelUsage(
                prompt_tokens=int(usage_payload.get("prompt_tokens") or 0),
                completion_tokens=int(usage_payload.get("completion_tokens") or 0),
                total_tokens=int(usage_payload.get("total_tokens") or 0),
            ),
            raw_response=payload,
        )

    def _error_response(
        self,
        *,
        started: float,
        error_code: str,
        error_message: str,
    ) -> ModelResponse:
        return ModelResponse(
            ok=False,
            provider=self.config.provider,
            model=self.config.model,
            latency_ms=_latency_ms(started),
            error_code=error_code,
            error_message=error_message,
        )


def _latency_ms(started: float) -> int:
    return int((perf_counter() - started) * 1000)


def _retry_delay(attempt: int) -> float:
    return min(0.2 * (attempt + 1), 1.0)
