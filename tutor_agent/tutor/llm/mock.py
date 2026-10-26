"""Scripted provider for tests and offline demos (no model required)."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Any

from tutor.llm.base import CancelToken, ChatMessage, GenerationParams, LLMError, LLMProvider, ProviderStatus

Responder = Callable[[list[ChatMessage], dict[str, Any] | None], str]


class MockProvider(LLMProvider):
    """Returns queued responses, or the result of a responder callback.

    ``fail_with`` makes every call raise the given error (to test fallback).
    ``calls`` records (messages, schema) for assertions.
    """

    name = "Mock"

    def __init__(
        self,
        responses: list[str | dict] | None = None,
        responder: Responder | None = None,
        is_local: bool = True,
        fail_with: LLMError | None = None,
        model: str = "mock-model",
    ):
        super().__init__(model)
        self.responses = list(responses or [])
        self.responder = responder
        self.is_local = is_local
        self.fail_with = fail_with
        self.calls: list[tuple[list[ChatMessage], dict[str, Any] | None]] = []

    def _next(self, messages: list[ChatMessage], schema: dict[str, Any] | None) -> str:
        self.calls.append((messages, schema))
        if self.fail_with:
            raise self.fail_with
        if self.responder:
            return self.responder(messages, schema)
        if not self.responses:
            return "OK."
        r = self.responses.pop(0)
        return json.dumps(r) if isinstance(r, dict) else r

    def _stream(self, messages: list[ChatMessage], params: GenerationParams, cancel: CancelToken) -> Iterator[str]:
        text = self._next(messages, None)
        for i in range(0, len(text), 12):
            cancel.check()
            yield text[i : i + 12]

    def _complete_json(self, messages, schema, params, cancel) -> str:
        return self._next(messages, schema)

    def check_status(self) -> ProviderStatus:
        return ProviderStatus(ok=True, provider=self.name, model=self.model, is_local=self.is_local, message="Mock ready")
