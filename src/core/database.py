# clipboard_manager/src/core/database.py
"""
SQLite database operations for clipboard history
"""
import json
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional

from appdirs import user_data_dir

logger = logging.getLogger(__name__)


class ClipboardDatabase:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            data_dir = Path(user_data_dir("ClipboardManager", "YourName"))
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "clipboard.db"

        self.db_path = db_path
        self.connection = None
        self.init_database()

    def init_database(self):
        """Initialize database and create tables"""
        try:
            self.connection = sqlite3.connect(
                str(self.db_path), check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row

            cursor = self.connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clipboard_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    preview TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    metadata TEXT
                )
            """
            )

            # Create index for better performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON clipboard_history(timestamp DESC)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_pinned
                ON clipboard_history(is_pinned)
            """
            )

            self.connection.commit()
            logger.info(f"Database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def add_item(
        self,
        content_type: str,
        content: str,
        preview: str = None,
        metadata: dict = None,
    ) -> int:
        """Add new clipboard item"""
        try:
            cursor = self.connection.cursor()

            # Check for duplicates (avoid adding same content consecutively)
            cursor.execute(
                """
                SELECT id FROM clipboard_history
                WHERE content = ? AND content_type = ?
                ORDER BY timestamp DESC LIMIT 1
            """,
                (content, content_type),
            )

            existing = cursor.fetchone()
            if existing:
                # Update timestamp of existing item
                cursor.execute(
                    """
                    UPDATE clipboard_history
                    SET timestamp = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (existing["id"],),
                )
                self.connection.commit()
                return existing["id"]

            # Add new item
            metadata_json = json.dumps(metadata) if metadata else None
            cursor.execute(
                """
                INSERT INTO clipboard_history
                (content_type, content, preview, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (content_type, content, preview, metadata_json),
            )

            item_id = cursor.lastrowid
            self.connection.commit()

            # Clean up old items (keep only recent ones)
            self.cleanup_old_items()

            return item_id

        except Exception as e:
            logger.error(f"Failed to add clipboard item: {e}")
            return -1

    def get_items(self, limit: int = 25, include_pinned: bool = True) -> List[dict]:
        """Get clipboard items with optional limit"""
        try:
            cursor = self.connection.cursor()

            if include_pinned:
                # Get pinned items first, then recent items
                cursor.execute(
                    """
                    SELECT * FROM clipboard_history
                    WHERE is_pinned = TRUE
                    ORDER BY timestamp DESC
                """
                )
                pinned_items = [dict(row) for row in cursor.fetchall()]

                remaining_limit = limit - len(pinned_items)
                cursor.execute(
                    """
                    SELECT * FROM clipboard_history
                    WHERE is_pinned = FALSE
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (remaining_limit,),
                )
                recent_items = [dict(row) for row in cursor.fetchall()]

                return pinned_items + recent_items
            else:
                cursor.execute(
                    """
                    SELECT * FROM clipboard_history
                    ORDER BY is_pinned DESC, timestamp DESC
                    LIMIT ?
                """,
                    (limit,),
                )
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get clipboard items: {e}")
            return []

    def pin_item(self, item_id: int, pinned: bool = True) -> bool:
        """Pin or unpin a clipboard item"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE clipboard_history
                SET is_pinned = ?
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
        """Delete a clipboard item"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                DELETE FROM clipboard_history
                WHERE id = ?
            """,
                (item_id,),
            )

            self.connection.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            return False

    def clear_history(self, keep_pinned: bool = True) -> bool:
        """Clear clipboard history"""
        try:
            cursor = self.connection.cursor()

            if keep_pinned:
                cursor.execute(
                    """
                    DELETE FROM clipboard_history
                    WHERE is_pinned = FALSE
                """
                )
            else:
                cursor.execute("DELETE FROM clipboard_history")

            self.connection.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return False

    def cleanup_old_items(self, max_items: int = 100):
        """Remove old unpinned items beyond limit"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                DELETE FROM clipboard_history
                WHERE is_pinned = FALSE
                AND id NOT IN (
                    SELECT id FROM clipboard_history
                    WHERE is_pinned = FALSE
                    ORDER BY timestamp DESC
                    LIMIT ?
                )
            """,
                (max_items,),
            )

            self.connection.commit()

        except Exception as e:
            logger.error(f"Failed to cleanup old items: {e}")

    def get_stats(self) -> dict:
        """Get database statistics"""
        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT COUNT(*) as total FROM clipboard_history")
            total = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) as pinned FROM clipboard_history "
                "WHERE is_pinned = TRUE"
            )
            pinned = cursor.fetchone()["pinned"]

            return {
                "total_items": total,
                "pinned_items": pinned,
                "regular_items": total - pinned,
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total_items": 0, "pinned_items": 0, "regular_items": 0}

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
