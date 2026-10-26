import pytest
from pydantic import BaseModel

from tutor.config import AppConfig, OperatingMode
from tutor.llm.base import CancelToken, Cancelled, ChatMessage, GenerationParams, ProviderUnavailable, StructuredOutputError
from tutor.llm.mock import MockProvider
from tutor.llm.router import ProviderRouter, Task
from tutor.llm.structured import extract_json, generate_structured


def cfg(mode, consent=True, to_cloud=False, to_local=True, cloud_tasks=("explain",)):
    c = AppConfig(mode=mode)
    c.cloud.enabled, c.cloud.consent_given = True, consent
    c.fallback.fallback_to_cloud, c.fallback.fallback_to_local = to_cloud, to_local
    c.hybrid.cloud_tasks = list(cloud_tasks)
    return c


def test_local_mode_never_uses_cloud_even_with_fallback_enabled():
    local = MockProvider(fail_with=ProviderUnavailable("down"), is_local=True)
    cloud = MockProvider(responses=["cloud!"], is_local=False)
    r = ProviderRouter(cfg(OperatingMode.LOCAL, to_cloud=True), local, cloud)
    assert r.chain(Task.EXPLAIN) == [local]
    with pytest.raises(ProviderUnavailable):
        r.run(Task.EXPLAIN, lambda p: p.chat([ChatMessage("user", "hi")], GenerationParams()))
    assert cloud.calls == []
    assert not r.transmits_externally()


def test_cloud_requires_consent():
    cloud = MockProvider(is_local=False)
    r = ProviderRouter(cfg(OperatingMode.CLOUD, consent=False, to_local=False), None, cloud)
    assert r.chain(Task.EXPLAIN) == []


def test_cloud_failure_falls_back_to_local_and_announces():
    notes = []
    local = MockProvider(responses=["local answer"])
    cloud = MockProvider(fail_with=ProviderUnavailable("down", "offline"), is_local=False)
    r = ProviderRouter(cfg(OperatingMode.CLOUD), local, cloud, notify=notes.append)
    out = "".join(r.stream(Task.EXPLAIN, [ChatMessage("user", "x")], GenerationParams(), CancelToken()))
    assert out == "local answer"
    assert notes and "Switching to" in notes[0] and "stays on this computer" in notes[0]


def test_hybrid_routes_by_task():
    local, cloud = MockProvider(is_local=True), MockProvider(is_local=False)
    r = ProviderRouter(cfg(OperatingMode.HYBRID, cloud_tasks=("explain",)), local, cloud)
    assert r.primary(Task.EXPLAIN) is cloud
    assert r.primary(Task.EVALUATE) is local
    assert r.chain(Task.EVALUATE) == [local]  # no silent escalation to cloud


def test_hybrid_local_to_cloud_fallback_only_when_enabled_and_announced():
    notes = []
    local = MockProvider(fail_with=ProviderUnavailable("down"))
    cloud = MockProvider(responses=["from cloud"], is_local=False)
    r = ProviderRouter(cfg(OperatingMode.HYBRID, to_cloud=True, cloud_tasks=()), local, cloud, notify=notes.append)
    assert r.run(Task.EVALUATE, lambda p: p.chat([ChatMessage("user", "x")], GenerationParams())) == "from cloud"
    assert "CLOUD" in notes[0]


def test_cancellation_does_not_fall_back():
    tok = CancelToken()
    tok.cancel()
    local = MockProvider(responses=["never"])
    cloud = MockProvider(responses=["never"], is_local=False)
    r = ProviderRouter(cfg(OperatingMode.CLOUD), local, cloud)
    with pytest.raises(Cancelled):
        list(r.stream(Task.EXPLAIN, [ChatMessage("user", "x")], GenerationParams(), tok))
    assert local.calls == []


class Pt(BaseModel):
    x: int
    y: int


def test_extract_json_variants():
    assert extract_json('Sure! ```json\n{"x": 1, "y": 2}\n``` done') == {"x": 1, "y": 2}
    assert extract_json('noise {"x": 1, "y": {"z": "}"}} tail') == {"x": 1, "y": {"z": "}"}}


def test_structured_repair_then_success():
    p = MockProvider(responses=["not json", {"x": 1, "y": 2}])
    assert generate_structured(p, [ChatMessage("user", "go")], Pt, GenerationParams()).x == 1
    assert len(p.calls) == 2


def test_structured_bounded_retries():
    p = MockProvider(responses=["bad", "bad", "bad", "bad"])
    with pytest.raises(StructuredOutputError):
        generate_structured(p, [ChatMessage("user", "go")], Pt, GenerationParams(), max_repairs=1)
    assert len(p.calls) == 2  # never endless


def test_ollama_requests_keep_fixed_context_and_keep_alive(monkeypatch):
    """Changing num_ctx between requests forces Ollama to reload the model (minutes on CPU laptops)."""
    import json as _json

    import httpx

    from tutor.llm.ollama import OllamaProvider

    bodies = []

    def handler(request):
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"capabilities": ["completion"], "model_info": {}})
        bodies.append(_json.loads(request.content))
        return httpx.Response(200, text=_json.dumps({"message": {"content": "{\"x\": 1, \"y\": 2}"}, "done": True}) + "\n")

    p = OllamaProvider("m", num_ctx=8192, keep_alive="30m")
    monkeypatch.setattr(p, "_client", lambda timeout=None: httpx.Client(base_url="http://x", transport=httpx.MockTransport(handler)))
    p.chat([ChatMessage("user", "hi")], GenerationParams(num_ctx=2048))
    generate_structured(p, [ChatMessage("user", "hi")], Pt, GenerationParams(num_ctx=16384))
    assert [b["options"]["num_ctx"] for b in bodies] == [8192, 8192]
    assert all(b["keep_alive"] == "30m" for b in bodies)
    assert isinstance(bodies[1]["format"], dict)  # JSON-schema constrained output
