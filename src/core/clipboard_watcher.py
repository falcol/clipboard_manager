# ===============================================
# FILE: src/core/enhanced_clipboard_watcher.py
# Enhanced clipboard watcher using new content manager
# ===============================================

"""
Enhanced clipboard watcher with improved content management
"""
import logging

from PySide6.QtCore import QObject, QTimer
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from core.content_manager import ContentManager
from core.database import EnhancedClipboardDatabase
from utils.config import Config

logger = logging.getLogger(__name__)


class EnhancedClipboardWatcher(QObject):
    """Enhanced clipboard watcher with intelligent content management"""

    content_changed = pyqtSignal(str, dict)  # content_type, item_data

    def __init__(
        self,
        database: EnhancedClipboardDatabase,
        content_manager: ContentManager,
        config: Config,
    ):
        super().__init__()
        self.database = database
        self.content_manager = content_manager
        self.config = config
        self.clipboard = QApplication.clipboard()
        self.last_content_hash = None
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)

    def start(self):
        """Start enhanced clipboard monitoring"""
        self.running = True
        self.timer.start(300)  # Check every 300ms for better responsiveness
        logger.info("Enhanced clipboard watcher started")

    def stop(self):
        """Stop clipboard monitoring"""
        self.running = False
        self.timer.stop()
        logger.info("Enhanced clipboard watcher stopped")

    def check_clipboard(self):
        """Enhanced clipboard change detection"""
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
        """Enhanced text content handling"""
        if not text or not text.strip():
            return

        # Generate content hash for deduplication
        import hashlib

        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

        if content_hash == self.last_content_hash:
            return

        # Skip very large content
        max_length = self.config.get("max_text_length", 1000000)
        if len(text) > max_length:
            logger.warning(f"Text content too large ({len(text)} chars), skipping")
            return

        # Use content manager for optimization
        text_analysis = self.content_manager.optimize_text_content(text)

        # Add to database
        item_id = self.database.add_text_item(
            content=text,
            metadata={"analysis": text_analysis, "source": "clipboard_watch"},
        )

        if item_id > 0:
            self.last_content_hash = content_hash

            # Emit signal with enhanced data
            item_data = {
                "id": item_id,
                "content_type": "text",
                "content": text,
                "preview": text_analysis["preview"],
                "metadata": text_analysis,
            }

            self.content_changed.emit("text", item_data)
            logger.debug(f"Added enhanced text item {item_id} ({len(text)} chars)")

    def handle_image_content(self, pixmap: QPixmap):
        """Enhanced image content handling"""
        if pixmap.isNull():
            return

        try:
            # Use content manager for optimized storage
            image_path, thumbnail_path, image_data, thumbnail_data = (
                self.content_manager.store_image(pixmap)
            )

            if not image_path:
                logger.error("Failed to store image")
                return

            # Generate content hash for deduplication
            import hashlib

            content_hash = hashlib.sha256(image_data).hexdigest()[:16]

            if content_hash == self.last_content_hash:
                return

            # Add to database
            item_id = self.database.add_image_item(
                image_data=image_data,
                thumbnail_data=thumbnail_data,
                width=pixmap.width(),
                height=pixmap.height(),
                image_format="PNG",
                metadata={
                    "source": "clipboard_watch",
                    "original_size": len(image_data),
                },
            )

            if item_id > 0:
                self.last_content_hash = content_hash

                # Emit signal with enhanced data
                item_data = {
                    "id": item_id,
                    "content_type": "image",
                    "file_path": image_path,
                    "thumbnail_path": thumbnail_path,
                    "width": pixmap.width(),
                    "height": pixmap.height(),
                    "preview": thumbnail_path,
                }

                self.content_changed.emit("image", item_data)
                logger.debug(
                    # flake8: noqa: E501
                    f"Added enhanced image item {item_id} ({pixmap.width()}x{pixmap.height()})"
                )

        except Exception as e:
            logger.error(f"Error handling image content: {e}")

    def update_config(self):
        """Update configuration settings"""
        # Reload any cached config values
        pass
