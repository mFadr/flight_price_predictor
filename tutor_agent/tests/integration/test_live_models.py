"""Optional integration tests against a REAL configured model.

Skipped by default. Run with:
    set TUTOR_LIVE=1
    .venv\\Scripts\\python -m pytest tests/integration -s
Optional: TUTOR_LIVE_MODEL=llama3.2:3b  (defaults to llama3.1:8b)
"""

import os
import time

import pytest

from tutor.config import AppConfig, OperatingMode
from tutor.domain import Correctness
from tutor.llm.ollama import OllamaProvider
from tutor.llm.router import ProviderRouter

pytestmark = pytest.mark.skipif(os.environ.get("TUTOR_LIVE") != "1", reason="set TUTOR_LIVE=1 to run live model tests")


@pytest.fixture(scope="module")
def live_ctx(tmp_path_factory):
    from tutor.app import AppContext
    model = os.environ.get("TUTOR_LIVE_MODEL", "llama3.1:8b")
    cfg = AppConfig(mode=OperatingMode.LOCAL)
    cfg.ollama.model = model
    provider = OllamaProvider(model, timeout_s=600)
    status = provider.check_status()
    if not status.ok:
        pytest.skip(status.message)
    ctx = AppContext(root=tmp_path_factory.mktemp("live"), router=ProviderRouter(cfg, provider, None), configure_logging=False)
    ctx.cfg.ollama.model = model
    ctx.cfg.ollama.timeout_s = 600
    ctx.engine.reload_config(ctx.cfg)
    yield ctx
    ctx.db.close()


def test_live_workflow(live_ctx):
    eng = live_ctx.engine
    s = eng.start_session("Mathematics", "Linear equations", goal="solve two-step linear equations", level=2)
    t = time.time()
    r = eng.opening(s)
    print(f"\n[opening {time.time() - t:.0f}s]\n{r.messages[-1].content}\n")
    assert len(r.messages[-1].content) > 20

    t = time.time()
    ex = eng.new_exercise(s, "first").exercise
    print(f"[exercise {time.time() - t:.0f}s] validated={ex.validated} type={ex.answer_type.value} "
          f"expected={ex.expected_answer!r} eq={ex.equation!r}\n{ex.statement}\nhints={ex.hints}\n")
    assert ex.statement

    t = time.time()
    r = eng.submit_answer(s, "x = 999", "I moved the constant to the other side")
    print(f"[feedback {time.time() - t:.0f}s]\n{r.messages[-1].content}\n")
    if ex.validated:
        assert r.evaluation.correctness == Correctness.INCORRECT  # deterministic check must win

    t = time.time()
    r = eng.hint(s)
    print(f"[hint {time.time() - t:.0f}s]\n{r.messages[-1].content}\n")
    assert "Hint 1/5" in r.messages[-1].content
