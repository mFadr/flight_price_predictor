"""Answer evaluation: deterministic verification first, LLM diagnosis second, then reconciliation.

The LLM is never treated as infallible: where a deterministic check exists, its
verdict on the final answer wins and any disagreement is recorded.
"""

from __future__ import annotations

import logging
import re
from typing import Literal

from pydantic import BaseModel, Field

from tutor.domain import (
    AnswerType,
    Correctness,
    ErrorCategory,
    Evaluation,
    Exercise,
    ReasoningQuality,
    VerificationResult,
    VerificationStatus,
)
from tutor.engine.hints import leaks_answer
from tutor.llm.base import CancelToken, ChatMessage, GenerationParams, LLMError
from tutor.llm.router import ProviderRouter, Task
from tutor.llm.structured import generate_structured
from tutor.tools import math_verify as mv
from tutor.tools.code_runner import CodeRunner
from tutor.tools.units import check_quantity

log = logging.getLogger(__name__)
V = VerificationStatus

ErrorLit = Literal[tuple(["none"] + [c.value for c in ErrorCategory])]  # type: ignore[valid-type]


class EvaluationDraft(BaseModel):
    correctness: Literal["correct", "partially_correct", "incorrect", "insufficient_evidence"]
    reasoning_quality: Literal["sound", "partially_sound", "flawed", "not_shown"]
    score: float = Field(0.0, description="0.0-1.0 partial credit")
    error_category: ErrorLit = "none"  # type: ignore[valid-type]
    what_is_correct: str = Field("", description="what the student did correctly")
    earliest_error: str = Field("", description="the first step where reasoning goes wrong, quoted/paraphrased; empty if none")
    why_wrong: str = ""
    applicable_rule: str = Field("", description="the concept or rule that applies")
    how_to_reconsider: str = Field("", description="a question or prompt helping the student fix it WITHOUT giving the answer")
    diagnosis_confidence: Literal["low", "medium", "high"] = "medium"
    clarifying_question: str = Field("", description="ask this if the student's reasoning is too unclear to diagnose")
    suggested_followup: str = Field("", description="a short corrective or follow-up exercise idea")


EVAL_PROMPT = """Evaluate the student's attempt at this exercise. Assess the FINAL ANSWER and the REASONING separately.

Exercise: {statement}
Answer type: {answer_type}
Expected answer: {expected}
{rubric}{mistakes}
Automatic check (computed by software - treat as authoritative for the final answer):
{verification}
{steps}
<student_answer>
Final answer: {answer}
Reasoning: {reasoning}
</student_answer>

Diagnosis process: identify what is correct; find the EARLIEST meaningful error; explain why it is wrong and which rule applies;
if the reasoning is missing or ambiguous, set diagnosis_confidence low and ask a clarifying question instead of guessing a misconception.
If the final answer is right but the reasoning is invalid, use error_category "correct_answer_invalid_reasoning".
Never reveal the expected answer in how_to_reconsider.
Write every text field addressed directly to the student as "you" (e.g. "You correctly…"), never "the student"."""


def deterministic_check(ex: Exercise, answer: str, runner: CodeRunner | None) -> VerificationResult:
    t, ans = ex.answer_type, answer.strip()
    if not ans:
        return VerificationResult(status=V.PARSE_ERROR, method="input check", details="No answer given.")
    if not ex.validated and t not in (AnswerType.MULTIPLE_CHOICE,):
        return VerificationResult(status=V.UNVERIFIABLE, method=ex.verification_method or "AI judgement",
                                  details="No reliable automatic check available for this exercise.")
    if t == AnswerType.EXPRESSION:
        return mv.check_expression(_strip_label(ans), ex.expected_answer)
    if t == AnswerType.EQUATION_SOLUTIONS:
        return mv.check_solutions(ans, ex.expected_answer, ex.variable)
    if t == AnswerType.NUMERIC:
        if ex.unit:
            return check_quantity(ans, f"{ex.expected_answer} {ex.unit}", rel_tol=max(ex.tolerance, 1e-6))
        return mv.check_numeric(ans, ex.expected_answer, rel_tol=max(ex.tolerance, 1e-9))
    if t == AnswerType.MULTIPLE_CHOICE:
        return _check_choice(ex, ans)
    if t == AnswerType.CODE and runner is not None:
        vr, _ = runner.verify(ans, ex.code_tests)
        return vr
    return VerificationResult(status=V.UNVERIFIABLE, method="AI judgement with rubric",
                              details="Open-ended answer: evaluated against the rubric by the AI model, not verified deterministically.")


def _strip_label(ans: str) -> str:
    # "f'(x) = 6x" -> "6x" ; keep expressions containing '=' only on the right
    return ans.split("=")[-1] if ans.count("=") == 1 else ans


def _check_choice(ex: Exercise, ans: str) -> VerificationResult:
    method = "Exact choice comparison"
    if ex.correct_choice is None:
        return VerificationResult(status=V.UNVERIFIABLE, method=method)
    a = ans.strip().lower().rstrip(").:")
    idx = None
    if len(a) == 1 and a.isalpha():
        idx = ord(a) - ord("a")
    elif a.isdigit():
        idx = int(a) - 1
    else:
        for i, c in enumerate(ex.choices):
            if c.strip().lower() == a or re.sub(r"^[a-e][).:]\s*", "", c.strip().lower()) == a:
                idx = i
    if idx is None or not 0 <= idx < len(ex.choices):
        return VerificationResult(status=V.PARSE_ERROR, method=method, details="Please answer with the letter of a choice (A, B, C…).")
    ok = idx == ex.correct_choice
    return VerificationResult(status=V.CORRECT if ok else V.INCORRECT, method=method,
                              details="Correct choice." if ok else "That is not the correct choice.")


def _is_math(ex: Exercise) -> bool:
    return ex.answer_type in (AnswerType.EXPRESSION, AnswerType.EQUATION_SOLUTIONS, AnswerType.NUMERIC)


class Evaluator:
    def __init__(self, router: ProviderRouter, runner: CodeRunner, params: GenerationParams):
        self.router = router
        self.runner = runner
        self.params = params

    def evaluate(self, ex: Exercise, answer: str, reasoning: str, solution_viewed: bool = False,
                 cancel: CancelToken | None = None) -> Evaluation:
        ver = deterministic_check(ex, answer, self.runner)
        steps = mv.check_steps(reasoning) if reasoning.strip() and _is_math(ex) else []
        first_bad = mv.earliest_error(steps)

        draft: EvaluationDraft | None = None
        try:
            draft = self._llm_eval(ex, answer, reasoning, ver, steps, cancel)
        except LLMError as exc:
            if type(exc).__name__ == "Cancelled":
                raise
            log.warning("LLM evaluation failed: %s", type(exc).__name__)
        ev = reconcile(ex, ver, draft, first_bad, bool(reasoning.strip()))
        ev.feedback = compose_feedback(ex, ev, reveal=solution_viewed)
        return ev

    def _llm_eval(self, ex, answer, reasoning, ver, steps, cancel) -> EvaluationDraft:
        rubric = ("Rubric:\n" + "\n".join(f"- {r}" for r in ex.rubric) + "\n") if ex.rubric else ""
        mistakes = ("Common mistakes:\n" + "\n".join(f"- {m}" for m in ex.common_mistakes) + "\n") if ex.common_mistakes else ""
        step_txt = ("Automatic step-by-step check of the student's reasoning:\n" + mv.format_step_report(steps)) if steps else ""
        expected = ex.expected_answer
        if ex.answer_type == AnswerType.MULTIPLE_CHOICE and ex.correct_choice is not None:
            expected = f"choice {chr(65 + ex.correct_choice)}: {ex.choices[ex.correct_choice]}"
        if ex.answer_type == AnswerType.CODE:
            expected = "a function passing the tests; reference:\n" + ex.reference_solution
        prompt = EVAL_PROMPT.format(
            statement=ex.statement, answer_type=ex.answer_type.value, expected=expected or "(see rubric)",
            rubric=rubric, mistakes=mistakes,
            verification=f"[{ver.status.value}] {ver.method}: {ver.details}",
            steps=step_txt, answer=answer[:4000], reasoning=reasoning[:4000] or "(none given)",
        )
        msgs = [ChatMessage("system", "You are a careful, fair examiner and tutor. Diagnose errors precisely and respectfully."),
                ChatMessage("user", prompt)]
        params = GenerationParams(temperature=0.1, top_p=self.params.top_p, max_tokens=max(700, self.params.max_tokens),
                                  num_ctx=self.params.num_ctx)
        return self.router.run(Task.EVALUATE, lambda p: generate_structured(p, msgs, EvaluationDraft, params, cancel))


def reconcile(ex: Exercise, ver: VerificationResult, d: EvaluationDraft | None, first_bad, has_reasoning: bool) -> Evaluation:
    llm_quality = ReasoningQuality(d.reasoning_quality) if d else (ReasoningQuality.NOT_SHOWN if not has_reasoning else ReasoningQuality.PARTIALLY_SOUND)
    if not has_reasoning:
        llm_quality = ReasoningQuality.NOT_SHOWN
    if first_bad is not None and llm_quality == ReasoningQuality.SOUND:
        llm_quality = ReasoningQuality.FLAWED
    cat = None
    if d and d.error_category != "none":
        cat = ErrorCategory(d.error_category)
    ev = Evaluation(
        correctness=Correctness.INSUFFICIENT_EVIDENCE, reasoning_quality=llm_quality, verification=ver,
        what_is_correct=d.what_is_correct if d else "", earliest_error=d.earliest_error if d else "",
        why_wrong=d.why_wrong if d else "", applicable_rule=d.applicable_rule if d else "",
        how_to_reconsider=d.how_to_reconsider if d else "", clarifying_question=d.clarifying_question if d else "",
        suggested_followup=d.suggested_followup if d else "",
        diagnosis_confidence=d.diagnosis_confidence if d else "low",
    )
    llm_c = Correctness(d.correctness) if d else None
    if first_bad is not None:
        ev.earliest_error = f"Step {first_bad.index + 1} (`{first_bad.text}`): {first_bad.note}" + (
            f". {ev.earliest_error}" if ev.earliest_error else "")

    if ver.status == V.CORRECT:
        ev.answer_correct = True
        if llm_quality == ReasoningQuality.FLAWED:
            ev.correctness, ev.score = Correctness.PARTIALLY_CORRECT, 0.5
            cat = ErrorCategory.RIGHT_ANSWER_BAD_REASONING
        elif llm_quality == ReasoningQuality.PARTIALLY_SOUND:
            ev.correctness, ev.score = Correctness.CORRECT, 0.85
        else:
            ev.correctness, ev.score = Correctness.CORRECT, 1.0 if llm_quality == ReasoningQuality.SOUND else 0.9
            if cat != ErrorCategory.UNCLEAR:
                cat = None
        if llm_c in (Correctness.INCORRECT,):
            ev.reconciliation_note = "The AI model judged the answer incorrect, but the automatic check confirms it; the check was used."
        ev.diagnosis_confidence = "high"
    elif ver.status == V.INCORRECT:
        ev.answer_correct = False
        ev.correctness = Correctness.INCORRECT
        ev.score = min(d.score if d else 0.0, 0.4) if llm_quality in (ReasoningQuality.SOUND, ReasoningQuality.PARTIALLY_SOUND) else 0.0
        if llm_c == Correctness.CORRECT:
            ev.reconciliation_note = "The AI model judged the answer correct, but the automatic check found it incorrect; the check was used."
        if ver.data.get("dimension_mismatch") or ver.data.get("units_missing"):
            cat = ErrorCategory.UNITS
        elif cat is None:
            cat = ErrorCategory.CALCULATION if first_bad else None
    elif ver.status == V.PARTIAL:
        ev.answer_correct = False
        ev.correctness = Correctness.PARTIALLY_CORRECT
        ev.score = float(ver.score or 0.5) * 0.8
    elif ver.status == V.PARSE_ERROR:
        ev.correctness = Correctness.INSUFFICIENT_EVIDENCE
        ev.diagnosis_confidence = "low"
        ev.clarifying_question = ev.clarifying_question or f"I couldn't read your answer automatically ({ver.details}). Could you write it in a simpler form, e.g. `x = 4` or `3*x^2 + 2`?"
        cat = ErrorCategory.SYNTAX if ex.answer_type == AnswerType.CODE else None
    else:  # UNVERIFIABLE -> rubric judgement by the model
        if d is None:
            ev.correctness = Correctness.INSUFFICIENT_EVIDENCE
            ev.clarifying_question = "I could not evaluate this answer automatically and the AI model did not respond. Please try again."
        else:
            ev.correctness = llm_c or Correctness.INSUFFICIENT_EVIDENCE
            ev.score = max(0.0, min(1.0, d.score))
            ev.answer_correct = {Correctness.CORRECT: True, Correctness.INCORRECT: False}.get(ev.correctness)
            if ev.diagnosis_confidence == "high":
                ev.diagnosis_confidence = "medium"  # no deterministic support
    if ev.correctness == Correctness.CORRECT and cat not in (None, ErrorCategory.RIGHT_ANSWER_BAD_REASONING):
        cat = None
    # Guard against over-confident diagnoses: without concrete, checkable work we cannot know
    # WHICH misconception caused a wrong answer, so ask instead of asserting one.
    if ev.correctness in (Correctness.INCORRECT, Correctness.PARTIALLY_CORRECT) and not _has_checkable_work(ex, first_bad, has_reasoning, ver):
        if ev.diagnosis_confidence == "high":
            ev.diagnosis_confidence = "low" if not has_reasoning else "medium"
        if cat in (ErrorCategory.CONCEPTUAL, ErrorCategory.FORMULA, ErrorCategory.ASSUMPTION, ErrorCategory.LOGIC, ErrorCategory.MISREAD):
            cat = None  # a specific misconception is not supported by the evidence
        # Statements about steps the student never showed are speculation - drop them.
        ev.earliest_error, ev.why_wrong = "", ""
        if not ev.clarifying_question:
            ev.clarifying_question = "Could you write out your steps, one per line? Then I can point to exactly where it goes wrong."
    ev.error_category = cat
    return ev


def _has_checkable_work(ex: Exercise, first_bad, has_reasoning: bool, ver: VerificationResult) -> bool:
    if first_bad is not None or ex.answer_type == AnswerType.CODE:
        return True  # the step checker or the test run gives concrete evidence
    if ver.data.get("dimension_mismatch") or ver.data.get("units_missing"):
        return True
    return False


def _drop_leaks(text: str, ex: Exercise) -> str:
    if not text or not leaks_answer(text, ex):
        return text
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(s for s in sentences if not leaks_answer(s, ex))


def compose_feedback(ex: Exercise, ev: Evaluation, reveal: bool = False) -> str:
    """Structured, respectful feedback built from the reconciled evaluation."""
    v = ev.verification
    out: list[str] = []
    head = {
        Correctness.CORRECT: "✅ **Correct.**",
        Correctness.PARTIALLY_CORRECT: "🟡 **Partly correct.**",
        Correctness.INCORRECT: "❌ **Not quite yet.**",
        Correctness.INSUFFICIENT_EVIDENCE: "❔ **I need a bit more information to judge this.**",
    }[ev.correctness]
    out.append(head)
    clean = (lambda t: t) if reveal or ev.correctness == Correctness.CORRECT else (lambda t: _drop_leaks(t, ex))
    if ev.what_is_correct:
        out.append("**What's right:** " + clean(ev.what_is_correct))
    if ev.correctness != Correctness.CORRECT or ev.error_category == ErrorCategory.RIGHT_ANSWER_BAD_REASONING:
        if ev.error_category == ErrorCategory.RIGHT_ANSWER_BAD_REASONING:
            out.append("**Note:** your final answer is right, but the reasoning that leads to it has a problem.")
        if ev.earliest_error:
            out.append("**Where it first goes wrong:** " + clean(ev.earliest_error))
        if ev.why_wrong and ev.why_wrong.strip() not in ev.earliest_error:
            out.append("**Why:** " + clean(ev.why_wrong))
        if ev.applicable_rule:
            out.append("**Rule to use:** " + clean(ev.applicable_rule))
        if ev.how_to_reconsider:
            out.append("**Try this:** " + clean(ev.how_to_reconsider))
    if ev.clarifying_question and ev.correctness != Correctness.CORRECT and (
            ev.diagnosis_confidence != "high" or ev.correctness == Correctness.INSUFFICIENT_EVIDENCE):
        out.append("**Question for you:** " + ev.clarifying_question)
    if ev.error_category and ev.error_category != ErrorCategory.RIGHT_ANSWER_BAD_REASONING:
        out.append(f"*Error type: {ev.error_category.label} · diagnosis confidence: {ev.diagnosis_confidence}*")
    if v:
        if v.status in (V.CORRECT, V.INCORRECT, V.PARTIAL):
            badge = f"🔎 *Checked automatically - {v.method}.*"
            if v.details and ex.answer_type == AnswerType.CODE:
                badge += "\n\n" + v.details
            elif v.details and (reveal or ev.correctness == Correctness.CORRECT or not leaks_answer(v.details, ex)):
                badge += f" {v.details}"
            out.append(badge)
        elif v.status == V.UNVERIFIABLE:
            out.append("⚠️ *Not verified deterministically - evaluated by the AI model" + (" against a rubric" if ex.rubric else "") + ". It may be mistaken.*")
    if ev.reconciliation_note:
        out.append("ℹ️ *" + ev.reconciliation_note + "*")
    return "\n\n".join(out)
