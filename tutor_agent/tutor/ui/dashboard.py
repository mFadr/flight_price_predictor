"""Dashboard: model status, recent sessions, revision topics, recommendations, new session dialog."""

from __future__ import annotations

import html

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from tutor.app import AppContext
from tutor.domain import LEVEL_NAMES, SUBJECTS, Session, SessionStatus, TeachingStyle
from tutor.llm.base import ProviderStatus
from tutor.storage.backup import export_session
from tutor.ui import workers


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    f = QFrame()
    f.setProperty("class", "card")
    v = QVBoxLayout(f)
    v.setContentsMargins(14, 12, 14, 12)
    t = QLabel(title)
    t.setProperty("class", "h2")
    v.addWidget(t)
    return f, v


class NewSessionDialog(QDialog):
    def __init__(self, ctx: AppContext, parent=None, subject: str = "", topic: str = ""):
        super().__init__(parent)
        self.setWindowTitle("New tutoring session")
        self.setMinimumWidth(480)
        prof = ctx.db.load_profile()
        form = QFormLayout(self)
        self.subject = QComboBox()
        self.subject.setEditable(True)
        for s in dict.fromkeys(prof.subjects + SUBJECTS):
            self.subject.addItem(s)
        if subject:
            self.subject.setCurrentText(subject)
        self.topic = QLineEdit(topic)
        self.topic.setPlaceholderText("e.g. chain rule, recursion, hypothesis testing, elasticity, projectile motion")
        self.goal = QLineEdit()
        self.goal.setPlaceholderText("optional - e.g. prepare for Friday's exam, understand my homework question")
        self.level = QComboBox()
        for lv, name in LEVEL_NAMES.items():
            self.level.addItem(f"{lv} · {name}", lv)
        self.level.setCurrentIndex(prof.default_level - 1)
        self.style = QComboBox()
        for st in TeachingStyle:
            self.style.addItem(st.label, st)
        self.style.setCurrentIndex(list(TeachingStyle).index(prof.teaching_style))
        self.socratic = QCheckBox("Socratic mode (guided questions and graduated hints)")
        self.socratic.setChecked(prof.preferences.prefers_hints)
        self.materials = QCheckBox("Use my uploaded learning materials when relevant")
        self.materials.setChecked(True)
        form.addRow("Subject:", self.subject)
        form.addRow("Topic:", self.topic)
        form.addRow("Goal:", self.goal)
        form.addRow("Level:", self.level)
        form.addRow("Teaching style:", self.style)
        form.addRow(self.socratic)
        form.addRow(self.materials)
        note = QLabel("The level is a teaching preference, not a judgement - you can change it any time.")
        note.setProperty("class", "muted")
        note.setWordWrap(True)
        form.addRow(note)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setText("Start learning")
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

    def _ok(self) -> None:
        if not self.topic.text().strip():
            self.topic.setFocus()
            return
        self.accept()

    def values(self) -> dict:
        return dict(subject=self.subject.currentText().strip() or "Other", topic=self.topic.text().strip(),
                    goal=self.goal.text().strip(), level=self.level.currentData(), style=self.style.currentData(),
                    socratic=self.socratic.isChecked(), use_materials=self.materials.isChecked())


class Dashboard(QWidget):
    open_session = Signal(object, bool)  # session, start
    goto = Signal(str)

    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self._status_worker = None
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        head = QHBoxLayout()
        t = QLabel("Your learning desk")
        t.setProperty("class", "h1")
        head.addWidget(t, 1)
        b = QPushButton("＋  Start a new session")
        b.setProperty("class", "primary")
        b.clicked.connect(lambda: self.new_session())
        head.addWidget(b)
        root.addLayout(head)

        grid = QGridLayout()
        grid.setSpacing(14)
        root.addLayout(grid, 1)

        f, v = card("Recent sessions")
        self.sessions = QListWidget()
        self.sessions.itemDoubleClicked.connect(self._resume)
        v.addWidget(self.sessions, 1)
        row = QHBoxLayout()
        for text, fn in (("Resume", self._resume), ("Export notes", self._export), ("Delete…", self._delete)):
            bt = QPushButton(text)
            bt.clicked.connect(fn)
            if text.startswith("Delete"):
                bt.setProperty("class", "danger")
            row.addWidget(bt)
        row.addStretch(1)
        v.addLayout(row)
        grid.addWidget(f, 0, 0, 2, 1)

        f, v = card("AI model")
        self.model_info = QTextBrowser()
        self.model_info.setOpenExternalLinks(True)
        self.model_info.setMaximumHeight(170)
        v.addWidget(self.model_info)
        row = QHBoxLayout()
        bt = QPushButton("Test connection")
        bt.clicked.connect(self.check_model)
        row.addWidget(bt)
        bt = QPushButton("Settings…")
        bt.clicked.connect(lambda: self.goto.emit("settings"))
        row.addWidget(bt)
        row.addStretch(1)
        v.addLayout(row)
        grid.addWidget(f, 0, 1)

        f, v = card("Needs revision & recommended next")
        self.recs = QListWidget()
        self.recs.itemDoubleClicked.connect(self._start_rec)
        v.addWidget(self.recs)
        hint = QLabel("Double-click to start a session on it.")
        hint.setProperty("class", "muted")
        v.addWidget(hint)
        grid.addWidget(f, 1, 1)

        f, v = card("Active subjects")
        self.subjects = QLabel("")
        self.subjects.setWordWrap(True)
        v.addWidget(self.subjects)
        grid.addWidget(f, 2, 0, 1, 2)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 2)

    # ------------------------------------------------------------ data
    def refresh(self) -> None:
        self.sessions.clear()
        for s in self.ctx.db.list_sessions(40):
            state = "✔" if s.status == SessionStatus.COMPLETED else "●"
            it = QListWidgetItem(f"{state}  {s.subject} · {s.topic}    —  {s.updated.astimezone():%d %b %Y %H:%M}  (level {s.level})")
            it.setData(Qt.ItemDataRole.UserRole, s.id)
            it.setToolTip("Completed" if s.status == SessionStatus.COMPLETED else "In progress - double-click to resume")
            self.sessions.addItem(it)
        self.recs.clear()
        k = self.ctx.engine.knowledge
        for st in k.revision_candidates(6):
            it = QListWidgetItem(f"{st.state.label}: {st.concept}  ({st.subject} · {st.topic})")
            it.setData(Qt.ItemDataRole.UserRole, (st.subject, st.topic))
            it.setToolTip(st.rationale)
            self.recs.addItem(it)
        for s in self.ctx.db.list_sessions(5, SessionStatus.COMPLETED):
            for step in (s.summary.next_steps if s.summary else [])[:1]:
                it = QListWidgetItem(f"Next step: {step}  ({s.subject} · {s.topic})")
                it.setData(Qt.ItemDataRole.UserRole, (s.subject, s.topic))
                self.recs.addItem(it)
        if not self.recs.count():
            self.recs.addItem("Nothing yet - recommendations appear after a few exercises.")
        prof = self.ctx.db.load_profile()
        subj = {s.subject for s in self.ctx.db.list_sessions(200)} | set(prof.subjects)
        counts = {}
        for st in k.all_statuses():
            counts.setdefault(st.subject, []).append(st.state.label)
        lines = []
        for s in sorted(subj):
            states = counts.get(s, [])
            demo = sum(1 for x in states if x.startswith("Demonstrated"))
            lines.append(f"<b>{html.escape(s)}</b>: {len(states)} concept(s) with evidence, {demo} demonstrated")
        self.subjects.setText("<br>".join(lines) or "No subjects yet - start a session or set your subjects in Profile.")

    def check_model(self) -> None:
        if self._status_worker:
            return
        self.model_info.setHtml("<i>Checking model availability…</i>")
        router = self.ctx.router

        def job(_c, _t):
            out = []
            for p in router.chain("explain")[:2] or ([router.local] if router.local else []):
                out.append(p.check_status())
            return out
        w = workers.Worker(job)
        w.signals.done.connect(self._show_status)
        w.signals.done.connect(self._maybe_warm_up)
        w.signals.failed.connect(lambda m: self.model_info.setHtml(f"<b>Check failed:</b> {html.escape(m)}"))
        w.signals.finished.connect(lambda: setattr(self, "_status_worker", None))
        self._status_worker = w
        workers.start(w)

    def _show_status(self, statuses: list[ProviderStatus]) -> None:
        cfg = self.ctx.cfg
        parts = [f"<p>Mode: <b>{cfg.mode.value}</b> - " + (
            "everything stays on this computer." if not self.ctx.router.transmits_externally() else
            "<span style='color:#8a4b00'><b>conversation content is sent to a cloud provider.</b></span>") + "</p>"]
        for st in statuses:
            icon = "🟢" if st.ok else "🔴"
            where = "local" if st.is_local else "cloud"
            parts.append(f"<p>{icon} <b>{html.escape(st.provider)}</b> · {html.escape(st.model)} ({where})<br>{html.escape(st.message)}</p>")
            if st.troubleshooting:
                parts.append("<ul>" + "".join(f"<li>{html.escape(t)}</li>" for t in st.troubleshooting) + "</ul>")
            if not st.ok and st.available_models:
                parts.append("<p>Installed models: " + html.escape(", ".join(st.available_models[:12])) + "</p>")
        self.model_info.setHtml("".join(parts))

    def _maybe_warm_up(self, statuses: list[ProviderStatus]) -> None:
        """Load the local model into RAM in the background so the first question is not slow."""
        local = self.ctx.router.local
        if not (statuses and statuses[0].ok and statuses[0].is_local and hasattr(local, "warm_up")):
            return
        if local.is_loaded() or getattr(self, "_warm_worker", None):
            return
        self._base_status = self.model_info.toHtml()
        self.model_info.append("<p>⏳ <b>Loading the model into memory…</b> The first start can take a few minutes on "
                               "laptops with little free RAM; you can already start a session.</p>")
        w = workers.Worker(lambda _c, _t: local.warm_up())
        w.signals.done.connect(lambda ok: self.model_info.append(
            "<p>✅ Model loaded and ready.</p>" if ok else "<p>⚠ The model could not be preloaded; it will load on the first question.</p>"))
        w.signals.finished.connect(lambda: setattr(self, "_warm_worker", None))
        self._warm_worker = w
        workers.start(w)

    # ------------------------------------------------------------ actions
    def new_session(self, subject: str = "", topic: str = "") -> None:
        dlg = NewSessionDialog(self.ctx, self, subject, topic)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            s = self.ctx.engine.start_session(**dlg.values())
            self.open_session.emit(s, True)

    def _selected(self) -> Session | None:
        it = self.sessions.currentItem()
        return self.ctx.db.get_session(it.data(Qt.ItemDataRole.UserRole)) if it else None

    def _resume(self, *_):
        s = self._selected()
        if s:
            self.open_session.emit(s, False)

    def _export(self) -> None:
        s = self._selected()
        if s:
            p = export_session(self.ctx.db, s, self.ctx.paths.exports)
            QMessageBox.information(self, "Exported", f"Saved to:\n{p}")

    def _delete(self) -> None:
        s = self._selected()
        if not s:
            return
        if QMessageBox.warning(self, "Delete session", f"Permanently delete the session '{s.topic}' and its evidence?\nThis cannot be undone.",
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.ctx.db.delete_session(s.id)
            self.refresh()

    def _start_rec(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.new_session(*data)
