"""Assessment Center: quizzes (practice/exam/timed), business cases, final assessment, review."""

from __future__ import annotations

import json
import random
import time

import pandas as pd
import streamlit as st

from analytics_lab.assessment import cases as case_mod
from analytics_lab.assessment.bank import EXERCISES_BY_ID, FINAL_EXERCISES, QUESTIONS, QUESTIONS_BY_ID, filter_questions, sample_questions, stratified_sample
from analytics_lab.assessment.grading import grade_mcq
from analytics_lab.i18n import get_lang, t
from analytics_lab.models import LEVELS, MODULES
from analytics_lab.ui import state
from analytics_lab.ui.components.exercise import render_exercise
from analytics_lab.ui.components.mcq import LETTERS, feedback, question_input
from analytics_lab.ui.components.outputs import evidence_blocks

SECTIONS = ["Quiz", "Business cases", "Final assessment", "History & review"]


def render() -> None:
    st.title(t("Assessment Center"))
    st.session_state.setdefault("assess_tab", SECTIONS[0])
    section = st.segmented_control(t("Section"), SECTIONS, format_func=t, key="assess_tab", label_visibility="collapsed") or SECTIONS[0]
    if section == "Quiz":
        _quiz_section()
    elif section == "Business cases":
        _cases()
    elif section == "Final assessment":
        _final()
    else:
        _history()
    st.caption(t("Coding challenges are in **Practice & Coding Lab -> Coding challenges** (and inside each lesson)."))


# --------------------------------------------------------------------------- quiz engine
def _start_quiz(qs, mode: str, shuffle_answers: bool, minutes: float | None, kind: str, config: dict) -> None:
    store = state.store()
    orders = {}
    for q in qs:
        o = list(range(len(q.options)))
        if shuffle_answers and q.shuffle:
            random.shuffle(o)
        orders[q.id] = o
    attempt = store.start_quiz(kind, len(qs), minutes, config)
    st.session_state["quiz"] = {
        "attempt": attempt, "qids": [q.id for q in qs], "orders": orders, "mode": mode, "kind": kind,
        "deadline": time.time() + minutes * 60 if minutes else None, "minutes": minutes, "answers": {}, "checked": [],
        "idx": 0, "finished": False, "timed_out": False, "config": config, "nonce": random.randint(0, 10**9),
    }
    store.log("quiz_started", str(attempt), mode)


def _finish(quiz: dict, timed_out: bool = False) -> None:
    store = state.store()
    if quiz["mode"] != "immediate":
        for qid in quiz["qids"]:
            q = QUESTIONS_BY_ID[qid]
            chosen = quiz["answers"].get(qid, [])
            store.record_response(quiz["attempt"], q, [str(c) for c in chosen], grade_mcq(q, chosen).correct)
    n_correct = sum(grade_mcq(QUESTIONS_BY_ID[q], quiz["answers"].get(q, [])).correct for q in quiz["qids"])
    store.finish_quiz(quiz["attempt"], n_correct, timed_out)
    quiz["finished"] = True
    quiz["timed_out"] = timed_out


def _time_left(quiz: dict) -> float | None:
    return None if not quiz["deadline"] else quiz["deadline"] - time.time()


def _quiz_section() -> None:
    quiz = st.session_state.get("quiz")
    if quiz and quiz["kind"] != "final":
        if quiz["finished"]:
            _results(quiz)
        else:
            _run_quiz(quiz)
        return
    _builder()


def _builder() -> None:
    store = state.store()
    preset = st.session_state.pop("quiz_preset", None)
    st.markdown(t("Build a quiz from the question bank. Questions are tagged by module, topic, tool, difficulty and competency."))
    resp = store.responses()
    missed = set()
    if not resp.empty:
        last = resp.sort_values("response_id").groupby("question_id").last()
        missed = set(last[last["correct"] == 0].index)
    with st.form("quiz_builder"):
        c1, c2 = st.columns(2)
        mods = c1.multiselect(t("Modules"), list(MODULES), format_func=MODULES.get, key="qb_mod")
        diffs = c2.multiselect(t("Difficulty"), LEVELS, format_func=t, key="qb_diff")
        topics_all = sorted({q.topic for q in QUESTIONS if not mods or q.module in mods})
        topics = st.multiselect(t("Topics (optional)"), topics_all, format_func=t, key="qb_topics")
        c3, c4, c5 = st.columns(3)
        n = c3.slider(t("Number of questions"), 3, 30, 10, key="qb_n")
        mode = c4.radio(t("Feedback"), ["immediate", "end", "exam"], index=["immediate", "end"].index(store.get_setting("quiz_feedback")) if store.get_setting("quiz_feedback") in ("immediate", "end") else 0,
                        format_func=lambda m: t({"immediate": "Immediate (after each question)", "end": "At the end", "exam": "Exam mode (withheld until submission)"}[m]), key="qb_mode")
        shuffle = c5.toggle(t("Randomise answer order"), value=True, key="qb_shuffle")
        timed = c5.toggle(t("Timed"), value=False, key="qb_timed")
        minutes = c5.number_input(t("Minutes"), 1, 120, max(3, n), key="qb_minutes")
        review = st.toggle(t("Review mode: only questions I previously got wrong ({n})", n=len(missed)), value=preset == "review" and bool(missed), key="qb_review", disabled=not missed)
        go = st.form_submit_button(t("Start quiz"), type="primary", icon=":material/play_arrow:")
    if go:
        pool = [QUESTIONS_BY_ID[q] for q in missed] if review else filter_questions(mods, topics, diffs)
        if not pool:
            st.warning(t("No questions match these filters."))
            return
        recent = set(resp.tail(40)["question_id"]) if not resp.empty else set()
        qs = sample_questions(pool, min(n, len(pool)), avoid=recent if not review else set(), prefer=missed)
        _start_quiz(qs, mode, shuffle, minutes if timed else None, "exam" if mode == "exam" else "practice",
                    {"modules": mods, "difficulties": diffs, "topics": topics, "n": n, "mode": mode, "shuffle": shuffle, "minutes": minutes if timed else None, "review": review})
        st.rerun()
    st.caption(t("Question bank: {q} questions across {m} modules. Recently seen questions are avoided and previously missed ones are favoured.", q=len(QUESTIONS), m=len(MODULES)))


def _timer(quiz: dict) -> bool:
    left = _time_left(quiz)
    if left is None:
        return False
    if left <= 0:
        st.error(t("Time is up. Answers given so far have been submitted."))
        return True
    st.info(t("Time remaining: **{m}:{s:02d}** (deadline enforced on submission; the clock updates when you interact).", m=int(left // 60), s=int(left % 60)), icon=":material/timer:")
    return False


def _run_quiz(quiz: dict) -> None:
    qs = [QUESTIONS_BY_ID[q] for q in quiz["qids"]]
    key = f"quiz_{quiz['nonce']}"
    if _timer(quiz):
        _finish(quiz, timed_out=True)
        st.rerun()
    if st.button(t("Abandon quiz"), key=f"{key}_abandon", type="tertiary"):
        st.session_state.pop("quiz", None)
        st.rerun()

    if quiz["mode"] == "immediate":
        i = quiz["idx"]
        q = qs[i]
        st.progress(i / len(qs), text=t("Question {i} of {n}", i=i + 1, n=len(qs)) + f" · {MODULES[q.module]} · {t(q.topic)} · {t(q.difficulty)}")
        checked = q.id in quiz["checked"]
        with st.container(border=True):
            chosen = question_input(q, key, quiz["orders"][q.id], disabled=checked)
            if not checked:
                if st.button(t("Check answer"), type="primary", key=f"{key}_check_{i}", disabled=not chosen):
                    if _time_left(quiz) is not None and _time_left(quiz) <= 0:
                        _finish(quiz, timed_out=True)
                        st.rerun()
                    quiz["answers"][q.id] = chosen
                    quiz["checked"].append(q.id)
                    state.store().record_response(quiz["attempt"], q, [str(c) for c in chosen], grade_mcq(q, chosen).correct)
                    st.rerun()
            else:
                feedback(q, quiz["answers"][q.id], quiz["orders"][q.id])
                last = i == len(qs) - 1
                if st.button(t("See results") if last else t("Next question"), type="primary", key=f"{key}_next_{i}"):
                    if last:
                        _finish(quiz)
                    else:
                        quiz["idx"] += 1
                    st.rerun()
        return

    st.markdown(t("**{n} questions.**", n=len(qs)) + " " + (t("Exam mode: no feedback until you submit.") if quiz["mode"] == "exam" else t("Feedback is shown after submission.")))
    with st.form(f"{key}_form"):
        answers = {}
        for i, q in enumerate(qs, 1):
            st.markdown(f"###### {i}. {t(q.topic)} · {t(q.difficulty)}")
            answers[q.id] = question_input(q, key, quiz["orders"][q.id])
            st.divider()
        sub = st.form_submit_button(t("Submit answers"), type="primary")
    if sub:
        quiz["answers"] = answers
        timed_out = _time_left(quiz) is not None and _time_left(quiz) <= 0
        _finish(quiz, timed_out)
        st.rerun()


def _results(quiz: dict) -> None:
    qs = [QUESTIONS_BY_ID[q] for q in quiz["qids"]]
    res = [grade_mcq(q, quiz["answers"].get(q.id, [])) for q in qs]
    n = sum(r.correct for r in res)
    st.markdown(t("## Score: {n}/{total} ({pct:.0f}%)", n=n, total=len(qs), pct=100 * n / len(qs)))
    if quiz["timed_out"]:
        st.warning(t("Submitted after the time limit (or time ran out); unanswered questions count as incorrect."))
    df = pd.DataFrame({"module": [MODULES[q.module] for q in qs], "topic": [t(q.topic) for q in qs], "correct": [r.correct for r in res]})
    by_topic = df.groupby(["module", "topic"])["correct"].agg(["sum", "count"]).reset_index()
    by_topic["accuracy"] = (100 * by_topic["sum"] / by_topic["count"]).round(0)
    st.markdown(t("**Results by topic**"))
    st.dataframe(by_topic.rename(columns={"sum": "correct", "count": "questions"}).rename(columns=t), hide_index=True, width="stretch")
    weak = by_topic[by_topic["accuracy"] < 60]["topic"].tolist()
    if weak:
        st.info(t("Revise: {topics}. The dashboard will recommend targeted lessons.", topics=", ".join(weak)))
    st.markdown(t("**Question review**"))
    for i, (q, r) in enumerate(zip(qs, res), 1):
        with st.expander(f"{'✔' if r.correct else '✘'} {i}. {q.stem[:110]}"):
            feedback(q, quiz["answers"].get(q.id, []), quiz["orders"][q.id])
    c1, c2 = st.columns(2)
    if c1.button(t("Retry with a new set of questions"), type="primary", key="quiz_retry", icon=":material/refresh:"):
        cfg = quiz["config"]
        pool = filter_questions(cfg.get("modules"), cfg.get("topics"), cfg.get("difficulties"))
        missed = {q.id for q, r in zip(qs, res) if not r.correct}
        new = sample_questions(pool, min(cfg.get("n", len(qs)), len(pool)), avoid=set(quiz["qids"]), prefer=missed)
        _start_quiz(new, quiz["mode"], cfg.get("shuffle", True), cfg.get("minutes"), quiz["kind"], cfg)
        st.rerun()
    if c2.button(t("Build a different quiz"), key="quiz_new"):
        st.session_state.pop("quiz", None)
        st.rerun()


# --------------------------------------------------------------------------- business cases
@st.cache_data(show_spinner=False)
def _evidence(case_id: str, lang: str):
    case = case_mod.CASES_BY_ID[case_id]
    return case_mod.EVIDENCE_BUILDERS[case.evidence_builder]()


def _cases() -> None:
    store = state.store()
    st.markdown(t("Scenario-based assessments. **Decision questions are graded automatically.** Your written answer is assessed with a "
                  "**transparent rubric that you apply yourself** after comparing with an exemplar - the lab does not claim to grade free text automatically. "
                  "Total = 50% decision questions + 50% rubric self-assessment."))
    subs = store.case_submissions()
    done = subs.groupby("case_id")["total_score"].last().to_dict() if not subs.empty else {}
    cid = st.selectbox(t("Case"), list(case_mod.CASES_BY_ID), key="case_sel",
                       format_func=lambda c: f"{case_mod.CASES_BY_ID[c].title}" + (t("  ·  last score {s:.0f}", s=done[c]) if c in done else ""))
    case = case_mod.CASES_BY_ID[cid]
    st.markdown(f"### {case.title}")
    st.markdown(f":gray-background[{MODULES[case.module]}] · {case.scenario}")
    with st.container(border=True):
        with st.spinner(t("Preparing evidence...")):
            blocks = _evidence(cid, get_lang())
        evidence_blocks(blocks)
    skey = f"case_{cid}"
    if skey not in st.session_state:
        with st.form(f"form_{cid}"):
            answers = []
            for i, obj in enumerate(case.objectives):
                if obj.multi:
                    st.markdown(f"**{i + 1}. {obj.prompt}**")
                    answers.append([j for j, o in enumerate(obj.options) if st.checkbox(o, key=f"{skey}_o{i}_{j}")])
                else:
                    sel = st.radio(f"**{i + 1}. {obj.prompt}**", obj.options, index=None, key=f"{skey}_o{i}")
                    answers.append([obj.options.index(sel)] if sel is not None else [])
            text = st.text_area(t("**Written answer.**") + f" {case.prompt}", height=220, key=f"{skey}_text")
            ok = st.form_submit_button(t("Submit case"), type="primary")
        if ok:
            if any(not a for a in answers) or len(text.strip()) < 40:
                st.warning(t("Answer every decision question and write at least a few sentences."))
            else:
                st.session_state[skey] = {"answers": answers, "text": text}
                st.rerun()
        return

    sub = st.session_state[skey]
    obj_score, results = case_mod.score_objectives(case, sub["answers"])
    st.markdown(t("#### Decision questions: {s:.0f}%", s=obj_score))
    for obj, a, ok in zip(case.objectives, sub["answers"], results):
        icon = ":green[✔]" if ok else ":red[✘]"
        st.markdown(f"{icon} **{obj.prompt}**  \n{t('Your answer')}: {', '.join(obj.options[i] for i in a)}  \n{t('Correct')}: {', '.join(obj.options[i] for i in obj.correct)}  \n*{obj.explanation}*")
    st.markdown(t("#### Your written answer"))
    st.info(sub["text"])
    st.markdown(t("#### Exemplar answer"))
    st.success(case.exemplar)
    st.markdown(t("#### Rubric self-assessment"))
    st.caption(t("Compare your answer with the exemplar and the descriptors. Be honest - this is evidence for your own competency profile."))
    cov = case_mod.keyword_coverage(case.rubric, sub["text"])
    levels = {}
    for crit in case.rubric:
        c1, c2 = st.columns([2, 3])
        c1.markdown(f"**{crit.name}**  \n:gray[{crit.description}]")
        if crit.name in cov:
            c1.caption(t("Advisory (not scored): indicator words found - {words}", words=", ".join(cov[crit.name]) or t("none")))
        choice = c2.radio(crit.name, crit.levels, index=None, horizontal=True, key=f"{skey}_rub_{crit.name}", label_visibility="collapsed")
        levels[crit.name] = crit.levels.index(choice) if choice else None
    c1, c2 = st.columns(2)
    if c1.button(t("Save assessment"), type="primary", key=f"{skey}_save", disabled=any(v is None for v in levels.values())):
        self_score = case_mod.score_self_assessment(case.rubric, levels)
        total = case_mod.combined_score(obj_score, self_score)
        store.record_case(cid, sub["text"], obj_score, levels, self_score, total)
        st.success(t("Saved. Decision questions {o:.0f}% · self-assessment {s:.0f}% · total {tot:.0f}%.", o=obj_score, s=self_score, tot=total))
    if c2.button(t("Start this case again"), key=f"{skey}_again"):
        for k in [k for k in st.session_state if k.startswith(skey)]:
            del st.session_state[k]
        st.rerun()


# --------------------------------------------------------------------------- final assessment
def _final() -> None:
    st.markdown(t("The final competency assessment samples skills across all five modules: **15 exam-mode questions** (3 per module, at least one Advanced/Professional each, 30-minute limit) "
                  "plus **5 coding tasks** - one per module. Your competency profile combines this with all other evidence."))
    quiz = st.session_state.get("quiz")
    store = state.store()
    hist = store.quiz_history()
    finals = hist[hist["kind"] == "final"] if not hist.empty else hist
    if len(finals):
        st.markdown(t("Previous final attempts: ") + ", ".join(f"{s:.0f}%" for s in finals["score"]))
    st.markdown(t("#### Part A - Knowledge (exam mode)"))
    if quiz and quiz["kind"] == "final":
        if quiz["finished"]:
            _results_final(quiz)
        else:
            _run_quiz(quiz)
    elif st.button(t("Start Part A (30 minutes)"), type="primary", key="final_start", icon=":material/play_arrow:"):
        _start_quiz(stratified_sample(3), "exam", True, 30, "final", {"final": True, "n": 15})
        st.rerun()

    st.markdown(t("#### Part B - Practical tasks"))
    summary = store.exercise_summary()
    passed = set(summary[summary["passed"] == 1]["exercise_id"]) if not summary.empty else set()
    rows = [{t("Module"): MODULES[EXERCISES_BY_ID[e].module], t("Task"): EXERCISES_BY_ID[e].title, t("Status"): t("✅ passed") if e in passed else t("open")} for e in FINAL_EXERCISES]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.progress(len(passed & set(FINAL_EXERCISES)) / len(FINAL_EXERCISES), text=t("{n}/{total} practical tasks passed", n=len(passed & set(FINAL_EXERCISES)), total=len(FINAL_EXERCISES)))
    pick = st.selectbox(t("Open a practical task"), FINAL_EXERCISES, format_func=lambda e: EXERCISES_BY_ID[e].title, key="final_ex")
    with st.container(border=True):
        render_exercise(EXERCISES_BY_ID[pick], prefix="final")


def _results_final(quiz: dict) -> None:
    qs = [QUESTIONS_BY_ID[q] for q in quiz["qids"]]
    res = [grade_mcq(q, quiz["answers"].get(q.id, [])).correct for q in qs]
    df = pd.DataFrame({t("Module"): [MODULES[q.module] for q in qs], "correct": res}).groupby(t("Module"))["correct"].agg(["sum", "count"]).reset_index()
    df[t("Accuracy %")] = (100 * df["sum"] / df["count"]).round(0)
    st.markdown(t("**Part A score: {n}/{total} ({pct:.0f}%)**", n=sum(res), total=len(qs), pct=100 * sum(res) / len(qs)))
    st.dataframe(df.rename(columns={"sum": t("Correct"), "count": t("Questions")}), hide_index=True, width="stretch")
    for i, q in enumerate(qs, 1):
        with st.expander(f"{'✔' if res[i - 1] else '✘'} {i}. {q.stem[:110]}"):
            feedback(q, quiz["answers"].get(q.id, []), quiz["orders"][q.id])
    if st.button(t("Close results"), key="final_close"):
        st.session_state.pop("quiz", None)
        st.rerun()


# --------------------------------------------------------------------------- history
def _history() -> None:
    store = state.store()
    hist = store.quiz_history()
    if hist.empty:
        st.info(t("No completed quizzes yet."))
    else:
        h = hist[["attempt_id", "kind", "started_at", "n_questions", "n_correct", "score", "timed_out"]].sort_values("attempt_id", ascending=False)
        st.dataframe(h.rename(columns=t), hide_index=True, width="stretch")
        aid = st.selectbox(t("Review attempt"), h["attempt_id"], key="hist_sel")
        r = store.attempt_responses(int(aid))
        for _, row in r.iterrows():
            q = QUESTIONS_BY_ID.get(row["question_id"])
            if not q:
                continue
            chosen = [int(c) for c in json.loads(row["chosen"])] if row["chosen"] else []
            with st.expander(f"{'✔' if row['correct'] else '✘'} {q.stem[:120]}"):
                feedback(q, chosen, list(range(len(q.options))))
    subs = store.case_submissions()
    if not subs.empty:
        st.markdown(t("#### Business case submissions"))
        st.dataframe(subs[["case_id", "submitted_at", "objective_score", "self_score", "total_score"]].rename(columns=t), hide_index=True, width="stretch")
    ex = store.exercise_attempts()
    if not ex.empty:
        st.markdown(t("#### Coding submissions"))
        st.dataframe(ex[["exercise_id", "language", "submitted_at", "score", "passed", "hints_used", "solution_viewed"]].sort_values("submitted_at", ascending=False).rename(columns=t),
                     hide_index=True, width="stretch")
