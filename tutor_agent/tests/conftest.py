from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from tutor.app import AppContext  # noqa: E402
from tutor.config import AppConfig, OperatingMode  # noqa: E402
from tutor.llm.mock import MockProvider  # noqa: E402
from tutor.llm.router import ProviderRouter  # noqa: E402


LINEAR_EXERCISE = {
    "concept": "solving linear equations",
    "kind": "calculation",
    "objective": "Isolate the variable in a two-step linear equation.",
    "statement": "Solve for $x$: $3x - 7 = 11$.",
    "prerequisites": ["inverse operations"],
    "answer_type": "solutions",
    "expected_answer": "6",
    "equation": "3*x - 7 = 11",
    "variable": "x",
    "unit": "",
    "tolerance": 0.01,
    "choices": [],
    "correct_choice": -1,
    "function_name": "",
    "code_tests": [],
    "reference_solution": "",
    "starter_code": "",
    "rubric": [],
    "hints": [
        "What operation would undo the '- 7' on the left-hand side?",
        "Whatever you do to one side of an equation you must do to the other side.",
        "Add 7 to both sides first, then deal with the coefficient 3.",
    ],
    "solution_explanation": "Add 7 to both sides: 3x = 18.\nDivide both sides by 3.\nSo x = 6.",
    "common_mistakes": ["subtracting 7 instead of adding", "dividing only one side"],
    "related_concepts": ["balance method"],
}

EVAL_SIGN_ERROR = {
    "correctness": "incorrect",
    "reasoning_quality": "flawed",
    "score": 0.3,
    "error_category": "sign_or_arithmetic_error",
    "what_is_correct": "You correctly started by trying to remove the constant term.",
    "earliest_error": "When moving -7 to the right-hand side you subtracted 7 instead of adding it.",
    "why_wrong": "To undo subtracting 7 you must add 7 to both sides.",
    "applicable_rule": "Inverse operations keep both sides balanced.",
    "how_to_reconsider": "What do you get on the right-hand side if you add 7 to both sides?",
    "diagnosis_confidence": "high",
    "clarifying_question": "",
    "suggested_followup": "Try 2x - 5 = 9.",
}

EVAL_CORRECT = {
    "correctness": "correct", "reasoning_quality": "sound", "score": 1.0, "error_category": "none",
    "what_is_correct": "All steps are valid.", "earliest_error": "", "why_wrong": "", "applicable_rule": "",
    "how_to_reconsider": "", "diagnosis_confidence": "high", "clarifying_question": "", "suggested_followup": "",
}

SUMMARY = {
    "key_concepts": ["solving linear equations"],
    "strengths": ["isolating the variable"],
    "misconceptions": ["sign when moving terms across"],
    "next_steps": ["practise equations with negative constants"],
    "practice_task": "Solve 5 - 2x = 11.",
}


def schema_title(schema) -> str:
    return (schema or {}).get("title", "")


class ScriptedLLM:
    """Responder that answers based on the requested schema; records the prompts."""

    def __init__(self):
        self.exercises = [dict(LINEAR_EXERCISE)]
        self.evaluations: list[dict] = []
        self.chat_replies: list[str] = []
        self.prompts: list[list] = []

    def __call__(self, messages, schema):
        self.prompts.append(messages)
        title = schema_title(schema)
        if title == "ExerciseDraft":
            return json.dumps(self.exercises.pop(0) if len(self.exercises) > 1 else self.exercises[0])
        if title == "EvaluationDraft":
            return json.dumps(self.evaluations.pop(0) if self.evaluations else EVAL_CORRECT)
        if title == "SummaryDraft":
            return json.dumps(SUMMARY)
        if self.chat_replies:
            return self.chat_replies.pop(0)
        return "Let's explore this together. What do you already know about this topic?"


@pytest.fixture
def scripted():
    return ScriptedLLM()


@pytest.fixture
def ctx(tmp_path, scripted):
    cfg = AppConfig(mode=OperatingMode.LOCAL)
    local = MockProvider(responder=scripted, is_local=True)
    router = ProviderRouter(cfg, local, None)
    c = AppContext(root=tmp_path / "data dir ünicode", router=router, configure_logging=False)
    c.cfg.mode = OperatingMode.LOCAL
    c.engine.reload_config(c.cfg)
    yield c
    c.db.close()
