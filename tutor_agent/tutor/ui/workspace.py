"""Tutoring workspace: conversation, action bar, exercise panel, visual panel, topic status."""

from __future__ import annotations

import html
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QFont, QPixmap, QTextCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from tutor.app import AppContext
from tutor.domain import (
    LEVEL_NAMES,
    AnswerType,
    Exercise,
    Message,
    MessageKind,
    Role,
    Session,
    SessionStatus,
    TeachingStyle,
)
from tutor.engine.hints import HINT_LEVELS
from tutor.engine.tutor import TurnResult
from tutor.storage.backup import export_session
from tutor.tools.viz import VisualizationSpec
from tutor.ui import workers
from tutor.ui.render import Renderer, escape_plain
from tutor.ui.theme import palette


def _btn(text: str, tip: str, cls: str = "action") -> QPushButton:
    b = QPushButton(text)
    b.setToolTip(tip)
    b.setProperty("class", cls)
    return b


class Workspace(QWidget):
    session_changed = Signal()
    status_message = Signal(str)

    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.session: Session | None = None
        self.worker: workers.Worker | None = None
        self.renderer = Renderer(ctx.cfg.ui_font_size)
        self._html_cache: dict[str, str] = {}
        self._live = ""
        self._live_label = ""
        self._messages: list[Message] = []
        self._visuals: list[Message] = []
        self._timer = QTimer(self)
        self._timer.setInterval(90)
        self._timer.timeout.connect(self._render_live)
        self._build()
        self._set_busy(False)
        self._show_empty()

    # ================================================================ layout
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 8)

        # --- header with session controls
        head = QHBoxLayout()
        self.title = QLabel("No session")
        self.title.setProperty("class", "h2")
        head.addWidget(self.title, 1)
        head.addWidget(QLabel("Level:"))
        self.level_box = QComboBox()
        for lv, name in LEVEL_NAMES.items():
            self.level_box.addItem(f"{lv} · {name}", lv)
        self.level_box.setToolTip("Teaching level - a preference, not a judgement. Changing it fixes the level (auto-adjust off).")
        self.level_box.activated.connect(self._level_chosen)
        head.addWidget(self.level_box)
        self.auto_level = QCheckBox("Auto-adjust")
        self.auto_level.setToolTip("Let the tutor adjust the level based on evidence (several answers, never a single one).")
        self.auto_level.toggled.connect(self._auto_toggled)
        head.addWidget(self.auto_level)
        head.addWidget(QLabel("Style:"))
        self.style_box = QComboBox()
        for st in TeachingStyle:
            self.style_box.addItem(st.label, st)
        self.style_box.activated.connect(self._style_chosen)
        head.addWidget(self.style_box)
        self.socratic = QCheckBox("Socratic")
        self.socratic.setToolTip("Guide with questions and graduated hints instead of direct answers.")
        self.socratic.toggled.connect(self._socratic_toggled)
        head.addWidget(self.socratic)
        root.addLayout(head)

        split = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(split, 1)

        # --- left: conversation
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        self.view = QTextBrowser()
        self.view.setOpenLinks(False)
        self.view.anchorClicked.connect(self._anchor)
        lv.addWidget(self.view, 1)

        bar = QGridLayout()
        bar.setSpacing(6)
        self.b_hint = _btn("💡 Hint", "Next level of help: hint → reminder → next step → partial → full solution")
        self.b_diff = _btn("🔄 Explain differently", "Explain the last idea with another representation")
        self.b_sol = _btn("📘 Worked solution", "Show the complete worked solution")
        self.b_sim = _btn("➕ Similar problem", "A new problem using the same principle (transfer check)")
        self.b_easy = _btn("⬇ Easier", "Lower the level and give an easier problem")
        self.b_hard = _btn("⬆ Harder", "Raise the level and give a harder problem")
        self.b_check = _btn("🔎 Check my reasoning", "Check the reasoning typed in the input box step by step")
        self.b_end = _btn("✔ End && summarise", "Finish the session and save a summary")
        for i, b in enumerate((self.b_hint, self.b_diff, self.b_sol, self.b_check, self.b_sim, self.b_easy, self.b_hard, self.b_end)):
            bar.addWidget(b, i // 4, i % 4)
        lv.addLayout(bar)
        self.b_hint.clicked.connect(lambda: self._run(lambda c, t: self.ctx.engine.hint(self.session, c, t), "Thinking of a hint…"))
        self.b_diff.clicked.connect(lambda: self._run(lambda c, t: self.ctx.engine.explain_differently(self.session, c, t), "Finding another explanation…"))
        self.b_sol.clicked.connect(self._solution)
        self.b_sim.clicked.connect(lambda: self._exercise("similar"))
        self.b_easy.clicked.connect(lambda: self._exercise("easier"))
        self.b_hard.clicked.connect(lambda: self._exercise("harder"))
        self.b_check.clicked.connect(self._check_reasoning)
        self.b_end.clicked.connect(self._end)

        inp = QHBoxLayout()
        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("Ask a question, explain your thinking, or type your answer…   (Ctrl+Enter to send)")
        self.input.setFixedHeight(84)
        inp.addWidget(self.input, 1)
        col = QVBoxLayout()
        self.b_send = _btn("Send", "Send (Ctrl+Enter)", "primary")
        self.b_send.clicked.connect(self._send)
        self.b_cancel = _btn("Cancel", "Stop the current request")
        self.b_cancel.clicked.connect(self._cancel)
        col.addWidget(self.b_send)
        col.addWidget(self.b_cancel)
        inp.addLayout(col)
        lv.addLayout(inp)
        QShortcut(QKeySequence("Ctrl+Return"), self.input, activated=self._send)

        prog = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.busy_label = QLabel("")
        self.busy_label.setProperty("class", "muted")
        prog.addWidget(self.busy_label)
        prog.addWidget(self.progress, 1)
        lv.addLayout(prog)
        split.addWidget(left)

        # --- right: tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_exercise_tab(), "Exercise")
        self.tabs.addTab(self._build_visual_tab(), "Visual")
        self.tabs.addTab(self._build_status_tab(), "Topic status")
        split.addWidget(self.tabs)
        split.setSizes([760, 420])

    def _build_exercise_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.ex_view = QTextBrowser()
        self.ex_view.setMinimumHeight(160)
        v.addWidget(self.ex_view, 2)
        self.ex_meta = QLabel("")
        self.ex_meta.setWordWrap(True)
        self.ex_meta.setProperty("class", "muted")
        v.addWidget(self.ex_meta)
        self.answer_line = QLineEdit()
        self.answer_line.setPlaceholderText("Final answer, e.g.  x = 4   or   3*x^2 + 2   or   12.5 m/s   or   B")
        self.answer_line.returnPressed.connect(self._submit)
        self.code_edit = QPlainTextEdit()
        self.code_edit.setFont(QFont("Consolas", 10))
        self.code_edit.setPlaceholderText("Write your Python code here. It runs in an isolated sandbox against the exercise tests.")
        self.reasoning = QPlainTextEdit()
        self.reasoning.setPlaceholderText("Your reasoning / steps (one step per line) - optional but gives much better feedback")
        self.reasoning.setFixedHeight(110)
        form = QFormLayout()
        form.addRow("Answer:", self.answer_line)
        v.addLayout(form)
        v.addWidget(self.code_edit, 2)
        v.addWidget(QLabel("Reasoning:"))
        v.addWidget(self.reasoning)
        conf = QHBoxLayout()
        conf.addWidget(QLabel("How confident are you?"))
        self.confidence = QSlider(Qt.Orientation.Horizontal)
        self.confidence.setRange(0, 5)
        self.confidence.setValue(0)
        self.confidence.setToolTip("0 = not stated, 1 = guessing … 5 = very sure")
        self.conf_label = QLabel("not stated")
        self.confidence.valueChanged.connect(lambda x: self.conf_label.setText(["not stated", "guessing", "unsure", "somewhat", "fairly sure", "very sure"][x]))
        conf.addWidget(self.confidence, 1)
        conf.addWidget(self.conf_label)
        v.addLayout(conf)
        row = QHBoxLayout()
        self.hint_state = QLabel("")
        self.hint_state.setProperty("class", "muted")
        row.addWidget(self.hint_state, 1)
        self.b_submit = _btn("Submit answer", "Evaluate the answer (deterministic check where possible + diagnosis)", "primary")
        self.b_submit.clicked.connect(self._submit)
        row.addWidget(self.b_submit)
        v.addLayout(row)
        self.b_first = _btn("📝 Give me a practice problem", "Generate an exercise for the current concept", "primary")
        self.b_first.clicked.connect(lambda: self._exercise("first"))
        v.addWidget(self.b_first)
        return w

    def _build_visual_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.viz_pick = QComboBox()
        self.viz_pick.currentIndexChanged.connect(self._show_visual)
        v.addWidget(self.viz_pick)
        self.viz_img = QLabel("Diagrams from the tutor appear here.")
        self.viz_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.viz_img.setMinimumHeight(260)
        v.addWidget(self.viz_img, 1)
        self.viz_caption = QLabel("")
        self.viz_caption.setWordWrap(True)
        self.viz_caption.setProperty("class", "muted")
        v.addWidget(self.viz_caption)
        ask = QHBoxLayout()
        self.viz_elem = QComboBox()
        self.viz_elem.setToolTip("Pick a part of the diagram to ask about")
        self.viz_q = QLineEdit()
        self.viz_q.setPlaceholderText("Ask about this part of the diagram…")
        self.b_viz_ask = _btn("Ask", "Ask the tutor about the selected part")
        self.b_viz_ask.clicked.connect(self._ask_visual)
        ask.addWidget(self.viz_elem)
        ask.addWidget(self.viz_q, 1)
        ask.addWidget(self.b_viz_ask)
        v.addLayout(ask)
        plot = QHBoxLayout()
        self.plot_expr = QLineEdit()
        self.plot_expr.setPlaceholderText("Plot your own function, e.g.  x^3 - 3x ,  sin(x)/x")
        self.plot_range = QLineEdit("-5, 5")
        self.plot_range.setFixedWidth(70)
        b = _btn("Plot", "Plot locally with SymPy + Matplotlib")
        b.clicked.connect(self._plot)
        self.plot_expr.returnPressed.connect(self._plot)
        plot.addWidget(self.plot_expr, 1)
        plot.addWidget(self.plot_range)
        plot.addWidget(b)
        v.addLayout(plot)
        return w

    def _build_status_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.status_view = QTextBrowser()
        v.addWidget(self.status_view)
        b = _btn("Export session notes (Markdown)", "Save this session as a Markdown file in the exports folder")
        b.clicked.connect(self._export)
        v.addWidget(b)
        return w

    # ================================================================ session
    def open_session(self, session: Session, start: bool = False) -> None:
        if self.worker:
            self._cancel()
        self.session = session
        self._html_cache.clear()
        self._sync_controls()
        self._reload()
        if start:
            self._run(lambda c, t: self.ctx.engine.opening(self.session, c, t), "Preparing your session…")

    def _sync_controls(self) -> None:
        s = self.session
        if not s:
            return
        self.title.setText(f"{s.subject} · {s.topic}" + ("   (completed)" if s.status == SessionStatus.COMPLETED else ""))
        self.level_box.setCurrentIndex(s.level - 1)
        for w, val in ((self.auto_level, not s.level_locked), (self.socratic, s.socratic)):
            w.blockSignals(True)
            w.setChecked(val)
            w.blockSignals(False)
        self.style_box.setCurrentIndex(list(TeachingStyle).index(s.style))

    def _level_chosen(self) -> None:
        if not self.session:
            return
        lv = self.level_box.currentData()
        if lv != self.session.level:
            self.ctx.engine.set_level(self.session, lv, lock=True)
            self._sync_controls()
            self._reload()

    def _auto_toggled(self, on: bool) -> None:
        if self.session:
            self.session.level_locked = not on
            self.ctx.db.save_session(self.session)

    def _style_chosen(self) -> None:
        if self.session:
            self.session.style = self.style_box.currentData()
            self.ctx.db.save_session(self.session)

    def _socratic_toggled(self, on: bool) -> None:
        if self.session:
            self.session.socratic = on
            self.ctx.db.save_session(self.session)

    # ================================================================ rendering
    def _show_empty(self) -> None:
        self.view.setHtml("<div style='padding:40px; color:#5d6779; font-size:13pt'><h2>Welcome!</h2>"
                          "<p>Start a new session from the <b>Dashboard</b>, or resume a previous one.</p>"
                          "<p>The tutor explains, asks questions, gives graduated hints and checks your answers - "
                          "but the goal is that <b>you</b> learn to solve problems on your own.</p></div>")
        for b in (self.b_hint, self.b_diff, self.b_sol, self.b_sim, self.b_easy, self.b_hard, self.b_check, self.b_end,
                  self.b_send, self.b_submit, self.b_first):
            b.setEnabled(False)

    def _bubble(self, m: Message) -> str:
        if m.id in self._html_cache:
            return self._html_cache[m.id]
        c = palette(self.ctx.cfg.high_contrast)
        doc = self.view.document()
        if m.kind == MessageKind.NOTICE:
            body = f"<div style='color:{c['muted']}; font-size:9pt; margin:4px 30px'>ℹ️ {self.renderer.to_html(m.content, doc)}</div>"
        elif m.kind == MessageKind.VISUAL:
            url = QUrl.fromLocalFile(m.meta.get("path", "")).toString()
            body = (f"<table width='100%' cellpadding='8' style='margin:6px 0'><tr><td style='background:{c['tutor']}; border:1px solid {c['border']}'>"
                    f"<a href='viz:{m.id}'><img src='{url}' width='420'></a><br><span style='color:{c['muted']}'>📊 {html.escape(m.content)} "
                    f"<a href='viz:{m.id}'>open in Visual panel</a></span></td></tr></table>")
        else:
            student = m.role == Role.USER
            bg = c["student"] if student else {
                MessageKind.HINT: c["hint"], MessageKind.FEEDBACK: c["bad"] if m.meta.get("correctness") == "incorrect" else c["feedback"],
                MessageKind.SOLUTION: c["solution"], MessageKind.EXERCISE: c["exercise"], MessageKind.SUMMARY: c["feedback"],
            }.get(m.kind, c["tutor"])
            who = "You" if student else "Tutor"
            align = "margin-left:60px" if student else "margin-right:30px"
            body = (f"<table width='100%' cellpadding='10' style='margin:6px 0; {align}'><tr><td style='background:{bg}; border:1px solid {c['border']}'>"
                    f"<p style='margin:0; color:{c['muted']}; font-size:9pt'><b>{who}</b></p>{self.renderer.to_html(m.content, doc)}</td></tr></table>")
        self._html_cache[m.id] = body
        return body

    def _reload(self) -> None:
        if not self.session:
            return
        self._messages = self.ctx.db.messages(self.session.id)
        self._base_html = "".join(self._bubble(m) for m in self._messages)
        self._set_html(self._base_html)
        self._visuals = [m for m in self._messages if m.kind == MessageKind.VISUAL]
        self.viz_pick.blockSignals(True)
        self.viz_pick.clear()
        for i, m in enumerate(self._visuals):
            self.viz_pick.addItem(f"Diagram {i + 1}: {m.meta.get('spec', {}).get('kind', '')}", m.id)
        self.viz_pick.blockSignals(False)
        if self._visuals:
            self.viz_pick.setCurrentIndex(len(self._visuals) - 1)
            self._show_visual()
        self._refresh_exercise()
        self._refresh_status()
        self._set_busy(self.worker is not None)

    def _set_html(self, body: str) -> None:
        sb = self.view.verticalScrollBar()
        self.view.setHtml(f"<div style='font-size:{self.ctx.cfg.ui_font_size}pt'>{body}</div>")
        sb.setValue(sb.maximum())

    def _render_live(self) -> None:
        if not self._live:
            return
        c = palette(self.ctx.cfg.high_contrast)
        live = (f"<table width='100%' cellpadding='10' style='margin:6px 0; margin-right:30px'><tr><td style='background:{c['tutor']}; border:1px dashed {c['border']}'>"
                f"<span style='color:{c['muted']}; font-size:9pt'><b>Tutor</b> · writing…</span><br>{escape_plain(self._live)}</td></tr></table>")
        self._set_html(self._base_html + live)

    def _refresh_exercise(self) -> None:
        ex = self.ctx.engine.active_exercise(self.session) if self.session else None
        self.current_ex = ex
        if not ex:
            self.ex_view.setHtml("<p style='color:#5d6779'>No active exercise. Ask for a practice problem when you're ready.</p>")
            self.ex_meta.setText("")
            self.hint_state.setText("")
            self.code_edit.hide()
            self.answer_line.show()
            return
        doc = self.ex_view.document()
        self.ex_view.setHtml(self.renderer.to_html(self.ctx.engine.exercise_markdown(ex), doc))
        lvl = self.session.hint_levels.get(ex.id, 0)
        self.hint_state.setText(f"Help used: {lvl}/5" + (f" ({HINT_LEVELS[lvl]})" if lvl else " - none yet"))
        badge = "✔ answer key verified" if ex.validated else "⚠ answer key not machine-verified"
        self.ex_meta.setText(f"Objective: {ex.objective}\nChecking: {ex.verification_method} · {badge}")
        is_code = ex.answer_type == AnswerType.CODE
        self.code_edit.setVisible(is_code)
        self.answer_line.setVisible(not is_code)
        if is_code and not self.code_edit.toPlainText().strip():
            self.code_edit.setPlainText(ex.starter_code or f"def {ex.function_name}(...):\n    pass\n")

    def _refresh_status(self) -> None:
        if not self.session:
            return
        sts = [s for s in self.ctx.engine.knowledge.all_statuses(self.session.subject) if s.topic.lower() == self.session.topic.lower()]
        rows = "".join(
            f"<tr><td><b>{html.escape(s.concept)}</b></td><td>{s.state.label}</td><td>{s.attempts}</td><td>{s.certainty}</td></tr>"
            f"<tr><td colspan='4' style='color:#5d6779; font-size:9pt'>{html.escape(s.rationale)}</td></tr>" for s in sts)
        rec = self.ctx.engine.knowledge.recurring_errors(self.session.subject, self.session.topic)
        self.status_view.setHtml(
            f"<h3>{html.escape(self.session.topic)}</h3><table cellpadding='4' width='100%'>"
            f"<tr><th align='left'>Concept</th><th align='left'>State</th><th>Attempts</th><th>Certainty</th></tr>{rows or '<tr><td>No evidence yet.</td></tr>'}</table>"
            + (f"<p><b>Recurring errors:</b> {', '.join(c.label for c in rec)}</p>" if rec else "")
            + "<p style='color:#5d6779; font-size:9pt'>States are estimates from observed evidence. You can correct them on the Progress page.</p>")

    # ================================================================ actions
    def _run(self, fn: Callable, label: str) -> None:
        if not self.session or self.worker:
            return
        self._live, self._live_label = "", label
        w = workers.Worker(fn)
        w.signals.chunk.connect(self._on_chunk)
        w.signals.done.connect(self._on_done)
        w.signals.failed.connect(self._on_failed)
        w.signals.cancelled.connect(self._on_cancelled)
        w.signals.finished.connect(self._on_finished)
        self.worker = w
        self._set_busy(True)
        self._reload_soon()
        self._timer.start()
        workers.start(w)

    def _reload_soon(self) -> None:
        QTimer.singleShot(150, self._reload_messages_only)

    def _reload_messages_only(self) -> None:
        # Show the persisted user message immediately while the model works.
        if self.session:
            self._messages = self.ctx.db.messages(self.session.id)
            self._base_html = "".join(self._bubble(m) for m in self._messages)
            if not self._live:
                self._set_html(self._base_html)

    def _on_chunk(self, text: str) -> None:
        self._live += text

    def _on_done(self, result: object) -> None:
        if isinstance(result, TurnResult):
            if result.visuals:
                self.tabs.setCurrentIndex(1)
            elif result.exercise is not None and result.evaluation is None:
                self.tabs.setCurrentIndex(0)
                self.answer_line.clear()
                self.reasoning.clear()
                self.code_edit.clear()
                self.confidence.setValue(0)
            if result.summary:
                self.session_changed.emit()

    def _on_failed(self, msg: str) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("The tutor could not respond")
        box.setText(msg)
        box.setInformativeText("Your session is saved. Check Settings → AI Model (use 'Test connection'), then try again.")
        box.open()

    def _on_cancelled(self) -> None:
        self.status_message.emit("Request cancelled.")

    def _on_finished(self) -> None:
        self._timer.stop()
        self.worker = None
        self._live = ""
        if self.session:
            # The engine mutated and persisted this same Session object in the worker thread.
            self._sync_controls()
        self._reload()
        self.session_changed.emit()

    def _set_busy(self, busy: bool) -> None:
        has = self.session is not None
        active = has and self.session.status == SessionStatus.ACTIVE
        for b in (self.b_hint, self.b_diff, self.b_sol, self.b_sim, self.b_easy, self.b_hard, self.b_check, self.b_end, self.b_send):
            b.setEnabled(active and not busy)
        has_ex = getattr(self, "current_ex", None) is not None
        self.b_submit.setEnabled(active and not busy and has_ex)
        self.b_first.setEnabled(active and not busy)
        self.b_cancel.setEnabled(busy)
        self.progress.setVisible(busy)
        self.busy_label.setText(self._live_label if busy else "")

    def _cancel(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.busy_label.setText("Cancelling…")

    def _send(self) -> None:
        text = self.input.toPlainText().strip()
        if not text or not self.session or self.worker:
            return
        self.input.clear()
        self._run(lambda c, t: self.ctx.engine.respond(self.session, text, c, t), "Tutor is thinking…")

    def _submit(self) -> None:
        if not self.session or self.worker or not getattr(self, "current_ex", None):
            return
        ex: Exercise = self.current_ex
        ans = self.code_edit.toPlainText() if ex.answer_type == AnswerType.CODE else self.answer_line.text()
        if not ans.strip():
            self.answer_line.setFocus()
            return
        reasoning = self.reasoning.toPlainText()
        conf = self.confidence.value() or None
        self._run(lambda c, t: self.ctx.engine.submit_answer(self.session, ans, reasoning, conf, t), "Checking your answer…")

    def _solution(self) -> None:
        ex = getattr(self, "current_ex", None)
        if ex and not any(a.exercise_id == ex.id for a in self.ctx.db.attempts_for_session(self.session.id)):
            r = QMessageBox.question(self, "Show the full solution?",
                                     "You haven't attempted this problem yet. Trying first - even partially - helps you learn "
                                     "much more. A hint is also available.\n\nShow the complete solution anyway?")
            if r != QMessageBox.StandardButton.Yes:
                return
        self._run(lambda c, t: self.ctx.engine.worked_solution(self.session, c, t), "Preparing the worked solution…")

    def _exercise(self, mode: str) -> None:
        self._run(lambda c, t: self.ctx.engine.new_exercise(self.session, mode, t), "Creating and checking a practice problem…")

    def _check_reasoning(self) -> None:
        text = self.input.toPlainText().strip() or self.reasoning.toPlainText().strip()
        if not text and getattr(self, "current_ex", None) and self.current_ex.answer_type == AnswerType.CODE:
            text = self.code_edit.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Check my reasoning", "Type your steps (one per line) or code into the input box first.")
            return
        self.input.clear()
        self._run(lambda c, t: self.ctx.engine.check_reasoning(self.session, text, c, t), "Checking your reasoning…")

    def _end(self) -> None:
        if QMessageBox.question(self, "End session", "Finish this session and save a summary?") == QMessageBox.StandardButton.Yes:
            self._run(lambda c, t: self.ctx.engine.end_session(self.session, t), "Writing your session summary…")

    def _anchor(self, url: QUrl) -> None:
        if url.scheme() == "viz":
            mid = url.path() or url.toString().split(":", 1)[1]
            for i in range(self.viz_pick.count()):
                if self.viz_pick.itemData(i) == mid:
                    self.viz_pick.setCurrentIndex(i)
            self.tabs.setCurrentIndex(1)
        elif url.scheme() in ("http", "https", "file"):
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(url)

    # ================================================================ visuals
    def _current_visual(self) -> Message | None:
        mid = self.viz_pick.currentData()
        return next((m for m in self._visuals if m.id == mid), None)

    def _show_visual(self) -> None:
        m = self._current_visual()
        if not m:
            return
        pm = QPixmap(m.meta.get("path", ""))
        if not pm.isNull():
            self.viz_img.setPixmap(pm.scaledToWidth(min(560, max(300, self.tabs.width() - 30)), Qt.TransformationMode.SmoothTransformation))
        self.viz_caption.setText(m.meta.get("caption", ""))
        self.viz_elem.clear()
        self.viz_elem.addItem("whole diagram", "")
        for e in m.meta.get("elements", []):
            self.viz_elem.addItem(e, e)

    def _ask_visual(self) -> None:
        m = self._current_visual()
        if not m:
            return
        elem, q = self.viz_elem.currentData() or "", self.viz_q.text()
        self.viz_q.clear()
        self._run(lambda c, t: self.ctx.engine.ask_about_visual(self.session, m, elem, q, c, t), "Explaining the diagram…")

    def _plot(self) -> None:
        expr = self.plot_expr.text().strip()
        if not expr or not self.session:
            return
        try:
            lo, hi = (float(x) for x in self.plot_range.text().split(","))
        except ValueError:
            lo, hi = -5.0, 5.0
        spec = VisualizationSpec(kind="function_plot", expressions=[e.strip() for e in expr.split(";")], x_min=lo, x_max=hi,
                                 title=f"y = {expr}")
        self.ctx.engine.plot(self.session, spec)
        self._reload()
        self.tabs.setCurrentIndex(1)

    def _export(self) -> None:
        if not self.session:
            return
        p = export_session(self.ctx.db, self.session, self.ctx.paths.exports)
        QMessageBox.information(self, "Exported", f"Session notes saved to:\n{p}")
