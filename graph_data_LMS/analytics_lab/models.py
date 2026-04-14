"""Typed content models shared by the curriculum, assessments and UI."""

from __future__ import annotations

from dataclasses import dataclass, field

MODULES = {
    "descriptive": "Descriptive Analytics",
    "diagnostic": "Diagnostic Analytics",
    "predictive": "Predictive Analytics",
    "prescriptive": "Prescriptive Analytics",
    "visualization": "Data Visualization",
}
MODULE_QUESTIONS = {
    "descriptive": "What happened, what is happening, and how can we summarise business performance?",
    "diagnostic": "Why did something happen, and what evidence supports the explanation?",
    "predictive": "What is likely to happen next, and how reliable is that prediction?",
    "prescriptive": "What should we do, given the evidence, constraints, risks and resources?",
    "visualization": "How can data be communicated clearly, accurately and persuasively?",
}
MODULE_TOOLS = {
    "descriptive": ["SQL", "Excel", "Power BI"],
    "diagnostic": ["Python", "R", "SQL"],
    "predictive": ["Python", "R"],
    "prescriptive": ["Python", "R"],
    "visualization": ["Matplotlib", "Tableau", "Looker Studio", "Power BI", "Excel"],
}
LEVELS = ["Beginner", "Intermediate", "Advanced", "Professional"]


@dataclass(frozen=True)
class Competency:
    id: str
    name: str
    module: str
    description: str
    requires_practical: bool = False  # mastery needs coding/project evidence, not quiz scores alone
    foundational: bool = False


@dataclass
class WorkedExample:
    language: str  # python | sql | r | text | dax | excel
    code: str
    explanation: str
    runnable: bool = True
    search_path: str | None = None
    preload: dict[str, str] = field(default_factory=dict)


@dataclass
class Lesson:
    id: str
    module: str
    level: str
    title: str
    tools: list[str]
    minutes: int
    competencies: list[str]
    objectives: list[str]
    concept: str
    business_context: str
    worked_example: WorkedExample
    knowledge_check: list[str]          # question ids
    guided_exercise: str | None         # exercise id
    challenge: str | None               # exercise id (independent, fewer hints)
    summary: list[str]
    common_mistakes: list[str] = field(default_factory=list)
    extra_examples: list[WorkedExample] = field(default_factory=list)
    tool_workshop: str | None = None    # id of a tool simulation / guided assignment
    revision: str = ""                  # what to revisit if this felt hard
    next_lesson: str | None = None
    order: int = 0


@dataclass
class Option:
    text: str
    correct: bool = False
    why: str = ""   # why this option is right / why this distractor is wrong


@dataclass
class Question:
    id: str
    module: str
    topic: str
    tool: str
    difficulty: str          # Beginner | Intermediate | Advanced | Professional
    competency: str
    qtype: str               # single | multi
    stem: str
    options: list[Option]
    explanation: str
    lesson: str | None = None
    shuffle: bool = True     # False for options like "All of the above"
    code: str | None = None  # optional code/output block shown with the stem

    @property
    def correct_keys(self) -> set[int]:
        return {i for i, o in enumerate(self.options) if o.correct}


@dataclass
class Check:
    name: str
    code: str
    hint: str = ""
    weight: float = 1.0


@dataclass
class Exercise:
    id: str
    title: str
    module: str
    language: str             # python | sql | r
    difficulty: str
    topic: str
    competencies: list[str]
    business_question: str
    dataset: str              # schema name (or "none")
    tables: list[str]         # tables shown in the schema panel, e.g. ["retail.orders"]
    requirements: list[str]
    expected_output: str
    starter_code: str
    solution: str
    explanation: str
    hints: list[str]
    # SQL grading
    order_matters: bool = False
    float_tol: float = 0.01
    # Python / R grading
    checks: list[Check] = field(default_factory=list)
    visible_tests: list[str] = field(default_factory=list)
    preload: dict[str, str] = field(default_factory=dict)
    rubric: list[tuple[str, int]] = field(default_factory=list)
    sample_output: str = ""
    lesson: str | None = None
    kind: str = "practice"    # practice | challenge | capstone | final
    search_path: str | None = None

    @property
    def schema_tables(self) -> list[str]:
        return self.tables


@dataclass
class RubricCriterion:
    name: str
    description: str
    levels: list[str]       # descriptors for 0..3
    weight: float = 1.0
    indicators: list[str] = field(default_factory=list)  # advisory keyword cues (not used for scoring)


@dataclass
class CaseObjective:
    prompt: str
    options: list[str]
    correct: list[int]
    explanation: str
    multi: bool = False


@dataclass
class BusinessCase:
    id: str
    title: str
    module: str
    competencies: list[str]
    scenario: str
    evidence_builder: str          # name of a function in assessment.cases_evidence
    objectives: list[CaseObjective]
    prompt: str
    rubric: list[RubricCriterion]
    exemplar: str


@dataclass
class Milestone:
    id: str
    title: str
    description: str
    kind: str                      # exercise | case | text | checklist
    exercise_id: str | None = None
    checklist: list[str] = field(default_factory=list)
    rubric: list[RubricCriterion] = field(default_factory=list)


@dataclass
class Capstone:
    id: str
    title: str
    modules: list[str]
    competencies: list[str]
    datasets: list[str]
    brief: str
    requirements: list[str]
    milestones: list[Milestone]
    evaluation: list[str]
    strong_example: str
    prerequisites: list[str]       # lesson ids recommended before starting
