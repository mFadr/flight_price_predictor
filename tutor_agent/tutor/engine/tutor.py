"""The tutoring engine: pedagogical orchestration, independent of UI and LLM provider.

All public methods are synchronous and meant to run in a worker thread. They
persist every message immediately, so an interrupted session can be resumed.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from tutor.config import AppConfig, QualityPreset
from tutor.domain import (
    LEVEL_NAMES,
    AnswerType,
    Attempt,
    Correctness,
    Evaluation,
    Evidence,
    EvidenceKind,
    Exercise,
    Message,
    MessageKind,
    Role,
    Session,
    SessionSummary,
    StudentProfile,
    TeachingStyle,
)
from tutor.engine import difficulty, prompts
from tutor.engine.evaluator import Evaluator
from tutor.engine.exercises import ExerciseEngine
from tutor.engine.hints import HINT_LEVELS, MAX_LEVEL, leaks_answer, stored_hint
from tutor.engine.knowledge import KnowledgeModel
from tutor.llm.base import Cancelled, CancelToken, ChatMessage, GenerationParams, LLMError
from tutor.llm.router import ProviderRouter, Task
from tutor.llm.structured import generate_structured
from tutor.materials.library import MaterialLibrary
from tutor.storage.db import Database
from tutor.tools import math_verify as mv
from tutor.tools.code_runner import CodeRunner
from tutor.tools.viz import RenderedViz, VisualizationSpec, VizRenderer, extract_viz_blocks, safe_render

log = logging.getLogger(__name__)
ChunkFn = Callable[[str], None]

_WANTS_SOLUTION = re.compile(
    r"\b(full|complete|whole|worked)\s+(solution|answer|example)|show (me )?the (answer|solution)|just tell me|give me the (answer|solution)",
    re.I)
_FRUSTRATED = re.compile(r"frustrat|i give up|so confus|makes no sense|i (still )?don'?t get (it|this)|hate this|this is (too )?hard|annoy|stupid", re.I)
_WANTS_DIRECT = re.compile(r"just explain|explain (it )?directly|no (more )?questions|stop asking", re.I)
_QUESTION_START = re.compile(r"^\s*(how|why|what|when|where|which|who|can|could|would|should|is|are|do|does|explain|i don'?t|i do not|help|hint|wait)\b", re.I)


def params_from_config(cfg: AppConfig) -> GenerationParams:
    g = cfg.generation
    length = {"short": 450, "medium": 900, "long": 1600}.get(g.response_length, 900)
    max_tokens = min(g.max_response_tokens, length) if g.max_response_tokens else length
    # The preset changes answer length and prompt size, never num_ctx (that would force a model reload).
    if g.quality == QualityPreset.FAST:
        max_tokens = min(max_tokens, 600)
    elif g.quality == QualityPreset.QUALITY:
        max_tokens = max(max_tokens, 1200)
    return GenerationParams(temperature=g.temperature, top_p=g.top_p, max_tokens=max_tokens, num_ctx=cfg.ollama.num_ctx)


class SummaryDraft(BaseModel):
    key_concepts: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list, description="only strengths actually demonstrated")
    misconceptions: list[str] = Field(default_factory=list, description="mistakes or misconceptions that remain")
    next_steps: list[str] = Field(default_factory=list)
    practice_task: str = ""


@dataclass
class TurnResult:
    messages: list[Message] = field(default_factory=list)
    exercise: Exercise | None = None
    attempt: Attempt | None = None
    evaluation: Evaluation | None = None
    visuals: list[RenderedViz] = field(default_factory=list)
    summary: SessionSummary | None = None
    level_changed: bool = False


def looks_like_answer(text: str) -> bool:
    t = text.strip()
    if not t or len(t) > 1500:
        return False
    if t.endswith("?") or _QUESTION_START.match(t):
        return False
    return True


def split_answer(text: str) -> tuple[str, str]:
    """'reasoning ... \\n answer: x = 4' -> ('x = 4', full text)."""
    m = re.search(r"(?:final answer|answer)\s*[:=]\s*(.+)$", text, re.I | re.M)
    if m:
        return m.group(1).strip(), text.strip()
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) > 1:
        return lines[-1].strip(), text.strip()
    steps = mv.split_steps(text)
    if len(steps) > 1:
        return steps[-1], text.strip()
    return text.strip(), ""


class TutorEngine:
    def __init__(
        self,
        db: Database,
        router: ProviderRouter,
        cfg: AppConfig,
        runner: CodeRunner,
        renderer: VizRenderer,
        library: MaterialLibrary | None = None,
    ):
        self.db = db
        self.router = router
        self.cfg = cfg
        self.runner = runner
        self.renderer = renderer
        self.library = library
        self.knowledge = KnowledgeModel(db)
        self._pending_notices: list[str] = []
        self.router.notify = self._on_router_notice
        self.reload_config(cfg)

    def reload_config(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.router.cfg = cfg
        self.params = params_from_config(cfg)
        self.exercises = ExerciseEngine(self.router, self.runner, self.params)
        self.evaluator = Evaluator(self.router, self.runner, self.params)

    # ================================================================ helpers
    def _on_router_notice(self, msg: str) -> None:
        self._pending_notices.append(msg)

    def profile(self) -> StudentProfile:
        return self.db.load_profile()

    def _add(self, session: Session, role: Role, content: str, kind: MessageKind = MessageKind.CHAT, **meta) -> Message:
        m = Message(session_id=session.id, role=role, content=content, kind=kind, meta=meta)
        self.db.add_message(m)
        return m

    def _flush_notices(self, session: Session, result: TurnResult) -> None:
        while self._pending_notices:
            result.messages.append(self._add(session, Role.SYSTEM, self._pending_notices.pop(0), MessageKind.NOTICE))

    def active_exercise(self, session: Session) -> Exercise | None:
        return self.db.get_exercise(session.active_exercise_id) if session.active_exercise_id else None

    def _materials(self, session: Session, query: str) -> list[dict]:
        if not (session.use_materials and self.library):
            return []
        return self.library.search(f"{session.topic} {query}", session.subject)

    def _previous_summary(self, session: Session) -> str:
        prev = self.db.last_session_for(session.subject, session.topic, exclude_id=session.id)
        if prev and prev.summary:
            s = prev.summary
            bits = []
            if s.strengths:
                bits.append("understood: " + "; ".join(s.strengths[:3]))
            if s.misconceptions:
                bits.append("difficulties: " + "; ".join(s.misconceptions[:3]))
            if s.next_steps:
                bits.append("planned next: " + "; ".join(s.next_steps[:2]))
            return f"({prev.created:%Y-%m-%d}) " + " | ".join(bits)
        return ""

    def _system(self, session: Session, include_viz: bool = True) -> str:
        brief = self.knowledge.topic_brief(session.subject, session.topic)
        if self.router.transmits_externally() and not self.cfg.privacy.send_learning_history_to_cloud:
            brief = ""  # minimise data sent to the cloud
        if self.cfg.generation.quality == QualityPreset.FAST:
            include_viz = False  # shorter prompt for slow hardware
        return prompts.build_system_prompt(session, self.profile(), brief, self._previous_summary(session), include_viz)

    def _history(self, session: Session, cancel: CancelToken, drop_last_user: bool = False) -> list[ChatMessage]:
        """Conversation context within the character budget; older parts are summarised.

        ``drop_last_user``: the newest user message is already persisted (crash safety) but is
        re-sent as the explicit instruction, so leave it out here to avoid duplication.
        """
        msgs = [m for m in self.db.messages(session.id) if m.kind not in (MessageKind.NOTICE, MessageKind.VISUAL)]
        msgs = msgs[session.summarized_count:]
        if drop_last_user and msgs and msgs[-1].role == Role.USER:
            msgs = msgs[:-1]
        budget = self.cfg.context_char_budget
        if sum(len(m.content) for m in msgs) > budget and len(msgs) > 6:
            cut = len(msgs) // 2
            self._compress(session, msgs[:cut], cancel)
            msgs = msgs[cut:]
        out = []
        for m in msgs:
            role = "user" if m.role == Role.USER else "assistant"
            content = m.content if len(m.content) < budget // 3 else m.content[: budget // 3] + " …[truncated]"
            if out and out[-1].role == role:  # merge consecutive same-role turns
                out[-1] = ChatMessage(role, out[-1].content + "\n\n" + content)
            else:
                out.append(ChatMessage(role, content))
        return out

    def _compress(self, session: Session, old: list[Message], cancel: CancelToken) -> None:
        text = "\n".join(f"{m.role.value}: {m.content[:600]}" for m in old)
        if session.running_summary:
            text = "Earlier summary: " + session.running_summary + "\n" + text
        try:
            summary = self.router.run(Task.SUMMARY, lambda p: p.chat(
                [ChatMessage("user", prompts.COMPRESS.format(text=text[:8000]))],
                GenerationParams(temperature=0.2, max_tokens=250, num_ctx=self.params.num_ctx), cancel))
        except Cancelled:
            raise
        except LLMError:
            summary = " / ".join(m.content[:120] for m in old[-6:])  # degrade gracefully
        session.running_summary = summary.strip()[:1500]
        session.summarized_count += len(old)
        self.db.save_session(session)

    def _stream(self, session: Session, task: str, messages: list[ChatMessage], on_chunk: ChunkFn | None,
                cancel: CancelToken, params: GenerationParams | None = None) -> str:
        parts: list[str] = []
        try:
            for chunk in self.router.stream(task, messages, params or self.params, cancel):
                parts.append(chunk)
                if on_chunk:
                    on_chunk(chunk)
        except Cancelled:
            partial = "".join(parts).strip()
            if partial:  # preserve partial output safely
                self._add(session, Role.ASSISTANT, partial + "\n\n*[response cancelled]*")
            raise
        return "".join(parts)

    def _finish_assistant(self, session: Session, text: str, result: TurnResult, kind: MessageKind = MessageKind.CHAT,
                          **meta) -> None:
        cleaned, specs, errors = extract_viz_blocks(text)
        result.messages.append(self._add(session, Role.ASSISTANT, cleaned or "…", kind, **meta))
        for spec in specs:
            self._add_visual(session, spec, result)
        if errors:
            log.info("Ignored %d invalid visualisation spec(s)", len(errors))

    def _add_visual(self, session: Session, spec: VisualizationSpec, result: TurnResult) -> RenderedViz | None:
        viz, err = safe_render(self.renderer, spec)
        if viz is None:
            log.info("Visualisation failed: %s", err)
            result.messages.append(self._add(session, Role.SYSTEM, f"A diagram could not be drawn ({err}).", MessageKind.NOTICE))
            return None
        result.visuals.append(viz)
        result.messages.append(self._add(
            session, Role.ASSISTANT, viz.caption, MessageKind.VISUAL,
            path=viz.path, caption=viz.caption, elements=viz.elements, spec=spec.model_dump(exclude_defaults=True),
        ))
        return viz

    def _turn(self, session: Session, user_instruction: str, on_chunk: ChunkFn | None, cancel: CancelToken,
              result: TurnResult, query: str = "", kind: MessageKind = MessageKind.CHAT, task: str = Task.EXPLAIN,
              **meta) -> str:
        msgs = [ChatMessage("system", self._system(session))] + self._history(session, cancel, drop_last_user=True)
        mats = prompts.materials_block(self._materials(session, query)) if query else ""
        msgs.append(ChatMessage("user", user_instruction + ("\n\n" + mats if mats else "")))
        text = self._stream(session, task, msgs, on_chunk, cancel)
        self._finish_assistant(session, text, result, kind, **meta)
        self._flush_notices(session, result)
        return text

    # ================================================================ session lifecycle
    def start_session(self, subject: str, topic: str, goal: str = "", level: int | None = None,
                      style: TeachingStyle | None = None, socratic: bool = True, use_materials: bool = True) -> Session:
        prof = self.profile()
        s = Session(subject=subject, topic=topic.strip() or subject, goal=goal.strip(),
                    level=level or prof.default_level, style=style or prof.teaching_style, socratic=socratic,
                    use_materials=use_materials, current_concept=topic.strip())
        self.db.save_session(s)
        return s

    def opening(self, session: Session, on_chunk: ChunkFn | None = None, cancel: CancelToken | None = None) -> TurnResult:
        cancel = cancel or CancelToken()
        result = TurnResult()
        prev = self._previous_summary(session)
        continuity = (
            "There is a summary of a previous session on this topic in the system prompt: open with ONE sentence recalling it "
            "(e.g. what was understood and what was difficult) and suggest continuing from there."
            if prev else "This is the student's first session on this topic."
        )
        self._turn(session, prompts.OPENING.format(continuity=continuity) + "\n(Instruction from the app, not from the student.)",
                   on_chunk, cancel, result, query=session.goal)
        self.knowledge.record_introduced(session.subject, session.topic, session.current_concept or session.topic, session.id)
        return result

    def end_session(self, session: Session, cancel: CancelToken | None = None) -> TurnResult:
        cancel = cancel or CancelToken()
        result = TurnResult()
        attempts = self.db.attempts_for_session(session.id)
        evaluated = [a for a in attempts if a.evaluation]
        correct = sum(1 for a in evaluated if a.evaluation.correctness == Correctness.CORRECT)  # type: ignore[union-attr]
        errors = Counter(a.evaluation.error_category.label for a in evaluated if a.evaluation and a.evaluation.error_category)
        exercises = self.db.exercises_for_session(session.id)
        concepts = sorted({e.concept for e in exercises} | {session.topic})
        hints = sum(session.hint_levels.values())
        facts = (f"topic {session.topic}; exercises attempted {len({a.exercise_id for a in attempts})}, attempts {len(attempts)}, "
                 f"fully correct {correct}; hints used {hints}; worked solutions viewed {len(session.solutions_viewed)}; "
                 f"error types: {dict(errors) or 'none'}; concepts: {', '.join(concepts)}")
        statuses = [self.knowledge.status(session.subject, session.topic, c) for c in concepts]
        status_txt = "; ".join(f"{s.concept}: {s.state.label}" for s in statuses)
        draft: SummaryDraft | None = None
        try:
            msgs = [ChatMessage("system", self._system(session, include_viz=False))] + self._history(session, cancel)
            msgs.append(ChatMessage("user", prompts.SUMMARY.format(facts=facts + "; evidence-based states: " + status_txt)))
            draft = self.router.run(Task.SUMMARY, lambda p: generate_structured(
                p, msgs, SummaryDraft, GenerationParams(temperature=0.2, max_tokens=700, num_ctx=self.params.num_ctx), cancel))
        except Cancelled:
            raise
        except LLMError as exc:
            log.warning("Summary generation failed: %s", type(exc).__name__)
        summary = SessionSummary(
            key_concepts=(draft.key_concepts if draft else concepts)[:6],
            strengths=(draft.strengths if draft else [])[:5],
            misconceptions=(draft.misconceptions if draft else [k for k in errors])[:5],
            next_steps=(draft.next_steps if draft else [f"Practise {session.topic} with new problems"])[:4],
            practice_task=draft.practice_task if draft else "",
            tasks_attempted=len({a.exercise_id for a in attempts}), tasks_correct=correct,
            common_errors=[f"{k} (×{v})" for k, v in errors.most_common(4)],
        )
        summary.text = self._summary_markdown(summary, statuses)
        self.db.save_summary(session, summary)
        result.summary = summary
        result.messages.append(self._add(session, Role.ASSISTANT, summary.text, MessageKind.SUMMARY))
        self._flush_notices(session, result)
        return result

    @staticmethod
    def _summary_markdown(s: SessionSummary, statuses) -> str:
        out = ["## Session summary"]
        for title, items in (("Key concepts", s.key_concepts), ("Strengths you demonstrated", s.strengths),
                             ("Still to work on", s.misconceptions), ("Recommended next steps", s.next_steps)):
            if items:
                out.append(f"**{title}**\n" + "\n".join(f"- {i}" for i in items))
        out.append(f"**Exercises:** {s.tasks_attempted} attempted, {s.tasks_correct} answered fully correctly."
                   + (f" Common errors: {', '.join(s.common_errors)}." if s.common_errors else ""))
        if statuses:
            out.append("**Evidence-based status:** " + "; ".join(f"{x.concept} - {x.state.label} (certainty {x.certainty})" for x in statuses))
        out.append("*Completing exercises is not the same as mastery - the status above reflects how much evidence there is.*")
        if s.practice_task:
            out.append("**Practice task for next time:** " + s.practice_task)
        return "\n\n".join(out)

    # ================================================================ conversation
    def respond(self, session: Session, text: str, on_chunk: ChunkFn | None = None,
                cancel: CancelToken | None = None) -> TurnResult:
        cancel = cancel or CancelToken()
        ex = self.active_exercise(session)
        if ex and looks_like_answer(text) and not _WANTS_SOLUTION.search(text):
            answer, reasoning = split_answer(text)
            return self.submit_answer(session, answer, reasoning, cancel=cancel, raw_text=text)

        result = TurnResult()
        result.messages.append(self._add(session, Role.USER, text))
        notes = []
        if _WANTS_SOLUTION.search(text):
            if ex:
                return self._merge(result, self.worked_solution(session, on_chunk, cancel, record_user=False))
            notes.append("The student explicitly asked for a complete explanation / worked example: give it fully and directly, "
                         "then offer a similar problem to try.")
        if _FRUSTRATED.search(text):
            notes.append("The student sounds frustrated: be encouraging, switch to a clear, direct explanation with a small "
                         "concrete example; do not ask a chain of questions.")
        elif _WANTS_DIRECT.search(text):
            notes.append("The student asked for a direct explanation without Socratic questioning for now.")
        if ex:
            notes.append(f"There is an active exercise (do not reveal its answer unless asked for the solution): {ex.statement[:600]}")
        instruction = text if not notes else f"{text}\n\n[App note to tutor - not written by the student: {' '.join(notes)}]"
        self._turn(session, instruction, on_chunk, cancel, result, query=text)
        return result

    @staticmethod
    def _merge(a: TurnResult, b: TurnResult) -> TurnResult:
        b.messages = a.messages + b.messages
        return b

    # ================================================================ exercises
    def new_exercise(self, session: Session, mode: str = "similar", cancel: CancelToken | None = None,
                     concept: str | None = None) -> TurnResult:
        """mode: 'first' | 'similar' | 'easier' | 'harder'."""
        cancel = cancel or CancelToken()
        result = TurnResult()
        if mode in ("easier", "harder"):
            new_level = max(1, min(5, session.level + (1 if mode == "harder" else -1)))
            if new_level != session.level:
                self._set_level(session, new_level, f"you asked for a {mode} problem", result, by_user=True)
        previous = self.db.exercises_for_session(session.id)
        purpose = {
            "first": "This is the first practice task on this concept: keep it focused on the core idea.",
            "similar": "Create a problem that applies the SAME principle as the last one in a new context or with different numbers (a transfer check), not a superficial copy.",
            "easier": "The student wants an easier problem: fewer steps, simpler numbers, focus on the prerequisite idea.",
            "harder": "The student wants a harder problem: more steps, a less familiar context, or an edge case.",
        }.get(mode, "")
        recurring = self.knowledge.recurring_errors(session.subject, session.topic)
        if recurring:
            purpose += " The student has recurring errors of type: " + ", ".join(c.label.lower() for c in recurring) + \
                       " - design the problem so that this error would be noticed."
        prof = self.profile()
        ex = self.exercises.generate(session, concept or session.current_concept or session.topic, session.level, previous,
                                     purpose, prof.preferences.programming_language, cancel)
        self.db.save_exercise(ex)
        session.active_exercise_id = ex.id
        session.current_concept = ex.concept
        self.db.save_session(session)
        result.exercise = ex
        result.messages.append(self._add(session, Role.ASSISTANT, self.exercise_markdown(ex), MessageKind.EXERCISE, exercise_id=ex.id))
        self._flush_notices(session, result)
        return result

    @staticmethod
    def exercise_markdown(ex: Exercise) -> str:
        out = [f"### 📝 Practice ({LEVEL_NAMES[ex.difficulty]}) - {ex.concept}", ex.statement]
        if ex.answer_type == AnswerType.MULTIPLE_CHOICE:
            out.append("\n".join(f"**{chr(65 + i)}.** {c}" for i, c in enumerate(ex.choices)))
        if ex.answer_type == AnswerType.CODE and ex.starter_code:
            out.append(f"```python\n{ex.starter_code}\n```")
        how = {
            AnswerType.EQUATION_SOLUTIONS: f"Give the value(s) of {ex.variable}, e.g. `{ex.variable} = 3` or `2, -1`.",
            AnswerType.EXPRESSION: "Give an expression, e.g. `3*x^2 + 2`.",
            AnswerType.NUMERIC: "Give a number" + (f" with its unit (e.g. `12.5 {ex.unit}`)." if ex.unit else "."),
            AnswerType.MULTIPLE_CHOICE: "Answer with a letter.",
            AnswerType.CODE: f"Write the function `{ex.function_name}` in the exercise panel; it will be run against tests in a sandbox.",
        }.get(ex.answer_type, "Explain your answer in your own words.")
        out.append(f"*{how} Show your reasoning to get feedback on each step.*")
        out.append(f"<small>Checking method: {ex.verification_method}"
                   + ("" if ex.validated else " - answer key not machine-verified") + "</small>")
        return "\n\n".join(out)

    def submit_answer(self, session: Session, answer: str, reasoning: str = "", confidence: int | None = None,
                      cancel: CancelToken | None = None, raw_text: str | None = None) -> TurnResult:
        cancel = cancel or CancelToken()
        result = TurnResult()
        ex = self.active_exercise(session)
        if ex is None:
            result.messages.append(self._add(session, Role.SYSTEM, "There is no active exercise - ask for a practice problem first.", MessageKind.NOTICE))
            return result
        shown = raw_text or (f"**My answer:** {answer}" + (f"\n\n**My reasoning:**\n{reasoning}" if reasoning.strip() else ""))
        if ex.answer_type == AnswerType.CODE and not raw_text:
            shown = f"**My code:**\n```python\n{answer}\n```" + (f"\n\n{reasoning}" if reasoning.strip() else "")
        result.messages.append(self._add(session, Role.USER, shown, exercise_id=ex.id))
        hints_used = session.hint_levels.get(ex.id, 0)
        viewed = ex.id in session.solutions_viewed
        ev = self.evaluator.evaluate(ex, answer, reasoning, solution_viewed=viewed, cancel=cancel)
        attempt = Attempt(exercise_id=ex.id, session_id=session.id, answer=answer, reasoning=reasoning,
                          hints_used=hints_used, solution_viewed=viewed, evaluation=ev)
        self.db.save_attempt(attempt)
        if ev.correctness != Correctness.INSUFFICIENT_EVIDENCE:
            self.knowledge.record(Evidence(
                subject=session.subject, topic=session.topic, concept=ex.concept, kind=EvidenceKind.ATTEMPT,
                correct=ev.correctness == Correctness.CORRECT, score=ev.score, difficulty=ex.difficulty,
                assistance=5 if viewed else hints_used, error_category=ev.error_category,
                exercise_kind=ex.kind.value, exercise_id=ex.id, session_id=session.id,
            ))
        if confidence:
            self.knowledge.record(Evidence(subject=session.subject, topic=session.topic, concept=ex.concept,
                                           kind=EvidenceKind.SELF_REPORT, confidence=confidence, session_id=session.id))
        feedback = ev.feedback
        if ev.error_category and ev.error_category in self.knowledge.recurring_errors(session.subject, session.topic):
            feedback += f"\n\n🔁 *You've made this kind of mistake ({ev.error_category.label.lower()}) before - it's worth checking that step deliberately next time.*"
        if ev.correctness == Correctness.CORRECT:
            session.active_exercise_id = None
            feedback += ("\n\n**Next:** to check that the idea transfers, try **Give me a similar problem**"
                         + (" - this time without the solution." if viewed else "."))
            if confidence and confidence <= 2:
                feedback += " You marked low confidence - explaining *why* each step works is a great way to build it."
        elif ev.correctness == Correctness.INCORRECT and not ev.how_to_reconsider and not viewed:
            feedback += "\n\nHave another go - or press **Hint** for a nudge."
        result.messages.append(self._add(session, Role.ASSISTANT, feedback, MessageKind.FEEDBACK,
                                         exercise_id=ex.id, correctness=ev.correctness.value))
        result.attempt, result.evaluation, result.exercise = attempt, ev, ex
        self._adapt_level(session, result)
        self.db.save_session(session)
        self._flush_notices(session, result)
        return result

    # ================================================================ adaptive level
    def _attempts_since_level_change(self, session: Session) -> list[Attempt]:
        atts = self.db.attempts_for_session(session.id)
        if session.level_changed_at:
            atts = [a for a in atts if a.created > session.level_changed_at]
        return atts

    def _adapt_level(self, session: Session, result: TurnResult) -> None:
        decision = difficulty.decide(session.level, self._attempts_since_level_change(session))
        if not decision:
            return
        if session.level_locked:
            session.level_changed_at = datetime.now(timezone.utc)  # avoid repeating the same suggestion
            result.messages.append(self._add(
                session, Role.SYSTEM,
                f"Suggestion: level {decision.new_level} ({LEVEL_NAMES[decision.new_level]}) might suit you better because "
                f"{decision.reason}. You fixed the level yourself, so it was not changed.", MessageKind.NOTICE))
            return
        self._set_level(session, decision.new_level, decision.reason, result, by_user=False)

    def _set_level(self, session: Session, level: int, reason: str, result: TurnResult | None, by_user: bool) -> None:
        old = session.level
        session.level = level
        session.level_changed_at = datetime.now(timezone.utc)
        self.db.save_session(session)
        verb = "raised" if level > old else "lowered"
        who = "" if by_user else " You can override this at any time."
        msg = f"Level {verb} from {old} to {level} ({LEVEL_NAMES[level]}) because {reason}.{who}"
        m = self._add(session, Role.SYSTEM, msg, MessageKind.NOTICE)
        if result:
            result.messages.append(m)
            result.level_changed = True

    def set_level(self, session: Session, level: int, lock: bool = True) -> Message:
        session.level_locked = lock
        r = TurnResult()
        self._set_level(session, level, "you chose it", r, by_user=True)
        return r.messages[-1]

    # ================================================================ assistance
    def hint(self, session: Session, on_chunk: ChunkFn | None = None, cancel: CancelToken | None = None) -> TurnResult:
        cancel = cancel or CancelToken()
        result = TurnResult()
        ex = self.active_exercise(session)
        key = ex.id if ex else "__chat__"
        level = min(MAX_LEVEL, session.hint_levels.get(key, 0) + 1)
        if level == MAX_LEVEL and ex:
            return self.worked_solution(session, on_chunk, cancel)
        session.hint_levels[key] = level
        self.db.save_session(session)
        header = f"💡 **Hint {level}/{MAX_LEVEL} - {HINT_LEVELS[level]}**\n\n"
        result.messages.append(self._add(session, Role.USER, f"*(asked for a hint)*", MessageKind.HINT))
        text = stored_hint(ex, level) if ex else None
        if text:
            if on_chunk:
                on_chunk(header + text)
            result.messages.append(self._add(session, Role.ASSISTANT, header + text, MessageKind.HINT, level=level))
            return result
        extra = ""
        if ex:
            extra = (f"The exercise: {ex.statement}\nFor your eyes only (do NOT reveal the final answer): expected answer "
                     f"{ex.expected_answer or 'see solution'}; worked solution: {ex.solution_explanation[:1200]}\n")
        instruction = prompts.HINT_REQUEST.format(label=HINT_LEVELS[level], level=level, extra=extra)
        msgs = [ChatMessage("system", self._system(session, include_viz=False))] + self._history(session, cancel, drop_last_user=True)
        msgs.append(ChatMessage("user", instruction + "\n(Instruction from the app.)"))
        hint_text = ""
        for _ in range(2):
            hint_text = self._stream(session, Task.EXPLAIN, msgs, None, cancel)
            if not ex or level >= 4 or (not leaks_answer(hint_text, ex) and _relevant(hint_text, ex)):
                break
            msgs.append(ChatMessage("assistant", hint_text))
            msgs.append(ChatMessage("user", "That hint gives away the answer or is off-topic. Give a smaller, relevant hint."))
        else:
            hint_text = "Look again at what the problem gives you and what it asks for. Which rule or definition connects the two?"
        if on_chunk:
            on_chunk(header + hint_text)
        self._finish_assistant(session, header + hint_text, result, MessageKind.HINT, level=level)
        self._flush_notices(session, result)
        return result

    def worked_solution(self, session: Session, on_chunk: ChunkFn | None = None, cancel: CancelToken | None = None,
                        record_user: bool = True) -> TurnResult:
        cancel = cancel or CancelToken()
        result = TurnResult()
        ex = self.active_exercise(session)
        if record_user:
            result.messages.append(self._add(session, Role.USER, "*(asked for the worked solution)*", MessageKind.SOLUTION))
        if ex:
            if ex.id not in session.solutions_viewed:
                session.solutions_viewed.append(ex.id)
            session.hint_levels[ex.id] = MAX_LEVEL
            self.db.save_session(session)
            sol = ex.solution_explanation or "(No stored solution.)"
            if ex.answer_type == AnswerType.CODE and ex.reference_solution:
                sol += f"\n\n```python\n{ex.reference_solution}\n```"
            check = ("🔎 *The final answer was verified automatically (" + ex.verification_method + ").*"
                     if ex.validated else "⚠️ *This solution was produced by the AI model and could not be verified automatically.*")
            text = f"📘 **Complete worked solution**\n\n{sol}\n\n{check}\n\n**Your turn:** press **Give me a similar problem** and try one on your own."
            if on_chunk:
                on_chunk(text)
            result.messages.append(self._add(session, Role.ASSISTANT, text, MessageKind.SOLUTION, exercise_id=ex.id))
            return result
        self._turn(session, "Give a complete worked solution to the problem we are discussing, explaining every step and the "
                   "reason for it. Then offer a similar problem to try independently. (Instruction from the app.)",
                   on_chunk, cancel, result, kind=MessageKind.SOLUTION)
        return result

    def explain_differently(self, session: Session, on_chunk: ChunkFn | None = None, cancel: CancelToken | None = None) -> TurnResult:
        cancel = cancel or CancelToken()
        result = TurnResult()
        used = session.explanation_strategies[-4:]
        options = [s for s in prompts.STRATEGIES if s not in used] or prompts.STRATEGIES
        prof = self.profile()
        if prof.preferences.modality == "visual" and "visual/graphical picture" in options:
            options.insert(0, options.pop(options.index("visual/graphical picture")))
        result.messages.append(self._add(session, Role.USER, "*(asked: explain it differently)*"))
        text = self._turn(session, prompts.EXPLAIN_DIFFERENTLY.format(used=", ".join(used) or "none recorded",
                          options=", ".join(options[:5])) + " (Instruction from the app.)", on_chunk, cancel, result)
        m = re.search(r"Another way to see it:\s*([^*\n]+)", text)
        session.explanation_strategies.append((m.group(1).strip().lower() if m else options[0])[:40])
        self.db.save_session(session)
        return result

    def check_reasoning(self, session: Session, work: str, on_chunk: ChunkFn | None = None,
                        cancel: CancelToken | None = None) -> TurnResult:
        cancel = cancel or CancelToken()
        result = TurnResult()
        result.messages.append(self._add(session, Role.USER, "**Please check my reasoning:**\n\n" + work))
        verified = []
        steps = mv.check_steps(work)
        if any(s.ok is not None for s in steps[1:]):
            verified.append("Automatic SymPy step check (authoritative):\n" + mv.format_step_report(steps))
        is_code = "def " in work or "print(" in work or "```" in work
        ex = self.active_exercise(session)
        if is_code:
            code = re.sub(r"^```\w*\n|```$", "", work.strip(), flags=re.M)
            tests = ex.code_tests if ex and ex.answer_type == AnswerType.CODE else []
            vr, run = self.runner.verify(code, tests)
            verified.append("Sandboxed execution result (authoritative):\n" + vr.details +
                            (f"\nOutput:\n{run.stdout[:800]}" if run.stdout else ""))
        if ex:
            verified.append(f"Context - current exercise: {ex.statement[:600]}")
        if verified:
            report = "\n\n".join(verified)
            result.messages.append(self._add(session, Role.SYSTEM, "🔎 Automatic checks:\n\n" + report, MessageKind.NOTICE))
        instruction = prompts.CHECK_REASONING.format(verified="\n\n".join(verified) or "No automatic check was applicable.")
        instruction += f"\n<student_answer>\n{work[:5000]}\n</student_answer>\n(Instruction from the app.)"
        self._turn(session, instruction, on_chunk, cancel, result, query=work)
        return result

    # ================================================================ visuals
    def plot(self, session: Session, spec: VisualizationSpec) -> TurnResult:
        result = TurnResult()
        self._add_visual(session, spec, result)
        return result

    def ask_about_visual(self, session: Session, visual: Message, element: str, question: str,
                         on_chunk: ChunkFn | None = None, cancel: CancelToken | None = None) -> TurnResult:
        cancel = cancel or CancelToken()
        result = TurnResult()
        q = question.strip() or f"What does the {element} show?"
        result.messages.append(self._add(session, Role.USER, f"About the diagram ({element or 'whole diagram'}): {q}"))
        ctx = (f"The student is looking at a diagram generated by the app. Caption: {visual.meta.get('caption')}. "
               f"Spec: {visual.meta.get('spec')}. Elements: {visual.meta.get('elements')}. The student asks about: "
               f"'{element or 'the whole diagram'}'. Explain how this part connects to the concept, then ask a short check question.")
        self._turn(session, f"{q}\n\n[App note: {ctx}]", on_chunk, cancel, result, query=q)
        return result


def _relevant(hint: str, ex: Exercise) -> bool:
    words = set(re.findall(r"[a-z]{4,}", (ex.statement + " " + ex.solution_explanation + " " + ex.concept).lower()))
    hint_words = set(re.findall(r"[a-z]{4,}", hint.lower()))
    return bool(words & hint_words) or bool(re.search(r"[=+\-*/^]", hint))
