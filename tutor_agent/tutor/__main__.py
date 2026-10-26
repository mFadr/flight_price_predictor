"""Entry point:  python -m tutor"""

from __future__ import annotations

import logging
import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication, QMessageBox

    from tutor import APP_DISPLAY_NAME
    from tutor.app import AppContext
    from tutor.ui.main_window import MainWindow
    from tutor.ui.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName(APP_DISPLAY_NAME)
    try:
        ctx = AppContext()
    except Exception as exc:  # pragma: no cover - startup failure dialog
        logging.exception("Startup failed")
        QMessageBox.critical(None, APP_DISPLAY_NAME, f"The application could not start:\n{exc}")
        return 1
    apply_theme(app, ctx.cfg.ui_font_size, ctx.cfg.high_contrast)
    win = MainWindow(ctx)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
