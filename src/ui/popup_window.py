# clipboard_manager/src/ui/popup_window.py
"""
Windows 10 Dark Mode Clipboard Manager Popup Window
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
    """Windows 10 dark mode search bar widget"""

    search_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(36)
        self.setStyleSheet(Styles.get_search_bar_style())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)

        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setFixedSize(16, 16)
        search_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(search_icon)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clipboard history...")
        self.search_input.setStyleSheet(
            "border: none; background: transparent; color: #ffffff; font-size: 11px;"
        )
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)

        # Clear button
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(16, 16)
        self.clear_btn.setStyleSheet(
            """
            QPushButton {
                border: none;
                background: transparent;
                color: #888888;
                border-radius: 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background: #3d3d3d;
                color: #ffffff;
            }
        """
        )
        self.clear_btn.clicked.connect(self.clear_search)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)

    def on_search_changed(self, text):
        """Handle search text changes"""
        if text.strip():
            self.clear_btn.show()
        else:
            self.clear_btn.hide()
        self.search_requested.emit(text)

    def clear_search(self):
        """Clear search with proper signal emission"""
        self.search_input.clear()
        self.clear_btn.hide()
        self.search_requested.emit("")

    def focus_search(self):
        """Focus search input"""
        self.search_input.setFocus()


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


class PopupWindow(QWidget):
    """Windows 10 dark mode popup window"""

    def __init__(self, database: ClipboardDatabase, config: Config, system_tray=None):
        super().__init__()
        self.database = database
        self.config = config
        self.system_tray = system_tray
        self.clipboard_items = []
        self.all_items = []
        self.current_search = ""
        self.last_content_type = "text"  # Track last content type

        # Drag support variables
        self.dragging = False
        self.drag_start_position = None

        self.setup_window()
        self.setup_ui()
        self.load_items()

        # Focus tracking
        self.focus_timer = QTimer()
        self.focus_timer.setSingleShot(True)
        self.focus_timer.timeout.connect(self.check_focus)

    def setup_window(self):
        """Setup Windows 10 dark mode window properties"""
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(380, 650)  # Fixed width to prevent expansion

        # Subtle drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def setup_ui(self):
        """Setup Windows 10 dark mode UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main container
        self.container = QFrame()
        self.container.setStyleSheet(Styles.get_modern_popup_style())
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        self.header = QFrame()
        self.header.setFixedHeight(48)
        self.header.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d2d2d, stop:1 #1f1f1f);
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom: 1px solid #3d3d3d;
            }
        """
        )
        self.header.setCursor(Qt.CursorShape.SizeAllCursor)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        # Title
        title_layout = QHBoxLayout()

        # Drag indicator
        drag_icon = QLabel("⋮⋮")
        drag_icon.setFont(QFont("Segoe UI", 10))
        drag_icon.setStyleSheet("color: #cccccc; background: transparent;")
        drag_icon.setToolTip("Drag to move window")
        title_layout.addWidget(drag_icon)

        title_icon = QLabel("📋")
        title_icon.setFont(QFont("Segoe UI", 14))
        title_layout.addWidget(title_icon)

        title_label = QLabel("Clipboard Manager")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff; background: transparent;")
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
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 4px;
                padding: 4px 8px;
                color: #cccccc;
                font-weight: 500;
                font-size: 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                color: #ffffff;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """
        )
        self.clear_btn.clicked.connect(self.clear_history)
        actions_layout.addWidget(self.clear_btn)

        header_layout.addLayout(actions_layout)
        container_layout.addWidget(self.header)

        # Search bar
        self.search_bar = SearchBar()
        self.search_bar.search_requested.connect(self.on_search)
        container_layout.addWidget(self.search_bar)

        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet("background: #1f1f1f;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
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
        self.scroll_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_layout.setSpacing(2)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        content_layout.addWidget(self.scroll_area)

        container_layout.addWidget(content_frame)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(28)
        footer.setStyleSheet(
            """
            QFrame {
                background: #2d2d2d;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                border-top: 1px solid #3d3d3d;
            }
        """
        )

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 6, 16, 6)

        footer_label = QLabel("Click to paste • Ctrl+F to search • Drag header to move")
        footer_label.setFont(QFont("Segoe UI", 8))
        footer_label.setStyleSheet("color: #888888; background: transparent;")
        footer_layout.addWidget(footer_label)

        # Stats
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Segoe UI", 8))
        self.stats_label.setStyleSheet("color: #666666; background: transparent;")
        footer_layout.addWidget(self.stats_label)

        container_layout.addWidget(footer)
        main_layout.addWidget(self.container)

    # Mouse event handlers for dragging
    def mousePressEvent(self, event):
        """Handle mouse press for drag start"""
        if event.button() == Qt.MouseButton.LeftButton:
            header_rect = self.header.geometry()
            if header_rect.contains(event.position().toPoint()):
                self.dragging = True
                self.drag_start_position = event.globalPosition().toPoint() - self.pos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
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
        """Load clipboard items from database"""
        # Clear ALL existing widgets in scroll layout (including "No results" labels)
        while self.scroll_layout.count() > 1:  # Keep the stretch widget at the end
            child = self.scroll_layout.itemAt(0).widget()
            if child:
                child.deleteLater()
            self.scroll_layout.removeItem(self.scroll_layout.itemAt(0))

        # Clear clipboard items list
        self.clipboard_items.clear()

        # Load items from database
        self.all_items = self.database.get_items(limit=self.config.get("max_items", 50))

        # Apply search filter
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
                self.scroll_layout.insertWidget(
                    self.scroll_layout.count() - 1, clipboard_item
                )
        else:
            # Show empty state (only one message)
            if self.current_search.strip():
                empty_label = QLabel(f"🔍 No results found for '{self.current_search}'")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setStyleSheet(
                    """
                    color: #666666;
                    font-size: 12px;
                    padding: 30px;
                    background: transparent;
                """
                )
            else:
                empty_label = QLabel("📋 No clipboard history yet")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setStyleSheet(
                    """
                    color: #666666;
                    font-size: 12px;
                    padding: 30px;
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
            searchable_content = []

            if item.get("content"):
                searchable_content.append(str(item["content"]).lower())

            if item.get("preview"):
                searchable_content.append(str(item["preview"]).lower())

            if item.get("search_content"):
                searchable_content.append(str(item["search_content"]).lower())

            found = any(query_lower in content for content in searchable_content)

            if found:
                filtered.append(item)

        return filtered

    def on_search(self, query):
        """Handle search query"""
        self.current_search = query.strip()
        self.load_items()
        self.scroll_area.verticalScrollBar().setValue(0)

    def update_stats(self):
        """Update statistics display"""
        total_items = len(self.all_items)
        showing_items = len(self.clipboard_items)

        if self.current_search.strip():
            self.stats_label.setText(f"{showing_items} of {total_items} items")
        else:
            self.stats_label.setText(f"{total_items} items")

    def show_at_cursor(self):
        """Show popup at cursor position"""
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
        self.fade_animation.setDuration(150)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.start()

        # Refresh items
        self.load_items()

        # Start focus monitoring
        self.focus_timer.start(100)

    def check_focus(self):
        """Improved focus checking"""
        if not self.isVisible():
            return

        if self.dragging:
            self.focus_timer.start(100)
            return

        try:
            focused_widget = QApplication.focusWidget()
            mouse_pos = self.mapFromGlobal(QCursor.pos())

            has_focus = focused_widget and self.isAncestorOf(focused_widget)
            mouse_over = self.rect().contains(mouse_pos)

            if has_focus or mouse_over:
                self.focus_timer.start(100)
            else:
                self.hide()

        except Exception as e:
            logger.error(f"Error in focus check: {e}")
            self.focus_timer.start(100)

    def on_item_selected(self, item_data: Dict):
        """Handle item selection - paste directly like Windows clipboard manager"""
        try:
            # Store content type for notification
            self.last_content_type = item_data.get("content_type", "text")

            # Hide popup first
            self.hide()

            # Small delay to ensure popup is hidden
            QTimer.singleShot(100, lambda: self._paste_like_windows(item_data))

        except Exception as e:
            logger.error(f"Error handling item selection: {e}")
            self.hide()

    def _simulate_ctrl_v(self):
        """Simulate Ctrl+V keyboard shortcut with platform detection"""
        try:
            import platform

            current_platform = platform.system().lower()

            if current_platform == "windows":
                self._simulate_ctrl_v_windows()
            elif current_platform == "linux":
                self._simulate_ctrl_v_linux()
            elif current_platform == "darwin":  # macOS
                self._simulate_ctrl_v_macos()
            else:
                # Fallback for unknown platforms
                self._simulate_ctrl_v_fallback()

        except Exception as e:
            logger.error(f"Error simulating Ctrl+V: {e}")
            raise

    def _simulate_ctrl_v_windows(self):
        """Windows Ctrl+V simulation using keyboard library"""
        try:
            import keyboard

            keyboard.press_and_release("ctrl+v")
            logger.info("Simulated Ctrl+V on Windows successfully")
        except ImportError:
            logger.warning("keyboard library not available on Windows, using fallback")
            self._simulate_ctrl_v_fallback()
        except Exception as e:
            logger.error(f"Error simulating Ctrl+V on Windows: {e}")
            self._simulate_ctrl_v_fallback()

    def _simulate_ctrl_v_linux(self):
        """Linux Ctrl+V simulation using xdotool or pynput"""
        try:
            # Try xdotool first (most reliable on Linux)
            import subprocess

            result = subprocess.run(
                ["xdotool", "key", "ctrl+v"], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                logger.info("Simulated Ctrl+V on Linux using xdotool successfully")
                return
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        try:
            # Fallback to pynput
            from pynput import keyboard

            controller = keyboard.Controller()
            controller.press(keyboard.Key.ctrl)
            controller.press("v")
            controller.release("v")
            controller.release(keyboard.Key.ctrl)
            logger.info("Simulated Ctrl+V on Linux using pynput successfully")
        except ImportError:
            logger.warning(
                "Neither xdotool nor pynput available on Linux, using fallback"
            )
            self._simulate_ctrl_v_fallback()
        except Exception as e:
            logger.error(f"Error simulating Ctrl+V on Linux: {e}")
            self._simulate_ctrl_v_fallback()

    def _simulate_ctrl_v_macos(self):
        """macOS Cmd+V simulation using pynput"""
        try:
            from pynput import keyboard

            controller = keyboard.Controller()
            controller.press(keyboard.Key.cmd)
            controller.press("v")
            controller.release("v")
            controller.release(keyboard.Key.cmd)
            logger.info("Simulated Cmd+V on macOS successfully")
        except ImportError:
            logger.warning("pynput not available on macOS, using fallback")
            self._simulate_ctrl_v_fallback()
        except Exception as e:
            logger.error(f"Error simulating Cmd+V on macOS: {e}")
            self._simulate_ctrl_v_fallback()

    def _simulate_ctrl_v_fallback(self):
        """Fallback method - just copy to clipboard without paste"""
        logger.info("Using fallback method - content copied to clipboard")
        # Don't simulate paste, just leave content in clipboard
        # User can manually paste with Ctrl+V
        if hasattr(self, "system_tray") and self.system_tray:
            self.system_tray.show_notification(
                "Content Copied",
                "Content copied to clipboard. Use Ctrl+V to paste manually.",
                3000,
            )

    def _paste_like_windows(self, item_data: Dict):
        """Paste content like Windows clipboard manager behavior"""
        try:
            clipboard = QApplication.clipboard()

            # Save current clipboard content
            original_text = clipboard.text()
            original_pixmap = clipboard.pixmap()

            try:
                if item_data["content_type"] == "text":
                    # Set text to clipboard temporarily
                    clipboard.setText(item_data["content"])
                    logger.info(
                        f"Temporarily copied text to clipboard: "
                        f"{len(item_data['content'])} chars"
                    )

                elif item_data["content_type"] == "image":
                    # Set image to clipboard temporarily
                    if item_data.get("file_path"):
                        pixmap = QPixmap(item_data["file_path"])
                        if not pixmap.isNull():
                            clipboard.setPixmap(pixmap)
                            logger.info("Temporarily copied image to clipboard")
                        else:
                            logger.error(
                                f"Failed to load image from {item_data['file_path']}"
                            )
                            return
                    else:
                        try:
                            import base64

                            image_data = base64.b64decode(item_data["content"])
                            pixmap = ImageUtils.bytes_to_pixmap(image_data)
                            clipboard.setPixmap(pixmap)
                            logger.info("Temporarily copied image to clipboard")
                        except Exception as e:
                            logger.error(f"Failed to process image data: {e}")
                            return
                else:
                    logger.warning(f"Unknown content type: {item_data['content_type']}")
                    return

                # Simulate Ctrl+V to paste
                self._simulate_ctrl_v()

            finally:
                # Restore original clipboard content
                self._restore_clipboard(original_text, original_pixmap)

        except Exception as e:
            logger.error(f"Error pasting like Windows: {e}")
            # Fallback notification
            if hasattr(self, "system_tray") and self.system_tray:
                self.system_tray.show_notification(
                    "Paste Failed",
                    "Failed to paste content. Please try again.",
                    3000,
                )

    def _restore_clipboard(self, original_text: str, original_pixmap):
        """Restore original clipboard content"""
        try:
            # Small delay to ensure paste is complete
            QTimer.singleShot(
                200, lambda: self._do_restore_clipboard(original_text, original_pixmap)
            )

        except Exception as e:
            logger.error(f"Error scheduling clipboard restore: {e}")

    def _do_restore_clipboard(self, original_text: str, original_pixmap):
        """Actually restore clipboard content"""
        try:
            clipboard = QApplication.clipboard()

            if original_pixmap and not original_pixmap.isNull():
                clipboard.setPixmap(original_pixmap)
                logger.info("Restored original image to clipboard")
            elif original_text:
                clipboard.setText(original_text)
                logger.info("Restored original text to clipboard")
            else:
                clipboard.clear()
                logger.info("Cleared clipboard")

        except Exception as e:
            logger.error(f"Error restoring clipboard: {e}")

    def _get_last_content_type(self):
        """Get content type of last selected item"""
        # This is a simple implementation - you might want to store this in a variable
        return "text"  # Default fallback

    def on_pin_toggled(self, item_id: int, pinned: bool):
        """Handle pin toggle"""
        if self.database.pin_item(item_id, pinned):
            logger.info(f"Item {item_id} {'pinned' if pinned else 'unpinned'}")

    def on_delete_requested(self, item_id: int):
        """Handle delete request"""
        if self.database.delete_item(item_id):
            self.load_items()
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
        self.focus_timer.stop()
        self.dragging = False
        self.drag_start_position = None
        super().hideEvent(event)
