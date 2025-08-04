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
from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QPixmap

logger = logging.getLogger(__name__)


class ContentManager:
    """Intelligent content storage and retrieval manager"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.images_dir = data_dir / "images"
        self.thumbnails_dir = data_dir / "thumbnails"
        self.cache_dir = data_dir / "cache"

        # Create directories
        for directory in [self.images_dir, self.thumbnails_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # In-memory cache for frequently accessed items
        self.memory_cache = {}
        self.cache_size_limit = 50 * 1024 * 1024  # 50MB
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
                return self.memory_cache[cache_key]

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

    def optimize_text_content(self, content: str) -> dict:
        """Optimize and analyze text content"""
        try:
            # Basic text analysis
            lines = content.split("\n")
            words = content.split()

            # Detect content type
            content_type = self._detect_text_type(content)

            # Create optimized preview
            preview = self._create_smart_preview(content, content_type)

            # Generate search keywords
            keywords = self._extract_keywords(content)

            return {
                "preview": preview,
                "line_count": len(lines),
                "word_count": len(words),
                "char_count": len(content),
                "content_type": content_type,
                "keywords": keywords,
                "has_urls": "http" in content.lower(),
                "has_emails": "@" in content and "." in content,
            }

        except Exception as e:
            logger.error(f"Error optimizing text content: {e}")
            # flake8: noqa: E501
            return {"preview": f"{content[:100]}..." if len(content) > 100 else content}

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
        byte_array = QBuffer()
        byte_array.open(QIODevice.OpenModeFlag.WriteOnly)

        # Optimize based on format
        if format.upper() == "JPEG" and pixmap.hasAlphaChannel():
            # Convert to RGB for JPEG (no alpha)
            rgb_pixmap = QPixmap(pixmap.size())
            rgb_pixmap.fill("white")
            # Composite over white background
            # (This is a simplified version - full implementation would use QPainter)

        pixmap.save(byte_array, format, quality)
        return byte_array.data().data()

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
        # Simple keyword extraction - can be enhanced with NLP
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
        """Add pixmap to memory cache with size management"""
        # Estimate size (rough calculation)
        estimated_size = pixmap.width() * pixmap.height() * 4  # RGBA

        # Check if we have space
        if self.current_cache_size + estimated_size > self.cache_size_limit:
            self._cleanup_cache()

        # Add to cache
        self.memory_cache[key] = pixmap
        self.current_cache_size += estimated_size

    def _cleanup_cache(self):
        """Clean up memory cache (simple LRU-like strategy)"""
        # For now, just clear half the cache
        # A proper implementation would track access times
        items_to_remove = len(self.memory_cache) // 2

        keys_to_remove = list(self.memory_cache.keys())[:items_to_remove]
        for key in keys_to_remove:
            del self.memory_cache[key]

        # Recalculate cache size
        self.current_cache_size = self.current_cache_size // 2
        logger.info(f"Cache cleaned up, removed {items_to_remove} items")
