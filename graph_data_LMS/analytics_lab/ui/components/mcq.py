"""Multiple-choice rendering, answer randomisation and feedback."""

from __future__ import annotations

import random

import streamlit as st

from analytics_lab.assessment.bank import QUESTIONS_BY_ID
from analytics_lab.assessment.grading import grade_mcq
from analytics_lab.i18n import t
from analytics_lab.models import Question
from analytics_lab.ui import state

LETTERS = "ABCDEFGH"


def option_order(q: Question, key: str, shuffle: bool = True) -> list[int]:
    """Stable per-session shuffled option order for a question."""
    skey = f"order_{key}_{q.id}"
    if skey not in st.session_state:
        order = list(range(len(q.options)))
        if shuffle and q.shuffle:
            random.shuffle(order)
        st.session_state[skey] = order
    return st.session_state[skey]


def question_input(q: Question, key: str, order: list[int], disabled: bool = False) -> list[int]:
    """Render inputs and return chosen ORIGINAL option indices."""
    st.markdown(f"**{q.stem}**")
    if q.code:
        st.code(q.code, language="sql" if q.tool == "SQL" else "text")
    labels = [f"{LETTERS[i]}. {q.options[o].text}" for i, o in enumerate(order)]
    if q.qtype == "multi":
        st.caption(t("Select all that apply."))
        chosen = []
        for i, o in enumerate(order):
            if st.checkbox(labels[i], key=f"{key}_{q.id}_opt{o}", disabled=disabled):
                chosen.append(o)
        return chosen
    sel = st.radio(t("Answer"), labels, index=None, key=f"{key}_{q.id}_radio", label_visibility="collapsed", disabled=disabled)
    return [order[labels.index(sel)]] if sel is not None else []


def feedback(q: Question, chosen: list[int], order: list[int]) -> bool:
    res = grade_mcq(q, chosen)
    if res.correct:
        st.success(t("Correct."), icon=":material/check_circle:")
    elif q.qtype == "multi" and res.partial > 0:
        st.warning(t("Partially correct ({p:.0%}). A multi-select question counts as correct only when all choices match.", p=res.partial), icon=":material/error:")
    else:
        st.error(t("Not quite."), icon=":material/cancel:")
    for i, o in enumerate(order):
        opt = q.options[o]
        mark = "✔" if opt.correct else "✘"
        picked = " *" + t("(your answer)") + "*" if o in chosen else ""
        color = "green" if opt.correct else ("red" if o in chosen else "gray")
        st.markdown(f":{color}[{mark} **{LETTERS[i]}.** {opt.text}]{picked}  \n&nbsp;&nbsp;&nbsp;&nbsp;{opt.why}")
    st.info(q.explanation, icon=":material/school:")
    return res.correct


def knowledge_check(qids: list[str], key: str) -> float | None:
    """Lesson knowledge check (immediate feedback). Returns score 0-100 once submitted."""
    qs = [QUESTIONS_BY_ID[q] for q in qids if q in QUESTIONS_BY_ID]
    if not qs:
        st.caption(t("No knowledge-check questions for this lesson."))
        return None
    done_key = f"kc_done_{key}"
    store = state.store()
    if done_key not in st.session_state:
        with st.form(f"kc_form_{key}"):
            answers = {}
            for i, q in enumerate(qs, 1):
                st.markdown(t("###### Question {i} of {n} · {topic}", i=i, n=len(qs), topic=t(q.topic)))
                answers[q.id] = question_input(q, f"kc_{key}", option_order(q, f"kc_{key}"))
                st.divider()
            submitted = st.form_submit_button(t("Check my answers"), type="primary")
        if submitted:
            if any(not a for a in answers.values()):
                st.warning(t("Answer every question before checking."))
                return None
            attempt = store.start_quiz("lesson_check", len(qs), config={"lesson_key": key})
            n_correct = 0
            for q in qs:
                ok = grade_mcq(q, answers[q.id]).correct
                n_correct += ok
                store.record_response(attempt, q, [str(a) for a in answers[q.id]], ok)
            store.finish_quiz(attempt, n_correct)
            st.session_state[done_key] = {"answers": answers, "score": 100 * n_correct / len(qs)}
            st.rerun()
        return None
    result = st.session_state[done_key]
    st.markdown(t("### Score: {s:.0f}%", s=result["score"]))
    for i, q in enumerate(qs, 1):
        with st.container(border=True):
            st.markdown(t("**Question {i}.**", i=i) + f" {q.stem}")
            if q.code:
                st.code(q.code, language="sql" if q.tool == "SQL" else "text")
            feedback(q, result["answers"][q.id], option_order(q, f"kc_{key}"))
    if st.button(t("Try these questions again"), key=f"kc_retry_{key}"):
        for k in list(st.session_state.keys()):
            if k.startswith(f"kc_{key}_") or k.startswith(f"order_kc_{key}_") or k == done_key:
                del st.session_state[k]
        st.rerun()
    return result["score"]
