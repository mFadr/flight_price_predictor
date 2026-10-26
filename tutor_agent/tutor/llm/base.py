"""Provider-independent LLM interface.

The tutoring engine only talks to :class:`LLMProvider`; concrete adapters live
in sibling modules. New providers implement ``_stream`` and ``_complete_json``.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel


class LLMError(Exception):
    """Base error; ``user_message`` is safe to show in the UI."""

    def __init__(self, message: str, user_message: str | None = None, retryable: bool = False):
        super().__init__(message)
        self.user_message = user_message or message
        self.retryable = retryable


class ProviderUnavailable(LLMError):
    pass


class ModelNotFound(LLMError):
    pass


class RateLimited(LLMError):
    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message, "The cloud provider is rate-limiting requests. Please wait a moment.", True)
        self.retry_after = retry_after


class BudgetExceeded(LLMError):
    pass


class Cancelled(LLMError):
    def __init__(self) -> None:
        super().__init__("cancelled", "Request cancelled.")


class StructuredOutputError(LLMError):
    pass


class CancelToken:
    """Thread-safe cancellation flag passed down to providers."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def check(self) -> None:
        if self._event.is_set():
            raise Cancelled()


@dataclass
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class GenerationParams:
    temperature: float = 0.4
    top_p: float = 0.9
    max_tokens: int = 900
    num_ctx: int | None = None
    stop: list[str] = field(default_factory=list)


@dataclass
class ModelCapabilities:
    model: str
    available: bool
    context_length: int | None = None
    supports_tools: bool | None = None
    supports_structured_output: bool | None = None
    supports_streaming: bool = True
    notes: list[str] = field(default_factory=list)


@dataclass
class ProviderStatus:
    ok: bool
    provider: str
    model: str
    is_local: bool
    message: str
    capabilities: ModelCapabilities | None = None
    available_models: list[str] = field(default_factory=list)
    troubleshooting: list[str] = field(default_factory=list)


class LLMProvider(ABC):
    name: str = "provider"
    is_local: bool = True

    def __init__(self, model: str):
        self.model = model

    # --------------------------------------------------------- public API
    def stream_chat(
        self, messages: list[ChatMessage], params: GenerationParams, cancel: CancelToken | None = None
    ) -> Iterator[str]:
        cancel = cancel or CancelToken()
        for chunk in self._stream(messages, params, cancel):
            cancel.check()
            yield chunk

    def chat(self, messages: list[ChatMessage], params: GenerationParams, cancel: CancelToken | None = None) -> str:
        return "".join(self.stream_chat(messages, params, cancel))

    def complete_json(
        self,
        messages: list[ChatMessage],
        schema: dict[str, Any],
        params: GenerationParams,
        cancel: CancelToken | None = None,
    ) -> str:
        """Return raw text that should contain a JSON object matching ``schema``."""
        cancel = cancel or CancelToken()
        cancel.check()
        out = self._complete_json(messages, schema, params, cancel)
        cancel.check()
        return out

    # --------------------------------------------------------- adapter hooks
    @abstractmethod
    def _stream(self, messages: list[ChatMessage], params: GenerationParams, cancel: CancelToken) -> Iterator[str]:
        ...

    @abstractmethod
    def _complete_json(
        self, messages: list[ChatMessage], schema: dict[str, Any], params: GenerationParams, cancel: CancelToken
    ) -> str:
        ...

    @abstractmethod
    def check_status(self) -> ProviderStatus:
        ...

    def list_models(self) -> list[str]:
        return [self.model]

    def describe(self) -> str:
        where = "local" if self.is_local else "cloud"
        return f"{self.name} · {self.model} ({where})"


def schema_for(model: type[BaseModel]) -> dict[str, Any]:
    return model.model_json_schema()
