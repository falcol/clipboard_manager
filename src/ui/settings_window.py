# clipboard_manager/src/ui/settings_window.py
"""
Settings window for configuration
"""
import logging

from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ui.styles import Styles
from utils.config import Config

logger = logging.getLogger(__name__)


class SettingsWindow(QDialog):
    """Settings configuration window"""

    settings_changed = pyqtSignal()

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup the UI"""
        self.setWindowTitle("Clipboard Manager Settings")
        self.setFixedSize(400, 300)
        self.setStyleSheet(Styles.get_settings_window_style())

        layout = QVBoxLayout(self)

        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)

        # Max items
        self.max_items_spin = QSpinBox()
        self.max_items_spin.setRange(10, 100)
        self.max_items_spin.setValue(25)
        general_layout.addRow("Max clipboard items:", self.max_items_spin)

        # Max text length
        self.max_text_spin = QSpinBox()
        self.max_text_spin.setRange(1000, 50000)
        self.max_text_spin.setValue(10000)
        general_layout.addRow("Max text length:", self.max_text_spin)

        # Auto-start
        self.autostart_check = QCheckBox("Start with system")
        general_layout.addRow(self.autostart_check)

        layout.addWidget(general_group)

        # Appearance settings
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        # Theme (placeholder for future)
        theme_label = QLabel("Dark theme (always on)")
        theme_label.setStyleSheet("color: #888;")
        appearance_layout.addRow(theme_label)

        layout.addWidget(appearance_group)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_settings)

        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def load_settings(self):
        """Load current settings"""
        self.max_items_spin.setValue(self.config.get("max_items", 25))
        self.max_text_spin.setValue(self.config.get("max_text_length", 10000))
        self.autostart_check.setChecked(self.config.get("autostart", False))

    def save_settings(self):
        """Save settings"""
        try:
            self.config.set("max_items", self.max_items_spin.value())
            self.config.set("max_text_length", self.max_text_spin.value())
            self.config.set("autostart", self.autostart_check.isChecked())

            self.config.save()
            self.settings_changed.emit()

            # Handle autostart
            from utils.autostart import AutostartManager

            autostart_manager = AutostartManager()

            if self.autostart_check.isChecked():
                autostart_manager.enable()
            else:
                autostart_manager.disable()

            self.accept()

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def reset_settings(self):
        """Reset to default settings"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config.reset_to_defaults()
            self.load_settings()
