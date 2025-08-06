# ===============================================
# FILE: src/core/migrations.py
# Simple database schema migration system
# ===============================================

"""
Simple schema migration system for clipboard database
Ensures database structure is up-to-date without data loss
"""
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from appdirs import user_data_dir

logger = logging.getLogger(__name__)


class DatabaseMigrations:
    """Simple schema migration manager for single database"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            data_dir = Path(user_data_dir("ClipboardManager", "B1Corp"))
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "clipboard.db"

        self.db_path = db_path
        self.current_version = 3  # Increment when schema changes

    def needs_migration(self) -> bool:
        """Check if database needs schema migration"""
        if not self.db_path.exists():
            return True

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA user_version")
            db_version = cursor.fetchone()[0]
            conn.close()

            return db_version < self.current_version
        except Exception as e:
            logger.error(f"Error checking database version: {e}")
            return True

    def migrate(self) -> bool:
        """Run all necessary migrations"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get current version
            cursor.execute("PRAGMA user_version")
            current_version = cursor.fetchone()[0]

            logger.info(f"Current database version: {current_version}")
            logger.info(f"Target database version: {self.current_version}")

            # Run migrations step by step
            if current_version < 1:
                self._migrate_to_v1(cursor)
                current_version = 1

            if current_version < 2:
                self._migrate_to_v2(cursor)
                current_version = 2

            if current_version < 3:
                self._migrate_to_v3(cursor)
                current_version = 3

            # Update version
            cursor.execute(f"PRAGMA user_version = {self.current_version}")
            conn.commit()
            conn.close()

            logger.info("Database migration completed successfully")
            return True

        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            if "conn" in locals():
                conn.rollback()
                conn.close()
            return False

    def _migrate_to_v1(self, cursor: sqlite3.Cursor):
        """Create initial database schema"""
        logger.info("Running migration to version 1: Create base tables")

        # Main clipboard items table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clipboard_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL,
                content_hash TEXT UNIQUE,
                timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                is_pinned BOOLEAN DEFAULT FALSE,
                access_count INTEGER DEFAULT 0,
                metadata TEXT,
                search_content TEXT
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

        # Image content table
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

        # Create basic indexes
        self._create_indexes(cursor)

    def _migrate_to_v2(self, cursor: sqlite3.Cursor):
        """Add rich text support"""
        logger.info("Running migration to version 2: Add rich text support")

        # Add columns for rich text (if not exists)
        self._add_column_if_not_exists(cursor, "text_content", "html_content", "TEXT")
        self._add_column_if_not_exists(cursor, "text_content", "format", "TEXT")

    def _migrate_to_v3(self, cursor: sqlite3.Cursor):
        """Future schema changes"""
        logger.info("Running migration to version 3: Future enhancements")

        # Add any future schema changes here
        # Example: new columns, tables, indexes

    def _add_column_if_not_exists(
        self, cursor: sqlite3.Cursor, table: str, column: str, column_type: str
    ):
        """Add column to table if it doesn't exist"""
        try:
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]

            if column not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                logger.info(f"Added column {column} to table {table}")
            else:
                logger.debug(f"Column {column} already exists in table {table}")

        except Exception as e:
            logger.error(f"Error adding column {column} to {table}: {e}")

    def _create_indexes(self, cursor: sqlite3.Cursor):
        """Create database indexes for performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON clipboard_items(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_pinned ON clipboard_items(is_pinned DESC)",
            "CREATE INDEX IF NOT EXISTS idx_access_count ON clipboard_items(access_count DESC)",
            "CREATE INDEX IF NOT EXISTS idx_content_hash ON clipboard_items(content_hash)",
            "CREATE INDEX IF NOT EXISTS idx_search_content ON clipboard_items(search_content)",
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"Error creating index: {e}")

    def get_database_info(self) -> dict:
        """Get current database information"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get version
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]

            # Get table count
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            # Get total items
            cursor.execute("SELECT COUNT(*) FROM clipboard_items")
            item_count = cursor.fetchone()[0]

            conn.close()

            return {
                "version": version,
                "table_count": table_count,
                "item_count": item_count,
                "file_path": str(self.db_path),
                "file_size": (
                    self.db_path.stat().st_size if self.db_path.exists() else 0
                ),
            }

        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {"error": str(e)}
