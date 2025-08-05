import logging
import platform

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .styles import Styles

logger = logging.getLogger(__name__)


class AboutPopup(QDialog):
    def __init__(self, hotkey_display: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About Clipboard Manager")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(400, 300)
        self.setStyleSheet(Styles.get_about_popup_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("🔷 Clipboard Manager v1.0")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Content
        message = (
            "A modern clipboard history manager with:\n\n"
            "• Windows style interface\n"
            "• Smart content detection\n"
            "• Search and filtering\n"
            "• Pin important items\n"
            "• Cross-platform support\n\n"
            f"Hotkey: {hotkey_display}"
        )

        content_label = QLabel(message)
        content_label.setWordWrap(True)
        content_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        content_label.setStyleSheet(
            "font-size: 12px; color: #cccccc; line-height: 1.4;"
        )

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(80, 30)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            """
        )

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)

        layout.addWidget(title_label)
        layout.addWidget(content_label)
        layout.addStretch()
        layout.addLayout(button_layout)

        # Auto-close after 10 seconds
        QTimer.singleShot(10000, self.close)

    def showEvent(self, event):
        """Override show event to log when popup is shown"""
        super().showEvent(event)

    def closeEvent(self, event):
        """Override close event to log when popup is closed"""
        super().closeEvent(event)


def show_about_popup(parent=None):
    try:

        current_platform = platform.system().lower()
        hotkey_display = {
            "windows": "Windows+C",
            "linux": "Super+V",
        }.get(current_platform, "Cmd+C")

        popup = AboutPopup(hotkey_display, parent)
        popup.show()
        popup.raise_()
        popup.activateWindow()

    except Exception as e:
        logger.error(f"Error in show_about_popup: {e}")
        raise
