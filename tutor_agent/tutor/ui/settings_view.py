"""AI model, privacy and execution settings."""

from __future__ import annotations

import html

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from tutor.app import AppContext
from tutor.config import AppConfig, OperatingMode, QualityPreset
from tutor.credentials import delete_api_key, get_api_key, mask, set_api_key
from tutor.llm import build_router
from tutor.llm.ollama import OllamaProvider
from tutor.ui import workers

CLOUD_WARNING = (
    "When cloud mode is enabled, the text of your tutoring conversations (and short excerpts of your materials) "
    "is sent over the internet to the provider you configure and processed on their servers under their terms. "
    "It is NOT private or offline just because this app runs locally.\n\n"
    "Your learning history, profile and progress stay on this computer; only the context needed for the current "
    "request is sent.\n\nDo you want to allow this?"
)


class SettingsView(QWidget):
    config_applied = Signal()

    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.worker = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        t = QLabel("Settings")
        t.setProperty("class", "h1")
        outer.addWidget(t)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll, 1)
        body = QWidget()
        scroll.setWidget(body)
        v = QVBoxLayout(body)

        g = QGroupBox("Where does the AI model run?")
        gv = QVBoxLayout(g)
        self.mode_group = QButtonGroup(self)
        self.r_local = QRadioButton("Fully local (Ollama) - nothing leaves this computer  [recommended]")
        self.r_hybrid = QRadioButton("Hybrid - local by default, cloud only for selected tasks")
        self.r_cloud = QRadioButton("Cloud - use an online API for all AI tasks")
        for i, r in enumerate((self.r_local, self.r_hybrid, self.r_cloud)):
            self.mode_group.addButton(r, i)
            gv.addWidget(r)
        self.transmit = QLabel("")
        self.transmit.setWordWrap(True)
        gv.addWidget(self.transmit)
        v.addWidget(g)

        g = QGroupBox("Local model (Ollama)")
        f = QFormLayout(g)
        self.o_url = QLineEdit()
        self.o_model = QComboBox()
        self.o_model.setEditable(True)
        self.o_timeout = QSpinBox()
        self.o_timeout.setRange(30, 1800)
        self.o_timeout.setSuffix(" s")
        self.o_ctx = QComboBox()
        for n in (2048, 4096, 8192, 16384, 32768):
            self.o_ctx.addItem(f"{n:,} tokens", n)
        row = QHBoxLayout()
        b = QPushButton("Refresh installed models")
        b.clicked.connect(self._list_models)
        row.addWidget(b)
        row.addStretch(1)
        f.addRow("Ollama URL:", self.o_url)
        f.addRow("Model:", self.o_model)
        f.addRow(row)
        f.addRow("Response timeout:", self.o_timeout)
        f.addRow("Context window:", self.o_ctx)
        help_ = QLabel("Install: download Ollama from ollama.com, then run <code>ollama pull llama3.1:8b</code> "
                       "(≈5 GB, needs ~8 GB free RAM) or a smaller model such as <code>llama3.2:3b</code> / "
                       "<code>qwen2.5:3b</code> for laptops with 8 GB RAM. No GPU is required, but CPU-only answers are slower.")
        help_.setWordWrap(True)
        help_.setProperty("class", "muted")
        f.addRow(help_)
        v.addWidget(g)

        g = QGroupBox("Cloud model (OpenAI-compatible API)")
        f = QFormLayout(g)
        self.c_enabled = QCheckBox("Enable cloud provider")
        self.c_name = QLineEdit()
        self.c_url = QLineEdit()
        self.c_model = QLineEdit()
        self.c_key = QLineEdit()
        self.c_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.c_key.setPlaceholderText("paste a new key to store it in Windows Credential Manager")
        self.c_key_state = QLabel("")
        self.c_struct = QComboBox()
        self.c_struct.addItems(["json_schema", "json_object", "prompt"])
        self.c_struct.setToolTip("How structured output is requested. Use 'prompt' if the provider rejects response_format.")
        self.c_limit = QSpinBox()
        self.c_limit.setRange(1, 10000)
        self.c_max_out = QSpinBox()
        self.c_max_out.setRange(100, 16000)
        self.h_explain = QCheckBox("explanations & conversation")
        self.h_exercise = QCheckBox("exercise generation")
        self.h_evaluate = QCheckBox("answer evaluation")
        self.h_summary = QCheckBox("session summaries")
        hy = QHBoxLayout()
        for w in (self.h_explain, self.h_exercise, self.h_evaluate, self.h_summary):
            hy.addWidget(w)
        krow = QHBoxLayout()
        krow.addWidget(self.c_key, 1)
        b = QPushButton("Remove key")
        b.clicked.connect(self._remove_key)
        krow.addWidget(b)
        f.addRow(self.c_enabled)
        f.addRow("Provider name:", self.c_name)
        f.addRow("Base URL:", self.c_url)
        f.addRow("Model identifier:", self.c_model)
        f.addRow("API key:", krow)
        f.addRow("", self.c_key_state)
        f.addRow("Structured output:", self.c_struct)
        f.addRow("Max requests / day:", self.c_limit)
        f.addRow("Max output tokens:", self.c_max_out)
        f.addRow("Hybrid: use cloud for", hy)
        v.addWidget(g)

        g = QGroupBox("Fallback")
        f = QFormLayout(g)
        self.fb_local = QCheckBox("If the cloud fails, fall back to the local model (data stays local)")
        self.fb_cloud = QCheckBox("If the local model fails, fall back to the cloud (hybrid mode only; always announced)")
        f.addRow(self.fb_local)
        f.addRow(self.fb_cloud)
        v.addWidget(g)

        g = QGroupBox("Generation")
        f = QFormLayout(g)
        self.quality = QComboBox()
        self.quality.addItem("Fast - shorter prompts and answers (slow laptops)", QualityPreset.FAST)
        self.quality.addItem("Balanced", QualityPreset.BALANCED)
        self.quality.addItem("Quality - larger context, longer answers", QualityPreset.QUALITY)
        self.temp = QDoubleSpinBox()
        self.temp.setRange(0, 1.5)
        self.temp.setSingleStep(0.1)
        self.length = QComboBox()
        self.length.addItems(["short", "medium", "long"])
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(64, 8192)
        f.addRow("Speed vs quality:", self.quality)
        f.addRow("Temperature:", self.temp)
        f.addRow("Response length:", self.length)
        f.addRow("Max response tokens:", self.max_tokens)
        v.addWidget(g)

        g = QGroupBox("Privacy & safety")
        f = QFormLayout(g)
        self.p_history = QCheckBox("Allow sending a concise summary of my progress on the current topic to the cloud")
        self.p_logging = QCheckBox("Diagnostic logging (event metadata only - never secrets or conversation text)")
        self.code_timeout = QDoubleSpinBox()
        self.code_timeout.setRange(1, 60)
        self.code_timeout.setSuffix(" s")
        self.code_mem = QSpinBox()
        self.code_mem.setRange(64, 2048)
        self.code_mem.setSuffix(" MB")
        f.addRow(self.p_history)
        f.addRow(self.p_logging)
        f.addRow("Code sandbox time limit:", self.code_timeout)
        f.addRow("Code sandbox memory limit:", self.code_mem)
        v.addWidget(g)

        row = QHBoxLayout()
        b = QPushButton("Save settings")
        b.setProperty("class", "primary")
        b.clicked.connect(self._save)
        row.addWidget(b)
        self.b_test = QPushButton("Test connection")
        self.b_test.clicked.connect(self._test)
        row.addWidget(self.b_test)
        row.addStretch(1)
        v.addLayout(row)
        self.test_out = QTextBrowser()
        self.test_out.setMaximumHeight(160)
        v.addWidget(self.test_out)
        v.addStretch(1)
        self.mode_group.idToggled.connect(lambda *_: self._update_transmit())
        self.c_enabled.toggled.connect(lambda *_: self._update_transmit())

    # ------------------------------------------------------------ load / save
    def refresh(self) -> None:
        c = self.ctx.cfg
        {OperatingMode.LOCAL: self.r_local, OperatingMode.HYBRID: self.r_hybrid, OperatingMode.CLOUD: self.r_cloud}[c.mode].setChecked(True)
        self.o_url.setText(c.ollama.base_url)
        self.o_model.setCurrentText(c.ollama.model)
        self.o_timeout.setValue(int(c.ollama.timeout_s))
        self.o_ctx.setCurrentIndex(max(0, self.o_ctx.findData(c.ollama.num_ctx)))
        self.c_enabled.setChecked(c.cloud.enabled)
        self.c_name.setText(c.cloud.provider_name)
        self.c_url.setText(c.cloud.base_url)
        self.c_model.setText(c.cloud.model)
        self.c_key.clear()
        self.c_key_state.setText("Stored key: " + mask(get_api_key(c.cloud.api_key_env)))
        self.c_struct.setCurrentText(c.cloud.structured_output)
        self.c_limit.setValue(c.cloud.max_requests_per_day)
        self.c_max_out.setValue(c.cloud.max_output_tokens)
        for w, task in ((self.h_explain, "explain"), (self.h_exercise, "exercise"), (self.h_evaluate, "evaluate"), (self.h_summary, "summary")):
            w.setChecked(task in c.hybrid.cloud_tasks)
        self.fb_local.setChecked(c.fallback.fallback_to_local)
        self.fb_cloud.setChecked(c.fallback.fallback_to_cloud)
        self.quality.setCurrentIndex(self.quality.findData(c.generation.quality))
        self.temp.setValue(c.generation.temperature)
        self.length.setCurrentText(c.generation.response_length)
        self.max_tokens.setValue(c.generation.max_response_tokens)
        self.p_history.setChecked(c.privacy.send_learning_history_to_cloud)
        self.p_logging.setChecked(c.privacy.diagnostic_logging)
        self.code_timeout.setValue(c.code_timeout_s)
        self.code_mem.setValue(c.code_memory_mb)
        self._update_transmit()

    def _mode(self) -> OperatingMode:
        return [OperatingMode.LOCAL, OperatingMode.HYBRID, OperatingMode.CLOUD][max(0, self.mode_group.checkedId())]

    def _update_transmit(self) -> None:
        if self._mode() == OperatingMode.LOCAL or not self.c_enabled.isChecked():
            self.transmit.setText("🔒 <b>External data transmission: OFF.</b> No conversation content leaves this computer.")
        else:
            self.transmit.setText("☁️ <b>External data transmission: ON.</b> Conversation content for "
                                  + ("all tasks" if self._mode() == OperatingMode.CLOUD else "the selected tasks")
                                  + " is sent to the cloud provider.")

    def _form_config(self) -> AppConfig:
        c = self.ctx.cfg.model_copy(deep=True)
        c.mode = self._mode()
        c.ollama.base_url = self.o_url.text().strip() or "http://localhost:11434"
        c.ollama.model = self.o_model.currentText().strip()
        c.ollama.timeout_s = float(self.o_timeout.value())
        c.ollama.num_ctx = self.o_ctx.currentData()
        c.cloud.enabled = self.c_enabled.isChecked()
        c.cloud.provider_name = self.c_name.text().strip() or "OpenAI-compatible"
        c.cloud.base_url = self.c_url.text().strip()
        c.cloud.model = self.c_model.text().strip()
        c.cloud.structured_output = self.c_struct.currentText()
        c.cloud.max_requests_per_day = self.c_limit.value()
        c.cloud.max_output_tokens = self.c_max_out.value()
        c.hybrid.cloud_tasks = [t for w, t in ((self.h_explain, "explain"), (self.h_exercise, "exercise"),
                                               (self.h_evaluate, "evaluate"), (self.h_summary, "summary")) if w.isChecked()]
        c.fallback.fallback_to_local = self.fb_local.isChecked()
        c.fallback.fallback_to_cloud = self.fb_cloud.isChecked()
        c.generation.quality = self.quality.currentData()
        c.generation.temperature = self.temp.value()
        c.generation.response_length = self.length.currentText()
        c.generation.max_response_tokens = self.max_tokens.value()
        c.privacy.send_learning_history_to_cloud = self.p_history.isChecked()
        c.privacy.diagnostic_logging = self.p_logging.isChecked()
        c.code_timeout_s = self.code_timeout.value()
        c.code_memory_mb = self.code_mem.value()
        return c

    def _save(self) -> None:
        c = self._form_config()
        if c.mode != OperatingMode.LOCAL and c.cloud.enabled and not c.cloud.consent_given:
            if QMessageBox.warning(self, "Data will leave this computer", CLOUD_WARNING,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            c.cloud.consent_given = True
        if not c.cloud.enabled:
            c.cloud.consent_given = False
        key = self.c_key.text().strip()
        if key:
            if not set_api_key(c.cloud.api_key_env, key):
                QMessageBox.warning(self, "API key", "The key could not be stored in the Windows Credential Manager. "
                                    f"You can set the environment variable {c.cloud.api_key_env} instead.")
            self.c_key.clear()
        self.ctx.apply_config(c)
        self.refresh()
        self.config_applied.emit()
        QMessageBox.information(self, "Settings", "Settings saved. Active model: " + self.ctx.router.describe())

    def _remove_key(self) -> None:
        delete_api_key(self.ctx.cfg.cloud.api_key_env)
        self.refresh()

    # ------------------------------------------------------------ checks
    def _list_models(self) -> None:
        models = OllamaProvider(self.o_model.currentText(), self.o_url.text().strip()).list_models()
        cur = self.o_model.currentText()
        self.o_model.clear()
        self.o_model.addItems(models)
        self.o_model.setCurrentText(cur)
        if not models:
            self.test_out.setHtml("Ollama is not reachable, or no models are installed. Start Ollama and run "
                                  "<code>ollama pull llama3.1:8b</code>.")

    def _test(self) -> None:
        if self.worker:
            return
        cfg = self._form_config()
        cfg.cloud.consent_given = True  # testing a connection sends no conversation content
        router = build_router(cfg)
        self.test_out.setHtml("<i>Testing…</i>")
        self.b_test.setEnabled(False)

        def job(_c, _t):
            out = [router.local.check_status()]
            if router.cloud:
                out.append(router.cloud.check_status())
            return out

        def show(sts):
            parts = []
            for st in sts:
                parts.append(f"<p>{'🟢' if st.ok else '🔴'} <b>{html.escape(st.provider)}</b> · {html.escape(st.model)}: {html.escape(st.message)}</p>")
                if st.troubleshooting:
                    parts.append("<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in st.troubleshooting) + "</ul>")
                if st.available_models and not st.ok:
                    parts.append("<p>Available: " + html.escape(", ".join(st.available_models[:15])) + "</p>")
            self.test_out.setHtml("".join(parts))
        w = workers.Worker(job)
        w.signals.done.connect(show)
        w.signals.failed.connect(lambda m: self.test_out.setHtml(html.escape(m)))
        w.signals.finished.connect(lambda: (self.b_test.setEnabled(True), setattr(self, "worker", None)))
        self.worker = w
        workers.start(w)
