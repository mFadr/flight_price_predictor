"""Application styling (light 'study desk' theme + optional high contrast)."""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

ACCENT = "#3b6fd8"
COLORS = {
    "bg": "#f4f6fa", "panel": "#ffffff", "border": "#d9dee8", "text": "#1d2433", "muted": "#5d6779",
    "tutor": "#ffffff", "student": "#e8f0ff", "hint": "#fff7e0", "feedback": "#eefaf1", "bad": "#fdeeee",
    "solution": "#f1ecff", "notice": "#eef1f6", "exercise": "#fffdf3",
}
HC = {"bg": "#000000", "panel": "#000000", "border": "#ffffff", "text": "#ffffff", "muted": "#e0e0e0",
      "tutor": "#000000", "student": "#001a4d", "hint": "#332600", "feedback": "#00290f", "bad": "#330000",
      "solution": "#1f0033", "notice": "#1a1a1a", "exercise": "#1a1a00"}


def palette(high_contrast: bool) -> dict[str, str]:
    return HC if high_contrast else COLORS


def apply_theme(app: QApplication, font_size: int = 11, high_contrast: bool = False) -> None:
    c = palette(high_contrast)
    app.setStyle("Fusion")
    f = QFont("Segoe UI", font_size)
    app.setFont(f)
    app.setStyleSheet(f"""
    QWidget {{ color: {c['text']}; }}
    QMainWindow, QStackedWidget > QWidget {{ background: {c['bg']}; }}
    QListWidget#nav {{ background: #1f2a44; color: #dfe6f5; border: none; padding-top: 12px; font-size: {font_size + 1}pt; }}
    QListWidget#nav::item {{ padding: 10px 14px; border-radius: 6px; margin: 2px 8px; }}
    QListWidget#nav::item:selected {{ background: {ACCENT}; color: white; }}
    QListWidget#nav::item:hover {{ background: #2e3b5c; }}
    QFrame.card, QGroupBox {{ background: {c['panel']}; border: 1px solid {c['border']}; border-radius: 10px; }}
    QGroupBox {{ margin-top: 14px; padding: 10px; font-weight: 600; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; }}
    QLabel.h1 {{ font-size: {font_size + 8}pt; font-weight: 700; }}
    QLabel.h2 {{ font-size: {font_size + 3}pt; font-weight: 600; }}
    QLabel.muted {{ color: {c['muted']}; }}
    QPushButton {{ background: {c['panel']}; border: 1px solid {c['border']}; border-radius: 6px; padding: 6px 12px; }}
    QPushButton:hover {{ border-color: {ACCENT}; }}
    QPushButton:disabled {{ color: #9aa3b2; }}
    QPushButton.primary {{ background: {ACCENT}; color: white; border: none; font-weight: 600; }}
    QPushButton.primary:disabled {{ background: #9db5e8; }}
    QPushButton.action {{ padding: 6px 10px; }}
    QPushButton.danger {{ color: #b3261e; }}
    QTextBrowser, QPlainTextEdit, QLineEdit, QTableWidget, QListWidget, QComboBox, QSpinBox, QDoubleSpinBox {{
        background: {c['panel']}; border: 1px solid {c['border']}; border-radius: 6px; }}
    QPlainTextEdit, QLineEdit {{ padding: 4px; }}
    QTabWidget::pane {{ border: 1px solid {c['border']}; border-radius: 8px; background: {c['panel']}; }}
    QTabBar::tab {{ padding: 6px 14px; }}
    QStatusBar {{ background: {c['panel']}; border-top: 1px solid {c['border']}; }}
    QLabel#badgeLocal {{ background: #e3f6e8; color: #1e6b34; border-radius: 9px; padding: 2px 10px; font-weight: 600; }}
    QLabel#badgeCloud {{ background: #fff0d9; color: #8a4b00; border-radius: 9px; padding: 2px 10px; font-weight: 600; }}
    QLabel#badgeOff {{ background: #fdeeee; color: #9b1c1c; border-radius: 9px; padding: 2px 10px; font-weight: 600; }}
    """)
