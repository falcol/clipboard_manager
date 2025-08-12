# clipboard_manager/src/ui/popup_window/clipboard_item.py
"""
Windows 10 Dark Mode Clipboard Manager Popup Window
"""
import logging
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from utils.qss_loader import QSSLoader

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

        # Set object name for QSS targeting
        self.setObjectName("clipboardItem")
        self.setProperty("selected", False)
        self.setProperty("pressed", False)

        # Initialize QSS loader
        self.qss_loader = QSSLoader()

        self.setup_ui()
        self.setup_animations()

        # Apply QSS stylesheet
        # REMOVE local QSS apply (use global)
        # if hasattr(self, "qss_loader"):
        #     self.qss_loader.apply_stylesheet(self, "main.qss")
        #     self.qss_loader.apply_stylesheet(self, "themes/dark_win11.qss")

    def setup_ui(self):
        """Setup Windows 10 dark mode UI for clipboard item - EXACTLY like styles.py"""
        # Increase height to fit 3 lines of text with font 13px
        self.setFixedHeight(90)  # Increase from 80 to 90
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)  # Reduced spacing

        # Content type icon - INLINE STYLE like original (styles.py doesn't define icon styling)
        content_icon = self.get_content_icon()
        icon_label = QLabel(content_icon)
        icon_label.setFixedSize(20, 20)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Prefer QSS: set object name and style via stylesheet
        icon_label.setObjectName("iconLabel")
        layout.addWidget(icon_label)

        # Main content area with fixed width
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        # Preview content - FIXED: Handle both text and image
        if self.item_data["content_type"] == "image":
            preview_widget = self._create_image_preview()
        else:
            preview_widget = self._create_text_preview()

        content_layout.addWidget(preview_widget)

        # Add content with stretch factor but limited width
        layout.addLayout(content_layout, 1)

        # Action buttons - ensure they're always visible
        self.actions_widget = QWidget()
        self.actions_widget.setFixedWidth(32)
        self.actions_layout = QVBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(4)
        self.actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Pin button
        self.pin_btn = QPushButton()
        self.pin_btn.setObjectName("pinButton")  # base state
        self.pin_btn.setFixedSize(24, 24)
        self.pin_btn.setToolTip("Pin/Unpin item")
        self.pin_btn.clicked.connect(self.toggle_pin)
        self.actions_layout.addWidget(self.pin_btn)

        # Delete button (use system icon theme with fallback emoji)
        self.delete_btn = QPushButton()
        try:
            delete_icon = QIcon.fromTheme("edit-delete")
            if not delete_icon.isNull():
                self.delete_btn.setIcon(delete_icon)
            else:
                self.delete_btn.setText("🗑")
        except Exception:
            self.delete_btn.setText("🗑")
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setToolTip("Delete item")
        self.delete_btn.clicked.connect(self.delete_item)
        self.actions_layout.addWidget(self.delete_btn)

        layout.addWidget(self.actions_widget)

        # Update pin button and delete button styles AFTER widgets are created
        self.update_pin_button()
        # Accessibility names
        try:
            self.pin_btn.setAccessibleName("Pin item")
            self.delete_btn.setAccessibleName("Delete item")
        except Exception:
            pass
        # REMOVE delete_btn.setStyleSheet(...)
        # self.delete_btn.setStyleSheet(self.qss_loader.load_stylesheet("main.qss"))

    def setup_animations(self):
        """Setup hover animations"""
        self.shadow_effect = QGraphicsDropShadowEffect()
        # Slightly reduced blur radius for better performance on Linux
        self.shadow_effect.setBlurRadius(6)
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
        """Update pin button appearance using EXACTLY styles.py methods"""
        if self.item_data.get("is_pinned"):
            # Prefer system icon if available; fallback to emoji
            pin_icon = QIcon.fromTheme("flag-red")
            if not pin_icon.isNull():
                self.pin_btn.setIcon(pin_icon)
                self.pin_btn.setText("")
            else:
                self.pin_btn.setText("📌")
            self.pin_btn.setObjectName("pinButtonActive")
        else:
            pin_icon = QIcon.fromTheme("flag")
            if not pin_icon.isNull():
                self.pin_btn.setIcon(pin_icon)
                self.pin_btn.setText("")
            else:
                self.pin_btn.setText("📍")
            self.pin_btn.setObjectName("pinButton")
        self.pin_btn.setStyleSheet("")  # ensure QSS re-evaluates
        self._repolish(self.pin_btn)

    def mousePressEvent(self, event):
        """Handle mouse click to select item"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setProperty("pressed", True)
            self._repolish(self)
            self.item_selected.emit(self.item_data)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setProperty("pressed", False)
            self._repolish(self)
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter (hover) - use QSS hover states"""
        self.is_hovered = True
        self.shadow_effect.setEnabled(True)
        # QSS handles hover styling automatically
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave - use QSS normal states"""
        self.is_hovered = False
        self.shadow_effect.setEnabled(False)
        # QSS handles normal styling automatically
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

    def _create_text_preview(self):
        """Create text preview respecting original format"""
        format_type = self.item_data.get("format", "plain")
        content = self.item_data.get("content", "")
        original_mime_types = self.item_data.get("original_mime_types", [])

        # For code from IDEs - always show as plain text even if HTML is available
        if format_type == "plain" or "text/plain" in original_mime_types:
            # Show as plain text (most common for code)
            preview_text = self.item_data.get("preview", content[:150])
            preview_label = QLabel(preview_text)
            preview_label.setObjectName("contentLabel")  # Use QSS for styling
            return self._style_text_label(preview_label)

        elif format_type == "html" and "text/html" in original_mime_types:
            # Only render HTML if it's genuinely HTML content (not code with HTML wrapper)
            if self._is_genuine_html_content(content):
                # Use QTextEdit for proper HTML rendering
                preview_widget = QTextEdit()
                preview_widget.setReadOnly(True)
                preview_widget.setMaximumHeight(60)
                preview_widget.setVerticalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                )
                preview_widget.setHorizontalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                )

                safe_html = self._safe_html_preview(content)
                preview_widget.setHtml(safe_html)

                # Apply basic styling via QSS
                preview_widget.setObjectName(
                    "htmlPreview"
                )  # Use QSS instead of inline style
                return preview_widget
            else:
                # Treat as plain text even if it has HTML wrapper
                import re

                plain_content = re.sub(r"<[^>]+>", "", content)
                preview_label = QLabel(plain_content[:150])
                preview_label.setObjectName("contentLabel")
                return self._style_text_label(preview_label)

        elif format_type == "rtf":
            # RTF preview
            preview_label = QLabel()
            preview_label.setObjectName("contentLabel")
            preview_label.setTextFormat(Qt.TextFormat.RichText)
            rtf_text = self._rtf_to_display_text(content)
            preview_label.setText(rtf_text)
            return self._style_text_label(preview_label)

        else:
            # Default plain text
            preview_text = self.item_data.get("preview", content[:150])
            preview_label = QLabel(preview_text)
            preview_label.setObjectName("contentLabel")
            return self._style_text_label(preview_label)

    def _safe_html_preview(self, html: str) -> str:
        """Create safe HTML preview for display"""
        max_length = 300

        # Truncate if too long
        if len(html) > max_length:
            html = html[:max_length] + "..."

        # Basic HTML sanitization
        import re

        # Remove dangerous tags
        html = re.sub(
            r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(
            r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE
        )

        # Remove attributes except basic styling
        html = re.sub(r'<(\w+)[^>]*?(style="[^"]*")?[^>]*>', r"<\1 \2>", html)

        # Ensure proper structure for preview
        if not html.strip().startswith("<"):
            html = f'<div style="color: white; font-size: 10px;">{html}</div>'

        return html

    def _rtf_to_display_text(self, rtf: str) -> str:
        """Convert RTF to basic formatted text"""
        import re

        # Remove RTF control words
        text = re.sub(r"\\[a-z0-9]+\b", "", rtf)
        text = re.sub(r"[{}]", "", text)

        # Basic formatting conversion
        text = text.replace("\\b", "<b>").replace("\\b0", "</b>")
        text = text.replace("\\i", "<i>").replace("\\i0", "</i>")

        return text[:200] + "..." if len(text) > 200 else text

    def _style_text_label(self, label: QLabel) -> QLabel:
        """Apply consistent styling to text labels - EXACTLY like original"""
        label.setWordWrap(True)
        label.setFont(QFont(QApplication.font().family(), 13))
        # NO setStyleSheet - styles.py doesn't define font styling inline
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Calculate height EXACTLY for 3 lines with font 13px
        font_metrics = label.fontMetrics()
        line_height = font_metrics.height()
        # Ensure exactly 3 lines, no truncation
        label.setFixedHeight(line_height * 3)  # Remove +8 padding, only 3 lines exactly
        label.setMaximumWidth(280)
        label.setMinimumWidth(100)

        return label

    def _create_image_preview(self):
        """Create image preview with proper thumbnail like Windows Clipboard"""
        preview_container = QWidget()
        preview_container.setFixedHeight(64)  # Larger for better image display (64px)
        preview_container.setObjectName("imagePreviewContainer")  # Use QSS

        layout = QHBoxLayout(preview_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Image thumbnail
        thumbnail_label = QLabel()
        thumbnail_label.setFixedSize(56, 56)  # Square thumbnail (56px)
        # Remove inline style, use QSS

        # Load and display thumbnail
        thumbnail_loaded = False

        # Method 1: Try thumbnail_path first (optimized)
        if self.item_data.get("thumbnail_path"):
            try:
                pixmap = QPixmap(self.item_data["thumbnail_path"])
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        54,
                        54,  # Slightly smaller than label for border
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    thumbnail_label.setPixmap(scaled_pixmap)
                    thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    thumbnail_loaded = True
                    logger.debug(
                        f"Loaded thumbnail from {self.item_data['thumbnail_path']}"
                    )
            except Exception as e:
                logger.warning(f"Failed to load thumbnail: {e}")

        # Method 2: Try file_path (full image)
        if not thumbnail_loaded and self.item_data.get("file_path"):
            try:
                pixmap = QPixmap(self.item_data["file_path"])
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        54,
                        54,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    thumbnail_label.setPixmap(scaled_pixmap)
                    thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    thumbnail_loaded = True
                    logger.debug(f"Loaded image from {self.item_data['file_path']}")
            except Exception as e:
                logger.warning(f"Failed to load image: {e}")

        # Method 3: Try base64 content
        if not thumbnail_loaded and self.item_data.get("content"):
            try:
                import base64

                from utils.image_utils import ImageUtils

                content = self.item_data["content"]
                if content.startswith("data:image"):
                    base64_data = content.split(",")[1] if "," in content else content
                    image_data = base64.b64decode(base64_data)
                else:
                    image_data = base64.b64decode(content)

                pixmap = ImageUtils.bytes_to_pixmap(image_data)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        54,
                        54,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    thumbnail_label.setPixmap(scaled_pixmap)
                    thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    thumbnail_loaded = True
                    logger.debug("Loaded image from base64 content")
            except Exception as e:
                logger.warning(f"Failed to decode base64 image: {e}")

        # Fallback: Show placeholder
        if not thumbnail_loaded:
            thumbnail_label.setText("🖼️")
            thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Remove inline style, use QSS

        layout.addWidget(thumbnail_label)

        # Image info text
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        # Image type and size
        width = self.item_data.get("width", 0)
        height = self.item_data.get("height", 0)
        format_type = self.item_data.get("format", "image")

        type_label = QLabel(f"{format_type.upper()}")
        type_label.setObjectName("imageTypeLabel")  # Use QSS instead of inline style
        info_layout.addWidget(type_label)

        if width and height:
            size_label = QLabel(f"{width} × {height} px")
            size_label.setObjectName(
                "imageSizeLabel"
            )  # Use QSS instead of inline style
            info_layout.addWidget(size_label)

        # Timestamp or additional info
        timestamp = self.item_data.get("created_at", "")
        if timestamp:
            time_label = QLabel(f"Copied: {timestamp[:16]}")  # Show date/time
            time_label.setObjectName(
                "imageTimeLabel"
            )  # Use QSS instead of inline style
            info_layout.addWidget(time_label)

        info_layout.addStretch()
        layout.addWidget(info_widget, 1)

        return preview_container

    def _is_genuine_html_content(self, content: str) -> bool:
        """Check if content is genuine HTML (not just code wrapped in HTML)"""
        import re

        # Simple heuristic: if it's mostly code-like content, treat as plain
        code_indicators = [
            r"def\s+\w+\(",  # Python functions
            r"function\s+\w+\(",  # JavaScript functions
            r"class\s+\w+",  # Class definitions
            r"import\s+\w+",  # Import statements
            r"#include\s*<",  # C/C++ includes
            r"console\.log\(",  # Console logs
            r"print\s*\(",  # Print statements
        ]

        # Remove HTML tags to check actual content
        plain_content = re.sub(r"<[^>]+>", "", content)

        # If content matches code patterns, treat as plain text
        for pattern in code_indicators:
            if re.search(pattern, plain_content, re.IGNORECASE):
                return False

        # Check if it has meaningful HTML structure (not just wrapper)
        html_structure_tags = [
            "<p",
            "<div",
            "<span",
            "<h1",
            "<h2",
            "<ul",
            "<ol",
            "<table",
        ]
        html_tag_count = sum(1 for tag in html_structure_tags if tag in content.lower())

        # If it has multiple HTML structure tags, likely genuine HTML
        return html_tag_count >= 2

    def _repolish(self, w: QWidget):
        # Force QSS re-apply for dynamic properties
        w.style().unpolish(w)
        w.style().polish(w)
        w.update()
