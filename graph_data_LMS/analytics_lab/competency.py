"""Competency scoring and adaptive recommendations.

The model is deliberately transparent (shown verbatim on the My Progress page):

* **Knowledge** - recency-weighted accuracy on the last 20 questions tagged with the competency.
* **Practical** - mean best score on attempted coding exercises tagged with it. A pass that was
  only achieved after viewing the solution is capped at 70. *Coverage* = attempted / available.
* **Application** - business-case scores and self-assessed capstone milestones tagged with it.
* **Score** - weighted mean of the available components: 35% knowledge, 45% practical, 20% application.
* **Mastered** - score >= threshold, at least 3 pieces of evidence, and - for competencies flagged
  *requires practical evidence* - practical >= threshold with >= 50% exercise coverage.
  Quiz scores alone can never produce mastery of such a competency.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from analytics_lab.assessment.bank import EXERCISES, QUESTIONS_BY_ID
from analytics_lab.assessment.capstones import CAPSTONES
from analytics_lab.assessment.cases import CASES_BY_ID
from analytics_lab.curriculum import LESSONS, LESSONS_BY_ID, learning_path
from analytics_lab.curriculum.competencies import BY_ID as COMPETENCIES
from analytics_lab.curriculum.competencies import COMPETENCIES as COMP_LIST
from analytics_lab.i18n import t
from analytics_lab.models import LEVELS, MODULES
from analytics_lab.progress.store import ProgressStore

WEIGHTS = {"knowledge": 0.35, "practical": 0.45, "application": 0.20}
ASSISTED_CAP = 70.0


@dataclass
class CompetencyScore:
    id: str
    name: str
    module: str
    knowledge: float | None
    n_questions: int
    practical: float | None
    coverage: float
    n_exercises: int
    application: float | None
    n_applications: int
    score: float | None
    status: str
    requires_practical: bool


def _recency_weighted_accuracy(correct: pd.Series) -> float:
    vals = correct.tail(20).to_numpy(dtype=float)
    w = np.linspace(0.5, 1.0, len(vals))
    return float(100 * (vals * w).sum() / w.sum())


def compute_competencies(store: ProgressStore, threshold: float = 80.0) -> list[CompetencyScore]:
    responses = store.responses()
    ex_attempts = store.exercise_attempts()
    cases = store.case_submissions()
    milestones = store.milestones()

    # Effective best score per exercise (assisted passes capped).
    eff: dict[str, float] = {}
    if not ex_attempts.empty:
        for ex_id, g in ex_attempts.groupby("exercise_id"):
            unassisted = g[g["solution_viewed"] == 0]["score"].max() if (g["solution_viewed"] == 0).any() else np.nan
            assisted = g[g["solution_viewed"] == 1]["score"].max() if (g["solution_viewed"] == 1).any() else np.nan
            best = np.nanmax([unassisted if not np.isnan(unassisted) else -1, min(assisted, ASSISTED_CAP) if not np.isnan(assisted) else -1])
            eff[ex_id] = float(max(best, 0))

    case_scores: dict[str, float] = {}
    if not cases.empty:
        case_scores = cases.sort_values("submission_id").groupby("case_id")["total_score"].last().to_dict()

    cap_scores: dict[str, list[float]] = {}
    if not milestones.empty:
        for cap in CAPSTONES:
            ms = milestones[(milestones["capstone_id"] == cap.id) & milestones["score"].notna()]
            text_ids = {m.id for m in cap.milestones if m.kind in ("text", "checklist")}
            vals = ms[ms["milestone_id"].isin(text_ids)]["score"].tolist()
            for comp in cap.competencies:
                cap_scores.setdefault(comp, []).extend(vals)

    out = []
    for comp in COMP_LIST:
        r = responses[responses["competency"] == comp.id] if not responses.empty else responses
        knowledge = _recency_weighted_accuracy(r["correct"]) if len(r) else None
        tagged = [e.id for e in EXERCISES if comp.id in e.competencies]
        attempted = [eff[e] for e in tagged if e in eff]
        practical = float(np.mean(attempted)) if attempted else None
        coverage = len(attempted) / len(tagged) if tagged else 0.0
        apps = [v for cid, v in case_scores.items() if cid in CASES_BY_ID and comp.id in CASES_BY_ID[cid].competencies]
        apps += cap_scores.get(comp.id, [])
        application = float(np.mean(apps)) if apps else None

        parts = {"knowledge": knowledge, "practical": practical, "application": application}
        avail = {k: v for k, v in parts.items() if v is not None}
        score = sum(WEIGHTS[k] * v for k, v in avail.items()) / sum(WEIGHTS[k] for k in avail) if avail else None
        evidence = len(r) + len(attempted) + len(apps)

        if score is None:
            status = "Not started"
        elif score >= threshold and evidence >= 3 and (
            not comp.requires_practical or (practical is not None and practical >= threshold and coverage >= 0.5)
        ):
            status = "Mastered"
        elif score >= threshold:
            status = "Needs practical evidence" if comp.requires_practical else "Needs more evidence"
        elif score >= 50:
            status = "Developing"
        else:
            status = "Needs work"
        out.append(CompetencyScore(comp.id, comp.name, comp.module, knowledge, len(r), practical, coverage, len(attempted),
                                   application, len(apps), round(score, 1) if score is not None else None, status, comp.requires_practical))
    return out


def competency_frame(scores: list[CompetencyScore]) -> pd.DataFrame:
    return pd.DataFrame([s.__dict__ for s in scores])


def module_scores(scores: list[CompetencyScore]) -> dict[str, float | None]:
    out = {}
    for m in MODULES:
        vals = [s.score for s in scores if s.module == m and s.score is not None]
        out[m] = round(float(np.mean(vals)), 1) if vals else None
    return out


# --------------------------------------------------------------------------- #
# Dashboard metrics                                                            #
# --------------------------------------------------------------------------- #
def completion_summary(store: ProgressStore) -> dict:
    """Overall completion = completed items / all items (lessons + exercises + capstone milestones)."""
    done_lessons = store.completed_lessons()
    ex = store.exercise_summary()
    passed = set(ex[ex["passed"] == 1]["exercise_id"]) if not ex.empty else set()
    ms = store.milestones()
    done_ms = int((ms["status"] == "completed").sum()) if not ms.empty else 0
    total_ms = sum(len(c.milestones) for c in CAPSTONES)
    total = len(LESSONS) + len(EXERCISES) + total_ms
    done = len(done_lessons) + len(passed & {e.id for e in EXERCISES}) + done_ms
    resp = store.responses()
    attempts = store.exercise_attempts()
    return {
        "completion_pct": round(100 * done / total, 1) if total else 0.0,
        "lessons_done": len(done_lessons),
        "lessons_total": len(LESSONS),
        "exercises_passed": len(passed),
        "exercises_total": len(EXERCISES),
        "milestones_done": done_ms,
        "milestones_total": total_ms,
        "quiz_accuracy": round(100 * resp["correct"].mean(), 1) if len(resp) else None,
        "questions_answered": len(resp),
        "exercise_pass_rate": round(100 * attempts["passed"].mean(), 1) if len(attempts) else None,
        "submissions": len(attempts),
        "streak": store.streak(),
    }


def outstanding(store: ProgressStore) -> list[str]:
    items = []
    status = store.lesson_status()
    for lid, row in status.items():
        if row["status"] != "completed" and lid in LESSONS_BY_ID:
            items.append(t("Finish lesson **{title}**", title=LESSONS_BY_ID[lid].title))
    ex = store.exercise_summary()
    if not ex.empty:
        from analytics_lab.assessment.bank import EXERCISES_BY_ID

        for _, r in ex[ex["passed"] == 0].iterrows():
            e = EXERCISES_BY_ID.get(r["exercise_id"])
            if e:
                items.append(t("Pass exercise **{title}** (best {best:.0f}/100 after {n} attempt(s))", title=e.title, best=r["best_score"], n=r["attempts"]))
    ms = store.milestones()
    for cap in CAPSTONES:
        sub = ms[ms["capstone_id"] == cap.id] if not ms.empty else ms
        if len(sub) and (sub["status"] == "completed").sum() < len(cap.milestones):
            items.append(t("Continue capstone **{title}** ({n}/{total} milestones)", title=cap.title, n=int((sub["status"] == "completed").sum()), total=len(cap.milestones)))
    return items


# --------------------------------------------------------------------------- #
# Recommendations                                                              #
# --------------------------------------------------------------------------- #
@dataclass
class Recommendation:
    title: str
    reason: str
    kind: str        # lesson | exercise | quiz | capstone
    target: str
    priority: int


def _first_lesson_for(comp_id: str, levels: tuple[str, ...] = ("Beginner", "Intermediate")) -> str | None:
    for lesson in sorted(LESSONS, key=lambda x: x.order):
        if comp_id in lesson.competencies and lesson.level in levels:
            return lesson.id
    for lesson in sorted(LESSONS, key=lambda x: x.order):
        if comp_id in lesson.competencies:
            return lesson.id
    return None


def recommend(store: ProgressStore, threshold: float = 80.0, limit: int = 5, now: datetime | None = None) -> list[Recommendation]:
    now = now or datetime.now()
    recs: list[Recommendation] = []
    completed = store.completed_lessons()
    responses = store.responses()
    attempts = store.exercise_attempts()
    scores = {s.id: s for s in compute_competencies(store, threshold)}

    if responses.empty and attempts.empty and not completed:
        first = learning_path()[0]
        return [Recommendation(t("Start with: {title}", title=first.title),
                               t("You have not started yet. The learning path begins with SQL fundamentals because every later module relies on querying data correctly."), "lesson", first.id, 0)]

    # 1) Weak foundations
    for s in scores.values():
        comp = COMPETENCIES[s.id]
        if comp.foundational and s.knowledge is not None and s.n_questions >= 3 and s.knowledge < 50:
            lid = _first_lesson_for(s.id)
            if lid:
                recs.append(Recommendation(t("Revisit fundamentals: {title}", title=LESSONS_BY_ID[lid].title),
                                           t("Your recent quiz accuracy on *{name}* is {acc:.0f}% over {n} questions. "
                                             "Later topics build on this, so a quick review now will save time.", name=comp.name, acc=s.knowledge, n=s.n_questions), "lesson", lid, 1))

    # 2) Repeated mistakes on a topic (last 14 days)
    if not responses.empty:
        r = responses.copy()
        r["answered_at"] = pd.to_datetime(r["answered_at"])
        recent = r[r["answered_at"] >= now - timedelta(days=14)]
        topic_stats = recent.groupby("topic")["correct"].agg(["count", "sum"])
        topic_stats["wrong"] = topic_stats["count"] - topic_stats["sum"]
        for topic, row in topic_stats[(topic_stats["wrong"] >= 2) & (topic_stats["sum"] / topic_stats["count"] < 0.6)].iterrows():
            qids = recent[(recent["topic"] == topic)]["question_id"]
            lessons = [QUESTIONS_BY_ID[q].lesson for q in qids if q in QUESTIONS_BY_ID and QUESTIONS_BY_ID[q].lesson]
            if lessons:
                lid = max(set(lessons), key=lessons.count)
                recs.append(Recommendation(t("Targeted revision: {topic}", topic=t(topic)),
                                           t("You missed {wrong} of {n} recent questions on *{topic}*. Lesson '{title}' covers it, including common mistakes.",
                                             wrong=int(row["wrong"]), n=int(row["count"]), topic=t(topic), title=LESSONS_BY_ID[lid].title), "lesson", lid, 2))

    # 3) Exercises with repeated failed attempts
    if not attempts.empty:
        from analytics_lab.assessment.bank import EXERCISES_BY_ID

        g = attempts.groupby("exercise_id").agg(n=("passed", "size"), passed=("passed", "max"), best=("score", "max"))
        for ex_id, row in g[(g["n"] >= 2) & (g["passed"] == 0)].iterrows():
            e = EXERCISES_BY_ID.get(ex_id)
            if e:
                why = t("You have made {n} attempts at '{title}' (best {best:.0f}/100).", n=int(row["n"]), title=e.title, best=row["best"])
                if e.lesson:
                    recs.append(Recommendation(t("Review the worked example in '{title}'", title=LESSONS_BY_ID[e.lesson].title),
                                               why + " " + t("Re-reading the worked solution and using the next hint usually unblocks this."), "lesson", e.lesson, 2))
                else:
                    recs.append(Recommendation(t("Retry '{title}' with hints", title=e.title), why, "exercise", ex_id, 3))

    # 4) Spaced review of missed questions (> 3 days ago, not since answered correctly)
    if not responses.empty:
        r = responses.copy()
        r["answered_at"] = pd.to_datetime(r["answered_at"])
        last = r.sort_values("response_id").groupby("question_id").last()
        due = last[(last["correct"] == 0) & (last["answered_at"] <= now - timedelta(days=3))]
        if len(due):
            recs.append(Recommendation(t("Spaced review: {n} previously missed question(s)", n=len(due)),
                                       t("Revisiting missed concepts after a few days strengthens long-term retention. The Assessment Center can build a review quiz from them."),
                                       "quiz", "review", 3))

    # 5) Consistent success -> increase difficulty
    for s in scores.values():
        if s.score is not None and s.score >= threshold and (s.n_questions + s.n_exercises) >= 3:
            nxt = [l for l in sorted(LESSONS, key=lambda x: (LEVELS.index(x.level), x.order))
                   if s.id in l.competencies and l.id not in completed and LEVELS.index(l.level) >= 1]
            if nxt:
                recs.append(Recommendation(t("Step up: {title} ({level})", title=nxt[0].title, level=t(nxt[0].level)),
                                           t("You are scoring {score:.0f} on *{name}*. Moving to harder material keeps you learning.", score=s.score, name=s.name), "lesson", nxt[0].id, 4))
            else:
                attempted_ids = set(attempts["exercise_id"]) if not attempts.empty else set()
                hard = [e for e in EXERCISES if s.id in e.competencies and e.kind == "challenge" and e.id not in attempted_ids]
                if hard:
                    recs.append(Recommendation(t("Challenge: {title}", title=hard[0].title),
                                               t("You are scoring {score:.0f} on *{name}* - try an independent challenge.", score=s.score, name=s.name), "exercise", hard[0].id, 4))

    # 6) Capstone readiness
    ms = store.milestones()
    for cap in CAPSTONES:
        started = (not ms.empty) and (ms["capstone_id"] == cap.id).any()
        if not started and all(p in completed for p in cap.prerequisites):
            recs.append(Recommendation(t("Ready for capstone: {title}", title=cap.title),
                                       t("You have completed its prerequisite lessons ({lessons}). Capstones provide the practical evidence needed for mastery.", lessons=", ".join(cap.prerequisites)),
                                       "capstone", cap.id, 2))

    # 7) Default: next lesson on the path
    for lesson in learning_path():
        if lesson.id not in completed:
            recs.append(Recommendation(t("Next on your path: {title}", title=lesson.title),
                                       t("The next uncompleted lesson on the recommended path ({level}, {module}).", level=t(lesson.level), module=MODULES[lesson.module]), "lesson", lesson.id, 5))
            break

    seen, unique = set(), []
    for rec in sorted(recs, key=lambda x: x.priority):
        key = (rec.kind, rec.target)
        if key not in seen:
            seen.add(key)
            unique.append(rec)
    return unique[:limit]
