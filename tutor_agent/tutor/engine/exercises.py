"""Exercise generation and deterministic self-validation."""

from __future__ import annotations

import logging
import re
from typing import Literal

from pydantic import BaseModel, Field

from tutor.domain import AnswerType, CodeTest, Exercise, ExerciseKind, Session, VerificationStatus
from tutor.engine.hints import leaks_answer, solution_consistent
from tutor.llm.base import CancelToken, ChatMessage, GenerationParams
from tutor.llm.router import ProviderRouter, Task
from tutor.llm.structured import generate_structured
from tutor.tools import math_verify as mv
from tutor.tools.code_runner import CodeRunner
from tutor.tools.safe_parse import MathParseError, parse_math, to_number
from tutor.tools.units import parse_quantity

log = logging.getLogger(__name__)

AnswerTypeLit = Literal["expression", "solutions", "numeric", "multiple_choice", "code", "short_text", "proof"]
KindLit = Literal[
    "conceptual", "multiple_choice", "short_answer", "calculation", "proof", "programming", "debugging",
    "statistical_interpretation", "economic_reasoning", "physics_problem", "multi_step",
]


class CodeTestDraft(BaseModel):
    call: str
    expected: str


class ExerciseDraft(BaseModel):
    """What the LLM fills in. Kept flat and simple for small local models."""
    concept: str = Field(description="the specific concept practised, 2-5 words")
    kind: KindLit
    objective: str = Field(description="learning objective, one sentence")
    statement: str = Field(description="the problem statement shown to the student (Markdown, LaTeX in $...$)")
    prerequisites: list[str] = Field(default_factory=list)
    answer_type: AnswerTypeLit
    expected_answer: str = Field("", description="final answer only, machine-checkable (see instructions)")
    equation: str = Field("", description="for answer_type 'solutions': the equation, e.g. '2*x+5=13'")
    variable: str = "x"
    unit: str = Field("", description="SI unit of a numeric answer, e.g. 'm/s', or empty")
    tolerance: float = Field(0.01, description="relative tolerance for numeric answers")
    choices: list[str] = Field(default_factory=list)
    correct_choice: int = Field(-1, description="0-based index of the correct choice, -1 if not multiple choice")
    function_name: str = ""
    code_tests: list[CodeTestDraft] = Field(default_factory=list)
    reference_solution: str = Field("", description="for code: a correct Python solution")
    starter_code: str = ""
    rubric: list[str] = Field(default_factory=list, description="criteria for open answers")
    hints: list[str] = Field(default_factory=list, description="exactly 3 progressive hints that do NOT reveal the answer")
    solution_explanation: str = Field(description="complete worked solution, step by step, ending with the final answer")
    common_mistakes: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)


GEN_INSTRUCTIONS = """Create ONE practice exercise for the student.
Subject: {subject}. Topic: {topic}. Concept: {concept}. Difficulty level {level} of 5 ({level_desc}).
{purpose}
Answer-type rules (choose the most checkable type that fits):
- "solutions": solving an equation for a variable. expected_answer = comma-separated values, e.g. "4" or "2, -3"; also fill "equation" (e.g. "x^2+x-6=0") and "variable".
- "expression": the answer is an algebraic expression, e.g. "3*x^2 + 2". Use * for multiplication and ^ for powers.
- "numeric": the answer is one number (fractions like 3/4 allowed); put the unit in "unit" (SI symbols like m/s, N, J) or leave empty.
- "multiple_choice": 3-5 "choices", "correct_choice" is the 0-based index.
- "code": write a {lang} function; give "function_name", 3-5 "code_tests" with "call" like "f(2, 3)" and "expected" as a Python literal like "5"; "reference_solution" must pass all tests; only use the standard library.
- "short_text" / "proof": give a "rubric" of 2-4 concrete criteria.
Hints: exactly 3, progressively more helpful, none may contain the final answer.
The solution_explanation must reach exactly the expected_answer.
{avoid}
Vary numbers, context and representation. Mark any invented real-world data as hypothetical."""


def _similar(a: str, b: str) -> float:
    wa, wb = set(re.findall(r"\w+", a.lower())), set(re.findall(r"\w+", b.lower()))
    return len(wa & wb) / max(1, len(wa | wb))


class ExerciseEngine:
    def __init__(self, router: ProviderRouter, runner: CodeRunner, params: GenerationParams):
        self.router = router
        self.runner = runner
        self.params = params

    # ------------------------------------------------------------ generation
    def generate(
        self,
        session: Session,
        concept: str,
        level: int,
        previous: list[Exercise],
        purpose: str = "",
        programming_language: str = "Python",
        cancel: CancelToken | None = None,
        system_prompt: str = "",
    ) -> Exercise:
        from tutor.engine.prompts import LEVELS

        avoid = ""
        if previous:
            listed = "\n".join(f"- {p.statement[:160]}" for p in previous[-5:])
            avoid = "Do NOT repeat or superficially vary these earlier exercises:\n" + listed
        prompt = GEN_INSTRUCTIONS.format(
            subject=session.subject, topic=session.topic, concept=concept or session.topic, level=level,
            level_desc=LEVELS[level].split(":")[0], purpose=purpose, lang=programming_language, avoid=avoid,
        )
        params = GenerationParams(temperature=min(1.0, self.params.temperature + 0.3), top_p=self.params.top_p,
                                  max_tokens=max(1200, self.params.max_tokens), num_ctx=self.params.num_ctx)
        msgs = [ChatMessage("system", system_prompt or "You write high-quality, correct practice exercises for students."),
                ChatMessage("user", prompt)]
        problems = ""
        last: Exercise | None = None
        for attempt in range(2):  # at most one regeneration
            if problems:
                msgs = msgs + [ChatMessage("user", "The previous exercise failed automatic checks: " + problems +
                                           " Create a corrected exercise.")]
            draft = self.router.run(Task.EXERCISE, lambda p: generate_structured(p, msgs, ExerciseDraft, params, cancel))
            ex = self.from_draft(draft, session, level)
            # Track evidence under the requested concept, not the model's paraphrase of it,
            # so one idea does not split into several "concepts" in the knowledge model.
            ex.concept = concept or session.topic
            ok, notes = self.validate(ex, previous)
            ex.validated = ok
            ex.validation_notes = " ".join(x for x in (ex.validation_notes, notes) if x)
            last = ex
            if ok:
                return ex
            problems = notes
            log.info("Exercise failed validation (attempt %d): %s", attempt + 1, notes[:200])
        assert last is not None
        return self.degrade(last)

    @staticmethod
    def from_draft(d: ExerciseDraft, session: Session, level: int) -> Exercise:
        return Exercise(
            session_id=session.id, subject=session.subject, topic=session.topic, concept=d.concept or session.topic,
            kind=ExerciseKind(d.kind), difficulty=level, objective=d.objective, statement=d.statement,
            prerequisites=d.prerequisites, answer_type=AnswerType(d.answer_type), expected_answer=d.expected_answer.strip(),
            equation=d.equation.strip(), variable=(d.variable or "x").strip() or "x", unit=d.unit.strip(),
            tolerance=min(max(d.tolerance or 0.01, 1e-9), 0.1), choices=d.choices,
            correct_choice=d.correct_choice if 0 <= d.correct_choice < len(d.choices) else None,
            function_name=d.function_name.strip(), code_tests=[CodeTest(call=t.call, expected=t.expected) for t in d.code_tests],
            reference_solution=d.reference_solution, starter_code=d.starter_code, rubric=d.rubric, hints=d.hints[:3],
            solution_explanation=d.solution_explanation, common_mistakes=d.common_mistakes, related_concepts=d.related_concepts,
            verification_method=_method_for(AnswerType(d.answer_type)),
        )

    # ------------------------------------------------------------ validation
    def validate(self, ex: Exercise, previous: list[Exercise]) -> tuple[bool, str]:
        problems: list[str] = []
        if len(ex.statement.strip()) < 15:
            problems.append("problem statement is missing or too short")
        for p in previous:
            if _similar(p.statement, ex.statement) > 0.8:
                problems.append("too similar to an earlier exercise")
                break
        t = ex.answer_type
        try:
            if t == AnswerType.EXPRESSION:
                parse_math(ex.expected_answer)
            elif t == AnswerType.NUMERIC:
                parse_quantity(f"{ex.expected_answer} {ex.unit}") if ex.unit else to_number(ex.expected_answer.split("=")[-1])
            elif t == AnswerType.EQUATION_SOLUTIONS:
                mv.parse_solution_set(ex.expected_answer, ex.variable)
                if ex.equation:
                    res = mv.verify_equation_solutions(ex.equation, ex.expected_answer, ex.variable)
                    if res.status == VerificationStatus.INCORRECT and res.data.get("solutions"):
                        # Deterministic correction: trust SymPy, not the model.
                        ex.expected_answer = ", ".join(res.data["solutions"])
                        ex.validation_notes = "Expected answer corrected by SymPy."
                        if not solution_consistent(ex):
                            problems.append("worked solution disagrees with the SymPy-verified answer")
        except MathParseError as exc:
            problems.append(f"expected answer is not machine-readable ({exc})")
        if t == AnswerType.MULTIPLE_CHOICE and (len(ex.choices) < 2 or ex.correct_choice is None):
            problems.append("multiple-choice question needs >= 2 choices and a valid correct_choice")
        if t == AnswerType.CODE:
            if not ex.function_name or len(ex.code_tests) < 2:
                problems.append("code exercise needs a function_name and at least 2 tests")
            elif not ex.reference_solution.strip():
                problems.append("code exercise needs a reference solution")
            else:
                vr, _ = self.runner.verify(ex.reference_solution, ex.code_tests)
                if vr.status != VerificationStatus.CORRECT:
                    problems.append("reference solution fails its own tests: " + vr.details.splitlines()[0])
        if t in (AnswerType.SHORT_TEXT, AnswerType.PROOF) and not ex.rubric:
            problems.append("open question needs a rubric")
        leaking = [i + 1 for i, h in enumerate(ex.hints) if leaks_answer(h, ex)]
        if leaking:
            ex.hints = [h for i, h in enumerate(ex.hints) if i + 1 not in leaking]
        if t in (AnswerType.EXPRESSION, AnswerType.NUMERIC, AnswerType.EQUATION_SOLUTIONS) and not solution_consistent(ex):
            # Textual check only - note it but do not reject (solutions may format numbers differently).
            ex.validation_notes = (ex.validation_notes + " Worked solution may not state the final answer verbatim.").strip()
        return not problems, "; ".join(problems)

    @staticmethod
    def degrade(ex: Exercise) -> Exercise:
        """After failed validation: keep the exercise but never claim deterministic checking."""
        if ex.answer_type in (AnswerType.EXPRESSION, AnswerType.NUMERIC, AnswerType.EQUATION_SOLUTIONS, AnswerType.CODE):
            ex.answer_type = AnswerType.SHORT_TEXT
            if not ex.rubric:
                ex.rubric = ["Final answer matches the worked solution", "Reasoning is shown and valid"]
        ex.verification_method = "AI judgement with rubric (automatic checks failed: " + ex.validation_notes + ")"
        ex.validated = False
        return ex


def _method_for(t: AnswerType) -> str:
    return {
        AnswerType.EXPRESSION: "SymPy symbolic equivalence",
        AnswerType.EQUATION_SOLUTIONS: "SymPy solution-set comparison",
        AnswerType.NUMERIC: "Numeric comparison with tolerance (unit-aware)",
        AnswerType.MULTIPLE_CHOICE: "Exact choice comparison",
        AnswerType.CODE: "Sandboxed execution against test cases",
        AnswerType.SHORT_TEXT: "AI judgement with explicit rubric",
        AnswerType.PROOF: "AI judgement with explicit rubric",
    }[t]
