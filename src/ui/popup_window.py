# clipboard_manager/src/ui/popup_window.py
"""
Main popup window for clipboard history
"""
import base64
import logging
from typing import Dict

from PySide6.QtCore import Qt, QTimer
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QCursor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.database import ClipboardDatabase
from ui.styles import Styles
from utils.config import Config
from utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class ClipboardItem(QFrame):
    """Individual clipboard item widget"""

    item_selected = pyqtSignal(dict)
    pin_toggled = pyqtSignal(int, bool)
    delete_requested = pyqtSignal(int)

    def __init__(self, item_data: Dict, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.setup_ui()
        self.setFixedHeight(80)
        self.setStyleSheet(Styles.get_clipboard_item_style())

    def setup_ui(self):
        """Setup the UI for clipboard item"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Content area
        content_layout = QVBoxLayout()

        # Preview
        if self.item_data["content_type"] == "text":
            preview_text = self.item_data.get("preview", "")[:100]
            preview_label = QLabel(preview_text)
            preview_label.setWordWrap(True)
            preview_label.setFont(QFont("Arial", 9))
        else:  # image
            preview_label = QLabel()
            if self.item_data.get("preview"):
                try:
                    preview_data = self.item_data["preview"]
                    thumbnail_data = base64.b64decode(preview_data)
                    pixmap = ImageUtils.bytes_to_pixmap(thumbnail_data)
                    preview_label.setPixmap(
                        pixmap.scaled(
                            48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                    )
                except Exception as e:
                    preview_label.setText("Image")
                    logger.error(f"Error loading image preview: {e}")
            else:
                preview_label.setText("Image")

        content_layout.addWidget(preview_label)

        # Timestamp
        timestamp_label = QLabel(self.item_data.get("timestamp", ""))
        timestamp_label.setFont(QFont("Arial", 7))
        timestamp_label.setStyleSheet("color: #666;")
        content_layout.addWidget(timestamp_label)

        layout.addLayout(content_layout, 1)

        # Buttons
        button_layout = QVBoxLayout()

        # Pin button
        pin_btn = QPushButton("📌" if self.item_data.get("is_pinned") else "📍")
        pin_btn.setFixedSize(24, 24)
        pin_btn.setToolTip("Pin/Unpin")
        pin_btn.clicked.connect(self.toggle_pin)
        button_layout.addWidget(pin_btn)

        # Delete button
        delete_btn = QPushButton("🗑")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setToolTip("Delete")
        delete_btn.clicked.connect(self.delete_item)
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        # Make clickable
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)

    def mousePressEvent(self, event):
        """Handle mouse click to select item"""
        if event.button() == Qt.LeftButton:
            self.item_selected.emit(self.item_data)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter (hover)"""
        self.setStyleSheet(Styles.get_clipboard_item_style(hovered=True))
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave"""
        self.setStyleSheet(Styles.get_clipboard_item_style())
        super().leaveEvent(event)

    def toggle_pin(self):
        """Toggle pin status"""
        new_pin_status = not self.item_data.get("is_pinned", False)
        self.pin_toggled.emit(self.item_data["id"], new_pin_status)

    def delete_item(self):
        """Delete this item"""
        self.delete_requested.emit(self.item_data["id"])


class PopupWindow(QWidget):
    """Main popup window for clipboard history"""

    def __init__(self, database: ClipboardDatabase, config: Config):
        super().__init__()
        self.database = database
        self.config = config
        self.clipboard_items = []

        self.setup_ui()
        self.setup_window()
        self.load_items()

        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

    def setup_window(self):
        """Setup window properties"""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 500)
        self.setStyleSheet(Styles.get_popup_window_style())

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("📋 Clipboard History")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title_label)

        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.setFixedSize(80, 25)
        clear_btn.clicked.connect(self.clear_history)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Scroll area for items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        # Footer
        footer_label = QLabel("Click to paste • Super+V to show")
        footer_label.setFont(QFont("Arial", 8))
        footer_label.setStyleSheet("color: #888;")
        footer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer_label)

    def load_items(self):
        """Load clipboard items from database"""
        # Clear existing items
        for item in self.clipboard_items:
            item.deleteLater()
        self.clipboard_items.clear()

        # Load items from database
        items = self.database.get_items(limit=self.config.get("max_items", 25))

        for item_data in items:
            clipboard_item = ClipboardItem(item_data)
            clipboard_item.item_selected.connect(self.on_item_selected)
            clipboard_item.pin_toggled.connect(self.on_pin_toggled)
            clipboard_item.delete_requested.connect(self.on_delete_requested)

            self.clipboard_items.append(clipboard_item)
            # Insert at the beginning (before stretch)
            self.scroll_layout.insertWidget(
                self.scroll_layout.count() - 1, clipboard_item
            )

        if not items:
            no_items_label = QLabel("No clipboard history yet")
            no_items_label.setAlignment(Qt.AlignCenter)
            no_items_label.setStyleSheet("color: #888; font-style: italic;")
            self.scroll_layout.insertWidget(0, no_items_label)

    def show_at_cursor(self):
        """Show popup at cursor position"""
        # Get cursor position
        cursor_pos = QCursor.pos()

        # Adjust position to keep window on screen
        screen = QApplication.primaryScreen().geometry()

        x = cursor_pos.x() - self.width() // 2
        y = cursor_pos.y() - self.height() // 2

        # Ensure window stays on screen
        x = max(10, min(x, screen.width() - self.width() - 10))
        y = max(10, min(y, screen.height() - self.height() - 10))

        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

        # Auto-hide after 10 seconds
        self.hide_timer.start(10000)

        # Refresh items
        self.load_items()

    def on_item_selected(self, item_data: Dict):
        """Handle item selection - paste to clipboard"""
        try:
            clipboard = QApplication.clipboard()

            if item_data["content_type"] == "text":
                clipboard.setText(item_data["content"])
            elif item_data["content_type"] == "image":
                image_data = base64.b64decode(item_data["content"])
                pixmap = ImageUtils.bytes_to_pixmap(image_data)
                clipboard.setPixmap(pixmap)

            self.hide()
            logger.info(f"Pasted item {item_data['id']} to clipboard")

        except Exception as e:
            logger.error(f"Error pasting item: {e}")

    def on_pin_toggled(self, item_id: int, pinned: bool):
        """Handle pin toggle"""
        if self.database.pin_item(item_id, pinned):
            self.load_items()  # Refresh display
            logger.info(f"Item {item_id} {'pinned' if pinned else 'unpinned'}")

    def on_delete_requested(self, item_id: int):
        """Handle delete request"""
        if self.database.delete_item(item_id):
            self.load_items()  # Refresh display
            logger.info(f"Item {item_id} deleted")

    def clear_history(self):
        """Clear clipboard history"""
        self.database.clear_history(keep_pinned=True)
        self.load_items()
        logger.info("Clipboard history cleared")

    def update_config(self):
        """Update configuration"""
        self.load_items()  # Refresh with new settings

    def focusOutEvent(self, event):
        """Hide window when focus is lost"""
        self.hide()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.hide()
        super().keyPressEvent(event)
