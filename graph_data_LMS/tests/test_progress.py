"""Progress persistence, export, reset and recovery."""

from datetime import date, timedelta

from analytics_lab.assessment.bank import EXERCISES_BY_ID, QUESTIONS_BY_ID
from analytics_lab.progress.store import ProgressStore


def test_persists_across_restarts(tmp_path):
    path = tmp_path / "p.db"
    s1 = ProgressStore(path)
    s1.complete_lesson("ds1", 66.7)
    s1.set_setting("mastery_threshold", 85)
    ex = EXERCISES_BY_ID["ex_sql_ds1_headline"]
    s1.record_exercise(ex, True, 100, "SELECT 1", {"score": 100})
    del s1
    s2 = ProgressStore(path)  # simulates an application restart
    assert "ds1" in s2.completed_lessons()
    assert s2.get_setting("mastery_threshold") == "85"
    assert len(s2.exercise_attempts("ex_sql_ds1_headline")) == 1


def test_quiz_recording_and_history(store):
    q = QUESTIONS_BY_ID["q_ds_001"]
    a = store.start_quiz("practice", 1)
    store.record_response(a, q, ["0"], True)
    store.finish_quiz(a, 1)
    h = store.quiz_history()
    assert h.iloc[0]["score"] == 100 and len(store.attempt_responses(a)) == 1


def test_exercise_summary_assisted_flag(store):
    ex = EXERCISES_BY_ID["ex_sql_ds1_headline"]
    store.record_exercise(ex, False, 40, "x", {})
    store.record_exercise(ex, True, 100, "y", {}, solution_viewed=True)
    s = store.exercise_summary().iloc[0]
    assert s["attempts"] == 2 and s["passed"] == 1 and s["passed_unassisted"] == 0


def test_streak(store):
    today = date.today()
    with store.conn() as c:
        for d in (today, today - timedelta(days=1), today - timedelta(days=2), today - timedelta(days=5)):
            c.execute("INSERT INTO activity(ts, kind) VALUES (?, 'x')", (d.isoformat() + "T10:00:00",))
    assert store.streak(today) == 3


def test_export_and_reset(store):
    store.complete_lesson("ds1")
    store.set_setting("learner_name", "Sam")
    data = store.export_all()
    assert data["lesson_progress"] and data["settings"]
    store.reset(keep_settings=True)
    assert not store.completed_lessons() and store.get_setting("learner_name") == "Sam"
    store.reset(keep_settings=False)
    assert store.get_setting("learner_name") == ""


def test_corrupted_database_is_recovered(tmp_path):
    path = tmp_path / "bad.db"
    path.write_bytes(b"this is not a sqlite database" * 100)
    s = ProgressStore(path)
    s.complete_lesson("ds1")
    assert "ds1" in s.completed_lessons()
    assert list(tmp_path.glob("bad.corrupt-*.db"))


def test_milestones_upsert(store):
    store.set_milestone("cap1", "m1", "in_progress", 50, "draft")
    store.set_milestone("cap1", "m1", "completed", 90, "final")
    m = store.milestones("cap1")
    assert len(m) == 1 and m.iloc[0]["status"] == "completed" and m.iloc[0]["score"] == 90
