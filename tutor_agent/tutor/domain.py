"""Pydantic domain models shared by all modules."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str = "") -> str:
    return prefix + uuid.uuid4().hex[:12]


# ---------------------------------------------------------------- enumerations

SUBJECTS = [
    "Mathematics",
    "Programming",
    "Statistics & Probability",
    "Economics & Finance",
    "Physics",
    "Other",
]


class TeachingStyle(str, Enum):
    BALANCED = "balanced"            # default: short explanation + guided questions + practice
    GUIDED_DISCOVERY = "guided_discovery"
    DIRECT = "direct"
    WORKED_EXAMPLES = "worked_examples"
    PRACTICE_FIRST = "practice_first"
    DEBUGGING = "debugging"
    EXAM_PREP = "exam_prep"

    @property
    def label(self) -> str:
        return {
            "balanced": "Balanced (recommended)",
            "guided_discovery": "Guided discovery",
            "direct": "Direct explanation",
            "worked_examples": "Worked examples",
            "practice_first": "Practice-first",
            "debugging": "Debugging & error analysis",
            "exam_prep": "Exam preparation",
        }[self.value]


LEVEL_NAMES = {1: "Beginner", 2: "Basic", 3: "Intermediate", 4: "Advanced", 5: "Expert"}


class MasteryState(str, Enum):
    NOT_ASSESSED = "not_assessed"
    INTRODUCED = "introduced"
    DEVELOPING = "developing"
    DEMONSTRATED = "demonstrated"
    NEEDS_REVISION = "needs_revision"

    @property
    def label(self) -> str:
        return {
            "not_assessed": "Not assessed",
            "introduced": "Introduced",
            "developing": "Developing",
            "demonstrated": "Demonstrated understanding",
            "needs_revision": "Needs revision",
        }[self.value]


class ErrorCategory(str, Enum):
    CONCEPTUAL = "conceptual_misunderstanding"
    ASSUMPTION = "incorrect_assumption"
    CALCULATION = "calculation_error"
    SIGN_ARITHMETIC = "sign_or_arithmetic_error"
    FORMULA = "incorrect_formula_selection"
    MISSING_STEP = "missing_intermediate_step"
    LOGIC = "logical_inconsistency"
    MISREAD = "misinterpreted_question"
    SYNTAX = "syntax_error"
    PROGRAM_LOGIC = "programming_logic_error"
    STATS_TERMS = "misuse_of_statistical_terminology"
    UNITS = "incorrect_units_or_dimensions"
    RIGHT_ANSWER_BAD_REASONING = "correct_answer_invalid_reasoning"
    UNCLEAR = "unclear_or_incomplete_explanation"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").capitalize()


class AnswerType(str, Enum):
    EXPRESSION = "expression"          # algebraic expression, checked by SymPy equivalence
    EQUATION_SOLUTIONS = "solutions"   # set of values for a variable
    NUMERIC = "numeric"                # number, optional unit, tolerance
    MULTIPLE_CHOICE = "multiple_choice"
    CODE = "code"                      # Python function checked with test cases
    SHORT_TEXT = "short_text"          # rubric-based
    PROOF = "proof"                    # rubric-based


class ExerciseKind(str, Enum):
    CONCEPTUAL = "conceptual"
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    CALCULATION = "calculation"
    PROOF = "proof"
    PROGRAMMING = "programming"
    DEBUGGING = "debugging"
    STATISTICAL = "statistical_interpretation"
    ECONOMIC = "economic_reasoning"
    PHYSICS = "physics_problem"
    MULTI_STEP = "multi_step"


# ---------------------------------------------------------------- profile

class LearningPreferences(BaseModel):
    explanation_length: Literal["short", "medium", "long"] = "medium"
    modality: Literal["visual", "verbal", "mixed"] = "mixed"
    examples_first: bool = False
    rigor: Literal["informal", "standard", "rigorous"] = "standard"
    programming_language: str = "Python"
    prefers_hints: bool = True  # hints vs. direct explanations


class Accessibility(BaseModel):
    font_size: int = 11
    high_contrast: bool = False
    reduce_animation: bool = False


class StudentProfile(BaseModel):
    name: str = ""
    academic_level: str = "University (undergraduate)"
    subjects: list[str] = Field(default_factory=list)
    teaching_style: TeachingStyle = TeachingStyle.BALANCED
    default_level: int = Field(3, ge=1, le=5)
    preferences: LearningPreferences = Field(default_factory=LearningPreferences)
    accessibility: Accessibility = Field(default_factory=Accessibility)
    goals: str = ""


# ---------------------------------------------------------------- session

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class MessageKind(str, Enum):
    CHAT = "chat"
    HINT = "hint"
    FEEDBACK = "feedback"
    SOLUTION = "solution"
    EXERCISE = "exercise"
    NOTICE = "notice"        # system notices (model switch, level change...)
    SUMMARY = "summary"
    VISUAL = "visual"


class Message(BaseModel):
    id: str = Field(default_factory=lambda: new_id("m_"))
    session_id: str
    role: Role
    content: str
    kind: MessageKind = MessageKind.CHAT
    meta: dict[str, Any] = Field(default_factory=dict)
    created: datetime = Field(default_factory=now_utc)


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class Session(BaseModel):
    id: str = Field(default_factory=lambda: new_id("s_"))
    subject: str
    topic: str
    goal: str = ""
    level: int = Field(3, ge=1, le=5)
    level_locked: bool = False          # student overrode the level
    style: TeachingStyle = TeachingStyle.BALANCED
    socratic: bool = True
    use_materials: bool = True
    status: SessionStatus = SessionStatus.ACTIVE
    running_summary: str = ""           # summary of older, trimmed conversation
    summarized_count: int = 0           # how many leading context messages running_summary covers
    explanation_strategies: list[str] = Field(default_factory=list)
    active_exercise_id: str | None = None
    hint_levels: dict[str, int] = Field(default_factory=dict)       # exercise id -> highest hint level shown
    solutions_viewed: list[str] = Field(default_factory=list)      # exercise ids
    level_changed_at: datetime | None = None
    current_concept: str = ""
    summary: "SessionSummary | None" = None
    created: datetime = Field(default_factory=now_utc)
    updated: datetime = Field(default_factory=now_utc)


# ---------------------------------------------------------------- exercises

class CodeTest(BaseModel):
    call: str            # e.g. "add(2, 3)"
    expected: str        # Python literal, e.g. "5"


class Exercise(BaseModel):
    id: str = Field(default_factory=lambda: new_id("ex_"))
    session_id: str = ""
    subject: str
    topic: str
    concept: str
    kind: ExerciseKind = ExerciseKind.SHORT_ANSWER
    difficulty: int = Field(3, ge=1, le=5)
    objective: str = ""
    statement: str
    prerequisites: list[str] = Field(default_factory=list)
    answer_type: AnswerType = AnswerType.SHORT_TEXT
    expected_answer: str = ""
    equation: str = ""             # equation being solved (for SymPy validation of 'solutions')
    variable: str = "x"
    tolerance: float = 1e-6        # relative tolerance for numeric answers
    unit: str = ""
    choices: list[str] = Field(default_factory=list)
    correct_choice: int | None = None
    function_name: str = ""
    code_tests: list[CodeTest] = Field(default_factory=list)
    reference_solution: str = ""
    starter_code: str = ""
    rubric: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    solution_explanation: str = ""
    verification_method: str = ""
    common_mistakes: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)
    validated: bool = False           # passed deterministic self-check
    validation_notes: str = ""
    created: datetime = Field(default_factory=now_utc)

    @field_validator("difficulty", mode="before")
    @classmethod
    def _clamp(cls, v: Any) -> int:
        try:
            return max(1, min(5, int(v)))
        except (TypeError, ValueError):
            return 3


class VerificationStatus(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"
    UNVERIFIABLE = "unverifiable"   # no deterministic method applies
    PARSE_ERROR = "parse_error"     # student input could not be interpreted


class VerificationResult(BaseModel):
    status: VerificationStatus
    method: str                      # human-readable, e.g. "SymPy symbolic equivalence"
    details: str = ""
    score: float | None = None       # e.g. fraction of tests passed
    data: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_deterministic(self) -> bool:
        return self.status not in (VerificationStatus.UNVERIFIABLE,)


class Correctness(str, Enum):
    CORRECT = "correct"
    PARTIALLY_CORRECT = "partially_correct"
    INCORRECT = "incorrect"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ReasoningQuality(str, Enum):
    SOUND = "sound"
    PARTIALLY_SOUND = "partially_sound"
    FLAWED = "flawed"
    NOT_SHOWN = "not_shown"


class Evaluation(BaseModel):
    """Final, reconciled evaluation of one student attempt."""
    correctness: Correctness
    answer_correct: bool | None = None
    reasoning_quality: ReasoningQuality = ReasoningQuality.NOT_SHOWN
    score: float = Field(0.0, ge=0.0, le=1.0)
    error_category: ErrorCategory | None = None
    what_is_correct: str = ""
    earliest_error: str = ""
    why_wrong: str = ""
    applicable_rule: str = ""
    how_to_reconsider: str = ""
    diagnosis_confidence: Literal["low", "medium", "high"] = "medium"
    clarifying_question: str = ""
    feedback: str = ""
    suggested_followup: str = ""
    verification: VerificationResult | None = None
    reconciliation_note: str = ""


class Attempt(BaseModel):
    id: str = Field(default_factory=lambda: new_id("a_"))
    exercise_id: str
    session_id: str
    answer: str
    reasoning: str = ""
    hints_used: int = 0
    solution_viewed: bool = False
    evaluation: Evaluation | None = None
    created: datetime = Field(default_factory=now_utc)


# ---------------------------------------------------------------- knowledge

class EvidenceKind(str, Enum):
    INTRODUCED = "introduced"          # concept was explained
    ATTEMPT = "attempt"                # exercise attempt
    EXPLANATION = "explanation"        # student explained the concept in own words
    SELF_REPORT = "self_report"        # student-stated confidence


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: new_id("e_"))
    subject: str
    topic: str
    concept: str
    kind: EvidenceKind
    correct: bool | None = None
    score: float | None = None
    difficulty: int = 3
    assistance: int = 0            # 0 = none, number of hints; 5 = full solution viewed
    error_category: ErrorCategory | None = None
    exercise_kind: str = ""
    exercise_id: str = ""
    session_id: str = ""
    confidence: int | None = None  # self-reported 1-5
    note: str = ""
    created: datetime = Field(default_factory=now_utc)


class ConceptStatus(BaseModel):
    subject: str
    topic: str
    concept: str
    state: MasteryState
    evidence_count: int
    attempts: int
    independent_successes: int
    recent_success_rate: float | None
    certainty: Literal["none", "low", "medium", "high"]
    rationale: str
    recurring_errors: list[ErrorCategory] = Field(default_factory=list)
    overridden: bool = False
    override_note: str = ""
    last_seen: datetime | None = None


# ---------------------------------------------------------------- summaries

class SessionSummary(BaseModel):
    key_concepts: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    practice_task: str = ""
    tasks_attempted: int = 0
    tasks_correct: int = 0
    common_errors: list[str] = Field(default_factory=list)
    text: str = ""


Session.model_rebuild()
