"""Learning materials management (PDF/TXT/MD, processed locally)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tutor.app import AppContext
from tutor.domain import SUBJECTS
from tutor.materials.library import ocr_available
from tutor.ui import workers


class Materials(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.worker = None
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        t = QLabel("Learning materials")
        t.setProperty("class", "h1")
        root.addWidget(t)
        info = QLabel(
            "Add lecture notes, slides (as PDF), formula sheets or assignment texts. Text is extracted <b>on this computer</b> "
            "and the tutor uses short relevant excerpts with page references. If cloud mode is enabled, only those excerpts "
            "are sent - never whole documents. Instructions inside documents are treated as data and ignored."
            + ("" if ocr_available() else "<br><i>OCR for scanned PDFs is unavailable (install Tesseract OCR to enable it).</i>"))
        info.setWordWrap(True)
        info.setProperty("class", "muted")
        root.addWidget(info)
        row = QHBoxLayout()
        row.addWidget(QLabel("Subject:"))
        self.subject = QComboBox()
        self.subject.addItem("(any subject)", "")
        for s in SUBJECTS:
            self.subject.addItem(s, s)
        row.addWidget(self.subject)
        self.b_add = QPushButton("Add files…")
        self.b_add.setProperty("class", "primary")
        self.b_add.clicked.connect(self._add)
        row.addWidget(self.b_add)
        b = QPushButton("Remove selected")
        b.setProperty("class", "danger")
        b.clicked.connect(self._delete)
        row.addWidget(b)
        row.addStretch(1)
        self.status = QLabel("")
        row.addWidget(self.status)
        root.addLayout(row)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["File", "Subject", "Pages", "Status", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        root.addWidget(self.table, 1)

    def refresh(self) -> None:
        rows = self.ctx.library.list()
        self.table.setRowCount(len(rows))
        for r, m in enumerate(rows):
            for c, v in enumerate([m["filename"], m["subject"] or "any", str(m["pages"]), m["status"], m["note"] or ""]):
                it = QTableWidgetItem(v)
                it.setData(Qt.ItemDataRole.UserRole, m["id"])
                self.table.setItem(r, c, it)

    def _add(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Add learning materials", str(Path.home()), "Documents (*.pdf *.txt *.md)")
        if not files or self.worker:
            return
        subject = self.subject.currentData()

        def job(_c, cancel):
            out = []
            for f in files:
                cancel.check()
                try:
                    out.append((Path(f).name, self.ctx.library.ingest(Path(f), subject), None))
                except Exception as exc:
                    out.append((Path(f).name, None, str(exc)))
            return out
        self.b_add.setEnabled(False)
        self.status.setText("Extracting text locally…")
        w = workers.Worker(job)
        w.signals.done.connect(self._done)
        w.signals.failed.connect(lambda m: QMessageBox.warning(self, "Import failed", m))
        w.signals.finished.connect(self._finished)
        self.worker = w
        workers.start(w)

    def _done(self, results) -> None:
        msgs = []
        for name, res, err in results:
            if err:
                msgs.append(f"✘ {name}: {err}")
            else:
                msgs.append(f"{'✔' if res.status in ('ok', 'duplicate') else '⚠'} {name}: {res.pages} page(s), {res.chunks} passages. {res.note}")
        QMessageBox.information(self, "Materials", "\n".join(msgs))

    def _finished(self) -> None:
        self.worker = None
        self.b_add.setEnabled(True)
        self.status.setText("")
        self.refresh()

    def _delete(self) -> None:
        r = self.table.currentRow()
        if r < 0:
            return
        mid = self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)
        name = self.table.item(r, 0).text()
        if QMessageBox.question(self, "Remove material", f"Remove '{name}' and its extracted text from the app?\n"
                                "(Your original file elsewhere is not touched.)") == QMessageBox.StandardButton.Yes:
            self.ctx.library.delete(mid)
            self.refresh()
