# ===============================================
# FILE: src/core/enhanced_clipboard_watcher.py
# clipboard watcher using new content manager
# ===============================================

"""
clipboard watcher with improved content management
"""
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from PySide6.QtCore import QObject, QTimer
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from core.content_manager import ContentManager
from core.database import ClipboardDatabase
from utils.config import Config

logger = logging.getLogger(__name__)


class ClipboardWatcher(QObject):
    """clipboard watcher with intelligent content management"""

    content_changed = pyqtSignal(str, dict)  # content_type, item_data

    def __init__(
        self,
        database: ClipboardDatabase,
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
        # Polling timer fallback (Wayland, edge cases)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)

        # Debounce timer for signal-based clipboard change handling
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self.check_clipboard)

        # Prefer Qt clipboard signal over polling when available
        try:
            self.clipboard.dataChanged.connect(self._on_clipboard_changed)
            self._signal_connected = True
        except Exception:
            self._signal_connected = False

        # Background executor for DB writes and heavy tasks (avoid UI freeze)
        self._executor = ThreadPoolExecutor(max_workers=2)

    def start(self):
        """Start clipboard monitoring"""
        self.running = True
        # Start polling only if signal cannot be used
        if not getattr(self, "_signal_connected", False):
            poll_ms = int(self.config.get("clipboard_poll_ms", 300))
            self.timer.start(poll_ms)  # Fallback polling
        logger.info("clipboard watcher started")

    def stop(self):
        """Stop clipboard monitoring"""
        self.running = False
        self.timer.stop()
        self._debounce_timer.stop()
        # Ensure background workers do not keep the process alive
        try:
            if getattr(self, "_executor", None) is not None:
                # Cancel pending and do not wait for long-running tasks
                self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception as e:
            logger.error(f"Error shutting down clipboard watcher executor: {e}")
        logger.info("clipboard watcher stopped")

    def _on_clipboard_changed(self):
        """Debounced handler for clipboard dataChanged signal."""
        if not self.running:
            return
        # Debounce bursts (apps may emit multiple changes rapidly)
        interval_ms = max(
            50, min(250, int(self.config.get("clipboard_signal_debounce_ms", 120)))
        )
        self._debounce_timer.start(interval_ms)

    def check_clipboard(self):
        """clipboard change detection - preserve ALL formats like Windows"""
        if not self.running:
            return

        try:
            mime_data = self.clipboard.mimeData()

            # [DISABLED] Skip Windows-like file list clipboard (file copies)
            try:
                if (
                    hasattr(mime_data, "hasUrls") and mime_data.hasUrls()
                ) or mime_data.hasFormat("text/uri-list"):
                    logger.debug("Skipping file/URL clipboard content (text/uri-list)")
                    return
            except Exception:
                pass

            # Collect ALL available formats (Windows-like behavior)
            available_formats = {
                "text": mime_data.text() if mime_data.hasText() else None,
                "html": mime_data.html() if mime_data.hasHtml() else None,
                "rtf": None,
                "image": mime_data.hasImage(),
            }

            # Handle RTF
            if mime_data.hasFormat("text/rtf"):
                rtf_data = mime_data.data("text/rtf")
                available_formats["rtf"] = bytes(rtf_data.data()).decode(
                    "utf-8", errors="ignore"
                )

            # Determine primary content and format (like Windows logic)
            primary_content = None
            primary_format = "plain"
            original_mime_types = []

            # Build mime types list
            if available_formats["text"]:
                original_mime_types.append("text/plain")
            if available_formats["html"]:
                original_mime_types.append("text/html")
            if available_formats["rtf"]:
                original_mime_types.append("text/rtf")
            if available_formats["image"]:
                original_mime_types.append("image")

            # Choose primary content (Windows prioritizes meaningful text)
            if available_formats["text"] and available_formats["text"].strip():
                primary_content = available_formats["text"]
                primary_format = "plain"
                # But we'll store HTML too if available
            elif available_formats["html"] and available_formats["html"].strip():
                primary_content = available_formats["html"]
                primary_format = "html"
            elif available_formats["rtf"]:
                primary_content = available_formats["rtf"]
                primary_format = "rtf"
            elif available_formats["image"]:
                self.handle_image_content(self.clipboard.pixmap())
                return
            else:
                return

            # Handle multi-format content (Windows-like)
            self.handle_multi_format_content(
                primary_content, primary_format, available_formats, original_mime_types
            )

        except Exception as e:
            logger.error(f"Error checking clipboard: {e}")

    def handle_text_content(
        self, content: str, content_type: str, mime_types: Optional[list] = None
    ):
        """Handle text content with preserved MIME information"""
        if not content or not content.strip():
            return

        # Generate content hash for deduplication
        combined = f"{content_type}:{content}"
        content_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]

        if content_hash == self.last_content_hash:
            return

        # Skip very large content
        max_length = self.config.get("max_text_length", 1000000)
        if len(content) > max_length:
            logger.warning(f"Text content too large ({len(content)} chars), skipping")
            return

        # metadata with MIME type info
        metadata = {
            "format": content_type,
            "source": "clipboard_watch",
            "content_type": content_type,
            "original_mime_types": mime_types or [f"text/{content_type}"],
            "preferred_format": content_type,
        }

        # Offload DB write to background thread
        def _worker():
            try:
                item_id = self.database.add_text_item(
                    content=content, metadata=metadata
                )
                if item_id > 0:
                    # Update last hash and emit signal back to UI (queued)
                    self.last_content_hash = content_hash
                    item_data = {
                        "id": item_id,
                        "content_type": "text",
                        "content": content,
                        "format": content_type,
                        "original_mime_types": mime_types,
                        "preview": (
                            content[:150] + "..." if len(content) > 150 else content
                        ),
                    }
                    self.content_changed.emit("text", item_data)
                    logger.debug(
                        f"Added text item {item_id} with format {content_type}"
                    )
            except Exception as e:
                logger.error(f"DB worker error (text): {e}")

        self._executor.submit(_worker)

    def handle_image_content(self, pixmap: QPixmap):
        """image content handling"""
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

            # Offload DB write to background thread (file I/O already done above)
            def _worker():
                try:
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
                            f"Added image item {item_id} ({pixmap.width()}x{pixmap.height()})"
                        )
                except Exception as e:
                    logger.error(f"DB worker error (image): {e}")

            self._executor.submit(_worker)

        except Exception as e:
            logger.error(f"Error handling image content: {e}")

    def handle_multi_format_content(
        self,
        primary_content: str,
        primary_format: str,
        all_formats: dict,
        mime_types: list,
    ):
        """Handle content with multiple formats like Windows Clipboard"""
        if not primary_content or not primary_content.strip():
            return

        # Generate content hash for deduplication
        combined = f"{primary_format}:{primary_content}"
        content_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]

        if content_hash == self.last_content_hash:
            return

        # Skip very large content
        max_length = self.config.get("max_text_length", 1000000)
        if len(primary_content) > max_length:
            logger.warning(
                f"Content too large ({len(primary_content)} chars), skipping"
            )
            return

        # metadata with ALL formats preserved
        metadata = {
            "format": primary_format,
            "source": "clipboard_watch",
            "content_type": primary_format,
            "original_mime_types": mime_types,
            "preferred_format": primary_format,
            "has_html": bool(all_formats.get("html")),
            "has_rtf": bool(all_formats.get("rtf")),
            "multi_format": len([f for f in all_formats.values() if f]) > 1,
        }

        # Store with HTML content if available (Windows behavior)
        html_content = all_formats.get("html") if all_formats.get("html") else None

        # Offload DB write to background thread
        def _worker():
            try:
                item_id = self.database.add_multi_format_text_item(
                    content=primary_content,
                    html_content=html_content,
                    format_type=primary_format,
                    metadata=metadata,
                )
                if item_id > 0:
                    self.last_content_hash = content_hash
                    item_data = {
                        "id": item_id,
                        "content_type": "text",
                        "content": primary_content,
                        "html_content": html_content,
                        "format": primary_format,
                        "original_mime_types": mime_types,
                        "preview": (
                            primary_content[:150] + "..."
                            if len(primary_content) > 150
                            else primary_content
                        ),
                    }
                    self.content_changed.emit("text", item_data)
                    logger.debug(
                        f"Added multi-format item {item_id} with format {primary_format}"
                    )
            except Exception as e:
                logger.error(f"DB worker error (multi-format): {e}")

        self._executor.submit(_worker)

    def update_config(self):
        """Update configuration settings"""
        # Reload any cached config values
        pass
