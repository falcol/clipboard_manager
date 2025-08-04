# clipboard_manager/src/ui/popup_window.py
"""
Enhanced popup window with modern UI inspired by GNOME Clipboard Indicator
"""
import base64
import logging
from typing import Dict

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QColor, QCursor, QFont, QPixmap
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
    """Enhanced search bar widget with modern design and system fonts"""

    search_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(50)  # Increased height
        self.setStyleSheet(Styles.get_search_bar_style())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Enhanced search icon
        search_icon = QLabel("🔍")
        search_icon.setFixedSize(24, 24)
        search_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        search_icon.setStyleSheet("color: #4facfe; font-size: 16px;")
        layout.addWidget(search_icon)

        # Enhanced search input with system font
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clipboard history...")
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                border: none;
                background: transparent;
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 0px;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        """
        )
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)

        # Enhanced clear button
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(24, 24)
        self.clear_btn.setStyleSheet(
            """
            QPushButton {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.6);
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                color: #ffffff;
            }
        """
        )
        self.clear_btn.clicked.connect(self.clear_search)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)

    def on_search_changed(self, text):
        """Handle search text changes"""
        if text.strip():  # Only show clear button if there's actual content
            self.clear_btn.show()
        else:
            self.clear_btn.hide()
        # Always emit search request, even for empty strings
        self.search_requested.emit(text)

    def clear_search(self):
        """Clear search with proper signal emission"""
        self.search_input.clear()  # This will trigger textChanged signal
        self.clear_btn.hide()
        # Explicitly emit empty search to ensure proper reset
        self.search_requested.emit("")

    def focus_search(self):
        """Focus search input"""
        self.search_input.setFocus()


class ClipboardItem(QFrame):
    """Enhanced clipboard item widget with proper text display (2 lines max)"""

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
        """Setup modern UI for clipboard item with system fonts"""
        # Increased height to accommodate 2 lines of text
        self.setFixedHeight(90)
        self.setStyleSheet(Styles.get_modern_clipboard_item_style())
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Content type icon and preview
        icon_layout = QVBoxLayout()

        # Content type icon
        content_icon = self.get_content_icon()
        icon_label = QLabel(content_icon)
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #4facfe; font-size: 16px;")
        icon_layout.addWidget(icon_label)

        # Pinned indicator
        if self.item_data.get("is_pinned"):
            pin_indicator = QLabel("📌")
            pin_indicator.setFixedSize(16, 16)
            pin_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pin_indicator.setStyleSheet("font-size: 10px;")
            icon_layout.addWidget(pin_indicator)
        else:
            icon_layout.addStretch()

        layout.addLayout(icon_layout)

        # Main content area with proper text display
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        # Preview content with proper 2-line display
        if self.item_data["content_type"] == "text":
            preview_text = self.item_data.get("preview", "")

            preview_label = QLabel(preview_text)
            # Enable word wrap for 2 lines
            preview_label.setWordWrap(True)
            preview_label.setFont(QFont("Sans Serif", 11))  # System font
            preview_label.setStyleSheet(
                """
                color: #ffffff;
                font-weight: 500;
                line-height: 1.3;
            """
            )
            # Set size policy and constraints for exactly 2 lines
            preview_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )

            # Calculate height for exactly 2 lines
            font_metrics = preview_label.fontMetrics()
            line_height = font_metrics.height()
            preview_label.setFixedHeight(line_height * 2 + 4)  # 2 lines + small padding
            preview_label.setMinimumWidth(0)  # Allow shrinking

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
                        # Larger image preview to fit the increased height
                        preview_label.setPixmap(
                            pixmap.scaled(
                                50,
                                50,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                        )
                    else:
                        preview_label.setText("🖼️ Image")
                        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                except Exception as e:
                    logger.error(f"Error loading image preview: {e}")
                    preview_label.setText("🖼️ Image")
                    preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                preview_label.setText("🖼️ Image")
                preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Set fixed height for image preview
            preview_label.setFixedHeight(50)

            # Image info
            width = self.item_data.get("width", 0)
            height = self.item_data.get("height", 0)
            info_text = f"{width}×{height} pixels"
            if self.item_data.get("file_size"):
                size_kb = self.item_data["file_size"] // 1024
                info_text += f" • {size_kb}KB"

        content_layout.addWidget(preview_label)

        # Info and timestamp with proper spacing
        info_layout = QHBoxLayout()
        info_layout.setSpacing(8)

        info_label = QLabel(info_text)
        info_label.setFont(QFont("Sans Serif", 9))  # System font
        info_label.setStyleSheet("color: #aaa;")
        info_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        info_layout.addWidget(info_label)

        # Timestamp (always visible)
        timestamp = self.item_data.get("timestamp", "")
        if timestamp:
            from datetime import datetime

            try:
                # Format timestamp nicely
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
                timestamp_label = QLabel(time_str)
                timestamp_label.setFont(QFont("Sans Serif", 9))  # System font
                timestamp_label.setStyleSheet("color: #888;")
                timestamp_label.setFixedWidth(40)  # Fixed width to prevent layout shift
                info_layout.addWidget(timestamp_label)
            except Exception:
                pass

        content_layout.addLayout(info_layout)

        # Add content with stretch factor to take available space
        layout.addLayout(content_layout, 1)

        # Action buttons (always visible space reserved, buttons shown on hover)
        self.actions_widget = QWidget()
        self.actions_widget.setFixedWidth(70)  # Fixed width for buttons
        self.actions_layout = QHBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(4)

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

        # Initially set low opacity instead of hiding
        self.pin_btn.setStyleSheet(self.pin_btn.styleSheet() + "opacity: 0.3;")
        self.delete_btn.setStyleSheet(self.delete_btn.styleSheet() + "opacity: 0.3;")

        layout.addWidget(self.actions_widget)

    def setup_animations(self):
        """Setup enhanced hover animations with smooth effects"""
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(20)
        self.shadow_effect.setColor(QColor(79, 172, 254, 80))
        self.shadow_effect.setOffset(0, 4)
        self.shadow_effect.setEnabled(False)
        self.setGraphicsEffect(self.shadow_effect)

        # Add scale animation for smooth hover effect
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

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
        """Enhanced mouse enter with smooth animations"""
        self.is_hovered = True
        self.setStyleSheet(Styles.get_modern_clipboard_item_style(hovered=True))
        self.shadow_effect.setEnabled(True)

        # Smooth scale animation
        current_geometry = self.geometry()
        scaled_geometry = current_geometry.adjusted(-2, -2, 2, 2)
        self.scale_animation.setStartValue(current_geometry)
        self.scale_animation.setEndValue(scaled_geometry)
        self.scale_animation.start()

        # Show action buttons with fade effect
        self.pin_btn.setStyleSheet(
            self.pin_btn.styleSheet().replace("opacity: 0.3;", "opacity: 1.0;")
        )
        self.delete_btn.setStyleSheet(
            self.delete_btn.styleSheet().replace("opacity: 0.3;", "opacity: 1.0;")
        )

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Enhanced mouse leave with smooth animations"""
        self.is_hovered = False
        self.setStyleSheet(Styles.get_modern_clipboard_item_style())
        self.shadow_effect.setEnabled(False)

        # Smooth scale animation back
        current_geometry = self.geometry()
        original_geometry = current_geometry.adjusted(2, 2, -2, -2)
        self.scale_animation.setStartValue(current_geometry)
        self.scale_animation.setEndValue(original_geometry)
        self.scale_animation.start()

        # Fade action buttons
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


class PopupWindow(QWidget):
    """Enhanced popup window with improved focus handling and no auto-hide timer"""

    def __init__(self, database: ClipboardDatabase, config: Config):
        super().__init__()
        self.database = database
        self.config = config
        self.clipboard_items = []
        self.all_items = []  # Store all items for search
        self.current_search = ""

        # Drag support variables
        self.dragging = False
        self.drag_start_position = None

        self.setup_window()
        self.setup_ui()
        self.load_items()

        # Removed auto-hide timer - popup will only close when focus is lost or ESC pressed

        # Improved focus tracking with faster response
        self.focus_timer = QTimer()
        self.focus_timer.setSingleShot(True)
        self.focus_timer.timeout.connect(self.check_focus)

    def setup_window(self):
        """Setup modern window properties with drag support"""
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 650)  # Increased height to accommodate larger items

        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)

    def setup_ui(self):
        """Setup modern UI with enhanced design and system fonts"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main container with enhanced glassmorphism
        self.container = QFrame()
        self.container.setStyleSheet(Styles.get_modern_popup_style())
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Enhanced header with gradient
        self.header = QFrame()
        self.header.setFixedHeight(70)  # Increased height
        self.header.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4facfe, stop:1 #00f2fe);
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
        """
        )
        self.header.setCursor(Qt.CursorShape.SizeAllCursor)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(24, 18, 24, 18)

        # Enhanced title with system fonts
        title_layout = QHBoxLayout()

        # Drag indicator with better styling
        drag_icon = QLabel("⋮⋮")
        drag_icon.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
        drag_icon.setStyleSheet(
            "color: rgba(255,255,255,0.8); background: transparent;"
        )
        drag_icon.setToolTip("Drag to move window")
        title_layout.addWidget(drag_icon)

        title_icon = QLabel("📋")
        title_icon.setFont(QFont("Sans Serif", 18))
        title_layout.addWidget(title_icon)

        title_label = QLabel("Clipboard Manager")
        title_label.setFont(QFont("Sans Serif", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        header_layout.addLayout(title_layout)

        # Enhanced header actions
        actions_layout = QHBoxLayout()

        # Modern clear button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.1);
            }
        """
        )
        self.clear_btn.clicked.connect(self.clear_history)
        actions_layout.addWidget(self.clear_btn)

        header_layout.addLayout(actions_layout)
        container_layout.addWidget(self.header)

        # Enhanced search bar
        self.search_bar = SearchBar()
        self.search_bar.search_requested.connect(self.on_search)
        container_layout.addWidget(self.search_bar)

        # Enhanced content area
        content_frame = QFrame()
        content_frame.setStyleSheet("background: rgba(255, 255, 255, 0.02);")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Enhanced scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setStyleSheet(Styles.get_modern_scrollbar_style())

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(12, 12, 12, 12)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        content_layout.addWidget(self.scroll_area)

        container_layout.addWidget(content_frame)

        # Enhanced footer
        footer = QFrame()
        footer.setFixedHeight(45)  # Increased height
        footer.setStyleSheet(
            """
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
        """
        )

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 12, 24, 12)

        footer_label = QLabel("Click to paste • Ctrl+F to search • Drag header to move")
        footer_label.setFont(QFont("Sans Serif", 10, QFont.Weight.Normal))
        footer_label.setStyleSheet(
            "color: rgba(255, 255, 255, 0.7); background: transparent;"
        )
        footer_layout.addWidget(footer_label)

        # Enhanced stats
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Sans Serif", 10, QFont.Weight.Medium))
        self.stats_label.setStyleSheet(
            "color: rgba(255, 255, 255, 0.6); background: transparent;"
        )
        footer_layout.addWidget(self.stats_label)

        container_layout.addWidget(footer)
        main_layout.addWidget(self.container)

    # Mouse event handlers for dragging
    def mousePressEvent(self, event):
        """Handle mouse press for drag start"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on header
            header_rect = self.header.geometry()
            if header_rect.contains(event.position().toPoint()):
                self.dragging = True
                self.drag_start_position = event.globalPosition().toPoint() - self.pos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        # flake8: noqa: E501
        if (
            self.dragging
            and event.buttons() == Qt.MouseButton.LeftButton
            and self.drag_start_position
        ):
            new_pos = event.globalPosition().toPoint() - self.drag_start_position

            # Keep window on screen
            screen = QApplication.primaryScreen().geometry()
            new_pos.setX(max(0, min(new_pos.x(), screen.width() - self.width())))
            new_pos.setY(max(0, min(new_pos.y(), screen.height() - self.height())))

            self.move(new_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to end drag"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.drag_start_position = None
        super().mouseReleaseEvent(event)

    def load_items(self):
        """Load clipboard items from database with proper search handling"""
        # Clear existing items
        for item in self.clipboard_items:
            item.deleteLater()
        self.clipboard_items.clear()

        # Load items from database
        self.all_items = self.database.get_items(limit=self.config.get("max_items", 50))

        # Apply search filter properly
        if self.current_search.strip():
            items_to_show = self.filter_items(
                self.all_items, self.current_search.strip()
            )
        else:
            items_to_show = self.all_items

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
            if self.current_search.strip():
                empty_label = QLabel(f"🔍 No results found for '{self.current_search}'")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setStyleSheet(
                    """
                    color: #666;
                    font-size: 14px;
                    padding: 40px;
                    background: transparent;
                """
                )
            else:
                empty_label = QLabel("📋 No clipboard history yet")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        """Filter items based on search query with improved matching"""
        if not search_query:
            return items

        filtered = []
        query_lower = search_query.lower()

        for item in items:
            # Search in multiple fields
            searchable_content = []

            # Add main content
            if item.get("content"):
                searchable_content.append(str(item["content"]).lower())

            # Add preview
            if item.get("preview"):
                searchable_content.append(str(item["preview"]).lower())

            # Add metadata search content
            if item.get("search_content"):
                searchable_content.append(str(item["search_content"]).lower())

            # Check if query matches any searchable content
            found = any(query_lower in content for content in searchable_content)

            if found:
                filtered.append(item)

        return filtered

    def on_search(self, query):
        """Handle search query with proper state management"""
        # Update current search state
        self.current_search = query.strip()

        # Reload items with new search filter
        self.load_items()

        # Reset scroll position to top
        self.scroll_area.verticalScrollBar().setValue(0)

    def update_stats(self):
        """Update statistics display with proper search context"""
        total_items = len(self.all_items)
        showing_items = len(self.clipboard_items)

        if self.current_search.strip():
            self.stats_label.setText(f"{showing_items} of {total_items} items")
        else:
            self.stats_label.setText(f"{total_items} items")

    def show_at_cursor(self):
        """Show popup at cursor position with animation and proper search reset"""
        # Reset search when showing popup
        self.current_search = ""
        self.search_bar.clear_search()

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
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.start()

        # NO AUTO-HIDE TIMER - popup stays open until manually closed or focus lost

        # Refresh items (this will show all items since search is reset)
        self.load_items()

        # Start immediate focus monitoring with faster response
        self.focus_timer.start(100)  # Much faster focus checking

    def check_focus(self):
        """Improved focus checking - hide immediately when focus is lost"""
        if not self.isVisible():
            return

        # Don't hide while dragging
        if self.dragging:
            self.focus_timer.start(100)
            return

        try:
            focused_widget = QApplication.focusWidget()
            mouse_pos = self.mapFromGlobal(QCursor.pos())

            # Check if focus is within our window or mouse is over window
            has_focus = focused_widget and self.isAncestorOf(focused_widget)
            mouse_over = self.rect().contains(mouse_pos)

            if has_focus or mouse_over:
                # Still has focus or mouse over, continue monitoring
                self.focus_timer.start(100)
            else:
                # Lost focus and mouse not over window, hide immediately
                self.hide()

        except Exception as e:
            logger.error(f"Error in focus check: {e}")
            # Continue monitoring on error
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
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif (
            event.key() == Qt.Key.Key_F
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.search_bar.focus_search()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event):
        """Handle hide event with proper cleanup"""
        # Stop focus monitoring when hiding
        self.focus_timer.stop()
        self.dragging = False
        self.drag_start_position = None
        super().hideEvent(event)
