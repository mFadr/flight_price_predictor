"""Application configuration (TOML, validated with Pydantic).

Secrets are NEVER stored here - API keys live in the OS credential store
(see :mod:`tutor.secrets`).
"""

from __future__ import annotations

import logging
import tomllib
from enum import Enum
from pathlib import Path

import tomli_w
from pydantic import BaseModel, Field, ValidationError, field_validator

from tutor.app_paths import atomic_write_text

log = logging.getLogger(__name__)


class OperatingMode(str, Enum):
    LOCAL = "local"     # Ollama only - nothing leaves the computer
    CLOUD = "cloud"     # cloud provider for all LLM tasks
    HYBRID = "hybrid"   # local by default, cloud for explicitly selected tasks


class QualityPreset(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    QUALITY = "quality"


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "llama3.1:8b"
    # Read timeout between streamed chunks. CPU-only laptops can need minutes to process a long prompt.
    timeout_s: float = 300.0
    # One fixed context size for every request: changing it forces Ollama to reload the model.
    num_ctx: int = 8192
    # Keep the model in memory between questions (Ollama's default unloads after 5 minutes,
    # and reloading a 5 GB model on a RAM-constrained laptop can take minutes).
    keep_alive: str = "30m"


class CloudConfig(BaseModel):
    enabled: bool = False
    provider_name: str = "OpenAI-compatible"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    timeout_s: float = 90.0
    # Name of the keyring entry / environment variable holding the key.
    api_key_env: str = "TUTOR_CLOUD_API_KEY"
    structured_output: str = "json_schema"  # json_schema | json_object | prompt
    max_requests_per_day: int = 200
    max_output_tokens: int = 1500
    consent_given: bool = False  # user acknowledged that data leaves the computer


class GenerationConfig(BaseModel):
    temperature: float = Field(0.4, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    max_response_tokens: int = Field(900, ge=64, le=8192)
    quality: QualityPreset = QualityPreset.BALANCED
    response_length: str = "medium"  # short | medium | long


class FallbackConfig(BaseModel):
    # cloud -> local fallback (safe; keeps data local)
    fallback_to_local: bool = True
    # local -> cloud fallback; never used in LOCAL mode, and always announced.
    fallback_to_cloud: bool = False


class HybridConfig(BaseModel):
    # Which task kinds may use the cloud provider in hybrid mode.
    cloud_tasks: list[str] = Field(default_factory=lambda: ["explain"])


class PrivacyConfig(BaseModel):
    diagnostic_logging: bool = False  # verbose logs (never contain secrets or content)
    send_learning_history_to_cloud: bool = False  # only concise topic summary is sent if True


class AppConfig(BaseModel):
    mode: OperatingMode = OperatingMode.LOCAL
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    cloud: CloudConfig = Field(default_factory=CloudConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)
    hybrid: HybridConfig = Field(default_factory=HybridConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    code_timeout_s: float = 5.0
    code_memory_mb: int = 256
    context_char_budget: int = 12000
    ui_font_size: int = 11
    high_contrast: bool = False

    @field_validator("context_char_budget")
    @classmethod
    def _budget(cls, v: int) -> int:
        return max(2000, min(v, 200_000))

    @property
    def cloud_allowed(self) -> bool:
        return self.mode != OperatingMode.LOCAL and self.cloud.enabled and self.cloud.consent_given


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        cfg = AppConfig()
        save_config(cfg, path)
        return cfg
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        return AppConfig.model_validate(data)
    except (tomllib.TOMLDecodeError, ValidationError, OSError) as exc:
        # Preserve the broken file for the user, start with defaults.
        backup = path.with_suffix(".invalid.toml")
        try:
            path.replace(backup)
        except OSError:
            pass
        log.warning("Configuration invalid (%s); defaults loaded, old file kept as %s", type(exc).__name__, backup)
        cfg = AppConfig()
        save_config(cfg, path)
        return cfg


def save_config(cfg: AppConfig, path: Path) -> None:
    data = cfg.model_dump(mode="json")
    atomic_write_text(path, tomli_w.dumps(data))
