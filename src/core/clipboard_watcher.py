# clipboard_manager/src/core/clipboard_watcher.py
"""
Monitor clipboard changes and save to database
"""
import base64
import logging

from PySide6.QtCore import QObject, QTimer
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from core.database import ClipboardDatabase
from utils.config import Config
from utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class ClipboardWatcher(QObject):
    # Signal emitted when new clipboard content is detected
    content_changed = pyqtSignal(str, str)  # content_type, content

    def __init__(self, database: ClipboardDatabase, config: Config):
        super().__init__()
        self.database = database
        self.config = config
        self.clipboard = QApplication.clipboard()
        self.last_content = None
        self.last_content_type = None
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)

    def start(self):
        """Start monitoring clipboard"""
        self.running = True
        # Check clipboard every 500ms
        self.timer.start(500)
        logger.info("Clipboard watcher started")

    def stop(self):
        """Stop monitoring clipboard"""
        self.running = False
        self.timer.stop()
        logger.info("Clipboard watcher stopped")

    def check_clipboard(self):
        """Check for clipboard changes"""
        if not self.running:
            return

        try:
            mime_data = self.clipboard.mimeData()

            if mime_data.hasText():
                self.handle_text_content(mime_data.text())
            elif mime_data.hasImage():
                self.handle_image_content(self.clipboard.pixmap())

        except Exception as e:
            logger.error(f"Error checking clipboard: {e}")

    def handle_text_content(self, text: str):
        """Handle text clipboard content"""
        if not text or text == self.last_content:
            return

        # Skip very large text content to avoid memory issues
        max_length = self.config.get("max_text_length", 10000)
        if len(text) > max_length:
            logger.warning(f"Text content too large ({len(text)} chars), skipping")
            return

        # Create preview (first few lines)
        preview = self.create_text_preview(text)

        # Save to database
        item_id = self.database.add_item(
            content_type="text",
            content=text,
            preview=preview,
            metadata={"length": len(text)},
        )

        if item_id > 0:
            self.last_content = text
            self.last_content_type = "text"
            self.content_changed.emit("text", text)
            logger.debug(f"Added text item {item_id} ({len(text)} chars)")

    def handle_image_content(self, pixmap: QPixmap):
        """Handle image clipboard content"""
        if pixmap.isNull():
            return

        try:
            # Convert pixmap to bytes
            byte_array = ImageUtils.pixmap_to_bytes(pixmap)
            image_data = base64.b64encode(byte_array).decode("utf-8")

            # Skip if same as last content
            if image_data == self.last_content:
                return

            # Create thumbnail for preview
            thumbnail = ImageUtils.create_thumbnail(pixmap, (64, 64))
            thumbnail_data = base64.b64encode(
                ImageUtils.pixmap_to_bytes(thumbnail)
            ).decode("utf-8")

            # Save to database
            item_id = self.database.add_item(
                content_type="image",
                content=image_data,
                preview=thumbnail_data,
                metadata={
                    "width": pixmap.width(),
                    "height": pixmap.height(),
                    "size": len(byte_array),
                },
            )

            if item_id > 0:
                self.last_content = image_data
                self.last_content_type = "image"
                self.content_changed.emit("image", image_data)
                logger.debug(
                    f"Added image item {item_id} "
                    f"({pixmap.width()}x{pixmap.height()})"
                )

        except Exception as e:
            logger.error(f"Error handling image content: {e}")

    def create_text_preview(self, text: str, max_length: int = 100) -> str:
        """Create a preview of text content"""
        if len(text) <= max_length:
            return text

        # Try to break at word boundary
        preview = text[:max_length]
        last_space = preview.rfind(" ")
        if last_space > max_length * 0.7:  # If space is not too far back
            preview = preview[:last_space]

        return preview + "..."

    def update_config(self):
        """Update configuration settings"""
        # Reload config if needed
        pass
