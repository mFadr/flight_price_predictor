"""Application context: creates and wires all services (no UI code here)."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from tutor.app_paths import AppPaths
from tutor.config import AppConfig, load_config, save_config
from tutor.engine.tutor import TutorEngine
from tutor.llm import build_router
from tutor.llm.router import ProviderRouter
from tutor.logging_setup import setup_logging
from tutor.materials.library import MaterialLibrary
from tutor.storage.db import Database
from tutor.tools.code_runner import CodeRunner
from tutor.tools.viz import VizRenderer

log = logging.getLogger(__name__)


class AppContext:
    def __init__(self, root: Path | None = None, router: ProviderRouter | None = None, configure_logging: bool = True):
        self.paths = AppPaths.create(root)
        self.cfg: AppConfig = load_config(self.paths.config_file)
        if configure_logging:
            setup_logging(self.paths.logs, self.cfg.privacy.diagnostic_logging)
        self._cleanup_temp()
        self.db = Database(self.paths.database)
        self.router = router or build_router(self.cfg)
        self.runner = CodeRunner(self.paths.sandbox, self.cfg.code_timeout_s, self.cfg.code_memory_mb)
        self.renderer = VizRenderer(self.paths.viz)
        self.library = MaterialLibrary(self.db, self.paths.materials)
        self.engine = TutorEngine(self.db, self.router, self.cfg, self.runner, self.renderer, self.library)
        log.info("Application started (mode=%s)", self.cfg.mode.value)

    def _cleanup_temp(self) -> None:
        """Remove leftovers of interrupted sandbox runs; keep the visualisation cache bounded."""
        sandbox = self.paths.cache / "sandbox"
        if sandbox.exists():
            for d in sandbox.iterdir():
                shutil.rmtree(d, ignore_errors=True)
        viz = self.paths.cache / "viz"
        if viz.exists():
            files = sorted(viz.glob("*.png"), key=lambda p: p.stat().st_mtime)
            for f in files[:-500]:
                f.unlink(missing_ok=True)

    def apply_config(self, cfg: AppConfig) -> None:
        save_config(cfg, self.paths.config_file)
        self.cfg = cfg
        notify = self.router.notify
        self.router = build_router(cfg, notify)
        self.engine.router = self.router
        self.router.notify = self.engine._on_router_notice
        self.runner.timeout_s, self.runner.memory_mb = cfg.code_timeout_s, cfg.code_memory_mb
        self.engine.reload_config(cfg)
        setup_logging(self.paths.logs, cfg.privacy.diagnostic_logging)

    def reopen_database(self) -> None:
        self.db.close()
        self.db = Database(self.paths.database)
        self.engine.db = self.db
        self.engine.knowledge.db = self.db
        self.library.db = self.db
