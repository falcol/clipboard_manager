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
        self.config = config  # Keep the same variable name
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup the UI"""
        self.setWindowTitle("Clipboard Manager Settings")
        self.setFixedSize(400, 500)  # Increased height for new settings
        self.setStyleSheet(Styles.get_settings_window_style())

        layout = QVBoxLayout(self)

        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)

        # Max items (like Windows clipboard manager)
        self.max_items_spin = QSpinBox()
        self.max_items_spin.setRange(10, 100)
        self.max_items_spin.setValue(25)  # Windows default: 25 items
        general_layout.addRow("Max clipboard items:", self.max_items_spin)

        # Max text length (like Windows clipboard manager)
        self.max_text_spin = QSpinBox()
        self.max_text_spin.setRange(1000, 2000000)  # Up to 2MB like Windows
        self.max_text_spin.setValue(1000000)  # 1MB default like Windows
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

        # Performance settings (RAM optimization)
        performance_group = QGroupBox("Performance & RAM")
        performance_layout = QFormLayout(performance_group)

        # Cache size
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 100)
        self.cache_size_spin.setValue(25)
        self.cache_size_spin.setSuffix(" MB")
        performance_layout.addRow("Cache size:", self.cache_size_spin)

        # Thumbnail size
        self.thumbnail_size_spin = QSpinBox()
        self.thumbnail_size_spin.setRange(32, 128)
        self.thumbnail_size_spin.setValue(64)
        self.thumbnail_size_spin.setSuffix(" px")
        performance_layout.addRow("Thumbnail size:", self.thumbnail_size_spin)

        # Image quality
        self.image_quality_spin = QSpinBox()
        self.image_quality_spin.setRange(50, 95)
        self.image_quality_spin.setValue(85)
        self.image_quality_spin.setSuffix("%")
        performance_layout.addRow("Image quality:", self.image_quality_spin)

        # Cleanup interval
        self.cleanup_interval_spin = QSpinBox()
        self.cleanup_interval_spin.setRange(1, 48)
        self.cleanup_interval_spin.setValue(12)
        self.cleanup_interval_spin.setSuffix(" hours")
        performance_layout.addRow("Cleanup interval:", self.cleanup_interval_spin)

        layout.addWidget(performance_group)

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
        """Load settings from original config"""
        # Use original_config instead of working_config
        self.max_items_spin.setValue(self.config.get("max_items", 25))
        self.max_text_spin.setValue(self.config.get("max_text_length", 1000000))
        self.autostart_check.setChecked(self.config.get("autostart", False))

        # Performance settings
        self.cache_size_spin.setValue(self.config.get("cache_size_mb", 25))
        self.thumbnail_size_spin.setValue(self.config.get("thumbnail_size", 64))
        self.image_quality_spin.setValue(self.config.get("image_quality", 85))
        self.cleanup_interval_spin.setValue(
            self.config.get("cleanup_interval_hours", 12)
        )

    def save_settings(self):
        """Save settings only when Save button is clicked"""
        try:
            # Update original config from working config
            self.config.set("max_items", self.max_items_spin.value())
            self.config.set("max_text_length", self.max_text_spin.value())
            self.config.set("autostart", self.autostart_check.isChecked())

            # Performance settings
            self.config.set("cache_size_mb", self.cache_size_spin.value())
            self.config.set("thumbnail_size", self.thumbnail_size_spin.value())
            self.config.set("image_quality", self.image_quality_spin.value())
            self.config.set(
                "cleanup_interval_hours", self.cleanup_interval_spin.value()
            )

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
            self.config.reset_to_defaults()  # Use self.config
            self.load_settings()

    def reject(self):
        """Handle when cancel/close window"""
        self.load_settings()  # Reset to original config
        super().reject()

    def showEvent(self, event):
        """Ensure settings are loaded every time the window is opened"""
        self.load_settings()
        super().showEvent(event)
