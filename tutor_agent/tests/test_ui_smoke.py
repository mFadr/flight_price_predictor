"""Headless UI smoke tests (Qt offscreen) - the interface builds and drives the engine without blocking."""

import pytest

pytest.importorskip("pytestqt")

from tutor.domain import MessageKind  # noqa: E402
from tutor.ui.main_window import MainWindow  # noqa: E402
from tutor.ui.render import Renderer  # noqa: E402


@pytest.fixture
def win(qtbot, ctx, monkeypatch):
    monkeypatch.setattr(MainWindow, "_offer_resume", lambda self: None)
    w = MainWindow(ctx)
    qtbot.addWidget(w)
    return w


def test_all_pages_build_and_refresh(win):
    for i in range(win.nav.count()):
        win.nav.setCurrentRow(i)
    assert "local" in win.model_badge.text()


def test_session_flow_through_ui_is_non_blocking(win, ctx, qtbot):
    s = ctx.engine.start_session("Mathematics", "Linear equations")
    win._open_session(s, True)
    qtbot.waitUntil(lambda: win.workspace.worker is None, timeout=10000)
    assert win.workspace.b_hint.isEnabled()
    win.workspace._exercise("first")
    assert win.workspace.b_cancel.isEnabled()  # busy state while working in the background
    qtbot.waitUntil(lambda: win.workspace.worker is None, timeout=10000)
    assert win.workspace.current_ex is not None and win.workspace.b_submit.isEnabled()
    win.workspace.answer_line.setText("x = 6")
    win.workspace._submit()
    qtbot.waitUntil(lambda: win.workspace.worker is None, timeout=10000)
    kinds = [m.kind for m in ctx.db.messages(s.id)]
    assert MessageKind.FEEDBACK in kinds
    win.workspace.plot_expr.setText("x^2")
    win.workspace._plot()
    assert win.workspace.viz_pick.count() == 1


def test_math_and_code_rendering(qtbot):
    from PySide6.QtWidgets import QTextBrowser
    tb = QTextBrowser()
    qtbot.addWidget(tb)
    out = Renderer().to_html("Inline $x^2$ and display $$\\frac{a}{b}$$ and `$HOME` and\n```python\nprint('$x$')\n```", tb.document())
    assert out.count('src="math://') == 2  # code spans/blocks untouched
    assert "$HOME" in out and "print" in out
