"""Ollama adapter (local models, no internet required)."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any

import httpx

from tutor.llm.base import (
    CancelToken,
    ChatMessage,
    GenerationParams,
    LLMError,
    LLMProvider,
    ModelCapabilities,
    ModelNotFound,
    ProviderStatus,
    ProviderUnavailable,
)

log = logging.getLogger(__name__)

TROUBLESHOOTING = [
    "Install Ollama for Windows from https://ollama.com/download and start it (it runs in the system tray).",
    "Open a terminal and run:  ollama pull llama3.1:8b   (≈4.9 GB; needs ~8 GB RAM).",
    "Smaller laptops: try  ollama pull llama3.2:3b  or  qwen2.5:3b  and select it in Settings.",
    "Check that  http://localhost:11434  is reachable (run  ollama list  in a terminal).",
    "If you changed the Ollama port/host, update the base URL in Settings → AI Model.",
]


class OllamaProvider(LLMProvider):
    name = "Ollama"
    is_local = True

    def __init__(self, model: str, base_url: str = "http://localhost:11434", timeout_s: float = 300.0, num_ctx: int = 8192,
                 keep_alive: str = "30m"):
        super().__init__(model)
        self.keep_alive = keep_alive
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.num_ctx = num_ctx
        self._caps_cache: dict[str, ModelCapabilities] = {}

    # ----------------------------------------------------------- helpers
    def _client(self, timeout: float | None = None) -> httpx.Client:
        t = timeout or self.timeout_s
        return httpx.Client(base_url=self.base_url, timeout=httpx.Timeout(t, connect=5.0), trust_env=False)

    def _options(self, params: GenerationParams) -> dict[str, Any]:
        opts: dict[str, Any] = {
            "temperature": params.temperature,
            "top_p": params.top_p,
            "num_predict": params.max_tokens,
            # Always the provider's fixed value - a different num_ctx would trigger a full model reload.
            "num_ctx": self.num_ctx,
        }
        if params.stop:
            opts["stop"] = params.stop
        return opts

    @staticmethod
    def _msgs(messages: list[ChatMessage]) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def _raise_for(self, exc: Exception) -> None:
        if isinstance(exc, httpx.ConnectError):
            raise ProviderUnavailable(
                str(exc), "Cannot reach Ollama at %s. Is Ollama running?" % self.base_url, retryable=True
            ) from exc
        if isinstance(exc, httpx.TimeoutException):
            raise LLMError(str(exc), "The local model took too long to respond. Try a smaller model or shorter answers.", True) from exc
        raise LLMError(str(exc), f"Ollama error: {type(exc).__name__}") from exc

    def _check_response(self, resp: httpx.Response) -> None:
        if resp.status_code == 404:
            raise ModelNotFound(
                "model not found",
                f"Model '{self.model}' is not installed in Ollama. Run:  ollama pull {self.model}",
            )
        if resp.status_code >= 400:
            try:
                resp.read()
                detail = resp.json().get("error", "")
            except Exception:
                detail = ""
            raise LLMError(f"HTTP {resp.status_code}: {detail}", f"Ollama returned an error: {detail or resp.status_code}")

    # ----------------------------------------------------------- streaming
    def _stream(self, messages: list[ChatMessage], params: GenerationParams, cancel: CancelToken) -> Iterator[str]:
        body = {"model": self.model, "messages": self._msgs(messages), "stream": True, "options": self._options(params),
                "keep_alive": self.keep_alive}
        try:
            with self._client() as client, client.stream("POST", "/api/chat", json=body) as resp:
                self._check_response(resp)
                for line in resp.iter_lines():
                    if cancel.cancelled:
                        resp.close()
                        cancel.check()
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("error"):
                        raise LLMError(data["error"], f"Ollama error: {data['error']}")
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break
        except LLMError:
            raise
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            self._raise_for(exc)

    def _complete_json(
        self, messages: list[ChatMessage], schema: dict[str, Any], params: GenerationParams, cancel: CancelToken
    ) -> str:
        caps = self.capabilities()
        fmt: Any = schema if caps.supports_structured_output is not False else "json"
        body = {
            "model": self.model,
            "messages": self._msgs(messages),
            "stream": True,  # stream so we can honour cancellation
            "format": fmt,
            "options": self._options(params),
            "keep_alive": self.keep_alive,
        }
        parts: list[str] = []
        try:
            with self._client() as client, client.stream("POST", "/api/chat", json=body) as resp:
                self._check_response(resp)
                for line in resp.iter_lines():
                    if cancel.cancelled:
                        resp.close()
                        cancel.check()
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("error"):
                        raise LLMError(data["error"], f"Ollama error: {data['error']}")
                    parts.append(data.get("message", {}).get("content", ""))
                    if data.get("done"):
                        break
        except LLMError:
            raise
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            self._raise_for(exc)
        return "".join(parts)

    # ----------------------------------------------------------- warm-up
    def warm_up(self) -> bool:
        """Load the model into memory in advance (no prompt is processed)."""
        try:
            with self._client(timeout=max(self.timeout_s, 900)) as client:
                resp = client.post("/api/generate", json={"model": self.model, "keep_alive": self.keep_alive,
                                                          "options": {"num_ctx": self.num_ctx}})
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def is_loaded(self) -> bool:
        try:
            with self._client(timeout=3) as client:
                running = client.get("/api/ps").json().get("models", [])
                return any(m.get("name") in (self.model, f"{self.model}:latest") for m in running)
        except (httpx.HTTPError, ValueError):
            return False

    # ----------------------------------------------------------- status
    def list_models(self) -> list[str]:
        try:
            with self._client(timeout=5) as client:
                resp = client.get("/api/tags")
                resp.raise_for_status()
                return sorted(m["name"] for m in resp.json().get("models", []))
        except httpx.HTTPError:
            return []

    def capabilities(self) -> ModelCapabilities:
        if self.model in self._caps_cache:
            return self._caps_cache[self.model]
        caps = ModelCapabilities(model=self.model, available=False)
        try:
            with self._client(timeout=10) as client:
                resp = client.post("/api/show", json={"model": self.model})
                if resp.status_code == 200:
                    info = resp.json()
                    caps.available = True
                    capset = set(info.get("capabilities") or [])
                    caps.supports_tools = "tools" in capset if capset else None
                    # Ollama >= 0.5 supports JSON-schema constrained output for all completion models.
                    caps.supports_structured_output = True
                    for key, val in (info.get("model_info") or {}).items():
                        if key.endswith(".context_length"):
                            caps.context_length = int(val)
                    if caps.context_length and caps.context_length < 4096:
                        caps.notes.append("Small context window - long sessions will be summarised more aggressively.")
                    self._caps_cache[self.model] = caps
        except httpx.HTTPError:
            pass
        return caps

    def check_status(self) -> ProviderStatus:
        models = self.list_models()
        if not models and not self._reachable():
            return ProviderStatus(
                ok=False, provider=self.name, model=self.model, is_local=True,
                message=f"Ollama is not reachable at {self.base_url}.", troubleshooting=TROUBLESHOOTING,
            )
        if self.model not in models and f"{self.model}:latest" not in models:
            return ProviderStatus(
                ok=False, provider=self.name, model=self.model, is_local=True,
                message=f"Ollama is running, but model '{self.model}' is not installed.",
                available_models=models,
                troubleshooting=[f"Run:  ollama pull {self.model}", "…or pick one of the installed models in Settings."],
            )
        caps = self.capabilities()
        notes = []
        if caps.context_length:
            notes.append(f"context window {caps.context_length:,} tokens (app uses {self.num_ctx:,})")
        notes.append("tool calling: " + ("yes" if caps.supports_tools else "no/unknown"))
        notes.append("structured output: JSON schema")
        return ProviderStatus(
            ok=True, provider=self.name, model=self.model, is_local=True,
            message="Ready - " + "; ".join(notes), capabilities=caps, available_models=models,
        )

    def _reachable(self) -> bool:
        try:
            with self._client(timeout=3) as client:
                return client.get("/api/version").status_code == 200
        except httpx.HTTPError:
            return False
