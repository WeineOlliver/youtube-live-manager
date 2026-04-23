"""YouTube Live Manager — main application window."""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QLineEdit,
    QPlainTextEdit, QFileDialog, QFrame,
)

from core.youtube_api import get_token_status, refresh_token
from core.state import load_config, save_config
from ui.workers import CreateLivesWorker, ObsWatcherWorker

DARK_STYLE = """
QWidget {
    background-color: #111827;
    color: #f9fafb;
    font-family: "Segoe UI";
    font-size: 12px;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1f2937;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 4px 8px;
    color: #f9fafb;
}
QPushButton {
    background-color: #374151;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    color: #f9fafb;
}
QPushButton:hover { background-color: #4b5563; }
QPushButton:disabled { color: #6b7280; background-color: #1f2937; }
QPushButton#create_btn { background-color: #16a34a; font-weight: bold; }
QPushButton#create_btn:hover { background-color: #15803d; }
QPushButton#create_btn:disabled { background-color: #1f2937; color: #6b7280; }
QCheckBox::indicator {
    width: 36px; height: 18px;
    border-radius: 9px;
    background-color: #374151;
    border: 1px solid #4b5563;
}
QCheckBox::indicator:checked { background-color: #16a34a; }
"""

_LABEL_STYLE = "color: #9ca3af; font-size: 10px;"
_SECTION_TITLE_STYLE = "font-weight: bold; font-size: 12px;"
_LOG_STYLE = (
    "font-family: Consolas, monospace; font-size: 11px;"
    " background: #0d1117; color: #d1d5db;"
)


def _section() -> QFrame:
    f = QFrame()
    f.setStyleSheet("QFrame { background-color: #1f2937; border-radius: 6px; }")
    return f


def _label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(_LABEL_STYLE)
    return lbl


def _title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(_SECTION_TITLE_STYLE)
    return lbl


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._pending_ids: dict = {}
        self._create_worker = None
        self._obs_worker = None
        self.setWindowTitle("YouTube Live Manager")
        self.setFixedSize(960, 740)
        self.setStyleSheet(DARK_STYLE)
        self._build_ui()
        self._load_state()
        self._refresh_token_status()

    # ── close: save state ────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._save_state()
        if self._create_worker is not None and self._create_worker.isRunning():
            self._create_worker.quit()
            self._create_worker.wait(3000)
        if self._obs_worker is not None and self._obs_worker.isRunning():
            self._obs_worker.stop()
            self._obs_worker.wait(ObsWatcherWorker.POLL_INTERVAL_SECS * 1000 + 1000)
        super().closeEvent(event)

    # ── state ────────────────────────────────────────────────────────────────

    def _load_state(self):
        cfg = load_config()
        self._title_input.setText(cfg.get("title", ""))
        self._tags_input.setText(cfg.get("tags", ""))
        self._thumb_normal_input.setText(cfg.get("thumbnail_normal", ""))
        self._thumb_shorts_input.setText(cfg.get("thumbnail_shorts", ""))
        self._desc_input.setPlainText(cfg.get("description", ""))
        self._poll_fhd_q.setText(cfg.get("poll_fullhd_question", ""))
        self._poll_fhd_opts.setPlainText(cfg.get("poll_fullhd_options", ""))
        self._poll_shorts_q.setText(cfg.get("poll_shorts_question", ""))
        self._poll_shorts_opts.setPlainText(cfg.get("poll_shorts_options", ""))
        self._test_toggle.setChecked(cfg.get("test_mode", False))

    def _save_state(self):
        save_config({
            "title": self._title_input.text(),
            "tags": self._tags_input.text(),
            "thumbnail_normal": self._thumb_normal_input.text(),
            "thumbnail_shorts": self._thumb_shorts_input.text(),
            "description": self._desc_input.toPlainText(),
            "poll_fullhd_question": self._poll_fhd_q.text(),
            "poll_fullhd_options": self._poll_fhd_opts.toPlainText(),
            "poll_shorts_question": self._poll_shorts_q.text(),
            "poll_shorts_options": self._poll_shorts_opts.toPlainText(),
            "test_mode": self._test_toggle.isChecked(),
        })

    def get_config(self) -> dict:
        """Return current form values for workers."""
        return {
            "title": self._title_input.text(),
            "tags": [t.strip() for t in self._tags_input.text().split(",") if t.strip()],
            "thumbnail_normal": self._thumb_normal_input.text(),
            "thumbnail_shorts": self._thumb_shorts_input.text(),
            "description": self._desc_input.toPlainText(),
            "poll_fullhd_question": self._poll_fhd_q.text(),
            "poll_fullhd_options": [
                o.strip() for o in self._poll_fhd_opts.toPlainText().splitlines() if o.strip()
            ],
            "poll_shorts_question": self._poll_shorts_q.text(),
            "poll_shorts_options": [
                o.strip() for o in self._poll_shorts_opts.toPlainText().splitlines() if o.strip()
            ],
            "test_mode": self._test_toggle.isChecked(),
        }

    # ── token ────────────────────────────────────────────────────────────────

    def _refresh_token_status(self):
        is_valid, label = get_token_status()
        self._token_label.setText(label)
        color = "#22c55e" if is_valid else "#ef4444"
        self._token_dot.setStyleSheet(f"color: {color};")

    def _on_renew(self):
        try:
            refresh_token()
        except Exception as exc:
            self._token_label.setText(f"Erro ao renovar: {exc}")
            self._token_dot.setStyleSheet("color: #ef4444;")
            return
        self._refresh_token_status()

    @property
    def test_mode(self) -> bool:
        return self._test_toggle.isChecked()

    # ── public log/control API (called by workers) ───────────────────────────

    def append_log(self, line: str):
        self._log.appendPlainText(line)

    def clear_log(self):
        self._log.clear()

    def _on_create(self):
        if self._create_worker is not None and self._create_worker.isRunning():
            return
        self.clear_log()
        self.set_running(True)
        self._save_state()
        cfg = self.get_config()
        self._create_worker = CreateLivesWorker(cfg)
        self._create_worker.finished.connect(self._create_worker.deleteLater)
        self._create_worker.log_line.connect(self.append_log)
        self._create_worker.done.connect(self._on_lives_created)
        self._create_worker.failed.connect(lambda: self.set_running(False))
        self._create_worker.start()

    def _on_lives_created(self, ids: dict):
        self.append_log("✅ Lives criadas! Iniciando OBS watcher...")
        self._obs_worker = ObsWatcherWorker(
            stream_fhd_id=ids["stream_fhd_id"],
            stream_shorts_id=ids["stream_shorts_id"],
            bc_fhd_id=ids["bc_fhd_id"],
            bc_shorts_id=ids["bc_shorts_id"],
        )
        self._obs_worker.finished.connect(self._obs_worker.deleteLater)
        self._obs_worker.log_line.connect(self.append_log)
        self._obs_worker.went_live.connect(self._on_went_live)
        self._obs_worker.failed.connect(self._on_obs_failed)
        self._obs_worker.start()

    def _on_went_live(self):
        self._obs_worker = None
        self.set_running(False)

    def _on_obs_failed(self, msg: str):
        self.append_log(msg)
        self._obs_worker = None
        self.set_running(False)

    def set_running(self, running: bool):
        self._create_btn.setEnabled(not running)

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self._root = QVBoxLayout(central)
        self._root.setContentsMargins(12, 12, 12, 12)
        self._root.setSpacing(8)

        self._root.addLayout(self._build_top_bar())

        grid = QHBoxLayout()
        grid.setSpacing(8)
        grid.addWidget(self._build_content_section())
        grid.addWidget(self._build_thumbnails_section())
        self._root.addLayout(grid)

        self._root.addWidget(self._build_description_section())

        poll_row = QHBoxLayout()
        poll_row.setSpacing(8)
        poll_row.addWidget(self._build_poll_section("Full HD", "fullhd", "#3b82f6"))
        poll_row.addWidget(self._build_poll_section("Shorts", "shorts", "#f97316"))
        self._root.addLayout(poll_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        action_row.addWidget(self._build_actions_section(), stretch=0)
        action_row.addWidget(self._build_log_section(), stretch=1)
        self._root.addLayout(action_row)

    def _build_top_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(8)
        self._token_dot = QLabel("●")
        self._token_dot.setFixedWidth(14)
        self._token_label = QLabel("Verificando token...")
        self._renew_btn = QPushButton("Renovar")
        self._renew_btn.setFixedWidth(72)
        self._renew_btn.clicked.connect(self._on_renew)
        self._test_toggle = QCheckBox()
        self._test_toggle.setFixedWidth(44)
        bar.addWidget(self._token_dot)
        bar.addWidget(self._token_label)
        bar.addWidget(self._renew_btn)
        bar.addStretch()
        bar.addWidget(QLabel("Modo Teste"))
        bar.addWidget(self._test_toggle)
        return bar

    def _build_content_section(self) -> QFrame:
        frame = _section()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(4)
        layout.addWidget(_title("📋 Conteúdo da Live"))
        layout.addWidget(_label("Título"))
        self._title_input = QLineEdit()
        layout.addWidget(self._title_input)
        hint = QLabel('  ↳ Shorts: título + " | SHORTS" (automático)')
        hint.setStyleSheet("color: #6b7280; font-size: 10px;")
        layout.addWidget(hint)
        layout.addWidget(_label("Tags (separadas por vírgula)"))
        self._tags_input = QLineEdit()
        layout.addWidget(self._tags_input)
        layout.addStretch()
        return frame

    def _build_thumbnails_section(self) -> QFrame:
        frame = _section()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(4)
        layout.addWidget(_title("🖼️ Thumbnails"))
        layout.addWidget(_label("Normal (Full HD)"))
        self._thumb_normal_input = QLineEdit()
        row1 = QHBoxLayout()
        row1.addWidget(self._thumb_normal_input)
        browse1 = QPushButton("Browse")
        browse1.setFixedWidth(60)
        browse1.clicked.connect(lambda: self._browse_thumbnail(self._thumb_normal_input))
        row1.addWidget(browse1)
        layout.addLayout(row1)
        layout.addWidget(_label("Shorts"))
        self._thumb_shorts_input = QLineEdit()
        row2 = QHBoxLayout()
        row2.addWidget(self._thumb_shorts_input)
        browse2 = QPushButton("Browse")
        browse2.setFixedWidth(60)
        browse2.clicked.connect(lambda: self._browse_thumbnail(self._thumb_shorts_input))
        row2.addWidget(browse2)
        layout.addLayout(row2)
        layout.addStretch()
        return frame

    def _browse_thumbnail(self, target: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Thumbnail", "", "Imagens (*.png *.jpg *.jpeg)"
        )
        if path:
            target.setText(path)

    def _build_description_section(self) -> QFrame:
        frame = _section()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(4)
        layout.addWidget(_title("📝 Descrição"))
        self._desc_input = QPlainTextEdit()
        self._desc_input.setFixedHeight(90)
        layout.addWidget(self._desc_input)
        return frame

    def _build_poll_section(self, label: str, key: str, border_color: str) -> QWidget:
        """Build a poll config section with a colored left border bar."""
        container = QWidget()
        outer = QHBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        left_bar = QWidget()
        left_bar.setFixedWidth(3)
        left_bar.setStyleSheet(f"background-color: {border_color}; border-radius: 2px 0 0 2px;")
        outer.addWidget(left_bar)

        frame = QWidget()
        frame.setStyleSheet("background-color: #1f2937; border-radius: 0 6px 6px 0;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(4)
        layout.addWidget(_title(f"📊 Enquete — {label}"))
        layout.addWidget(_label("Pergunta"))
        q_input = QLineEdit()
        layout.addWidget(q_input)
        layout.addWidget(_label("Opções (uma por linha)"))
        opts_input = QPlainTextEdit()
        opts_input.setFixedHeight(56)
        layout.addWidget(opts_input)
        outer.addWidget(frame)

        if key == "fullhd":
            self._poll_fhd_q = q_input
            self._poll_fhd_opts = opts_input
        elif key == "shorts":
            self._poll_shorts_q = q_input
            self._poll_shorts_opts = opts_input
        else:
            raise ValueError(f"Unknown poll key: {key!r}")

        return container

    def _build_actions_section(self) -> QFrame:
        frame = _section()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(_title("🚀 Ações"))
        self._create_btn = QPushButton("Criar Ambas as Lives")
        self._create_btn.setObjectName("create_btn")
        self._create_btn.setMinimumWidth(180)
        self._create_btn.setMinimumHeight(40)
        self._create_btn.clicked.connect(self._on_create)
        layout.addWidget(self._create_btn)
        layout.addStretch()
        return frame

    def _build_log_section(self) -> QFrame:
        frame = _section()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(4)
        layout.addWidget(_title("📟 Status"))
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(_LOG_STYLE)
        self._log.setMinimumHeight(100)
        layout.addWidget(self._log)
        return frame
