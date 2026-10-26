"""The smallest complete tutoring workflow (prompt §22), end to end with a mocked LLM."""

import json

from conftest import EVAL_CORRECT, EVAL_SIGN_ERROR, LINEAR_EXERCISE

from tutor.app import AppContext
from tutor.domain import Correctness, ErrorCategory, MessageKind, Role, SessionStatus, VerificationStatus
from tutor.engine.hints import leaks_answer


def test_minimal_workflow(ctx, scripted):
    eng = ctx.engine
    # 1. student selects a topic
    s = eng.start_session("Mathematics", "Linear equations", goal="solve two-step equations", level=2)
    # 2-3. tutor explains and asks a question (streamed)
    chunks = []
    scripted.chat_replies.append("An equation is like a balance. **What do you think happens if we add 7 to one side only?**")
    r = eng.opening(s, on_chunk=chunks.append)
    assert "".join(chunks).startswith("An equation") and r.messages[-1].role == Role.ASSISTANT
    # practice problem
    r = eng.new_exercise(s, "first")
    ex = r.exercise
    assert ex.validated and ex.answer_type.value == "solutions"
    assert r.messages[-1].kind == MessageKind.EXERCISE
    # 4-6. student answers with a sign error; deterministic check + diagnosis
    scripted.evaluations.append(EVAL_SIGN_ERROR)
    r = eng.submit_answer(s, "x = 4/3", "3x - 7 = 11\n3x = 4\nx = 4/3", confidence=3)
    ev = r.evaluation
    assert ev.correctness == Correctness.INCORRECT
    assert ev.verification.status == VerificationStatus.INCORRECT
    assert "Step 2" in ev.earliest_error  # SymPy located the first wrong step
    assert ev.error_category == ErrorCategory.SIGN_ARITHMETIC
    assert "Where it first goes wrong" in ev.feedback and not leaks_answer(ev.feedback, ex)
    # 7. progressive hints (pre-generated, non-leaking, increasing level)
    h1 = eng.hint(s).messages[-1]
    h2 = eng.hint(s).messages[-1]
    assert "Hint 1/5" in h1.content and "Hint 2/5" in h2.content
    assert not leaks_answer(h1.content, ex) and not leaks_answer(h2.content, ex)
    # 8-9. second attempt is correct and verified
    scripted.evaluations.append(EVAL_CORRECT)
    r = eng.submit_answer(s, "x = 6", "3x - 7 = 11 => 3x = 18 => x = 6")
    assert r.evaluation.correctness == Correctness.CORRECT and r.evaluation.answer_correct
    assert "similar problem" in r.messages[-1].content
    # 10. saved locally and restorable after "restart"
    root = ctx.paths.root
    ctx.db.close()
    ctx2 = AppContext(root=root, router=ctx.router, configure_logging=False)
    s2 = ctx2.db.get_session(s.id)
    msgs = ctx2.db.messages(s.id)
    assert s2 is not None and s2.hint_levels[ex.id] == 2
    assert [m.kind for m in msgs].count(MessageKind.FEEDBACK) == 2
    attempts = ctx2.db.attempts_for_session(s.id)
    assert attempts[0].hints_used == 0 and attempts[1].hints_used == 2
    ctx2.db.close()


def test_hint_ladder_reaches_full_solution_and_records_it(ctx):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    ex = eng.new_exercise(s, "first").exercise
    levels = [eng.hint(s).messages[-1].content for _ in range(5)]
    assert "Hint 3/5" in levels[2] and "Partially worked" in levels[3]
    assert not leaks_answer(levels[3].split("Partially worked solution**")[1], ex)
    assert "Complete worked solution" in levels[4]
    assert ex.id in ctx.db.get_session(s.id).solutions_viewed


def test_solution_viewed_reduces_evidence_weight(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    eng.new_exercise(s, "first")
    eng.worked_solution(s)
    eng.submit_answer(s, "6")
    ev = ctx.db.evidence("Mathematics", "Linear equations")
    att = [e for e in ev if e.kind.value == "attempt"][0]
    assert att.assistance == 5
    assert eng.knowledge.status("Mathematics", "Linear equations", "Linear equations").independent_successes == 0


def test_llm_wrongly_says_correct_is_overridden(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    eng.new_exercise(s, "first")
    scripted.evaluations.append(EVAL_CORRECT)  # model is wrong
    r = eng.submit_answer(s, "x = 5")
    assert r.evaluation.correctness == Correctness.INCORRECT
    assert "automatic check" in r.evaluation.reconciliation_note


def test_correct_answer_with_invalid_reasoning(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    eng.new_exercise(s, "first")
    r = eng.submit_answer(s, "x = 6", "3x - 7 = 11\n3x = 4\nx = 6")
    assert r.evaluation.correctness == Correctness.PARTIALLY_CORRECT
    assert r.evaluation.error_category == ErrorCategory.RIGHT_ANSWER_BAD_REASONING


def test_unparseable_answer_asks_for_clarification(ctx):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    eng.new_exercise(s, "first")
    r = eng.submit_answer(s, "around six-ish @@")
    assert r.evaluation.correctness == Correctness.INSUFFICIENT_EVIDENCE
    assert "Question for you" in r.evaluation.feedback
    assert not [e for e in ctx.db.evidence() if e.kind.value == "attempt"]  # no evidence recorded


def test_adaptive_level_up_after_three_independent_correct(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations", level=2)
    variants = []
    for i, (eq, sol) in enumerate([("2*x+1=7", "3"), ("5*x-5=20", "5"), ("4*x+4=0", "-1")]):
        d = dict(LINEAR_EXERCISE, equation=eq, expected_answer=sol, statement=f"Exercise {i}: solve ${eq}$ for x, step by step.",
                 solution_explanation=f"... so x = {sol}")
        variants.append(d)
    scripted.exercises = variants + [variants[-1]]
    notices = []
    for d in variants:
        eng.new_exercise(s, "similar")
        r = eng.submit_answer(s, d["expected_answer"])
        notices += [m.content for m in r.messages if m.kind == MessageKind.NOTICE]
    assert s.level == 3 and any("raised from 2 to 3" in n for n in notices)


def test_locked_level_only_suggests(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations", level=2)
    eng.set_level(s, 2, lock=True)
    for eq, sol in [("2*x+1=7", "3"), ("5*x-5=20", "5"), ("4*x+4=0", "-1")]:
        scripted.exercises = [dict(LINEAR_EXERCISE, equation=eq, expected_answer=sol, statement=f"Solve ${eq}$ now please."), {}]
        scripted.exercises = scripted.exercises[:1]
        eng.new_exercise(s, "similar")
        r = eng.submit_answer(s, sol)
    assert s.level == 2
    assert any("Suggestion" in m.content for m in ctx.db.messages(s.id) if m.kind == MessageKind.NOTICE)


def test_harder_button_is_student_override(ctx):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations", level=3)
    r = eng.new_exercise(s, "harder")
    assert s.level == 4 and r.level_changed


def test_session_summary_and_continuity(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    eng.new_exercise(s, "first")
    scripted.evaluations.append(EVAL_SIGN_ERROR)
    eng.submit_answer(s, "x = 4/3")
    r = eng.end_session(s)
    assert r.summary.tasks_attempted == 1 and r.summary.tasks_correct == 0
    assert ctx.db.get_session(s.id).status == SessionStatus.COMPLETED
    assert "Completing exercises is not the same as mastery" in r.summary.text
    # next session on the same topic receives a concise summary of the previous one
    s2 = eng.start_session("Mathematics", "linear equations")
    scripted.prompts.clear()
    eng.opening(s2)
    system = scripted.prompts[-1][0].content
    assert "previous session" in system.lower() and "sign when moving terms across" in system


def test_frustration_switches_to_direct(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Derivatives")
    eng.respond(s, "I give up, this makes no sense")
    last_user = scripted.prompts[-1][-1].content
    assert "frustrated" in last_user and "direct explanation" in last_user


def test_explicit_solution_request_in_chat(ctx):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    eng.new_exercise(s, "first")
    r = eng.respond(s, "Please just show me the full solution")
    assert any(m.kind == MessageKind.SOLUTION and "worked solution" in m.content.lower() for m in r.messages)


def test_chat_answer_routed_to_evaluation(ctx):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    eng.new_exercise(s, "first")
    r = eng.respond(s, "3x = 18\nx = 6")
    assert r.evaluation is not None and r.evaluation.correctness == Correctness.CORRECT


def test_check_reasoning_includes_verified_step_report(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    r = eng.check_reasoning(s, "2x + 5 = 13\n2x = 18\nx = 9")
    notice = [m for m in r.messages if m.kind == MessageKind.NOTICE][0]
    assert "✘ Step 2" in notice.content
    assert "solution set changed" in scripted.prompts[-1][-1].content


def test_explain_differently_tracks_strategies(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Physics", "Newton's second law")
    scripted.chat_replies.append("*Another way to see it: everyday analogy*\nPushing a shopping cart...")
    eng.explain_differently(s)
    assert s.explanation_strategies == ["everyday analogy"]
    eng.explain_differently(s)
    assert "everyday analogy" in scripted.prompts[-1][-1].content  # told which strategy was already used


def test_model_viz_block_rendered(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Quadratics")
    scripted.chat_replies.append('Look at the parabola.\n```viz\n{"kind": "function_plot", "expressions": ["x^2-4"], "x_min": -3, "x_max": 3, "mark_x": [2]}\n```')
    r = eng.respond(s, "show me x^2-4")
    assert r.visuals and r.messages[0].content == "show me x^2-4"
    chat = [m for m in r.messages if m.kind == MessageKind.CHAT and m.role == Role.ASSISTANT][0]
    assert "```viz" not in chat.content
    vis = [m for m in r.messages if m.kind == MessageKind.VISUAL][0]
    assert any("point (2, 0)" in e for e in vis.meta["elements"])


def test_cancel_preserves_partial_output(ctx, scripted):
    from tutor.llm.base import Cancelled, CancelToken
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Limits")
    scripted.chat_replies.append("A limit describes what value a function approaches. " * 5)
    tok = CancelToken()
    got = []

    def on_chunk(c):
        got.append(c)
        if len(got) == 3:
            tok.cancel()

    try:
        eng.respond(s, "what is a limit", on_chunk=on_chunk, cancel=tok)
    except Cancelled:
        pass
    msgs = ctx.db.messages(s.id)
    assert msgs[-1].content.endswith("*[response cancelled]*")


def test_history_is_trimmed_and_summarised(ctx, scripted):
    eng = ctx.engine
    ctx.cfg.context_char_budget = 2000
    s = eng.start_session("Mathematics", "Integrals")
    for i in range(12):
        scripted.chat_replies.append(f"Reply {i} " + "x" * 300)
        eng.respond(s, f"question {i} " + "y" * 200)
    assert s.summarized_count > 0 and s.running_summary
    total = sum(len(m.content) for m in scripted.prompts[-1][1:])
    assert total < 2000 + 800


def test_code_exercise_end_to_end(ctx, scripted):
    code_ex = {
        **LINEAR_EXERCISE, "concept": "loops", "kind": "programming", "answer_type": "code", "expected_answer": "",
        "equation": "", "statement": "Write `total(nums)` returning the sum of a list without using sum().",
        "function_name": "total", "code_tests": [{"call": "total([1, 2, 3])", "expected": "6"}, {"call": "total([])", "expected": "0"}],
        "reference_solution": "def total(nums):\n    t = 0\n    for n in nums:\n        t += n\n    return t",
        "hints": ["Start with a running total of 0.", "Use a for loop over nums.", "Add each item to the total."],
        "solution_explanation": "Keep an accumulator...",
    }
    scripted.exercises = [code_ex]
    eng = ctx.engine
    s = eng.start_session("Programming", "Loops")
    ex = eng.new_exercise(s, "first").exercise
    assert ex.validated
    r = eng.submit_answer(s, "def total(nums):\n    t = 1\n    for n in nums:\n        t += n\n    return t")
    assert r.evaluation.verification.status == VerificationStatus.INCORRECT
    assert "0/2 tests passed" in r.evaluation.feedback


def test_exercise_with_wrong_answer_key_is_corrected_by_sympy(ctx, scripted):
    scripted.exercises = [dict(LINEAR_EXERCISE, expected_answer="5")]  # model got its own key wrong
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    ex = eng.new_exercise(s, "first").exercise
    assert ex.expected_answer == "6" and "corrected by SymPy" in ex.validation_notes


def test_broken_code_exercise_is_never_presented_as_verified(ctx, scripted):
    bad = {**LINEAR_EXERCISE, "answer_type": "code", "kind": "programming", "function_name": "f", "equation": "",
           "statement": "Write f(x) that doubles x, please.", "code_tests": [{"call": "f(2)", "expected": "5"}, {"call": "f(1)", "expected": "2"}],
           "reference_solution": "def f(x):\n    return 2*x"}
    scripted.exercises = [bad]
    eng = ctx.engine
    s = eng.start_session("Programming", "Functions")
    ex = eng.new_exercise(s, "first").exercise
    assert not ex.validated and ex.answer_type.value == "short_text" and "fails its own tests" in ex.verification_method
    prompts_with_schema = [p for p in scripted.prompts if "failed automatic checks" in p[-1].content]
    assert prompts_with_schema  # one regeneration attempt was made


def test_malformed_llm_evaluation_falls_back_to_deterministic(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    eng.new_exercise(s, "first")
    original = scripted.__call__

    def broken(messages, schema):
        if (schema or {}).get("title") == "EvaluationDraft":
            return "I think it's fine"
        return original(messages, schema)
    ctx.router.local.responder = broken
    r = eng.submit_answer(s, "x = 6")
    assert r.evaluation.correctness == Correctness.CORRECT  # deterministic check still works


def test_vague_reasoning_does_not_get_a_confident_specific_misconception(ctx, scripted):
    """Seen with the real llama3.1:8b: vague reasoning got 'incorrect formula selection, confidence high'."""
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    eng.new_exercise(s, "first")
    scripted.evaluations.append({**EVAL_SIGN_ERROR, "error_category": "incorrect_formula_selection", "diagnosis_confidence": "high"})
    r = eng.submit_answer(s, "x = 999", "I moved the number to the other side")
    ev = r.evaluation
    assert ev.correctness == Correctness.INCORRECT
    assert ev.error_category is None and ev.diagnosis_confidence != "high"
    assert "write out your steps" in ev.feedback
    assert "Where it first goes wrong" not in ev.feedback  # no speculation about unseen steps


def test_checkable_wrong_step_keeps_specific_diagnosis(ctx, scripted):
    eng = ctx.engine
    s = eng.start_session("Mathematics", "Linear equations")
    eng.new_exercise(s, "first")
    scripted.evaluations.append(EVAL_SIGN_ERROR)
    ev = eng.submit_answer(s, "x = 4/3", "3x - 7 = 11\n3x = 4\nx = 4/3").evaluation
    assert ev.error_category == ErrorCategory.SIGN_ARITHMETIC and ev.diagnosis_confidence == "high"
