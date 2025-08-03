# clipboard_manager/src/ui/popup_window.py
"""
Enhanced popup window with modern UI inspired by GNOME Clipboard Indicator
"""
import base64
import logging
from typing import Dict

from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QRect, Qt, QTimer
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QColor, QCursor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.database import EnhancedClipboardDatabase as ClipboardDatabase
from ui.styles import Styles
from utils.config import Config
from utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class SearchBar(QFrame):
    """Modern search bar widget"""

    search_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(40)
        self.setStyleSheet(Styles.get_search_bar_style())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setFixedSize(20, 20)
        search_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(search_icon)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clipboard history...")
        self.search_input.setStyleSheet(
            "border: none; background: transparent; color: #ffffff;"
        )
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)

        # Clear button
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(20, 20)
        self.clear_btn.setStyleSheet(
            """
            QPushButton {
                border: none;
                background: transparent;
                color: #888;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: #555;
                color: #fff;
            }
        """
        )
        self.clear_btn.clicked.connect(self.clear_search)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)

    def on_search_changed(self, text):
        if text:
            self.clear_btn.show()
        else:
            self.clear_btn.hide()
        self.search_requested.emit(text)

    def clear_search(self):
        self.search_input.clear()
        self.clear_btn.hide()

    def focus_search(self):
        self.search_input.setFocus()


class ClipboardItem(QFrame):
    """Enhanced clipboard item widget with modern design"""

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
        """Setup modern UI for clipboard item"""
        self.setFixedHeight(70)
        self.setStyleSheet(Styles.get_modern_clipboard_item_style())
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Content type icon and preview
        icon_layout = QVBoxLayout()

        # Content type icon
        content_icon = self.get_content_icon()
        icon_label = QLabel(content_icon)
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("color: #0078d4; font-size: 16px;")
        icon_layout.addWidget(icon_label)

        # Pinned indicator
        if self.item_data.get("is_pinned"):
            pin_indicator = QLabel("📌")
            pin_indicator.setFixedSize(16, 16)
            pin_indicator.setAlignment(Qt.AlignCenter)
            pin_indicator.setStyleSheet("font-size: 10px;")
            icon_layout.addWidget(pin_indicator)
        else:
            icon_layout.addStretch()

        layout.addLayout(icon_layout)

        # Main content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        # Preview content
        if self.item_data["content_type"] == "text":
            preview_text = self.item_data.get("preview", "")
            if len(preview_text) > 80:
                preview_text = preview_text[:77] + "..."

            preview_label = QLabel(preview_text)
            preview_label.setWordWrap(False)
            preview_label.setFont(QFont("Segoe UI", 10))
            preview_label.setStyleSheet("color: #ffffff; font-weight: 500;")

            # Content info
            char_count = self.item_data.get("char_count", len(preview_text))
            info_text = f"{char_count} characters"
            if self.item_data.get("word_count"):
                info_text += f" • {self.item_data['word_count']} words"

        else:  # image
            preview_label = QLabel()
            if self.item_data.get("preview"):
                try:
                    if self.item_data["preview"].startswith("data:"):
                        # Base64 data
                        preview_data = self.item_data["preview"].split(",")[1]
                        thumbnail_data = base64.b64decode(preview_data)
                    else:
                        # File path
                        with open(self.item_data["preview"], "rb") as f:
                            thumbnail_data = f.read()

                    pixmap = ImageUtils.bytes_to_pixmap(thumbnail_data)
                    if not pixmap.isNull():
                        preview_label.setPixmap(
                            pixmap.scaled(
                                40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation
                            )
                        )
                    else:
                        preview_label.setText("🖼️ Image")
                        preview_label.setAlignment(Qt.AlignCenter)
                except Exception as e:
                    logger.error(f"Error loading image preview: {e}")
                    preview_label.setText("🖼️ Image")
                    preview_label.setAlignment(Qt.AlignCenter)
            else:
                preview_label.setText("🖼️ Image")
                preview_label.setAlignment(Qt.AlignCenter)

            # Image info
            width = self.item_data.get("width", 0)
            height = self.item_data.get("height", 0)
            info_text = f"{width}×{height} pixels"
            if self.item_data.get("file_size"):
                size_kb = self.item_data["file_size"] // 1024
                info_text += f" • {size_kb}KB"

        content_layout.addWidget(preview_label)

        # Info and timestamp
        info_layout = QHBoxLayout()
        info_layout.setSpacing(8)

        info_label = QLabel(info_text)
        info_label.setFont(QFont("Segoe UI", 8))
        info_label.setStyleSheet("color: #aaa;")
        info_layout.addWidget(info_label)

        # Timestamp
        timestamp = self.item_data.get("timestamp", "")
        if timestamp:
            from datetime import datetime

            try:
                # Format timestamp nicely
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
                timestamp_label = QLabel(time_str)
                timestamp_label.setFont(QFont("Segoe UI", 8))
                timestamp_label.setStyleSheet("color: #888;")
                info_layout.addWidget(timestamp_label)
            except:
                pass

        info_layout.addStretch()
        content_layout.addLayout(info_layout)

        layout.addLayout(content_layout, 1)

        # Action buttons (hidden by default, shown on hover)
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(8)

        # Pin button
        self.pin_btn = QPushButton()
        self.pin_btn.setFixedSize(28, 28)
        self.pin_btn.setToolTip("Pin/Unpin item")
        self.update_pin_button()
        self.pin_btn.clicked.connect(self.toggle_pin)
        self.actions_layout.addWidget(self.pin_btn)

        # Delete button
        self.delete_btn = QPushButton("🗑")
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setToolTip("Delete item")
        self.delete_btn.setStyleSheet(Styles.get_action_button_style("delete"))
        self.delete_btn.clicked.connect(self.delete_item)
        self.actions_layout.addWidget(self.delete_btn)

        # Initially hide action buttons
        self.pin_btn.hide()
        self.delete_btn.hide()

        layout.addLayout(self.actions_layout)

    def setup_animations(self):
        """Setup hover animations"""
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(10)
        self.shadow_effect.setColor(QColor(0, 120, 212, 100))
        self.shadow_effect.setOffset(0, 2)
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
        if event.button() == Qt.LeftButton:
            self.item_selected.emit(self.item_data)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter (hover)"""
        self.is_hovered = True
        self.setStyleSheet(Styles.get_modern_clipboard_item_style(hovered=True))
        self.shadow_effect.setEnabled(True)

        # Show action buttons
        self.pin_btn.show()
        self.delete_btn.show()

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave"""
        self.is_hovered = False
        self.setStyleSheet(Styles.get_modern_clipboard_item_style())
        self.shadow_effect.setEnabled(False)

        # Hide action buttons
        self.pin_btn.hide()
        self.delete_btn.hide()

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


class PopupWindow(QWidget):
    """Enhanced popup window with modern design"""

    def __init__(self, database: ClipboardDatabase, config: Config):
        super().__init__()
        self.database = database
        self.config = config
        self.clipboard_items = []
        self.all_items = []  # Store all items for search
        self.current_search = ""

        self.setup_window()
        self.setup_ui()
        self.load_items()

        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

        # Focus tracking
        self.focus_timer = QTimer()
        self.focus_timer.setSingleShot(True)
        self.focus_timer.timeout.connect(self.check_focus)

    def setup_window(self):
        """Setup modern window properties"""
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(450, 600)

        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)

    def setup_ui(self):
        """Setup modern UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main container with rounded corners
        self.container = QFrame()
        self.container.setStyleSheet(Styles.get_modern_popup_style())
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0078d4, stop:1 #005a9e);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """
        )

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 15, 20, 15)

        # Title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel("📋")
        title_icon.setFont(QFont("Segoe UI", 16))
        title_layout.addWidget(title_icon)

        title_label = QLabel("Clipboard Manager")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        header_layout.addLayout(title_layout)

        # Header actions
        actions_layout = QHBoxLayout()

        # Clear all button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.1);
            }
        """
        )
        self.clear_btn.clicked.connect(self.clear_history)
        actions_layout.addWidget(self.clear_btn)

        header_layout.addLayout(actions_layout)
        container_layout.addWidget(header)

        # Search bar
        self.search_bar = SearchBar()
        self.search_bar.search_requested.connect(self.on_search)
        container_layout.addWidget(self.search_bar)

        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet("background: #2b2b2b;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(Styles.get_modern_scrollbar_style())

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(8, 8, 8, 8)
        self.scroll_layout.setSpacing(4)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        content_layout.addWidget(self.scroll_area)

        container_layout.addWidget(content_frame)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(35)
        footer.setStyleSheet(
            """
            QFrame {
                background: #1e1e1e;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top: 1px solid #404040;
            }
        """
        )

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 8, 20, 8)

        footer_label = QLabel("Click to paste • Ctrl+F to search • Esc to close")
        footer_label.setFont(QFont("Segoe UI", 9))
        footer_label.setStyleSheet("color: #aaa; background: transparent;")
        footer_layout.addWidget(footer_label)

        # Stats
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Segoe UI", 9))
        self.stats_label.setStyleSheet("color: #888; background: transparent;")
        footer_layout.addWidget(self.stats_label)

        container_layout.addWidget(footer)
        main_layout.addWidget(self.container)

    def load_items(self):
        """Load clipboard items from database"""
        # Clear existing items
        for item in self.clipboard_items:
            item.deleteLater()
        self.clipboard_items.clear()

        # Load items from database
        self.all_items = self.database.get_items(limit=self.config.get("max_items", 50))
        items_to_show = self.filter_items(self.all_items, self.current_search)

        if items_to_show:
            for item_data in items_to_show:
                clipboard_item = ClipboardItem(item_data)
                clipboard_item.item_selected.connect(self.on_item_selected)
                clipboard_item.pin_toggled.connect(self.on_pin_toggled)
                clipboard_item.delete_requested.connect(self.on_delete_requested)

                self.clipboard_items.append(clipboard_item)
                # Insert at the beginning (before stretch)
                self.scroll_layout.insertWidget(
                    self.scroll_layout.count() - 1, clipboard_item
                )
        else:
            # Show empty state
            empty_label = QLabel(
                "🔍 No items found"
                if self.current_search
                else "📋 No clipboard history yet"
            )
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet(
                """
                color: #666;
                font-size: 14px;
                padding: 40px;
                background: transparent;
            """
            )
            self.scroll_layout.insertWidget(0, empty_label)

        # Update stats
        self.update_stats()

    def filter_items(self, items, search_query):
        """Filter items based on search query"""
        if not search_query:
            return items

        filtered = []
        query_lower = search_query.lower()

        for item in items:
            # Search in content
            content = item.get("content", "")
            preview = item.get("preview", "")

            if query_lower in content.lower() or query_lower in preview.lower():
                filtered.append(item)

        return filtered

    def on_search(self, query):
        """Handle search query"""
        self.current_search = query
        self.load_items()

    def update_stats(self):
        """Update statistics display"""
        total_items = len(self.all_items)
        showing_items = len(self.clipboard_items)

        if self.current_search:
            self.stats_label.setText(f"{showing_items} of {total_items} items")
        else:
            self.stats_label.setText(f"{total_items} items")

    def show_at_cursor(self):
        """Show popup at cursor position with animation"""
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

        # Show with fade in effect
        self.setWindowOpacity(0)
        self.show()
        self.raise_()
        self.activateWindow()

        # Focus search bar
        self.search_bar.focus_search()

        # Fade in animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()

        # Auto-hide after 15 seconds
        self.hide_timer.start(15000)

        # Refresh items
        self.load_items()

        # Start focus monitoring
        self.focus_timer.start(100)

    def check_focus(self):
        """Check if window still has focus"""
        if self.isVisible():
            focused_widget = QApplication.focusWidget()
            if focused_widget is None or not self.isAncestorOf(focused_widget):
                # Check if mouse is over the window
                mouse_pos = self.mapFromGlobal(QCursor.pos())
                if not self.rect().contains(mouse_pos):
                    self.hide()
                    return

            # Continue monitoring
            self.focus_timer.start(100)

    def on_item_selected(self, item_data: Dict):
        """Handle item selection - paste to clipboard"""
        try:
            clipboard = QApplication.clipboard()

            if item_data["content_type"] == "text":
                clipboard.setText(item_data["content"])
            elif item_data["content_type"] == "image":
                if item_data.get("file_path"):
                    # Load from file
                    pixmap = QPixmap(item_data["file_path"])
                    if not pixmap.isNull():
                        clipboard.setPixmap(pixmap)
                else:
                    # Fallback to base64 data
                    image_data = base64.b64decode(item_data["content"])
                    pixmap = ImageUtils.bytes_to_pixmap(image_data)
                    clipboard.setPixmap(pixmap)

            # Update access count
            # TODO: Implement access count update in database

            self.hide()
            logger.info(f"Pasted item {item_data['id']} to clipboard")

        except Exception as e:
            logger.error(f"Error pasting item: {e}")

    def on_pin_toggled(self, item_id: int, pinned: bool):
        """Handle pin toggle"""
        if self.database.pin_item(item_id, pinned):
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
        self.load_items()

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            self.search_bar.focus_search()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event):
        """Handle hide event"""
        self.hide_timer.stop()
        self.focus_timer.stop()
        super().hideEvent(event)
