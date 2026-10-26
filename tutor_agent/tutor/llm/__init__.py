"""LLM provider layer."""

from __future__ import annotations

from collections.abc import Callable

from tutor.config import AppConfig
from tutor.credentials import get_api_key
from tutor.llm.base import LLMProvider
from tutor.llm.ollama import OllamaProvider
from tutor.llm.openai_compat import OpenAICompatibleProvider
from tutor.llm.router import ProviderRouter, Task


def build_router(cfg: AppConfig, notify: Callable[[str], None] | None = None) -> ProviderRouter:
    local: LLMProvider = OllamaProvider(
        cfg.ollama.model, cfg.ollama.base_url, cfg.ollama.timeout_s, cfg.ollama.num_ctx, cfg.ollama.keep_alive
    )
    cloud: LLMProvider | None = None
    if cfg.cloud.enabled:
        cloud = OpenAICompatibleProvider(
            model=cfg.cloud.model,
            base_url=cfg.cloud.base_url,
            api_key=get_api_key(cfg.cloud.api_key_env),
            name=cfg.cloud.provider_name,
            timeout_s=cfg.cloud.timeout_s,
            structured_output=cfg.cloud.structured_output,
            max_requests_per_day=cfg.cloud.max_requests_per_day,
            max_output_tokens=cfg.cloud.max_output_tokens,
        )
    return ProviderRouter(cfg, local, cloud, notify)


__all__ = ["build_router", "ProviderRouter", "Task"]
