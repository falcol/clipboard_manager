# ===============================================
# FILE: src/core/content_manager.py
# New content management system
# ===============================================

"""
Intelligent content management for clipboard items
"""
import hashlib
import json
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QPixmap

logger = logging.getLogger(__name__)


class ContentManager:
    """Intelligent content storage and retrieval manager"""

    def __init__(self, data_dir: Path, cache_size_mb: Optional[int] = None):
        self.data_dir = data_dir
        self.images_dir = data_dir / "images"
        self.thumbnails_dir = data_dir / "thumbnails"
        self.cache_dir = data_dir / "cache"

        # Create directories
        for directory in [self.images_dir, self.thumbnails_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # In-memory LRU cache for frequently accessed pixmaps - OPTIMIZED for RAM
        self.memory_cache: OrderedDict[str, QPixmap] = OrderedDict()
        # Configure cache size (bytes) - REDUCED from 50MB to 15MB default
        limit_mb = 15 if cache_size_mb is None else max(5, min(cache_size_mb, 100))
        self.cache_size_limit = limit_mb * 1024 * 1024
        self.current_cache_size = 0

    def store_image(
        self, pixmap: QPixmap, format: str = "PNG", quality: int = 95
    ) -> Tuple[str, str, bytes, bytes]:
        """
        Store image with optimization
        Returns: (image_path, thumbnail_path, image_data, thumbnail_data)
        """
        try:
            # Convert to bytes for hashing
            image_data = self._pixmap_to_bytes(pixmap, format, quality)
            content_hash = hashlib.sha256(image_data).hexdigest()[:16]

            # Generate file paths
            image_filename = f"{content_hash}.{format.lower()}"
            thumbnail_filename = f"{content_hash}_thumb.{format.lower()}"

            image_path = self.images_dir / image_filename
            thumbnail_path = self.thumbnails_dir / thumbnail_filename

            # Create optimized thumbnail (128x128 max)
            thumbnail_pixmap = self._create_optimized_thumbnail(pixmap)
            thumbnail_data = self._pixmap_to_bytes(thumbnail_pixmap, format, 85)

            # Save files if they don't exist
            if not image_path.exists():
                with open(image_path, "wb") as f:
                    f.write(image_data)

            if not thumbnail_path.exists():
                with open(thumbnail_path, "wb") as f:
                    f.write(thumbnail_data)

            return str(image_path), str(thumbnail_path), image_data, thumbnail_data

        except Exception as e:
            logger.error(f"Error storing image: {e}")
            return "", "", b"", b""

    def load_image(self, image_path: str) -> Optional[QPixmap]:
        """Load image with caching"""
        try:
            path = Path(image_path)
            if not path.exists():
                return None

            # Check memory cache first
            cache_key = str(path)
            if cache_key in self.memory_cache:
                # Promote to most-recently used
                pix = self.memory_cache.pop(cache_key)
                self.memory_cache[cache_key] = pix
                return pix

            # Load from disk
            pixmap = QPixmap()
            if pixmap.load(str(path)):
                # Add to cache if there's space
                self._add_to_cache(cache_key, pixmap)
                return pixmap

            return None

        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None

    def load_thumbnail(self, thumbnail_path: str) -> Optional[QPixmap]:
        """Load thumbnail with caching"""
        return self.load_image(thumbnail_path)  # Same logic for now

    def optimize_text_content(self, content: str, content_type: str = "text") -> dict:
        """Optimize text content với format detection"""
        try:
            # Basic analysis
            lines = content.split("\n")
            words = content.split()

            # Detect actual format if not specified
            if content_type == "text" and content.strip().startswith("<"):
                content_type = "html"

            # Create format-specific preview
            if content_type == "html":
                preview = self._create_html_preview(content)
                plain_text = self._html_to_plain_text(content)
            elif content_type == "rtf":
                preview = self._create_rtf_preview(content)
                plain_text = self._rtf_to_plain_text(content)
            else:
                preview = self._create_smart_preview(content, content_type)
                plain_text = content

            return {
                "preview": preview,
                "plain_text": plain_text[:500],
                "line_count": len(lines),
                "word_count": len(words),
                "char_count": len(content),
                "content_type": content_type,
                "format": content_type,
            }

        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            return {
                "preview": content[:100] + "..." if len(content) > 100 else content,
                "format": "plain",
            }

    def cleanup_orphaned_files(self, active_file_paths: set):
        """Remove files not referenced in database"""
        try:
            cleaned_count = 0

            # Check images directory
            for image_file in self.images_dir.iterdir():
                if str(image_file) not in active_file_paths:
                    image_file.unlink()
                    cleaned_count += 1

            # Check thumbnails directory
            for thumb_file in self.thumbnails_dir.iterdir():
                if str(thumb_file) not in active_file_paths:
                    thumb_file.unlink()
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} orphaned files")

        except Exception as e:
            logger.error(f"Error cleaning up orphaned files: {e}")

    # Private helper methods
    def _pixmap_to_bytes(self, pixmap: QPixmap, format: str, quality: int) -> bytes:
        """Convert QPixmap to bytes with optimization"""
        try:
            # Use QByteArray-backed buffer to avoid dangling data().data()
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)

            # Optimize based on format
            if format.upper() == "JPEG" and pixmap.hasAlphaChannel():
                # Convert ARGB to RGB by compositing over white background
                from PySide6.QtGui import QColor, QPainter

                rgb_pixmap = QPixmap(pixmap.size())
                rgb_pixmap.fill(QColor("white"))
                painter = QPainter(rgb_pixmap)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                rgb_pixmap.save(buffer, format, quality)
            else:
                pixmap.save(buffer, format, quality)

            buffer.close()
            # QByteArray supports data(); ensure a pure bytes object is returned
            return byte_array.data()
        except Exception as e:
            logger.error(f"Error converting pixmap to bytes: {e}")
            return b""

    def _create_optimized_thumbnail(
        self, pixmap: QPixmap, max_size: int = 128
    ) -> QPixmap:
        """Create optimized thumbnail"""
        from PySide6.QtCore import Qt

        return pixmap.scaled(
            max_size,
            max_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _detect_text_type(self, content: str) -> str:
        """Detect type of text content"""
        content_lower = content.lower()

        if content.startswith(("http://", "https://")):
            return "url"
        elif "@" in content and "." in content and len(content.split()) == 1:
            return "email"
        elif content.startswith(("/", "C:\\", "/home", "/usr")):
            return "file_path"
        elif any(
            keyword in content_lower
            for keyword in ["select", "insert", "update", "delete"]
        ):
            return "sql"
        elif any(
            keyword in content_lower
            for keyword in ["def ", "class ", "import ", "function"]
        ):
            return "code"
        elif content.strip().startswith(("{", "[")):
            return "json"
        else:
            return "text"

    def _create_smart_preview(self, content: str, content_type: str) -> str:
        """Create intelligent preview based on content type"""
        max_length = 150

        if content_type == "json":
            try:
                # Pretty format JSON preview
                data = json.loads(content)
                preview = json.dumps(data, indent=2)[:max_length]
                return preview + "..." if len(preview) >= max_length else preview
            except Exception:
                pass

        elif content_type == "code":
            # Take first few meaningful lines
            lines = content.split("\n")[:3]
            preview = "\n".join(lines)
            return (
                preview[:max_length] + "..." if len(preview) > max_length else preview
            )

        # Default text preview
        if len(content) <= max_length:
            return content

        # Smart word boundary breaking
        preview = content[:max_length]
        last_space = preview.rfind(" ")
        if last_space > max_length * 0.7:
            preview = preview[:last_space]

        return preview + "..."

    def _extract_keywords(self, content: str) -> list:
        """Extract searchable keywords from content"""
        # Simple keyword extraction - can be with NLP
        words = content.lower().split()

        # Filter out common words and short words
        stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
        }
        keywords = [
            word.strip('.,!?;:"()[]{}')
            for word in words
            if len(word) > 3 and word.lower() not in stop_words
        ]

        # Return unique keywords (first 10)
        return list(dict.fromkeys(keywords))[:10]

    def _add_to_cache(self, key: str, pixmap: QPixmap):
        """Add pixmap to memory cache with size management (LRU)."""
        # Estimate size (approx RGBA)
        estimated_size = max(0, pixmap.width() * pixmap.height() * 4)

        # If key exists, remove old before re-insert to update order and size
        if key in self.memory_cache:
            old = self.memory_cache.pop(key)
            self.current_cache_size -= max(0, old.width() * old.height() * 4)

        # Evict least-recently used until there is space
        while (
            self.current_cache_size + estimated_size > self.cache_size_limit
            and self.memory_cache
        ):
            evicted_key, evicted_pix = self.memory_cache.popitem(last=False)
            self.current_cache_size -= max(
                0, evicted_pix.width() * evicted_pix.height() * 4
            )
            logger.debug(f"LRU evicted from cache: {evicted_key}")

        # Insert as most-recently used
        self.memory_cache[key] = pixmap
        self.current_cache_size += estimated_size

    def _cleanup_cache(self):
        """Evict items until usage is under 80% of limit."""
        target = int(self.cache_size_limit * 0.8)
        removed = 0
        while self.current_cache_size > target and self.memory_cache:
            _, pix = self.memory_cache.popitem(last=False)
            self.current_cache_size -= max(0, pix.width() * pix.height() * 4)
            removed += 1
        if removed:
            logger.info(
                f"Cache cleaned up, removed {removed} items, size={self.current_cache_size} bytes"
            )

    def clear_cache(self):
        """Clear entire memory cache to free RAM"""
        removed_count = len(self.memory_cache)
        self.memory_cache.clear()
        self.current_cache_size = 0
        logger.info(f"Cleared entire cache, freed {removed_count} items")

    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring"""
        return {
            "cache_size_bytes": self.current_cache_size,
            "cache_limit_bytes": self.cache_size_limit,
            "cache_usage_percent": (self.current_cache_size / self.cache_size_limit)
            * 100,
            "cached_items": len(self.memory_cache),
        }

    def _create_html_preview(self, html: str) -> str:
        """Create safe HTML preview"""
        if len(html) > 300:
            html = html[:300] + "..."

        import re

        html = re.sub(
            r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(
            r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        return html

    def _html_to_plain_text(self, html: str) -> str:
        """Extract plain text from HTML"""
        import re

        text = re.sub(r"<[^>]+>", "", html)
        return re.sub(r"\s+", " ", text).strip()

    def _create_rtf_preview(self, rtf: str) -> str:
        """Create RTF preview"""
        return self._rtf_to_plain_text(rtf)[:200]

    def _rtf_to_plain_text(self, rtf: str) -> str:
        """Convert RTF to plain text"""
        import re

        text = re.sub(r"\\[a-z0-9]+\b|[{}]", "", rtf)
        return re.sub(r"\s+", " ", text).strip()
