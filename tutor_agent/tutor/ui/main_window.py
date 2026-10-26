"""Main window: navigation, pages, status bar with the active model and data-transmission indicator."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QStatusBar,
    QWidget,
)

from tutor import APP_DISPLAY_NAME, __version__
from tutor.app import AppContext
from tutor.domain import SessionStatus
from tutor.ui.dashboard import Dashboard
from tutor.ui.materials_view import Materials
from tutor.ui.profile_view import ProfileView
from tutor.ui.progress import Progress
from tutor.ui.settings_view import SettingsView
from tutor.ui.theme import apply_theme
from tutor.ui.workspace import Workspace

PAGES = [("dashboard", "🏠  Dashboard"), ("tutor", "🎓  Tutor"), ("progress", "📈  Progress"),
         ("materials", "📚  Materials"), ("profile", "👤  Profile & data"), ("settings", "⚙  Settings")]


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle(f"{APP_DISPLAY_NAME} {__version__}")
        self.resize(1320, 840)
        self.setMinimumSize(1000, 640)
        central = QWidget()
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(200)
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for _, label in PAGES:
            self.nav.addItem(label)
        lay.addWidget(self.nav)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.dashboard = Dashboard(ctx)
        self.workspace = Workspace(ctx)
        self.progress = Progress(ctx)
        self.materials = Materials(ctx)
        self.profile = ProfileView(ctx)
        self.settings = SettingsView(ctx)
        self.pages = {"dashboard": self.dashboard, "tutor": self.workspace, "progress": self.progress,
                      "materials": self.materials, "profile": self.profile, "settings": self.settings}
        for key, _ in PAGES:
            self.stack.addWidget(self.pages[key])
        self.nav.currentRowChanged.connect(self._page_changed)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self.model_badge = QLabel()
        sb.addPermanentWidget(self.model_badge)
        self.dashboard.open_session.connect(self._open_session)
        self.dashboard.goto.connect(self.goto)
        self.workspace.session_changed.connect(self.dashboard.refresh)
        self.workspace.status_message.connect(lambda m: sb.showMessage(m, 4000))
        self.settings.config_applied.connect(self._config_changed)
        self.profile.data_changed.connect(self._data_changed)
        self.profile.appearance_changed.connect(self._appearance)
        self._update_badge()
        self.nav.setCurrentRow(0)
        QTimer.singleShot(300, self.dashboard.check_model)
        QTimer.singleShot(600, self._offer_resume)

    def goto(self, key: str) -> None:
        self.nav.setCurrentRow([k for k, _ in PAGES].index(key))

    def _page_changed(self, row: int) -> None:
        self.stack.setCurrentIndex(row)
        page = self.stack.currentWidget()
        if hasattr(page, "refresh"):
            page.refresh()

    def _open_session(self, session, start: bool) -> None:
        self.goto("tutor")
        self.workspace.open_session(session, start)

    def _offer_resume(self) -> None:
        """Recovery after an interrupted run: offer to continue the most recent active session."""
        active = self.ctx.db.list_sessions(1, SessionStatus.ACTIVE)
        if active and self.ctx.db.messages(active[0].id):
            s = active[0]
            box = QMessageBox(self)
            box.setWindowTitle("Continue where you left off?")
            box.setText(f"Your session “{s.subject} · {s.topic}” was not finished. Continue it now?")
            box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            box.accepted.connect(lambda: self._open_session(s, False))
            box.open()

    def _update_badge(self) -> None:
        r = self.ctx.router
        desc = r.describe()
        if r.primary("explain") is None:
            self.model_badge.setObjectName("badgeOff")
            self.model_badge.setText("⚠ No AI model available - see Settings")
        elif r.transmits_externally():
            self.model_badge.setObjectName("badgeCloud")
            self.model_badge.setText(f"☁ {desc} - content is sent to the cloud")
        else:
            self.model_badge.setObjectName("badgeLocal")
            self.model_badge.setText(f"🔒 {desc} - local, offline")
        self.model_badge.style().unpolish(self.model_badge)
        self.model_badge.style().polish(self.model_badge)

    def _config_changed(self) -> None:
        self._update_badge()
        self.dashboard.check_model()

    def _data_changed(self) -> None:
        if self.workspace.session and not self.ctx.db.get_session(self.workspace.session.id):
            self.workspace.session = None
            self.workspace._show_empty()
        self.dashboard.refresh()

    def _appearance(self) -> None:
        apply_theme(QApplication.instance(), self.ctx.cfg.ui_font_size, self.ctx.cfg.high_contrast)
        self.workspace._html_cache.clear()
        self.workspace._reload()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.workspace.worker:
            self.workspace.worker.cancel()
        self.ctx.db.close()
        super().closeEvent(event)
