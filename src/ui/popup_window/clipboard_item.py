# clipboard_manager/src/ui/popup_window/clipboard_item.py
"""
Windows 10 Dark Mode Clipboard Manager Popup Window
"""
import base64
import logging
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.styles import Styles
from utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class ClipboardItem(QFrame):
    """Windows 10 dark mode clipboard item widget"""

    item_selected = pyqtSignal(dict)
    pin_toggled = pyqtSignal(int, bool)
    delete_requested = pyqtSignal(int)

    def __init__(self, item_data: Dict, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.is_hovered = False
        self.setup_ui()
        self.setup_animations()

    def setup_ui(self):
        """Setup Windows 10 dark mode UI for clipboard item"""
        # Increased height to accommodate 3 lines of text
        self.setFixedHeight(80)
        self.setStyleSheet(Styles.get_modern_clipboard_item_style())
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)  # Reduced spacing

        # Content type icon
        content_icon = self.get_content_icon()
        icon_label = QLabel(content_icon)
        icon_label.setFixedSize(20, 20)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #0078d4; font-size: 14px;")
        layout.addWidget(icon_label)

        # Main content area with fixed width
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        # Preview content
        if self.item_data["content_type"] == "text":
            preview_text = self.item_data.get("preview", "")
            preview_label = QLabel(preview_text)
            preview_label.setWordWrap(True)
            preview_label.setFont(QFont("Segoe UI", 10))
            preview_label.setStyleSheet(
                "color: #ffffff; font-weight: 500; line-height: 1.2;"
            )
            preview_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )

            # Three line height for better text display
            font_metrics = preview_label.fontMetrics()
            line_height = font_metrics.height()
            preview_label.setFixedHeight(line_height * 3 + 8)

            # Set maximum width for text to prevent layout expansion
            preview_label.setMaximumWidth(280)  # Limit text width
            preview_label.setMinimumWidth(100)  # Minimum width

        else:  # image
            preview_label = QLabel()
            if self.item_data.get("preview"):
                try:
                    if self.item_data["preview"].startswith("data:"):
                        preview_data = self.item_data["preview"].split(",")[1]
                        thumbnail_data = base64.b64decode(preview_data)
                    else:
                        with open(self.item_data["preview"], "rb") as f:
                            thumbnail_data = f.read()

                    pixmap = ImageUtils.bytes_to_pixmap(thumbnail_data)
                    if not pixmap.isNull():
                        # Reduced image size to fit better
                        preview_label.setPixmap(
                            pixmap.scaled(
                                48,  # Reduced from 128 to 48
                                48,  # Reduced from 128 to 48
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                        )
                    else:
                        preview_label.setText("🖼️")
                        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                except Exception as e:
                    logger.error(f"Error loading image preview: {e}")
                    preview_label.setText("🖼️")
                    preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                preview_label.setText("🖼️")
                preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            preview_label.setFixedHeight(48)  # Reduced from 32 to 48
            preview_label.setFixedWidth(48)  # Added fixed width

        content_layout.addWidget(preview_label)

        # Add content with stretch factor but limited width
        layout.addLayout(content_layout, 1)

        # Action buttons - ensure they're always visible
        self.actions_widget = QWidget()
        self.actions_widget.setFixedWidth(
            32
        )  # Reduced width since buttons are now vertical
        self.actions_layout = QVBoxLayout(
            self.actions_widget
        )  # Changed from QHBoxLayout to QVBoxLayout
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(4)
        self.actions_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )  # Center align the buttons

        # Pin button
        self.pin_btn = QPushButton()
        self.pin_btn.setFixedSize(24, 24)
        self.pin_btn.setToolTip("Pin/Unpin item")
        self.update_pin_button()
        self.pin_btn.clicked.connect(self.toggle_pin)
        self.actions_layout.addWidget(self.pin_btn)

        # Delete button
        self.delete_btn = QPushButton("🗑")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setToolTip("Delete item")
        self.delete_btn.setStyleSheet(Styles.get_action_button_style("delete"))
        self.delete_btn.clicked.connect(self.delete_item)
        self.actions_layout.addWidget(self.delete_btn)

        # Initially set low opacity
        self.pin_btn.setStyleSheet(self.pin_btn.styleSheet() + "opacity: 0.3;")
        self.delete_btn.setStyleSheet(self.delete_btn.styleSheet() + "opacity: 0.3;")

        layout.addWidget(self.actions_widget)

    def setup_animations(self):
        """Setup hover animations"""
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(8)
        self.shadow_effect.setColor(QColor(0, 120, 212, 80))
        self.shadow_effect.setOffset(0, 1)
        self.shadow_effect.setEnabled(False)
        self.setGraphicsEffect(self.shadow_effect)

    def get_content_icon(self):
        """Get icon based on content type"""
        content_type = self.item_data.get("content_type", "text")
        if content_type == "image":
            return "🖼️"
        elif content_type == "url":
            return "🔗"
        elif content_type == "code":
            return "💻"
        elif content_type == "json":
            return "📄"
        else:
            return "📝"

    def update_pin_button(self):
        """Update pin button appearance"""
        if self.item_data.get("is_pinned"):
            self.pin_btn.setText("📌")
            self.pin_btn.setStyleSheet(Styles.get_action_button_style("pin_active"))
        else:
            self.pin_btn.setText("📍")
            self.pin_btn.setStyleSheet(Styles.get_action_button_style("pin"))

    def mousePressEvent(self, event):
        """Handle mouse click to select item"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.item_selected.emit(self.item_data)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter (hover) - show buttons clearly"""
        self.is_hovered = True
        self.setStyleSheet(Styles.get_modern_clipboard_item_style(hovered=True))
        self.shadow_effect.setEnabled(True)

        # Show action buttons clearly
        self.pin_btn.setStyleSheet(
            self.pin_btn.styleSheet().replace("opacity: 0.3;", "opacity: 1.0;")
        )
        self.delete_btn.setStyleSheet(
            self.delete_btn.styleSheet().replace("opacity: 0.3;", "opacity: 1.0;")
        )

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave - fade buttons"""
        self.is_hovered = False
        self.setStyleSheet(Styles.get_modern_clipboard_item_style())
        self.shadow_effect.setEnabled(False)

        # Fade action buttonsc
        current_pin_style = self.pin_btn.styleSheet()
        current_delete_style = self.delete_btn.styleSheet()

        if "opacity: 1.0;" in current_pin_style:
            self.pin_btn.setStyleSheet(
                current_pin_style.replace("opacity: 1.0;", "opacity: 0.3;")
            )
        else:
            self.pin_btn.setStyleSheet(current_pin_style + "opacity: 0.3;")

        if "opacity: 1.0;" in current_delete_style:
            self.delete_btn.setStyleSheet(
                current_delete_style.replace("opacity: 1.0;", "opacity: 0.3;")
            )
        else:
            self.delete_btn.setStyleSheet(current_delete_style + "opacity: 0.3;")

        super().leaveEvent(event)

    def toggle_pin(self):
        """Toggle pin status"""
        new_pin_status = not self.item_data.get("is_pinned", False)
        self.item_data["is_pinned"] = new_pin_status
        self.update_pin_button()
        self.pin_toggled.emit(self.item_data["id"], new_pin_status)

    def delete_item(self):
        """Delete this item"""
        self.delete_requested.emit(self.item_data["id"])
