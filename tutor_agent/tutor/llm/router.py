"""Chooses which provider serves a request and applies explicit, announced fallbacks.

Invariants (tested):
* In LOCAL mode the cloud provider is never used, whatever the fallback config says.
* The cloud is only used when enabled AND the user has acknowledged data transmission.
* Every fallback is announced through ``notify`` - nothing switches silently.
* Cancellation never triggers a fallback.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from typing import TypeVar

from tutor.config import AppConfig, OperatingMode
from tutor.llm.base import (
    BudgetExceeded,
    Cancelled,
    CancelToken,
    ChatMessage,
    GenerationParams,
    LLMError,
    LLMProvider,
    ModelNotFound,
    ProviderUnavailable,
    RateLimited,
)

log = logging.getLogger(__name__)
T = TypeVar("T")


class Task:
    EXPLAIN = "explain"        # conversational tutoring / explanations
    EXERCISE = "exercise"      # exercise generation
    EVALUATE = "evaluate"      # answer evaluation / diagnosis
    SUMMARY = "summary"        # session summaries, context compression

    ALL = (EXPLAIN, EXERCISE, EVALUATE, SUMMARY)


_FALLBACK_ERRORS = (ProviderUnavailable, RateLimited, BudgetExceeded, ModelNotFound)


class ProviderRouter:
    def __init__(
        self,
        cfg: AppConfig,
        local: LLMProvider | None,
        cloud: LLMProvider | None,
        notify: Callable[[str], None] | None = None,
    ):
        self.cfg = cfg
        self.local = local
        self.cloud = cloud
        self.notify = notify or (lambda msg: None)

    # ------------------------------------------------------------ selection
    @property
    def cloud_usable(self) -> bool:
        return self.cloud is not None and self.cfg.cloud_allowed

    def chain(self, task: str) -> list[LLMProvider]:
        """Ordered providers to try for ``task``."""
        mode = self.cfg.mode
        out: list[LLMProvider] = []
        if mode == OperatingMode.LOCAL:
            if self.local:
                out.append(self.local)
            return out
        if mode == OperatingMode.CLOUD:
            if self.cloud_usable:
                out.append(self.cloud)  # type: ignore[arg-type]
            if self.local and self.cfg.fallback.fallback_to_local:
                out.append(self.local)
            return out
        # HYBRID
        wants_cloud = task in self.cfg.hybrid.cloud_tasks and self.cloud_usable
        if wants_cloud:
            out.append(self.cloud)  # type: ignore[arg-type]
            if self.local and self.cfg.fallback.fallback_to_local:
                out.append(self.local)
        else:
            if self.local:
                out.append(self.local)
            if self.cloud_usable and self.cfg.fallback.fallback_to_cloud:
                out.append(self.cloud)  # type: ignore[arg-type]
        return out

    def primary(self, task: str) -> LLMProvider | None:
        c = self.chain(task)
        return c[0] if c else None

    def describe(self, task: str = Task.EXPLAIN) -> str:
        p = self.primary(task)
        return p.describe() if p else "No model configured"

    def transmits_externally(self, task: str = Task.EXPLAIN) -> bool:
        return any(not p.is_local for p in self.chain(task)[:1])

    def _no_provider_error(self) -> LLMError:
        if self.cfg.mode == OperatingMode.LOCAL:
            return ProviderUnavailable("no local", "No local model is configured. Open Settings → AI Model.")
        if not self.cfg.cloud.consent_given:
            return LLMError("no consent", "Cloud mode needs your confirmation that data may be sent externally (Settings → AI Model).")
        return ProviderUnavailable("no provider", "No usable AI provider is configured. Open Settings → AI Model.")

    def _announce(self, failed: LLMProvider, exc: LLMError, nxt: LLMProvider) -> None:
        dest = "local model - data stays on this computer" if nxt.is_local else "CLOUD provider - content will leave this computer"
        msg = f"{failed.describe()} failed ({exc.user_message}). Switching to {nxt.describe()} [{dest}]."
        log.warning("Provider fallback: %s -> %s (%s)", failed.name, nxt.name, type(exc).__name__)
        self.notify(msg)

    # ------------------------------------------------------------ execution
    def run(self, task: str, fn: Callable[[LLMProvider], T]) -> T:
        providers = self.chain(task)
        if not providers:
            raise self._no_provider_error()
        last: LLMError | None = None
        for i, p in enumerate(providers):
            try:
                return fn(p)
            except Cancelled:
                raise
            except _FALLBACK_ERRORS as exc:
                last = exc
                if i + 1 < len(providers):
                    self._announce(p, exc, providers[i + 1])
                    continue
                raise
        assert last is not None
        raise last

    def stream(
        self, task: str, messages: list[ChatMessage], params: GenerationParams, cancel: CancelToken
    ) -> Iterator[str]:
        """Stream from the first working provider. Fallback only before the first chunk arrives."""
        providers = self.chain(task)
        if not providers:
            raise self._no_provider_error()
        for i, p in enumerate(providers):
            started = False
            try:
                for chunk in p.stream_chat(messages, params, cancel):
                    started = True
                    yield chunk
                return
            except Cancelled:
                raise
            except _FALLBACK_ERRORS as exc:
                if started or i + 1 >= len(providers):
                    raise
                self._announce(p, exc, providers[i + 1])
