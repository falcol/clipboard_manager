# clipboard_manager/src/ui/popup_window.py
"""
Windows 10 Dark Mode Clipboard Manager Popup Window
"""
import logging
import sys
from typing import Dict, Optional

from PySide6.QtCore import QEasingCurve, QMimeData, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QClipboard, QColor, QCursor, QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.database import EnhancedClipboardDatabase as ClipboardDatabase
from ui.popup_window.clipboard_item import ClipboardItem
from ui.popup_window.search_bar import SearchBar
from utils.config import Config
from utils.image_utils import ImageUtils
from utils.qss_loader import QSSLoader

logger = logging.getLogger(__name__)


class PopupWindow(QWidget):
    """Windows 10 dark mode popup window"""

    def __init__(self, database: ClipboardDatabase, config: Config, system_tray=None):
        super().__init__()
        self.database = database
        self.config = config
        self.system_tray = system_tray

        # Set object name for QSS targeting
        self.setObjectName("popupWindow")

        # Initialize QSS loader
        self.qss_loader = QSSLoader()

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

        # Apply QSS after all setup is complete
        #  Keep applying main.qss if needed for structure; global theme will override colors
        # self.qss_loader.apply_stylesheet_to_widget_and_children(self, "main.qss")
        # Theme: do application apply globally

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
        """Setup Windows 10 dark mode UI using QSS"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main container
        self.container = QFrame()
        self.container.setObjectName("mainContainer")  # Use QSS for styling
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        self.header = QFrame()
        self.header.setObjectName("header")  # Use QSS for styling
        self.header.setFixedHeight(48)
        self.header.setCursor(Qt.CursorShape.SizeAllCursor)
        self.header.setFrameShape(QFrame.Shape.NoFrame)  # flat header

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        # Title
        title_layout = QHBoxLayout()

        # Drag indicator
        drag_icon = QLabel("⋮⋮")
        drag_icon.setObjectName("dragIcon")  # Use QSS for styling
        drag_icon.setFont(QFont(QApplication.font().family(), 10))
        drag_icon.setToolTip("Drag to move window")
        title_layout.addWidget(drag_icon)

        title_icon = QLabel("📋")
        title_icon.setObjectName("titleIcon")  # Use QSS for styling
        title_icon.setFont(QFont(QApplication.font().family(), 14))
        title_layout.addWidget(title_icon)

        title_label = QLabel("Clipboard Manager")
        title_label.setObjectName("titleLabel")  # Use QSS for styling
        title_label.setFont(QFont(QApplication.font().family(), 12, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        header_layout.addLayout(title_layout)

        # Header actions
        actions_layout = QHBoxLayout()

        # Clear all button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setObjectName("clearAllButton")  # Use QSS for styling
        self.clear_btn.setFlat(True)  # flat look
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)  # pointer on hover
        self.clear_btn.clicked.connect(self.clear_history)
        actions_layout.addWidget(self.clear_btn)

        header_layout.addLayout(actions_layout)
        container_layout.addWidget(self.header)

        # Search bar
        self.search_bar = SearchBar()
        self.search_bar.search_requested.connect(self.on_search)
        container_layout.addWidget(self.search_bar)

        # Content area with proper QSS structure
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
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
        # QSS will handle scrollbar styling

        # Reduce repaint cost during scrolling for better performance on Linux
        try:
            self.scroll_area.setFrameShape(QFrame.NoFrame)
            self.scroll_area.viewport().setAttribute(
                Qt.WidgetAttribute.WA_OpaquePaintEvent, True
            )
        except Exception:
            pass

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
        footer.setObjectName("footer")  # Use QSS for styling
        footer.setFixedHeight(28)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 6, 16, 6)

        footer_label = QLabel("Click to paste • Ctrl+F to search • Drag header to move")
        footer_label.setObjectName("footerLabel")  # Use QSS for styling
        footer_label.setFont(QFont(QApplication.font().family(), 8))
        footer_layout.addWidget(footer_label)

        # Stats
        self.stats_label = QLabel()
        self.stats_label.setObjectName("statsLabel")  # Use QSS for styling
        self.stats_label.setFont(QFont(QApplication.font().family(), 8))
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
                empty_label.setObjectName(
                    "emptyStateLabel"
                )  # Use QSS instead of inline style
            else:
                empty_label = QLabel("📋 No clipboard history yet")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setObjectName(
                    "emptyStateLabel"
                )  # Use QSS instead of inline style
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
        """Handle clipboard item selection"""
        logger.info(f"Item selected: {item_data['id']}")

        # Copy to system clipboard FIRST
        copy_success = self._copy_to_system_clipboard(item_data)

        if copy_success:
            # Small delay to ensure clipboard is set
            QTimer.singleShot(50, self._simulate_ctrl_v)
        else:
            logger.error("Failed to copy to clipboard, skipping paste simulation")

        self.hide()

    def _copy_to_system_clipboard(self, item_data: Dict) -> bool:
        """Copy content like Windows Clipboard - preserve ALL formats including images"""
        try:
            content_type = item_data.get("content_type", "text")

            # [DISABLED] Do not handle Windows-like file lists
            original_mime_types = item_data.get("original_mime_types", []) or []
            if "text/uri-list" in original_mime_types:
                logger.info(
                    "Skipping file URI list clipboard item (file copy not supported)"
                )
                return False

            # Handle IMAGE content (Windows-like behavior)
            if content_type == "image":
                return self._copy_image_to_clipboard(item_data)

            # Handle TEXT content (existing logic)
            mime_data = QMimeData()
            content = item_data.get("content", "")
            html_content = item_data.get("html_content")
            format_type = item_data.get("format", "plain")
            original_mime_types = item_data.get("original_mime_types", [])

            # Validate content first
            if not content or not content.strip():
                logger.error("No content to copy")
                return False

            logger.info(
                f"Copying Windows-style: format={format_type}, has_html={bool(html_content)}, mime_types={original_mime_types}"
            )

            # Windows behavior: ALWAYS set plain text as fallback
            mime_data.setText(content)
            logger.info("Set plain text to clipboard")

            # Set HTML if available (Windows preserves both)
            if html_content and html_content.strip():
                mime_data.setHtml(html_content)
                logger.info("Set HTML content to clipboard (Windows-like multi-format)")
            elif format_type == "html" and content.strip().startswith("<"):
                # Fallback: if no separate HTML but content looks like HTML
                mime_data.setHtml(content)
                logger.info("Set HTML content from main content")

            # Handle RTF if available
            if format_type == "rtf":
                mime_data.setData("text/rtf", content.encode("utf-8"))
                logger.info("Set RTF content to clipboard")

            # Set to system clipboard (main clipboard, not selection)
            clipboard = QApplication.clipboard()
            clipboard.setMimeData(
                mime_data, QClipboard.Mode.Clipboard
            )  # Explicitly use main clipboard

            # Verify multi-format clipboard was set
            QTimer.singleShot(
                10,
                lambda: self._verify_multi_format_clipboard(content[:50], html_content),
            )

            return True

        except Exception as e:
            logger.error(f"Failed to copy multi-format to clipboard: {e}")
            return False

    def _copy_image_to_clipboard(self, item_data: Dict) -> bool:
        """Copy image content to clipboard like Windows Clipboard Manager"""
        try:
            logger.info(f"Copying image item: {item_data['id']}")

            # Method 1: Try to load from file_path first
            if item_data.get("file_path"):
                pixmap = QPixmap(item_data["file_path"])
                if not pixmap.isNull():
                    clipboard = QApplication.clipboard()
                    clipboard.setPixmap(pixmap, QClipboard.Mode.Clipboard)
                    logger.info(f"✓ Image copied from file: {item_data['file_path']}")

                    # Show notification
                    if hasattr(self, "system_tray") and self.system_tray:
                        self.system_tray.show_notification(
                            "Image Copied",
                            f"Image copied to clipboard ({pixmap.width()}×{pixmap.height()})",
                            2000,
                        )
                    return True
                else:
                    logger.warning(
                        f"Failed to load image from {item_data['file_path']}"
                    )

            # Method 2: Try to load from thumbnail_path
            if item_data.get("thumbnail_path"):
                pixmap = QPixmap(item_data["thumbnail_path"])
                if not pixmap.isNull():
                    clipboard = QApplication.clipboard()
                    clipboard.setPixmap(pixmap, QClipboard.Mode.Clipboard)
                    logger.info(
                        f"✓ Image copied from thumbnail: {item_data['thumbnail_path']}"
                    )
                    return True

            # Method 3: Try to decode from base64 content (fallback)
            if item_data.get("content"):
                try:
                    import base64

                    from utils.image_utils import ImageUtils

                    # Handle base64 data URLs
                    content = item_data["content"]
                    if content.startswith("data:image"):
                        # Extract base64 part
                        base64_data = (
                            content.split(",")[1] if "," in content else content
                        )
                        image_data = base64.b64decode(base64_data)
                    else:
                        # Assume raw base64
                        image_data = base64.b64decode(content)

                    pixmap = ImageUtils.bytes_to_pixmap(image_data)
                    if not pixmap.isNull():
                        clipboard = QApplication.clipboard()
                        clipboard.setPixmap(pixmap, QClipboard.Mode.Clipboard)
                        logger.info("✓ Image copied from base64 content")
                        return True

                except Exception as e:
                    logger.error(f"Failed to decode base64 image: {e}")

            # Method 4: Final fallback - create placeholder image
            logger.warning("Creating placeholder image for clipboard")
            placeholder_pixmap = QPixmap(100, 100)
            placeholder_pixmap.fill(QColor(128, 128, 128))  # Gray placeholder

            clipboard = QApplication.clipboard()
            clipboard.setPixmap(placeholder_pixmap, QClipboard.Mode.Clipboard)
            logger.info("✓ Placeholder image copied to clipboard")

            return True

        except Exception as e:
            logger.error(f"Failed to copy image to clipboard: {e}")
            return False

    def _verify_multi_format_clipboard(
        self, expected_text: str, expected_html: Optional[str] = None
    ):
        """Verify multi-format clipboard was set correctly"""
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData(QClipboard.Mode.Clipboard)

            has_text = mime_data.hasText() and expected_text in mime_data.text()
            has_html = (
                expected_html
                and mime_data.hasHtml()
                and expected_html[:50] in mime_data.html()
            )
            has_image = mime_data.hasImage()

            if has_text:
                logger.info("✓ Plain text verified in clipboard")
            else:
                logger.warning("✗ Plain text verification failed")

            if expected_html:
                if has_html:
                    logger.info("✓ HTML content verified in clipboard")
                else:
                    logger.warning("✗ HTML content verification failed")

            if has_image:
                logger.info("✓ Image content verified in clipboard")

            # Log available formats for debugging
            available = []
            if mime_data.hasText():
                available.append("text/plain")
            if mime_data.hasHtml():
                available.append("text/html")
            if mime_data.hasImage():
                available.append("image")

            logger.info(f"Clipboard formats available: {available}")

        except Exception as e:
            logger.error(f"Multi-format clipboard verification error: {e}")

    def _simulate_ctrl_v(self):
        """Simulate Ctrl+V using the actual clipboard content"""
        try:
            # Get current platform
            platform = sys.platform.lower()
            import os

            # Check if clipboard has content - FIX THE LOGIC HERE
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()

            has_content = (
                (mime_data.hasText() and mime_data.text().strip())
                or (mime_data.hasHtml() and mime_data.html().strip())
                or (mime_data.hasImage() and not clipboard.pixmap().isNull())
            )

            if has_content:
                logger.info("Clipboard has content, simulating paste...")

                # Wayland: skip key simulation; rely on clipboard being set
                if os.environ.get("WAYLAND_DISPLAY"):
                    self._simulate_ctrl_v_fallback()
                else:
                    if platform.startswith("win"):
                        self._simulate_ctrl_v_windows()
                    elif platform.startswith("linux"):
                        self._simulate_ctrl_v_linux()
                    elif platform.startswith("darwin"):
                        self._simulate_ctrl_v_macos()
                    else:
                        self._simulate_ctrl_v_fallback()
            else:
                logger.warning("No content in clipboard to paste")
                logger.debug(
                    f"Clipboard check: hasText={mime_data.hasText()}, hasHtml={mime_data.hasHtml()}, hasImage={mime_data.hasImage()}"
                )

        except Exception as e:
            logger.error(f"Error simulating paste: {e}")

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
