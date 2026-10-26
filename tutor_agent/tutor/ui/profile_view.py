"""Student profile, preferences, and data management (export / backup / delete)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from tutor.app import AppContext
from tutor.domain import LEVEL_NAMES, SUBJECTS, StudentProfile, TeachingStyle
from tutor.storage.backup import create_backup, restore_backup


class ProfileView(QWidget):
    data_changed = Signal()
    appearance_changed = Signal()

    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        t = QLabel("Profile & data")
        t.setProperty("class", "h1")
        outer.addWidget(t)
        sub = QLabel("These are preferences that shape how the tutor teaches - not permanent assumptions about your ability. "
                     "Everything here is stored only on this computer.")
        sub.setWordWrap(True)
        sub.setProperty("class", "muted")
        outer.addWidget(sub)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll, 1)
        body = QWidget()
        scroll.setWidget(body)
        v = QVBoxLayout(body)

        g = QGroupBox("About you")
        f = QFormLayout(g)
        self.name = QLineEdit()
        self.name.setPlaceholderText("optional")
        self.academic = QComboBox()
        self.academic.setEditable(True)
        self.academic.addItems(["High school", "University (undergraduate)", "University (graduate)", "Self-study / professional"])
        self.subjects = QListWidget()
        self.subjects.setMaximumHeight(130)
        for s in SUBJECTS:
            it = QListWidgetItem(s)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Unchecked)
            self.subjects.addItem(it)
        self.goals = QPlainTextEdit()
        self.goals.setFixedHeight(60)
        self.goals.setPlaceholderText("e.g. pass Calculus II, get comfortable with recursion")
        f.addRow("Name:", self.name)
        f.addRow("Academic level:", self.academic)
        f.addRow("Subjects:", self.subjects)
        f.addRow("Current goals:", self.goals)
        v.addWidget(g)

        g = QGroupBox("How you like to learn")
        f = QFormLayout(g)
        self.style = QComboBox()
        for st in TeachingStyle:
            self.style.addItem(st.label, st)
        self.level = QComboBox()
        for lv, n in LEVEL_NAMES.items():
            self.level.addItem(f"{lv} · {n}", lv)
        self.length = QComboBox()
        self.length.addItems(["short", "medium", "long"])
        self.modality = QComboBox()
        self.modality.addItems(["mixed", "visual", "verbal"])
        self.rigor = QComboBox()
        self.rigor.addItems(["informal", "standard", "rigorous"])
        self.examples_first = QCheckBox("Examples before theory")
        self.prefers_hints = QCheckBox("I prefer hints over direct explanations")
        self.lang = QLineEdit()
        f.addRow("Teaching style:", self.style)
        f.addRow("Default level:", self.level)
        f.addRow("Explanation depth:", self.length)
        f.addRow("Explanations:", self.modality)
        f.addRow("Mathematical rigour:", self.rigor)
        f.addRow(self.examples_first)
        f.addRow(self.prefers_hints)
        f.addRow("Programming language:", self.lang)
        v.addWidget(g)

        g = QGroupBox("Accessibility")
        f = QFormLayout(g)
        self.font = QSpinBox()
        self.font.setRange(9, 20)
        self.contrast = QCheckBox("High contrast colours")
        f.addRow("Font size:", self.font)
        f.addRow(self.contrast)
        v.addWidget(g)

        row = QHBoxLayout()
        b = QPushButton("Save profile")
        b.setProperty("class", "primary")
        b.clicked.connect(self._save)
        row.addWidget(b)
        b = QPushButton("View stored profile data")
        b.clicked.connect(self._inspect)
        row.addWidget(b)
        b = QPushButton("Delete profile")
        b.setProperty("class", "danger")
        b.clicked.connect(self._delete_profile)
        row.addWidget(b)
        row.addStretch(1)
        v.addLayout(row)

        g = QGroupBox("Your data")
        d = QVBoxLayout(g)
        self.loc = QLabel()
        self.loc.setWordWrap(True)
        self.loc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        d.addWidget(self.loc)
        row = QHBoxLayout()
        for text, fn, cls in (("Open data folder", self._open_folder, ""), ("Back up progress…", self._backup, ""),
                              ("Restore backup…", self._restore, ""), ("Delete ALL learning history…", self._delete_all, "danger")):
            b = QPushButton(text)
            if cls:
                b.setProperty("class", cls)
            b.clicked.connect(fn)
            row.addWidget(b)
        row.addStretch(1)
        d.addLayout(row)
        v.addWidget(g)
        v.addStretch(1)

    def refresh(self) -> None:
        p = self.ctx.db.load_profile()
        self.name.setText(p.name)
        self.academic.setCurrentText(p.academic_level)
        for i in range(self.subjects.count()):
            it = self.subjects.item(i)
            it.setCheckState(Qt.CheckState.Checked if it.text() in p.subjects else Qt.CheckState.Unchecked)
        self.goals.setPlainText(p.goals)
        self.style.setCurrentIndex(list(TeachingStyle).index(p.teaching_style))
        self.level.setCurrentIndex(p.default_level - 1)
        pr = p.preferences
        self.length.setCurrentText(pr.explanation_length)
        self.modality.setCurrentText(pr.modality)
        self.rigor.setCurrentText(pr.rigor)
        self.examples_first.setChecked(pr.examples_first)
        self.prefers_hints.setChecked(pr.prefers_hints)
        self.lang.setText(pr.programming_language)
        self.font.setValue(self.ctx.cfg.ui_font_size)
        self.contrast.setChecked(self.ctx.cfg.high_contrast)
        self.loc.setText(f"Data folder: {self.ctx.paths.root}\nExports: {self.ctx.paths.exports}\nBackups: {self.ctx.paths.backups}")

    def _profile_from_form(self) -> StudentProfile:
        p = self.ctx.db.load_profile()
        p.name = self.name.text().strip()
        p.academic_level = self.academic.currentText()
        p.subjects = [self.subjects.item(i).text() for i in range(self.subjects.count())
                      if self.subjects.item(i).checkState() == Qt.CheckState.Checked]
        p.goals = self.goals.toPlainText().strip()
        p.teaching_style = self.style.currentData()
        p.default_level = self.level.currentData()
        pr = p.preferences
        pr.explanation_length = self.length.currentText()
        pr.modality = self.modality.currentText()
        pr.rigor = self.rigor.currentText()
        pr.examples_first = self.examples_first.isChecked()
        pr.prefers_hints = self.prefers_hints.isChecked()
        pr.programming_language = self.lang.text().strip() or "Python"
        p.accessibility.font_size = self.font.value()
        p.accessibility.high_contrast = self.contrast.isChecked()
        return p

    def _save(self) -> None:
        self.ctx.db.save_profile(self._profile_from_form())
        cfg = self.ctx.cfg.model_copy(deep=True)
        if (cfg.ui_font_size, cfg.high_contrast) != (self.font.value(), self.contrast.isChecked()):
            cfg.ui_font_size, cfg.high_contrast = self.font.value(), self.contrast.isChecked()
            self.ctx.apply_config(cfg)
            self.appearance_changed.emit()
        QMessageBox.information(self, "Profile", "Profile saved.")
        self.data_changed.emit()

    def _inspect(self) -> None:
        data = self.ctx.db.load_profile().model_dump(mode="json")
        box = QMessageBox(self)
        box.setWindowTitle("Stored profile data")
        box.setText("This is everything stored in your profile:")
        box.setDetailedText(json.dumps(data, indent=2, ensure_ascii=False))
        box.exec()

    def _delete_profile(self) -> None:
        if QMessageBox.warning(self, "Delete profile", "Delete your profile and preferences? (Learning history is kept.)",
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.ctx.db.delete_profile()
            self.refresh()

    def _open_folder(self) -> None:
        if os.name == "nt":
            os.startfile(self.ctx.paths.root)  # noqa: S606 - user-initiated

    def _backup(self) -> None:
        target, _ = QFileDialog.getSaveFileName(self, "Save backup", str(self.ctx.paths.backups / "tutor-backup.zip"), "Backup (*.zip)")
        if not target:
            return
        p = create_backup(self.ctx.db, self.ctx.paths, Path(target))
        QMessageBox.information(self, "Backup", f"Backup saved to:\n{p}")

    def _restore(self) -> None:
        src, _ = QFileDialog.getOpenFileName(self, "Restore backup", str(self.ctx.paths.backups), "Backup (*.zip)")
        if not src:
            return
        if QMessageBox.warning(self, "Restore backup", "Replace your current learning history with this backup?\n"
                               "A safety copy of the current data is made first.",
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            self.ctx.db.close()
            safety = restore_backup(self.ctx.paths.database, self.ctx.paths, Path(src))
            QMessageBox.information(self, "Restored", f"Backup restored. Previous data saved as:\n{safety}")
        except Exception as exc:
            QMessageBox.critical(self, "Restore failed", str(exc))
        finally:
            self.ctx.reopen_database()
            self.data_changed.emit()

    def _delete_all(self) -> None:
        if QMessageBox.warning(self, "Delete all learning history",
                               "Permanently delete ALL sessions, exercises, attempts and progress?\n"
                               "Consider making a backup first. This cannot be undone.",
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self.ctx.db.delete_all_history()
        QMessageBox.information(self, "Deleted", "All learning history was deleted.")
        self.data_changed.emit()
