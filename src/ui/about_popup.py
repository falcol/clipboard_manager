import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

logger = logging.getLogger(__name__)


class AboutPopup(QDialog):
    def __init__(self, hotkey_display: str, parent=None):
        super().__init__(parent)

        # macOS-like lightweight dialog
        self.setWindowTitle("About B1Clip")
        self.setObjectName("aboutPopup")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(380, 260)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        # Header (title centered)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(0)

        title_label = QLabel("B1Clip")
        title_label.setObjectName("aboutTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_container = QHBoxLayout()
        title_container.addStretch()
        title_container.addWidget(title_label)
        title_container.addStretch()
        layout.addLayout(title_container)

        # Content
        content = QLabel(
            "A modern clipboard history manager with:\n\n"
            "• Smart content detection\n"
            "• Search and filtering\n"
            "• Pin important items\n"
            "• Cross-platform support\n\n"
            f"Hotkey: {hotkey_display}"
        )
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        content.setObjectName("aboutContent")
        layout.addWidget(content)

        layout.addStretch()

        # Footer buttons (right aligned, flat)
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(28)
        close_btn.setObjectName("aboutCloseButton")
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)

        layout.addLayout(footer)

    def showEvent(self, event):
        super().showEvent(event)

    def closeEvent(self, event):
        super().closeEvent(event)


def show_about_popup(parent=None):
    try:
        import platform

        current_platform = platform.system().lower()
        hotkey_display = {"windows": "Windows+C", "linux": "Super+C"}.get(
            current_platform, "Cmd+C"
        )

        popup = AboutPopup(hotkey_display, parent)
        popup.show()
        popup.raise_()
        popup.activateWindow()

    except Exception as e:
        logger.error(f"Error in show_about_popup: {e}")
        raise
