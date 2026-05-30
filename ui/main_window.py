"""YouTube Live Manager — main application window."""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QTabWidget, QInputDialog
)
from PyQt6.QtCore import Qt

from core.youtube_api import get_token_status, refresh_token
from core.state import load_config, save_config, DEFAULT_PROFILE
from ui.config_tab import ConfigTab

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
        self._build_ui()
        self._refresh_token_status()
        self._load_profiles()

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

    def _load_profiles(self):
        profiles = self._config.get("profiles", [])
        active_index = self._config.get("active_profile_index", 0)
        
        for profile_data in profiles:
            self._create_tab(profile_data)
            
        if active_index < self._tabs.count():
            self._tabs.setCurrentIndex(active_index)

    def _create_tab(self, profile_data: dict):
        tab = ConfigTab(profile_data, self._config)
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
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, ConfigTab):
                tab.stop_all()
        super().closeEvent(event)

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
