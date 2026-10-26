"""Evidence-based student knowledge model.

A concept's state is derived from recorded evidence only. The rules are
intentionally simple and transparent (each status carries a human-readable
rationale) so that students can understand - and correct - the assessment.

* NOT_ASSESSED - no evidence at all.
* INTRODUCED   - the concept was explained, but never practised.
* DEVELOPING   - some practice, but not yet enough independent success.
* DEMONSTRATED - >= 3 independent (low-assistance) correct answers on >= 3
                 different exercises, in >= 2 formats or difficulty levels,
                 and a recent success rate >= 75 %.
* NEEDS_REVISION - was demonstrated before, but recent attempts fail, or a
                 recurring error pattern dominates recent work.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from tutor.domain import (
    ConceptStatus,
    ErrorCategory,
    Evidence,
    EvidenceKind,
    MasteryState,
)
from tutor.storage.db import Database

INDEPENDENT_MAX_ASSISTANCE = 1   # at most one small hint
DEMONSTRATED_MIN_SUCCESSES = 3
RECENT_WINDOW = 5


def norm(concept: str) -> str:
    return " ".join(concept.strip().lower().split())


def _is_success(e: Evidence) -> bool:
    return bool(e.correct) and (e.score is None or e.score >= 0.8)


def _independent(e: Evidence) -> bool:
    return _is_success(e) and e.assistance <= INDEPENDENT_MAX_ASSISTANCE


def _demonstrated(scored: list[Evidence]) -> tuple[bool, str]:
    indep = [e for e in scored if _independent(e)]
    distinct = {e.exercise_id or e.id for e in indep}
    formats = {e.exercise_kind or e.kind.value for e in indep}
    levels = {e.difficulty for e in indep}
    recent = scored[-RECENT_WINDOW:]
    rate = sum(_is_success(e) for e in recent) / len(recent) if recent else 0.0
    if len(indep) < DEMONSTRATED_MIN_SUCCESSES:
        return False, f"{len(indep)} of {DEMONSTRATED_MIN_SUCCESSES} independent correct answers needed"
    if len(distinct) < DEMONSTRATED_MIN_SUCCESSES:
        return False, "successes come from too few different exercises"
    if len(formats) < 2 and len(levels) < 2:
        return False, "success shown in only one format and difficulty - needs a different kind of problem"
    if rate < 0.75:
        return False, f"recent success rate {rate:.0%} is below 75 %"
    return True, f"{len(indep)} independent correct answers across {len(formats)} format(s) and {len(levels)} level(s)"


def assess(evidence: list[Evidence], subject: str, topic: str, concept: str,
           override: tuple[MasteryState, str] | None = None) -> ConceptStatus:
    attempts = [e for e in evidence if e.kind == EvidenceKind.ATTEMPT]
    explanations = [e for e in evidence if e.kind == EvidenceKind.EXPLANATION and e.correct is not None]
    scored = sorted(attempts + explanations, key=lambda e: e.created)
    indep = [e for e in scored if _independent(e)]
    recent = scored[-RECENT_WINDOW:]
    rate = (sum(_is_success(e) for e in recent) / len(recent)) if recent else None

    last6 = [e.error_category for e in scored[-6:] if e.error_category]
    recurring = [cat for cat, n in Counter(last6).items() if n >= 2]

    n = len(scored)
    certainty = "none" if n == 0 else "low" if n <= 2 else "medium" if n <= 5 else "high"

    if not evidence:
        state, why = MasteryState.NOT_ASSESSED, "No evidence recorded yet."
    elif not scored:
        state, why = MasteryState.INTRODUCED, "The concept has been explained but not practised yet."
        certainty = "low"
    else:
        ok, reason = _demonstrated(scored)
        # Was it demonstrated before the most recent attempts?
        earlier_ok = len(scored) > 2 and _demonstrated(scored[:-2])[0]
        last_two_failed = len(scored) >= 2 and not any(_is_success(e) for e in scored[-2:])
        if earlier_ok and last_two_failed:
            state, why = MasteryState.NEEDS_REVISION, "Understanding was demonstrated earlier, but the last two attempts were incorrect."
        elif recurring and n >= 4 and rate is not None and rate < 0.5:
            cats = ", ".join(c.label.lower() for c in recurring)
            state, why = MasteryState.NEEDS_REVISION, f"A recurring error pattern ({cats}) appears in recent work."
        elif ok:
            state, why = MasteryState.DEMONSTRATED, "Demonstrated: " + reason + "."
        else:
            state, why = MasteryState.DEVELOPING, "Developing: " + reason + "."

    status = ConceptStatus(
        subject=subject, topic=topic, concept=concept, state=state,
        evidence_count=len(evidence), attempts=len(attempts), independent_successes=len(indep),
        recent_success_rate=rate, certainty=certainty, rationale=why, recurring_errors=recurring,
        last_seen=max((e.created for e in evidence), default=None),
    )
    if override:
        status.state, status.overridden, status.override_note = override[0], True, override[1]
        status.rationale = f"Set by you ({override[0].label}). Evidence-based estimate: {why}"
    return status


@dataclass
class KnowledgeModel:
    db: Database

    # ------------------------------------------------------------ recording
    def record(self, e: Evidence) -> None:
        e.concept = norm(e.concept)
        self.db.add_evidence(e)

    def record_introduced(self, subject: str, topic: str, concept: str, session_id: str) -> None:
        existing = self.db.evidence(subject, topic, norm(concept))
        if not any(x.kind == EvidenceKind.INTRODUCED and x.session_id == session_id for x in existing):
            self.record(Evidence(subject=subject, topic=topic, concept=concept, kind=EvidenceKind.INTRODUCED, session_id=session_id))

    # ------------------------------------------------------------ queries
    def status(self, subject: str, topic: str, concept: str) -> ConceptStatus:
        c = norm(concept)
        ev = self.db.evidence(subject, topic, c)
        return assess(ev, subject, topic, c, self.db.overrides().get((subject, topic, c)))

    def all_statuses(self, subject: str | None = None) -> list[ConceptStatus]:
        groups: dict[tuple[str, str, str], list[Evidence]] = {}
        for e in self.db.evidence(subject):
            groups.setdefault((e.subject, e.topic, norm(e.concept)), []).append(e)
        overrides = self.db.overrides()
        for key in overrides:
            if subject is None or key[0] == subject:
                groups.setdefault(key, [])
        out = [assess(ev, *key, override=overrides.get(key)) for key, ev in groups.items()]
        return sorted(out, key=lambda s: (s.subject, s.topic, s.concept))

    def recurring_errors(self, subject: str, topic: str) -> list[ErrorCategory]:
        ev = [e for e in self.db.evidence(subject, topic) if e.error_category][-8:]
        return [c for c, n in Counter(e.error_category for e in ev).items() if n >= 2]  # type: ignore[misc]

    def topic_brief(self, subject: str, topic: str, max_items: int = 6) -> str:
        """Concise, prompt-ready summary (no raw history)."""
        sts = [s for s in self.all_statuses(subject) if s.topic.lower() == topic.lower()]
        if not sts:
            return "No previous evidence for this topic."
        lines = []
        for s in sorted(sts, key=lambda s: s.last_seen or 0, reverse=True)[:max_items]:
            rate = f", recent success {s.recent_success_rate:.0%}" if s.recent_success_rate is not None else ""
            lines.append(f"- {s.concept}: {s.state.label} (evidence: {s.attempts} attempts{rate}; certainty {s.certainty})")
        rec = self.recurring_errors(subject, topic)
        if rec:
            lines.append("- Recurring error patterns: " + ", ".join(c.label.lower() for c in rec))
        return "\n".join(lines)

    def override(self, subject: str, topic: str, concept: str, state: MasteryState | None, note: str = "") -> None:
        self.db.set_override(subject, topic, norm(concept), state, note)

    def revision_candidates(self, limit: int = 5) -> list[ConceptStatus]:
        sts = self.all_statuses()
        prio = {MasteryState.NEEDS_REVISION: 0, MasteryState.DEVELOPING: 1, MasteryState.INTRODUCED: 2}
        cands = [s for s in sts if s.state in prio]
        return sorted(cands, key=lambda s: (prio[s.state], -(s.last_seen.timestamp() if s.last_seen else 0)))[:limit]
