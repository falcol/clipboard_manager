# ===============================================
# FILE: src/core/enhanced_database.py
# New enhanced database with optimized schema
# ===============================================

"""
Enhanced SQLite database with optimized schema for clipboard history
Replaces the old database.py file
"""
import hashlib
import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from appdirs import user_data_dir

logger = logging.getLogger(__name__)


class EnhancedClipboardDatabase:
    """Enhanced database with optimized schema and performance"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            data_dir = Path(user_data_dir("ClipboardManager", "YourName"))
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "clipboard_v2.db"

        self.db_path = db_path
        self.data_dir = db_path.parent
        self.images_dir = self.data_dir / "images"
        self.thumbnails_dir = self.data_dir / "thumbnails"

        # Create directories
        self.images_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)

        self.connection = None
        self.init_database()

    def init_database(self):
        """Initialize enhanced database schema"""
        try:
            self.connection = sqlite3.connect(
                str(self.db_path), check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row

            cursor = self.connection.cursor()

            # Main clipboard items table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clipboard_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL,
                    content_hash TEXT UNIQUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    access_count INTEGER DEFAULT 0,
                    metadata TEXT,
                    search_content TEXT -- For full-text search
                )
            """
            )

            # Text content table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS text_content (
                    id INTEGER PRIMARY KEY,
                    content TEXT NOT NULL,
                    preview TEXT,
                    char_count INTEGER,
                    word_count INTEGER,
                    FOREIGN KEY (id) REFERENCES clipboard_items (id) ON DELETE CASCADE
                )
            """
            )

            # Image content table (file-based storage)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS image_content (
                    id INTEGER PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    width INTEGER,
                    height INTEGER,
                    file_size INTEGER,
                    format TEXT,
                    FOREIGN KEY (id) REFERENCES clipboard_items (id) ON DELETE CASCADE
                )
            """
            )

            # Create indexes for better performance
            # flake8: noqa: E501
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON clipboard_items(timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_pinned ON clipboard_items(is_pinned DESC)",
                "CREATE INDEX IF NOT EXISTS idx_access_count ON clipboard_items(access_count DESC)",
                "CREATE INDEX IF NOT EXISTS idx_content_hash ON clipboard_items(content_hash)",
                "CREATE INDEX IF NOT EXISTS idx_search_content ON clipboard_items(search_content)",
            ]

            for index_sql in indexes:
                cursor.execute(index_sql)

            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")

            self.connection.commit()
            logger.info(f"Enhanced database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize enhanced database: {e}")
            raise

    def generate_content_hash(self, content: str, content_type: str) -> str:
        """Generate unique hash for content deduplication"""
        combined = f"{content_type}:{content}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def add_text_item(self, content: str, metadata: Optional[dict] = None) -> int:
        """Add text clipboard item with enhanced processing"""
        if self.connection is None:
            logger.error("Database connection not initialized")
            return -1

        try:
            # Generate content hash for deduplication
            content_hash = self.generate_content_hash(content, "text")

            # Check for existing item
            existing_id = self._get_existing_item_id(content_hash)
            if existing_id:
                # Update access count and timestamp
                self._update_item_access(existing_id)
                return existing_id

            cursor = self.connection.cursor()

            # Create preview (first 100 chars, smart word break)
            preview = self._create_text_preview(content)

            # Generate search content (cleaned text for searching)
            search_content = self._generate_search_content(content)

            # Calculate text statistics
            char_count = len(content)
            word_count = len(content.split())

            # Insert main item
            cursor.execute(
                """
                INSERT INTO clipboard_items
                (content_type, content_hash, metadata, search_content)
                VALUES (?, ?, ?, ?)
            """,
                (
                    "text",
                    content_hash,
                    json.dumps(metadata) if metadata else None,
                    search_content,
                ),
            )

            item_id = cursor.lastrowid

            # Insert text content
            cursor.execute(
                """
                INSERT INTO text_content
                (id, content, preview, char_count, word_count)
                VALUES (?, ?, ?, ?, ?)
            """,
                (item_id, content, preview, char_count, word_count),
            )

            self.connection.commit()

            # Cleanup old items if needed
            self._cleanup_old_items()

            logger.debug(f"Added text item {item_id} ({char_count} chars)")
            return item_id if item_id else -1

        except Exception as e:
            logger.error(f"Failed to add text item: {e}")
            self.connection.rollback()
            return -1

    def add_image_item(
        self,
        image_data: bytes,
        thumbnail_data: bytes,
        width: int,
        height: int,
        image_format: str = "PNG",
        metadata: Optional[dict] = None,
    ) -> int:
        """Add image clipboard item with file-based storage"""
        if self.connection is None:
            logger.error("Database connection not initialized")
            return -1

        try:
            # Generate content hash
            content_hash = self.generate_content_hash(
                hashlib.sha256(image_data).hexdigest(), "image"
            )

            # Check for existing item
            existing_id = self._get_existing_item_id(content_hash)
            if existing_id:
                self._update_item_access(existing_id)
                return existing_id

            cursor = self.connection.cursor()

            # Generate file paths
            image_filename = f"{content_hash}.{image_format.lower()}"
            thumbnail_filename = f"{content_hash}_thumb.{image_format.lower()}"

            image_path = self.images_dir / image_filename
            thumbnail_path = self.thumbnails_dir / thumbnail_filename

            # Save image files
            with open(image_path, "wb") as f:
                f.write(image_data)
            with open(thumbnail_path, "wb") as f:
                f.write(thumbnail_data)

            # Generate search content for images
            search_content = f"image {image_format.lower()} {width}x{height}"

            # Insert main item
            cursor.execute(
                """
                INSERT INTO clipboard_items
                (content_type, content_hash, metadata, search_content)
                VALUES (?, ?, ?, ?)
            """,
                (
                    "image",
                    content_hash,
                    json.dumps(metadata) if metadata else None,
                    search_content,
                ),
            )

            item_id = cursor.lastrowid

            # Insert image content
            cursor.execute(
                """
                INSERT INTO image_content
                (id, file_path, thumbnail_path, width, height, file_size, format)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    item_id,
                    str(image_path),
                    str(thumbnail_path),
                    width,
                    height,
                    len(image_data),
                    image_format,
                ),
            )

            self.connection.commit()

            # Cleanup old items
            self._cleanup_old_items()

            logger.debug(
                f"Added image item {item_id} ({width}x{height}, {len(image_data)} bytes)"
            )
            return item_id if item_id else -1

        except Exception as e:
            logger.error(f"Failed to add image item: {e}")
            self.connection.rollback()
            return -1

    def get_items(
        self,
        limit: int = 25,
        include_pinned: bool = True,
        search_query: Optional[str] = None,
    ) -> List[Dict]:
        """Get clipboard items with enhanced filtering and search"""
        if self.connection is None:
            logger.error("Database connection not initialized")
            return []

        try:
            cursor = self.connection.cursor()

            base_query = """
                SELECT ci.*,
                       tc.content as text_content, tc.preview as text_preview,
                       tc.char_count, tc.word_count,
                       ic.file_path, ic.thumbnail_path, ic.width, ic.height,
                       ic.file_size, ic.format
                FROM clipboard_items ci
                LEFT JOIN text_content tc ON ci.id = tc.id
                LEFT JOIN image_content ic ON ci.id = ic.id
            """

            conditions = []
            params = []

            # Add search filter
            if search_query:
                conditions.append("ci.search_content LIKE ?")
                params.append(f"%{search_query.lower()}%")

            # Build WHERE clause
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)

            # Order by pinned first, then by timestamp
            base_query += " ORDER BY ci.is_pinned DESC, ci.timestamp DESC"

            if limit:
                base_query += " LIMIT ?"
                params.append(limit)

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            items = []
            for row in rows:
                item = dict(row)

                # Add computed fields
                if item["content_type"] == "text":
                    item["content"] = item["text_content"]
                    item["preview"] = item["text_preview"]
                elif item["content_type"] == "image":
                    item["content"] = item["file_path"]  # Path to image file
                    item["preview"] = item["thumbnail_path"]  # Path to thumbnail

                # Parse metadata
                if item["metadata"]:
                    item["metadata"] = json.loads(item["metadata"])

                items.append(item)

            return items

        except Exception as e:
            logger.error(f"Failed to get items: {e}")
            return []

    def search_items(self, query: str, limit: int = 25) -> List[Dict]:
        """Advanced search with multiple strategies"""
        if not query:
            return self.get_items(limit=limit)

        # Use the enhanced get_items with search
        results = self.get_items(limit=limit, search_query=query)

        # TODO: Add fuzzy matching and content-based search here
        # This is where we can implement more advanced search algorithms

        return results

    def pin_item(self, item_id: int, pinned: bool = True) -> bool:
        """Pin or unpin a clipboard item"""
        if self.connection is None:
            logger.error("Database connection not initialized")
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE clipboard_items
                SET is_pinned = ?, timestamp = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (pinned, item_id),
            )

            self.connection.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to pin item {item_id}: {e}")
            return False

    def delete_item(self, item_id: int) -> bool:
        """Delete a clipboard item and associated files"""
        if self.connection is None:
            logger.error("Database connection not initialized")
            return False

        try:
            cursor = self.connection.cursor()

            # Get file paths before deletion
            cursor.execute(
                """
                SELECT file_path, thumbnail_path
                FROM image_content
                WHERE id = ?
            """,
                (item_id,),
            )

            image_row = cursor.fetchone()

            # Delete from database (cascades to content tables)
            cursor.execute("DELETE FROM clipboard_items WHERE id = ?", (item_id,))

            # Delete associated files
            if image_row:
                for file_path in [image_row["file_path"], image_row["thumbnail_path"]]:
                    if file_path and Path(file_path).exists():
                        Path(file_path).unlink()

            self.connection.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            return False

    def clear_history(self, keep_pinned: bool = True) -> bool:
        """Clear clipboard history with file cleanup"""
        if self.connection is None:
            logger.error("Database connection not initialized")
            return False

        try:
            cursor = self.connection.cursor()

            # Get file paths for items to be deleted
            if keep_pinned:
                cursor.execute(
                    """
                    SELECT ic.file_path, ic.thumbnail_path
                    FROM image_content ic
                    JOIN clipboard_items ci ON ic.id = ci.id
                    WHERE ci.is_pinned = FALSE
                """
                )
            else:
                cursor.execute("SELECT file_path, thumbnail_path FROM image_content")

            file_paths = cursor.fetchall()

            # Delete from database
            if keep_pinned:
                cursor.execute("DELETE FROM clipboard_items WHERE is_pinned = FALSE")
            else:
                cursor.execute("DELETE FROM clipboard_items")

            # Delete associated files
            for row in file_paths:
                for file_path in [row["file_path"], row["thumbnail_path"]]:
                    if file_path and Path(file_path).exists():
                        Path(file_path).unlink()

            self.connection.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return False

    # Private helper methods
    def _get_existing_item_id(self, content_hash: str) -> Optional[int]:
        """Check if item with content hash already exists"""
        if self.connection is None:
            logger.error("Database connection not initialized")
            return None

        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id FROM clipboard_items
            WHERE content_hash = ?
        """,
            (content_hash,),
        )

        row = cursor.fetchone()
        return row["id"] if row else None

    def _update_item_access(self, item_id: int):
        """Update access count and timestamp for existing item"""
        if self.connection is None:
            logger.error("Database connection not initialized")
            return

        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE clipboard_items
            SET access_count = access_count + 1,
                timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (item_id,),
        )
        self.connection.commit()

    def _create_text_preview(self, text: str, max_length: int = 100) -> str:
        """Create intelligent text preview"""
        if len(text) <= max_length:
            return text

        # Try to break at word boundary
        preview = text[:max_length]
        last_space = preview.rfind(" ")
        last_newline = preview.rfind("\n")

        # Break at the closest word/line boundary
        break_point = max(last_space, last_newline)
        if break_point > max_length * 0.7:
            preview = preview[:break_point]

        return preview.strip() + "..."

    def _generate_search_content(self, content: str) -> str:
        """Generate searchable content (lowercase, cleaned)"""
        # Simple implementation - can be enhanced with stemming, etc.
        return content.lower().strip()

    def _cleanup_old_items(self, max_items: int = 100):
        """Clean up old unpinned items"""
        if self.connection is None:
            logger.error("Database connection not initialized")
            return

        try:
            cursor = self.connection.cursor()

            # Get items to delete (old unpinned items beyond limit)
            cursor.execute(
                """
                SELECT ci.id, ic.file_path, ic.thumbnail_path
                FROM clipboard_items ci
                LEFT JOIN image_content ic ON ci.id = ic.id
                WHERE ci.is_pinned = FALSE
                ORDER BY ci.access_count ASC, ci.timestamp ASC
                LIMIT -1 OFFSET ?
            """,
                (max_items,),
            )

            items_to_delete = cursor.fetchall()

            # Delete old items
            for item in items_to_delete:
                # Delete files
                if item["file_path"] and Path(item["file_path"]).exists():
                    Path(item["file_path"]).unlink()
                if item["thumbnail_path"] and Path(item["thumbnail_path"]).exists():
                    Path(item["thumbnail_path"]).unlink()

                # Delete from database
                cursor.execute(
                    "DELETE FROM clipboard_items WHERE id = ?", (item["id"],)
                )

            if items_to_delete:
                self.connection.commit()
                logger.info(f"Cleaned up {len(items_to_delete)} old items")

        except Exception as e:
            logger.error(f"Failed to cleanup old items: {e}")

    def get_stats(self) -> Dict:
        """Get enhanced database statistics"""
        if self.connection is None:
            logger.error("Database connection not initialized")
            return {}

        try:
            cursor = self.connection.cursor()

            # Basic counts
            cursor.execute("SELECT COUNT(*) as total FROM clipboard_items")
            total = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) as pinned FROM clipboard_items WHERE is_pinned = TRUE"
            )
            pinned = cursor.fetchone()["pinned"]

            # Content type breakdown
            cursor.execute(
                """
                SELECT content_type, COUNT(*) as count
                FROM clipboard_items
                GROUP BY content_type
            """
            )
            content_types = {
                row["content_type"]: row["count"] for row in cursor.fetchall()
            }

            # Storage usage
            cursor.execute("SELECT SUM(file_size) as total_size FROM image_content")
            image_size = cursor.fetchone()["total_size"] or 0

            return {
                "total_items": total,
                "pinned_items": pinned,
                "regular_items": total - pinned,
                "content_types": content_types,
                "image_storage_bytes": image_size,
                "database_size_bytes": (
                    self.db_path.stat().st_size if self.db_path.exists() else 0
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total_items": 0, "pinned_items": 0, "regular_items": 0}

    def migrate_from_old_database(self, old_db_path: Path) -> bool:
        """Migrate data from old database format"""
        try:
            # Implementation for migrating from old database
            # This would read the old format and convert to new format
            logger.info("Database migration not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Enhanced database connection closed")
