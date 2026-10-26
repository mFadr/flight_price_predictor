"""Background execution so the UI never blocks during model requests."""

from __future__ import annotations

import logging
import traceback
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from tutor.llm.base import Cancelled, CancelToken, LLMError

log = logging.getLogger(__name__)


class WorkerSignals(QObject):
    chunk = Signal(str)
    done = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()


class Worker(QRunnable):
    """Runs ``fn(on_chunk, cancel)`` in the global thread pool."""

    def __init__(self, fn: Callable[[Callable[[str], None], CancelToken], Any]):
        super().__init__()
        self.fn = fn
        self.cancel_token = CancelToken()
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    def _emit(self, signal_name: str, *args) -> None:
        # The receiving widgets may already be gone (app closing while a request finishes).
        try:
            getattr(self.signals, signal_name).emit(*args)
        except RuntimeError:
            pass

    def run(self) -> None:  # noqa: D401 - Qt API
        try:
            result = self.fn(lambda text: self._emit("chunk", text), self.cancel_token)
            self._emit("done", result)
        except Cancelled:
            self._emit("cancelled")
        except LLMError as exc:
            log.warning("LLM error: %s", type(exc).__name__)
            self._emit("failed", exc.user_message)
        except Exception as exc:  # never crash the UI thread
            log.error("Worker failed: %s\n%s", exc, traceback.format_exc())
            self._emit("failed", f"Unexpected error: {type(exc).__name__}: {exc}")
        finally:
            self._emit("finished")

    def cancel(self) -> None:
        self.cancel_token.cancel()


def start(worker: Worker) -> Worker:
    QThreadPool.globalInstance().start(worker)
    return worker
