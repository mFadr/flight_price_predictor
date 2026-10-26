"""Progress dashboard: evidence-based concept states, error categories, corrections."""

from __future__ import annotations

from collections import Counter

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from tutor.app import AppContext
from tutor.domain import EvidenceKind, MasteryState
from tutor.storage.backup import export_progress

STATE_COLORS = {
    MasteryState.NOT_ASSESSED: "#eef1f6", MasteryState.INTRODUCED: "#e8f0ff", MasteryState.DEVELOPING: "#fff7e0",
    MasteryState.DEMONSTRATED: "#e3f6e8", MasteryState.NEEDS_REVISION: "#fdeeee",
}


class Progress(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        head = QHBoxLayout()
        t = QLabel("Learning progress")
        t.setProperty("class", "h1")
        head.addWidget(t, 1)
        self.subject = QComboBox()
        self.subject.currentIndexChanged.connect(self.refresh)
        head.addWidget(QLabel("Subject:"))
        head.addWidget(self.subject)
        root.addLayout(head)
        note = QLabel("These are estimates from recorded evidence - not exact scores. “Not assessed” means no evidence yet, "
                      "not a lack of knowledge. Select a row and choose “Correct this assessment” if it is wrong.")
        note.setWordWrap(True)
        note.setProperty("class", "muted")
        root.addWidget(note)

        split = QSplitter(Qt.Orientation.Vertical)
        root.addWidget(split, 1)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Subject", "Topic", "Concept", "State", "Attempts", "Independent ✔",
                                              "Certainty", "Recurring errors"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._show_detail)
        split.addWidget(self.table)

        bottom = QSplitter(Qt.Orientation.Horizontal)
        self.detail = QTextBrowser()
        bottom.addWidget(self.detail)
        self.fig = Figure(figsize=(4, 2.6), layout="tight")
        self.canvas = FigureCanvasQTAgg(self.fig)
        bottom.addWidget(self.canvas)
        split.addWidget(bottom)
        split.setSizes([380, 260])

        row = QHBoxLayout()
        for text, fn in (("Correct this assessment…", self._override), ("Export progress (Markdown)", self._export)):
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        row.addStretch(1)
        root.addLayout(row)
        self._statuses = []

    def refresh(self) -> None:
        cur = self.subject.currentData()
        all_st = self.ctx.engine.knowledge.all_statuses()
        subjects = sorted({s.subject for s in all_st})
        self.subject.blockSignals(True)
        self.subject.clear()
        self.subject.addItem("All subjects", None)
        for s in subjects:
            self.subject.addItem(s, s)
        idx = self.subject.findData(cur)
        self.subject.setCurrentIndex(max(0, idx))
        self.subject.blockSignals(False)
        cur = self.subject.currentData()
        self._statuses = [s for s in all_st if cur is None or s.subject == cur]
        self.table.setRowCount(len(self._statuses))
        for r, s in enumerate(self._statuses):
            vals = [s.subject, s.topic, s.concept, s.state.label + (" (set by you)" if s.overridden else ""),
                    str(s.attempts), str(s.independent_successes), s.certainty,
                    ", ".join(c.label for c in s.recurring_errors)]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c == 3:
                    it.setBackground(Qt.GlobalColor.transparent)
                    from PySide6.QtGui import QColor
                    it.setBackground(QColor(STATE_COLORS[s.state]))
                it.setToolTip(s.rationale)
                self.table.setItem(r, c, it)
        self._chart()
        self._summary()

    def _summary(self) -> None:
        sts = self._statuses
        need_evidence = [s for s in sts if s.certainty in ("none", "low")]
        revise = [s for s in sts if s.state == MasteryState.NEEDS_REVISION]
        ev = self.ctx.db.evidence(self.subject.currentData())
        attempts = [e for e in ev if e.kind == EvidenceKind.ATTEMPT]
        recent = attempts[-10:]
        rate = f"{sum(1 for e in recent if e.correct)}/{len(recent)} of the last attempts fully correct" if recent else "no attempts yet"
        html = [f"<p><b>Exercises attempted:</b> {len({e.exercise_id for e in attempts})} · <b>Recent performance:</b> {rate}</p>"]
        if revise:
            html.append("<p><b>Recommended review:</b> " + ", ".join(f"{s.concept} ({s.topic})" for s in revise[:6]) + "</p>")
        if need_evidence:
            html.append("<p><b>Needs more evidence before any conclusion:</b> " + ", ".join(s.concept for s in need_evidence[:8]) + "</p>")
        html.append("<p style='color:#5d6779'>Select a concept to see why it has its state.</p>")
        self.detail.setHtml("".join(html))

    def _show_detail(self) -> None:
        r = self.table.currentRow()
        if 0 <= r < len(self._statuses):
            s = self._statuses[r]
            last = s.last_seen.astimezone().strftime("%d %b %Y") if s.last_seen else "-"
            rate = f"{s.recent_success_rate:.0%}" if s.recent_success_rate is not None else "-"
            self.detail.setHtml(
                f"<h3>{s.concept}</h3><p><b>{s.state.label}</b> · certainty {s.certainty}</p><p>{s.rationale}</p>"
                f"<p>Evidence items: {s.evidence_count} · attempts: {s.attempts} · independent correct: {s.independent_successes} · "
                f"recent success: {rate} · last activity: {last}</p>"
                + (f"<p>Your note: {s.override_note}</p>" if s.override_note else ""))

    def _chart(self) -> None:
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ev = self.ctx.db.evidence(self.subject.currentData())
        cnt = Counter(e.error_category.label for e in ev if e.error_category)
        if cnt:
            labels, values = zip(*cnt.most_common(7))
            ax.barh(range(len(values)), values, color="#3b6fd8")
            ax.set_yticks(range(len(values)), [lb[:30] for lb in labels], fontsize=7)
            ax.invert_yaxis()
            ax.set_xlabel("number of attempts (raw count)", fontsize=8)
            ax.xaxis.get_major_locator().set_params(integer=True)
        else:
            ax.text(0.5, 0.5, "No errors recorded yet", ha="center", va="center")
            ax.axis("off")
        ax.set_title("Recurring error categories", fontsize=9)
        self.canvas.draw_idle()

    def _override(self) -> None:
        r = self.table.currentRow()
        if not 0 <= r < len(self._statuses):
            QMessageBox.information(self, "Correct assessment", "Select a concept first.")
            return
        s = self._statuses[r]
        dlg = QDialog(self)
        dlg.setWindowTitle("Correct this assessment")
        form = QFormLayout(dlg)
        box = QComboBox()
        box.addItem("Use the evidence-based estimate (remove my correction)", None)
        for st in MasteryState:
            box.addItem(st.label, st)
        note = QLineEdit(s.override_note)
        note.setPlaceholderText("Why? e.g. 'I already studied this in school'")
        form.addRow(QLabel(f"<b>{s.concept}</b> - currently: {s.state.label}"))
        form.addRow("New state:", box)
        form.addRow("Note:", note)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.ctx.engine.knowledge.override(s.subject, s.topic, s.concept, box.currentData(), note.text())
            self.refresh()

    def _export(self) -> None:
        p = export_progress(self.ctx.db, self._statuses, self.ctx.paths.exports)
        QMessageBox.information(self, "Exported", f"Saved to:\n{p}")
