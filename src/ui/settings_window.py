# clipboard_manager/src/ui/settings_window.py
"""
Enhanced settings window with modern design
"""
import logging

from PySide6.QtCore import Qt
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QFrame,
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
    """Enhanced settings configuration window with modern design"""

    settings_changed = pyqtSignal()

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup the enhanced UI with modern design"""
        self.setWindowTitle("Clipboard Manager Settings")
        self.setFixedSize(500, 400)  # Increased size
        self.setStyleSheet(Styles.get_enhanced_settings_window_style())

        # Main container with modern styling
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Title section
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("⚙️ Settings")
        title_label.setStyleSheet(
            """
            color: #4facfe;
            font-size: 18px;
            font-weight: bold;
            padding: 10px 0px;
        """
        )
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("Configure your clipboard manager preferences")
        subtitle_label.setStyleSheet(
            """
            color: rgba(255, 255, 255, 0.7);
            font-size: 12px;
            padding: 0px 0px 10px 0px;
        """
        )
        title_layout.addWidget(subtitle_label)

        main_layout.addWidget(title_frame)

        # General settings with enhanced design
        general_group = QGroupBox("📋 General Settings")
        general_layout = QFormLayout(general_group)
        general_layout.setSpacing(12)
        general_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Max items with better description
        max_items_label = QLabel("Maximum clipboard items:")
        max_items_label.setStyleSheet("color: #ffffff; font-weight: 500;")
        self.max_items_spin = QSpinBox()
        self.max_items_spin.setRange(10, 200)
        self.max_items_spin.setValue(25)
        self.max_items_spin.setToolTip("Maximum number of items to keep in history")
        general_layout.addRow(max_items_label, self.max_items_spin)

        # Max text length with better description
        max_text_label = QLabel("Maximum text length:")
        max_text_label.setStyleSheet("color: #ffffff; font-weight: 500;")
        self.max_text_spin = QSpinBox()
        self.max_text_spin.setRange(1000, 100000)
        self.max_text_spin.setValue(10000)
        self.max_text_spin.setToolTip("Maximum characters to store for text items")
        general_layout.addRow(max_text_label, self.max_text_spin)

        # Auto-start with better description
        autostart_label = QLabel("Start with system:")
        autostart_label.setStyleSheet("color: #ffffff; font-weight: 500;")
        self.autostart_check = QCheckBox("Enable auto-start")
        self.autostart_check.setToolTip(
            "Automatically start clipboard manager when system boots"
        )
        general_layout.addRow(autostart_label, self.autostart_check)

        main_layout.addWidget(general_group)

        # Appearance settings with enhanced design
        appearance_group = QGroupBox("🎨 Appearance")
        appearance_layout = QFormLayout(appearance_group)
        appearance_layout.setSpacing(12)
        appearance_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Theme info with better styling
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet("color: #ffffff; font-weight: 500;")
        theme_info = QLabel("Dark theme (always enabled)")
        theme_info.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-style: italic;")
        appearance_layout.addRow(theme_label, theme_info)

        # Notifications setting
        notifications_label = QLabel("Notifications:")
        notifications_label.setStyleSheet("color: #ffffff; font-weight: 500;")
        self.notifications_check = QCheckBox("Show notifications")
        self.notifications_check.setToolTip(
            "Show notifications for new clipboard items"
        )
        appearance_layout.addRow(notifications_label, self.notifications_check)

        main_layout.addWidget(appearance_group)

        # Advanced settings
        advanced_group = QGroupBox(" Advanced")
        advanced_layout = QFormLayout(advanced_group)
        advanced_layout.setSpacing(12)
        advanced_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Cleanup interval
        cleanup_label = QLabel("Cleanup interval (hours):")
        cleanup_label.setStyleSheet("color: #ffffff; font-weight: 500;")
        self.cleanup_spin = QSpinBox()
        self.cleanup_spin.setRange(1, 168)  # 1 hour to 1 week
        self.cleanup_spin.setValue(24)
        self.cleanup_spin.setToolTip("How often to clean up old items")
        advanced_layout.addRow(cleanup_label, self.cleanup_spin)

        main_layout.addWidget(advanced_group)

        # Enhanced buttons with better layout
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 10, 0, 0)

        # Reset button with warning style
        reset_btn = QPushButton("🔄 Reset to Defaults")
        reset_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 107, 107, 0.2);
                border: 1px solid rgba(255, 107, 107, 0.3);
                color: #ff6b6b;
            }
            QPushButton:hover {
                background: rgba(255, 107, 107, 0.3);
                border: 1px solid #ff6b6b;
            }
        """
        )
        reset_btn.clicked.connect(self.reset_settings)

        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)

        # Save button with primary style
        save_btn = QPushButton("💾 Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_settings)

        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        main_layout.addWidget(button_frame)

    def load_settings(self):
        """Load current settings with enhanced defaults"""
        self.max_items_spin.setValue(self.config.get("max_items", 25))
        self.max_text_spin.setValue(self.config.get("max_text_length", 10000))
        self.autostart_check.setChecked(self.config.get("autostart", False))
        self.notifications_check.setChecked(self.config.get("show_notifications", True))
        self.cleanup_spin.setValue(self.config.get("cleanup_interval_hours", 24))

    def save_settings(self):
        """Save settings with enhanced validation"""
        try:
            # Validate values
            if self.max_items_spin.value() < 10:
                QMessageBox.warning(self, "Warning", "Minimum 10 items required")
                return

            if self.max_text_spin.value() < 1000:
                QMessageBox.warning(self, "Warning", "Minimum 1000 characters required")
                return

            # Save settings
            self.config.set("max_items", self.max_items_spin.value())
            self.config.set("max_text_length", self.max_text_spin.value())
            self.config.set("autostart", self.autostart_check.isChecked())
            self.config.set("show_notifications", self.notifications_check.isChecked())
            self.config.set("cleanup_interval_hours", self.cleanup_spin.value())

            self.config.save()
            self.settings_changed.emit()

            # Handle autostart
            from utils.autostart import AutostartManager

            autostart_manager = AutostartManager()

            if self.autostart_check.isChecked():
                autostart_manager.enable()
            else:
                autostart_manager.disable()

            # Show success message
            QMessageBox.information(
                self,
                "Success",
                "Settings saved successfully! Changes will take effect immediately.",
            )

            self.accept()

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def reset_settings(self):
        """Reset to default settings with confirmation"""
        # flake8: noqa: E501
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config.reset_to_defaults()
            self.load_settings()
            QMessageBox.information(
                self, "Reset Complete", "Settings have been reset to defaults."
            )
