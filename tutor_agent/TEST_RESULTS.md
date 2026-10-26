# Test results

**Environment:** Windows 10 Home 19045 · Python 3.13.5 · PySide6 6.12 · Ollama 0.40.8. Hardware: Intel i7-1165G7 (4 cores), 16 GB RAM, integrated graphics only, so everything ran on the CPU.

## Automated suite (mocked LLM – no model or API required)

```
.venv\Scripts\python -m pytest -v
======================= 118 passed, 1 skipped in 11.24s =======================
```

| File | Tests | Covers |
|---|---|---|
| `test_workflow.py` | 24 ✅ | The full §22 workflow end to end: topic → explanation → question → answer → SymPy verification → diagnosis → hint → retry → verified correct → saved, reloaded and resumed. Also: the hint ladder up to the full solution, reduced evidence weight after a viewed solution, the LLM's verdict overridden by the software check, correct answer with invalid reasoning, clarification for unreadable answers, adaptive level up, the fixed level only suggesting changes, Easier/Harder as student override, the session summary and its continuity in the next session, frustration triggering direct explanation, explicit solution requests, chat answers routed to evaluation, the step check in "check my reasoning", strategy rotation in "explain differently", model diagrams rendered, cancellation keeping partial output, history trimming and summarising, code exercises in the sandbox, wrong answer keys corrected by SymPy, broken code exercises never shown as verified, malformed LLM evaluation falling back to the software check, and no confident misconception when the work can't be checked |
| `test_knowledge_and_difficulty.py` | 16 ✅ | Not assessed vs introduced; one easy correct answer is not mastery; variety and independence required; hint-heavy successes don't count; needs revision; recurring errors; student overrides. Difficulty never changes on a single answer; increase and decrease rules |
| `test_math_verify.py` | 20 ✅ | Symbolic equivalence, unsafe input rejected before SymPy, numbers with sign and order-of-magnitude hints, solution sets with partial credit, the earliest wrong step in a chain, unit and dimension checks |
| `test_code_runner.py` | 16 ✅ | Test cases and partial credit; static rejection of os, subprocess, socket, open, eval, `__import__` and dunder escapes; the **runtime** audit hook blocking file writes and reads even with the static check bypassed; timeout; error line numbers; float tolerance |
| `test_router_and_llm.py` | 10 ✅ | Local mode never uses the cloud; the cloud needs consent; announced fallback; hybrid routing per task; cancellation never triggers fallback; JSON extraction; one bounded repair round; fixed `num_ctx` and `keep_alive` in Ollama requests |
| `test_storage_materials_viz.py` | 29 ✅ | Exports never overwrite; no secrets in exports, config or logs; backup and restore; foreign zips rejected; deleting a session or profile; progress export and override; a broken config preserved; PDF ingestion with page references (non-ASCII file name); dedup cache; materials wrapped as untrusted data and placed in the user turn; all 14 visualisation kinds; equilibrium computed, not invented; synthetic data labelled; invalid specs ignored safely |
| `test_ui_smoke.py` | 3 ✅ | Every page builds; the session flow runs through the real UI in background workers and stays responsive (busy state and cancel); math and code rendering |
| `integration/test_live_models.py` | skipped by default | Real model, see below |

## Live integration test (real local model, `TUTOR_LIVE=1`)

Model: `llama3.1:8b` (Q4_K_M) in Ollama, CPU only. The test passed in both runs.

| Step | Run 1: cold, model reloaded | Run 2: model resident |
|---|---|---|
| Opening explanation + diagnostic question | 445 s | 91 s |
| Exercise generation + SymPy validation | 205 s | 71 s |
| Evaluation of a wrong answer (`x = 999`) | 85 s | 65 s |
| Hint 1 (validated hint stored with the exercise) | <1 s | <1 s |

**What the live runs showed:**

* The generated exercise (`2x + 5 = 11`) was **validated by SymPy** (answer key 3).
* The wrong answer was marked incorrect by the software check, not by the model.
* Both live runs exposed problems the mocks couldn't, and both were fixed and covered by regression tests:
  1. The model wrote feedback about "the student" in the third person.
  2. It claimed a specific misconception with *high* confidence from vague reasoning. Now the confidence is capped, speculative "where it went wrong" text is dropped, and the student is asked to show their steps.
* The cold start was dominated by **loading the model** (495 s in a separate probe), because only about 2 GB of RAM was free and the model was paged in from disk. A request with a different `num_ctx` forces such a reload. The fix: the app always sends one fixed `num_ctx`, keeps the model loaded with `keep_alive=30m`, and preloads it in the background at startup.
* Measured throughput: about 25 tokens/s for prompt processing and about 6.3 tokens/s for generation.

## Manual / visual checks

* Ran `python -m tutor` on the native Windows platform with a temporary data folder containing spaces and non-ASCII characters. The window opened, Ollama and `llama3.1:8b` were detected, the badge showed "local, offline", all data folders were created and the app exited with code 0.
* `scripts/demo_screenshots.py` rendered the real UI. The screenshots are in `docs/screenshots/`. Checked: LaTeX rendering, plot embedding, the verified-key badge, the help-level indicator, the progress table and chart, and the dashboard.

## Not verified

* The cloud provider against a real paid API: no key was available. The adapter, error handling and routing are covered with mocks only.
* OCR of scanned PDFs: Tesseract is not installed on the test machine.
* A PyInstaller-built executable, and Windows 11.
* Smaller local models such as `llama3.2:3b`: none was installed, and I did not download one.
