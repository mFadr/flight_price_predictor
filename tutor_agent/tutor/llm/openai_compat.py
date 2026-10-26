"""OpenAI-API-compatible cloud adapter (OpenAI, Azure-compatible gateways, OpenRouter, LM Studio, vLLM...)."""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Iterator
from datetime import date
from typing import Any

import httpx

from tutor.llm.base import (
    BudgetExceeded,
    CancelToken,
    ChatMessage,
    GenerationParams,
    LLMError,
    LLMProvider,
    ModelCapabilities,
    ModelNotFound,
    ProviderStatus,
    ProviderUnavailable,
    RateLimited,
)

log = logging.getLogger(__name__)


class RequestBudget:
    """Simple per-day request cap to keep cloud costs bounded."""

    def __init__(self, max_per_day: int):
        self.max_per_day = max_per_day
        self._day = date.today()
        self._count = 0
        self._lock = threading.Lock()
        self.tokens_in = 0
        self.tokens_out = 0

    def consume(self) -> None:
        with self._lock:
            if date.today() != self._day:
                self._day, self._count = date.today(), 0
            if self._count >= self.max_per_day:
                raise BudgetExceeded(
                    "daily budget", f"Daily cloud request limit ({self.max_per_day}) reached. Change it in Settings or use local mode."
                )
            self._count += 1

    @property
    def used_today(self) -> int:
        return self._count


class _RetryWithAdaptedParams(Exception):
    """Internal: the provider rejected a parameter we know how to replace; resend the request."""


# Each adaptation flips at most one flag, so two retries cover every combination.
_MAX_ADAPT_RETRIES = 2


class OpenAICompatibleProvider(LLMProvider):
    is_local = False

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str | None,
        name: str = "OpenAI-compatible",
        timeout_s: float = 90.0,
        structured_output: str = "json_schema",
        max_requests_per_day: int = 200,
        max_output_tokens: int = 1500,
    ):
        super().__init__(model)
        self.name = name
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.timeout_s = timeout_s
        self.structured_output = structured_output
        self.max_output_tokens = max_output_tokens
        self._use_max_completion_tokens = False
        self._omit_sampling = False
        self.budget = RequestBudget(max_requests_per_day)
        # Treat loopback endpoints (LM Studio, vLLM on localhost) as local.
        self.is_local = any(h in self.base_url for h in ("://localhost", "://127.0.0.1"))

    def __repr__(self) -> str:  # never show the key
        return f"OpenAICompatibleProvider(model={self.model!r}, base_url={self.base_url!r})"

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        return h

    def _client(self, timeout: float | None = None) -> httpx.Client:
        return httpx.Client(timeout=httpx.Timeout(timeout or self.timeout_s, connect=10.0), headers=self._headers())

    def _body(self, messages: list[ChatMessage], params: GenerationParams, stream: bool) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
        }
        if not self._omit_sampling:
            body["temperature"] = params.temperature
            body["top_p"] = params.top_p
        limit = min(params.max_tokens, self.max_output_tokens)
        if self._use_max_completion_tokens:
            # Reasoning models count hidden reasoning tokens against this limit, so give them room.
            body["max_completion_tokens"] = max(limit, self.max_output_tokens)
        else:
            body["max_tokens"] = limit
        return body

    def _adapt_to_error(self, detail: str) -> bool:
        """Adjust request shape for newer models (o-series, gpt-5...) that reject legacy parameters."""
        d = detail.lower()
        changed = False
        if "max_completion_tokens" in d and not self._use_max_completion_tokens:
            self._use_max_completion_tokens = changed = True
        if ("temperature" in d or "top_p" in d) and "unsupported" in d and not self._omit_sampling:
            self._omit_sampling = changed = True
        if changed:
            log.info("Adapting request parameters for model %s: %s", self.model, detail)
        return changed

    def _handle_status(self, resp: httpx.Response) -> None:
        if resp.status_code < 400:
            return
        try:
            resp.read()
            detail = resp.json().get("error", {})
            detail = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        except Exception:
            detail = ""
        if resp.status_code == 400 and self._adapt_to_error(detail):
            raise _RetryWithAdaptedParams(detail)
        if resp.status_code == 401:
            raise LLMError("401", "The cloud provider rejected the API key. Update it in Settings → AI Model.")
        if resp.status_code == 404:
            raise ModelNotFound("404", f"Model '{self.model}' was not found at the provider. {detail}")
        if resp.status_code == 429:
            ra = resp.headers.get("retry-after")
            raise RateLimited(detail or "rate limited", float(ra) if ra and ra.isdigit() else None)
        if resp.status_code >= 500:
            raise ProviderUnavailable(f"HTTP {resp.status_code}", "The cloud provider is temporarily unavailable.", True)
        raise LLMError(f"HTTP {resp.status_code}", f"Cloud provider error: {detail or resp.status_code}")

    def _wrap(self, exc: Exception) -> LLMError:
        if isinstance(exc, httpx.ConnectError):
            return ProviderUnavailable(str(exc), "Cannot reach the cloud provider (no internet connection?).", True)
        if isinstance(exc, httpx.TimeoutException):
            return LLMError(str(exc), "The cloud provider timed out.", True)
        return LLMError(str(exc), f"Cloud request failed: {type(exc).__name__}")

    def _stream(self, messages: list[ChatMessage], params: GenerationParams, cancel: CancelToken) -> Iterator[str]:
        if not self._api_key and not self.is_local:
            raise LLMError("no key", "No API key configured for the cloud provider.")
        self.budget.consume()
        for attempt in range(_MAX_ADAPT_RETRIES + 1):
            try:
                yield from self._stream_once(messages, params, cancel)
                return
            except _RetryWithAdaptedParams as exc:
                if attempt == _MAX_ADAPT_RETRIES:
                    raise LLMError("HTTP 400", f"Cloud provider error: {exc}") from exc

    def _stream_once(self, messages: list[ChatMessage], params: GenerationParams, cancel: CancelToken) -> Iterator[str]:
        try:
            with self._client() as client, client.stream(
                "POST", f"{self.base_url}/chat/completions", json=self._body(messages, params, True)
            ) as resp:
                self._handle_status(resp)
                for line in resp.iter_lines():
                    if cancel.cancelled:
                        resp.close()
                        cancel.check()
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    data = json.loads(payload)
                    if data.get("usage"):
                        self.budget.tokens_in += data["usage"].get("prompt_tokens", 0)
                        self.budget.tokens_out += data["usage"].get("completion_tokens", 0)
                    for choice in data.get("choices", []):
                        chunk = (choice.get("delta") or {}).get("content")
                        if chunk:
                            yield chunk
        except LLMError:
            raise
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            raise self._wrap(exc) from exc

    def _complete_json(
        self, messages: list[ChatMessage], schema: dict[str, Any], params: GenerationParams, cancel: CancelToken
    ) -> str:
        if not self._api_key and not self.is_local:
            raise LLMError("no key", "No API key configured for the cloud provider.")
        self.budget.consume()
        for attempt in range(_MAX_ADAPT_RETRIES + 1):
            body = self._body(messages, params, False)
            if self.structured_output == "json_schema":
                body["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {"name": "response", "schema": schema, "strict": False},
                }
            elif self.structured_output == "json_object":
                body["response_format"] = {"type": "json_object"}
            try:
                with self._client() as client:
                    resp = client.post(f"{self.base_url}/chat/completions", json=body)
                    self._handle_status(resp)
                    data = resp.json()
                break
            except _RetryWithAdaptedParams as exc:
                if attempt == _MAX_ADAPT_RETRIES:
                    raise LLMError("HTTP 400", f"Cloud provider error: {exc}") from exc
            except LLMError:
                raise
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                raise self._wrap(exc) from exc
        cancel.check()
        usage = data.get("usage") or {}
        self.budget.tokens_in += usage.get("prompt_tokens", 0)
        self.budget.tokens_out += usage.get("completion_tokens", 0)
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("bad response", "The cloud provider returned an unexpected response.") from exc

    def list_models(self) -> list[str]:
        try:
            with self._client(timeout=10) as client:
                resp = client.get(f"{self.base_url}/models")
                if resp.status_code == 200:
                    return sorted(m.get("id", "") for m in resp.json().get("data", []))
        except httpx.HTTPError:
            pass
        return []

    def check_status(self) -> ProviderStatus:
        if not self._api_key and not self.is_local:
            return ProviderStatus(
                ok=False, provider=self.name, model=self.model, is_local=False,
                message="No API key configured.", troubleshooting=["Enter your API key in Settings → AI Model → Cloud."],
            )
        try:
            with self._client(timeout=15) as client:
                resp = client.get(f"{self.base_url}/models")
        except httpx.HTTPError as exc:
            err = self._wrap(exc)
            return ProviderStatus(ok=False, provider=self.name, model=self.model, is_local=self.is_local, message=err.user_message)
        if resp.status_code == 401:
            return ProviderStatus(ok=False, provider=self.name, model=self.model, is_local=self.is_local, message="API key rejected (401).")
        models: list[str] = []
        if resp.status_code == 200:
            try:
                models = sorted(m.get("id", "") for m in resp.json().get("data", []))
            except Exception:
                models = []
        if models and self.model not in models:
            return ProviderStatus(
                ok=False, provider=self.name, model=self.model, is_local=self.is_local,
                message=f"Connected, but model '{self.model}' is not offered by this endpoint.", available_models=models,
            )
        caps = ModelCapabilities(
            model=self.model, available=True,
            supports_structured_output=self.structured_output != "prompt",
            notes=[f"structured output mode: {self.structured_output}"],
        )
        where = "on this computer" if self.is_local else "content is sent to the provider over the internet"
        return ProviderStatus(
            ok=True, provider=self.name, model=self.model, is_local=self.is_local,
            message=f"Ready ({where}). Requests today: {self.budget.used_today}/{self.budget.max_per_day}",
            capabilities=caps, available_models=models,
        )
