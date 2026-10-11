"""Reusable configuration tab widget."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QLineEdit, QPlainTextEdit, QFileDialog, QFrame
)
from PyQt6.QtCore import pyqtSignal

from ui.workers import CreateLivesWorker

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

    def __init__(self, profile_data: dict, global_config: dict, stream_key_provider):
        super().__init__()
        self._stream_key_provider = stream_key_provider
        self._pending_ids: dict = {}
        self._create_worker = None
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
        self._desc_input.setFixedHeight(120)
        layout.addWidget(self._desc_input)
        return frame

    def _build_actions_section(self) -> QFrame:
        frame = _section()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(_title("🚀 Ações"))

        self._enable_fhd_toggle = QCheckBox("Incluir Full HD")
        self._enable_fhd_toggle.setChecked(True)
        layout.addWidget(self._enable_fhd_toggle)

        self._enable_shorts_toggle = QCheckBox("Incluir Shorts")
        self._enable_shorts_toggle.setChecked(True)
        layout.addWidget(self._enable_shorts_toggle)

        layout.addSpacing(4)

        self._create_btn = QPushButton("Criar Lives")
        self._create_btn.setObjectName("create_btn")
        self._create_btn.setMinimumWidth(180)
        self._create_btn.setMinimumHeight(40)
        self._create_btn.clicked.connect(self._on_create)
        layout.addWidget(self._create_btn)
        
        self._delete_btn = QPushButton("🗑️ Deletar Lives de Teste")
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
        self._enable_fhd_toggle.setChecked(data.get("enable_fhd", True))
        self._enable_shorts_toggle.setChecked(data.get("enable_shorts", True))

    def get_data(self) -> dict:
        return {
            "name": self._profile_data.get("name", "Sem Nome"),
            "title": self._title_input.text(),
            "tags": self._tags_input.text(),
            "thumbnail_normal": self._thumb_normal_input.text(),
            "thumbnail_shorts": self._thumb_shorts_input.text(),
            "description": self._desc_input.toPlainText(),
            "enable_fhd": self._enable_fhd_toggle.isChecked(),
            "enable_shorts": self._enable_shorts_toggle.isChecked(),
        }

    def get_config_for_worker(self) -> dict:
        data = self.get_data()
        data["tags"] = [t.strip() for t in data["tags"].split(",") if t.strip()]
        data["test_mode"] = self._global_config.get("test_mode", False)
        data["firefox_profile"] = self._global_config.get("firefox_profile", "")
        keys = self._stream_key_provider()
        data["stream_key"] = keys["fhd"]
        data["stream_key_shorts"] = keys["shorts"]
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
        self._create_btn.setText("Criar Lives")
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
        self.append_log("✅ Lives criadas com sucesso!")
        self._pending_ids = ids
        self._restore_create_button()
        self.status_changed.emit()

    def _on_delete_streams(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja deletar as lives de teste de '{self._profile_data['name']}'?",
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
