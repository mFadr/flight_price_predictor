r"""Render the real UI with a scripted (mock) model and save screenshots - for docs and visual QA.

Usage:  .venv\Scripts\python scripts\demo_screenshots.py [output_dir]
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "windows" if os.name == "nt" else "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from PySide6.QtWidgets import QApplication  # noqa: E402

from conftest import EVAL_SIGN_ERROR, ScriptedLLM  # noqa: E402
from tutor.app import AppContext  # noqa: E402
from tutor.config import AppConfig  # noqa: E402
from tutor.llm.mock import MockProvider  # noqa: E402
from tutor.llm.router import ProviderRouter  # noqa: E402
from tutor.ui.main_window import MainWindow  # noqa: E402
from tutor.ui.theme import apply_theme  # noqa: E402

out = Path(sys.argv[1] if len(sys.argv) > 1 else "screenshots")
out.mkdir(parents=True, exist_ok=True)
app = QApplication(sys.argv)
llm = ScriptedLLM()
llm.chat_replies += [
    "Great goal! An equation is like a **balanced scale**: whatever you do to one side, you must do to the other.\n\n"
    "For example, in $3x - 7 = 11$ the unknown $x$ is hidden behind two operations.\n\n"
    "**Question:** which operation would you undo first - the $-7$ or the multiplication by $3$? Why?",
    "*Another way to see it: visual/graphical picture*\n\nThink of both sides as two functions. The solution is where the "
    "lines $y = 3x - 7$ and $y = 11$ meet.\n\n```viz\n{\"kind\": \"function_plot\", \"title\": \"Where 3x - 7 meets 11\", "
    "\"expressions\": [\"3x - 7\", \"11\"], \"x_min\": 0, \"x_max\": 9, \"mark_x\": [6]}\n```",
]
llm.evaluations.append(EVAL_SIGN_ERROR)
cfg = AppConfig()
ctx = AppContext(root=Path(tempfile.mkdtemp()) / "demo", router=ProviderRouter(cfg, MockProvider(responder=llm), None),
                 configure_logging=False)
apply_theme(app, 11)
eng = ctx.engine
s = eng.start_session("Mathematics", "Linear equations", goal="solve two-step equations for my exam", level=2)
eng.opening(s)
eng.new_exercise(s, "first")
eng.submit_answer(s, "x = 4/3", "3x - 7 = 11\n3x = 4\nx = 4/3", confidence=3)
eng.hint(s)
eng.explain_differently(s)
win = MainWindow(ctx)
win._offer_resume = lambda: None
win.resize(1360, 860)
win.show()
win._open_session(s, False)
app.processEvents()
win.workspace.view.verticalScrollBar().setValue(10**6)
for tab, name in ((0, "workspace_exercise"), (1, "workspace_visual")):
    win.workspace.tabs.setCurrentIndex(tab)
    app.processEvents()
    win.grab().save(str(out / f"{name}.png"))
for page in ("dashboard", "progress", "settings"):
    win.goto(page)
    app.processEvents()
    win.grab().save(str(out / f"{page}.png"))
print("saved to", out.resolve())
