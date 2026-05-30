"""Reusable configuration tab widget."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QLineEdit, QPlainTextEdit, QFileDialog, QFrame
)
from PyQt6.QtCore import pyqtSignal

from core.youtube_api import get_token_status, refresh_token
from ui.workers import CreateLivesWorker, ObsWatcherWorker

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


class ConfigTab(QWidget):
    status_changed = pyqtSignal()  # Signal to main window that something changed

    def __init__(self, profile_data: dict, global_config: dict):
        super().__init__()
        self._pending_ids: dict = {}
        self._create_worker = None
        self._obs_worker = None
        self._profile_data = profile_data
        self._global_config = global_config
        self._build_ui()
        self._load_data(profile_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        grid = QHBoxLayout()
        grid.setSpacing(8)
        grid.addWidget(self._build_content_section())
        grid.addWidget(self._build_thumbnails_section())
        layout.addLayout(grid)

        layout.addWidget(self._build_description_section())

        poll_row = QHBoxLayout()
        poll_row.setSpacing(8)
        poll_row.addWidget(self._build_poll_section("Full HD", "fullhd", "#3b82f6"))
        poll_row.addWidget(self._build_poll_section("Shorts", "shorts", "#f97316"))
        layout.addLayout(poll_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        action_row.addWidget(self._build_actions_section(), stretch=0)
        action_row.addWidget(self._build_log_section(), stretch=1)
        layout.addLayout(action_row)

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

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(_title(f"📊 Enquete — {label}"))
        title_row.addStretch()
        toggle = QCheckBox("Ativar")
        toggle.setChecked(True)
        title_row.addWidget(toggle)
        layout.addLayout(title_row)

        layout.addWidget(_label("Pergunta"))
        q_input = QLineEdit()
        layout.addWidget(q_input)
        layout.addWidget(_label("Opções (uma por linha)"))
        opts_input = QPlainTextEdit()
        opts_input.setFixedHeight(56)
        layout.addWidget(opts_input)
        outer.addWidget(frame)

        toggle.stateChanged.connect(
            lambda: (q_input.setEnabled(toggle.isChecked()),
                     opts_input.setEnabled(toggle.isChecked()))
        )

        if key == "fullhd":
            self._poll_fhd_q = q_input
            self._poll_fhd_opts = opts_input
            self._poll_fhd_toggle = toggle
        elif key == "shorts":
            self._poll_shorts_q = q_input
            self._poll_shorts_opts = opts_input
            self._poll_shorts_toggle = toggle

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
        
        # Note: Delete button visibility and enabled state should be handled by main window 
        # based on global test_mode and per-tab pending_ids
        self._delete_btn = QPushButton("🗑️ Deletar Streams de Teste")
        self._delete_btn.setObjectName("delete_btn")
        self._delete_btn.setMinimumWidth(180)
        self._delete_btn.setVisible(False)
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._on_delete_streams)
        layout.addWidget(self._delete_btn)
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

    def _load_data(self, data: dict):
        self._title_input.setText(data.get("title", ""))
        self._tags_input.setText(data.get("tags", ""))
        self._thumb_normal_input.setText(data.get("thumbnail_normal", ""))
        self._thumb_shorts_input.setText(data.get("thumbnail_shorts", ""))
        self._desc_input.setPlainText(data.get("description", ""))
        self._poll_fhd_q.setText(data.get("poll_fullhd_question", ""))
        self._poll_fhd_opts.setPlainText(data.get("poll_fullhd_options", ""))
        self._poll_shorts_q.setText(data.get("poll_shorts_question", ""))
        self._poll_shorts_opts.setPlainText(data.get("poll_shorts_options", ""))
        self._poll_fhd_toggle.setChecked(data.get("poll_fullhd_enabled", True))
        self._poll_shorts_toggle.setChecked(data.get("poll_shorts_enabled", True))

    def get_data(self) -> dict:
        return {
            "name": self._profile_data.get("name", "Sem Nome"),
            "title": self._title_input.text(),
            "tags": self._tags_input.text(),
            "thumbnail_normal": self._thumb_normal_input.text(),
            "thumbnail_shorts": self._thumb_shorts_input.text(),
            "description": self._desc_input.toPlainText(),
            "poll_fullhd_question": self._poll_fhd_q.text(),
            "poll_fullhd_options": self._poll_fhd_opts.toPlainText(),
            "poll_shorts_question": self._poll_shorts_q.text(),
            "poll_shorts_options": self._poll_shorts_opts.toPlainText(),
            "poll_fullhd_enabled": self._poll_fhd_toggle.isChecked(),
            "poll_shorts_enabled": self._poll_shorts_toggle.isChecked(),
        }

    def get_config_for_worker(self) -> dict:
        data = self.get_data()
        data["tags"] = [t.strip() for t in data["tags"].split(",") if t.strip()]
        data["poll_fullhd_options"] = [
            o.strip() for o in data["poll_fullhd_options"].splitlines() if o.strip()
        ]
        data["poll_shorts_options"] = [
            o.strip() for o in data["poll_shorts_options"].splitlines() if o.strip()
        ]
        data["test_mode"] = self._global_config.get("test_mode", False)
        data["firefox_profile"] = self._global_config.get("firefox_profile", "")
        return data

    def append_log(self, line: str):
        self._log.appendPlainText(line)

    def _on_create(self):
        if self._create_worker is not None and self._create_worker.isRunning():
            return
        self._log.clear()
        cfg = self.get_config_for_worker()
        self._create_worker = CreateLivesWorker(cfg)
        self._create_worker.finished.connect(self._create_worker.deleteLater)
        self._create_worker.log_line.connect(self.append_log)
        self._create_worker.done.connect(self._on_lives_created)
        self._create_worker.failed.connect(self._on_create_failed)
        self._create_worker.aborted.connect(self._on_aborted)
        self._create_worker.start()
        self._create_btn.setText("⛔ Cancelar")
        self._create_btn.clicked.disconnect()
        self._create_btn.clicked.connect(self._on_cancel)
        self.status_changed.emit()

    def _restore_create_button(self):
        self._create_btn.setText("Criar Ambas as Lives")
        self._create_btn.clicked.disconnect()
        self._create_btn.clicked.connect(self._on_create)
        self._create_btn.setEnabled(True)

    def _on_cancel(self):
        self._create_btn.setEnabled(False)
        if self._create_worker is not None:
            self._create_worker.request_stop()

    def _on_aborted(self):
        self.append_log("❌ Criação cancelada — recursos limpos")
        self._restore_create_button()
        self.status_changed.emit()

    def _on_create_failed(self):
        self._restore_create_button()
        self.status_changed.emit()

    def _on_lives_created(self, ids: dict):
        self.append_log("✅ Lives criadas! Iniciando OBS watcher...")
        self._pending_ids = ids
        self._create_btn.setText("⛔ Parar Watcher")
        self._create_btn.clicked.disconnect()
        self._create_btn.clicked.connect(self._on_stop_obs)
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
        self._obs_worker.stopped.connect(self._on_obs_stopped)
        self._obs_worker.start()
        self.status_changed.emit()

    def _on_stop_obs(self):
        self._create_btn.setEnabled(False)
        if self._obs_worker is not None:
            self._obs_worker.stop()

    def _on_obs_stopped(self):
        self.append_log("⛔ Watcher cancelado")
        self._obs_worker = None
        self._restore_create_button()
        self.status_changed.emit()

    def _on_went_live(self):
        self._obs_worker = None
        self._restore_create_button()
        self.status_changed.emit()

    def _on_obs_failed(self, msg: str):
        self.append_log(msg)
        self._obs_worker = None
        self._restore_create_button()
        self.status_changed.emit()

    def _on_delete_streams(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar os streams de teste de '{self._profile_data['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from ui.workers import DeleteResourcesWorker
            self._delete_btn.setEnabled(False)
            self._create_btn.setEnabled(False)
            worker = DeleteResourcesWorker(self._pending_ids)
            worker.finished.connect(worker.deleteLater)
            worker.log_line.connect(self.append_log)
            worker.done.connect(self._on_delete_done)
            worker.failed.connect(self._on_delete_failed)
            worker.start()

    def _on_delete_done(self):
        self._pending_ids = {}
        self._restore_create_button()
        self.status_changed.emit()

    def _on_delete_failed(self, msg: str):
        self.append_log(msg)
        self._restore_create_button()
        self.status_changed.emit()

    def update_test_mode(self, test_mode: bool):
        self._global_config["test_mode"] = test_mode
        self._delete_btn.setVisible(test_mode)
        self._delete_btn.setEnabled(test_mode and bool(self._pending_ids))

    def stop_all(self):
        if self._create_worker and self._create_worker.isRunning():
            self._create_worker.quit()
            self._create_worker.wait(3000)
        if self._obs_worker and self._obs_worker.isRunning():
            self._obs_worker.blockSignals(True)
            self._obs_worker.stop()
            self._obs_worker.wait(ObsWatcherWorker.POLL_INTERVAL_SECS * 1000 + 1000)
