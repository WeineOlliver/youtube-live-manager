"""YouTube Live Manager — main application window."""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QTabWidget, QInputDialog, QLineEdit
)
from PyQt6.QtCore import Qt

from core.youtube_api import get_token_status
from core.state import (
    load_config, save_config, load_stream_key, save_stream_key, DEFAULT_PROFILE,
)
from ui.config_tab import ConfigTab
from ui.workers import RenewTokenWorker

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
QPushButton#delete_btn { background-color: #7f1d1d; }
QPushButton#delete_btn:hover { background-color: #991b1b; }
QPushButton#delete_btn:disabled { background-color: #1f2937; color: #6b7280; }
QCheckBox::indicator {
    width: 36px; height: 18px;
    border-radius: 9px;
    background-color: #374151;
    border: 1px solid #4b5563;
}
QCheckBox::indicator:checked { background-color: #16a34a; }
QTabWidget::pane { border: 1px solid #374151; border-radius: 4px; top: -1px; }
QTabBar::tab {
    background: #1f2937;
    color: #9ca3af;
    padding: 8px 16px;
    border: 1px solid #374151;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #111827;
    color: #f9fafb;
    border-bottom: 2px solid #16a34a;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Live Manager")
        self.setFixedSize(980, 800)
        self.setStyleSheet(DARK_STYLE)
        
        self._config = load_config()
        self._renew_worker = None
        self._loading = True
        self._build_ui()
        self._refresh_token_status()
        self._load_profiles()
        self._loading = False
        self._save_state()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self._root = QVBoxLayout(central)
        self._root.setContentsMargins(12, 12, 12, 12)
        self._root.setSpacing(8)

        # Top Bar
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
        self._test_toggle.setChecked(self._config.get("test_mode", False))
        self._test_toggle.stateChanged.connect(self._on_test_mode_changed)
        
        bar.addWidget(self._token_dot)
        bar.addWidget(self._token_label)
        bar.addWidget(self._renew_btn)
        bar.addStretch()
        bar.addWidget(QLabel("Modo Teste"))
        bar.addWidget(self._test_toggle)
        self._root.addLayout(bar)

        # RTMP key rows
        self._key_inputs = {
            "fhd": self._add_key_row("Chave RTMP Full HD:", "fhd"),
            "shorts": self._add_key_row("Chave RTMP Shorts:", "shorts"),
        }

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._on_close_tab)
        self._tabs.currentChanged.connect(self._on_tab_changed)
        self._tabs.tabBarDoubleClicked.connect(self._on_rename_tab)
        
        self._add_btn = QPushButton("+ Novo Perfil")
        self._add_btn.clicked.connect(self._on_add_tab)
        self._tabs.setCornerWidget(self._add_btn, Qt.Corner.TopRightCorner)
        
        self._root.addWidget(self._tabs)

    def _on_rename_tab(self, index: int):
        old_name = self._tabs.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Renomear Perfil", "Novo Nome:", text=old_name)
        if ok and new_name:
            self._tabs.setTabText(index, new_name)
            self._save_state()

    def _add_key_row(self, label: str, kind: str) -> QLineEdit:
        row = QHBoxLayout()
        row.setSpacing(8)
        key_input = QLineEdit(load_stream_key(kind))
        key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_input.setPlaceholderText("Cole aqui a chave de transmissão criada no YouTube Studio")
        key_input.editingFinished.connect(lambda: save_stream_key(key_input.text(), kind))
        eye_btn = QPushButton("👁")
        eye_btn.setFixedWidth(32)
        eye_btn.setCheckable(True)
        eye_btn.toggled.connect(lambda visible: key_input.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        ))
        title = QLabel(label)
        title.setFixedWidth(130)
        row.addWidget(title)
        row.addWidget(key_input)
        row.addWidget(eye_btn)
        self._root.addLayout(row)
        return key_input

    def _stream_keys(self) -> dict:
        return {kind: inp.text() for kind, inp in self._key_inputs.items()}

    def _load_profiles(self):
        profiles = self._config.get("profiles", [])
        active_index = self._config.get("active_profile_index", 0)
        
        for profile_data in profiles:
            self._create_tab(profile_data)
            
        if active_index < self._tabs.count():
            self._tabs.setCurrentIndex(active_index)

    def _create_tab(self, profile_data: dict):
        tab = ConfigTab(profile_data, self._config, self._stream_keys)
        tab.status_changed.connect(self._save_state)
        index = self._tabs.addTab(tab, profile_data.get("name", "Nova Live"))
        tab.update_test_mode(self._test_toggle.isChecked())
        return index

    def _on_add_tab(self):
        name, ok = QInputDialog.getText(self, "Novo Perfil", "Nome do Perfil:")
        if ok and name:
            profile_data = DEFAULT_PROFILE.copy()
            profile_data["name"] = name
            index = self._create_tab(profile_data)
            self._tabs.setCurrentIndex(index)
            self._save_state()

    def _on_close_tab(self, index: int):
        if self._tabs.count() <= 1:
            return # Keep at least one tab
        
        tab = self._tabs.widget(index)
        tab.stop_all()
        self._tabs.removeTab(index)
        self._save_state()

    def _on_tab_changed(self, index: int):
        self._save_state()

    def _on_test_mode_changed(self):
        is_test = self._test_toggle.isChecked()
        self._config["test_mode"] = is_test
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, ConfigTab):
                tab.update_test_mode(is_test)
        self._save_state()

    def _save_state(self):
        # Tabs emit currentChanged while being added; saving then would write a
        # config with only some of the profiles.
        if self._loading:
            return
        profiles = []
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, ConfigTab):
                data = tab.get_data()
                data["name"] = self._tabs.tabText(i)
                profiles.append(data)
        
        self._config["profiles"] = profiles
        self._config["active_profile_index"] = self._tabs.currentIndex()
        self._config["test_mode"] = self._test_toggle.isChecked()
        save_config(self._config)

    def closeEvent(self, event):
        self._save_state()
        for kind, key in self._stream_keys().items():
            save_stream_key(key, kind)
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, ConfigTab):
                tab.stop_all()
        if self._renew_worker is not None:
            self._renew_worker.wait()
        super().closeEvent(event)

    def _refresh_token_status(self):
        is_valid, label = get_token_status()
        self._token_label.setText(label)
        color = "#22c55e" if is_valid else "#ef4444"
        self._token_dot.setStyleSheet(f"color: {color};")

    def _on_renew(self):
        if self._renew_worker is not None:
            return
        self._renew_btn.setEnabled(False)
        self._token_label.setText("Aguardando login no navegador...")
        self._renew_worker = RenewTokenWorker()
        self._renew_worker.done.connect(self._on_renew_done)
        self._renew_worker.finished.connect(self._on_renew_finished)
        self._renew_worker.finished.connect(self._renew_worker.deleteLater)
        self._renew_worker.start()

    def _on_renew_done(self, ok: bool, msg: str):
        if ok:
            self._refresh_token_status()
        else:
            self._token_label.setText(msg)
            self._token_dot.setStyleSheet("color: #ef4444;")

    def _on_renew_finished(self):
        self._renew_worker = None
        self._renew_btn.setEnabled(True)
