# ===============================================
# FILE: src/core/migration_manager.py
# Database migration manager
# ===============================================

"""
Database migration manager for upgrading from old schema
"""
import json
import logging
import shutil
import sqlite3
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class MigrationManager:
    """Handle database migrations and upgrades"""

    def __init__(self, old_db_path: Path, new_db_path: Path, data_dir: Path):
        self.old_db_path = old_db_path
        self.new_db_path = new_db_path
        self.data_dir = data_dir

    def needs_migration(self) -> bool:
        """Check if migration is needed"""
        return self.old_db_path.exists() and not self.new_db_path.exists()

    def migrate(self) -> bool:
        """Perform full migration from old to new database"""
        try:
            logger.info("Starting database migration...")

            # Create backup
            if not self._create_backup():
                return False

            # Import required classes
            from core.content_manager import ContentManager
            from core.database import EnhancedClipboardDatabase

            # Initialize new database and content manager
            new_db = EnhancedClipboardDatabase(self.new_db_path)
            content_manager = ContentManager(self.data_dir)

            # Get old data
            old_items = self._get_old_items()

            migrated_count = 0
            failed_count = 0

            for item in old_items:
                try:
                    if self._migrate_item(item, new_db, content_manager):
                        migrated_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(
                        f"Error migrating item {item.get('id', 'unknown')}: {e}"
                    )
                    failed_count += 1

            new_db.close()

            logger.info(
                f"Migration completed: {migrated_count} items migrated, {failed_count} failed"
            )

            # Rename old database
            if migrated_count > 0:
                old_backup_path = self.old_db_path.with_suffix(".db.old")
                self.old_db_path.rename(old_backup_path)
                logger.info(f"Old database backed up to {old_backup_path}")

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def _create_backup(self) -> bool:
        """Create backup of old database"""
        try:
            backup_path = self.old_db_path.with_suffix(".db.backup")
            shutil.copy2(self.old_db_path, backup_path)
            logger.info(f"Created backup at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def _get_old_items(self) -> List[Dict]:
        """Get all items from old database"""
        try:
            conn = sqlite3.connect(str(self.old_db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM clipboard_history
                ORDER BY timestamp DESC
            """
            )

            items = [dict(row) for row in cursor.fetchall()]
            conn.close()

            logger.info(f"Found {len(items)} items in old database")
            return items

        except Exception as e:
            logger.error(f"Error reading old database: {e}")
            return []

    def _migrate_item(self, old_item: Dict, new_db, content_manager) -> bool:
        """Migrate a single item to new format"""
        try:
            content_type = old_item.get("content_type", "text")

            if content_type == "text":
                return self._migrate_text_item(old_item, new_db, content_manager)
            elif content_type == "image":
                return self._migrate_image_item(old_item, new_db, content_manager)
            else:
                logger.warning(f"Unknown content type: {content_type}")
                return False

        except Exception as e:
            logger.error(f"Error migrating item: {e}")
            return False

    def _migrate_text_item(self, old_item: Dict, new_db, content_manager) -> bool:
        """Migrate text item"""
        try:
            content = old_item.get("content", "")
            if not content:
                return False

            # Parse old metadata
            old_metadata = {}
            if old_item.get("metadata"):
                try:
                    old_metadata = json.loads(old_item["metadata"])
                except Exception:
                    pass

            # Create new metadata with migration info
            new_metadata = {
                "migrated_from": "v1",
                "original_id": old_item.get("id"),
                "migration_date": "2024-01-01",  # Current date would be better
                **old_metadata,
            }

            # Add text item
            item_id = new_db.add_text_item(content=content, metadata=new_metadata)

            if item_id > 0:
                # Set pinned status and timestamp
                if old_item.get("is_pinned"):
                    new_db.pin_item(item_id, True)

                return True

            return False

        except Exception as e:
            logger.error(f"Error migrating text item: {e}")
            return False

    def _migrate_image_item(self, old_item: Dict, new_db, content_manager) -> bool:
        """Migrate image item"""
        try:
            # Old format stored images as base64 in content field
            import base64

            # from PySide6.QtGui import QPixmap
            from utils.image_utils import ImageUtils

            content = old_item.get("content", "")
            if not content:
                return False

            # Decode base64 image
            try:
                image_data = base64.b64decode(content)
                pixmap = ImageUtils.bytes_to_pixmap(image_data)

                if pixmap.isNull():
                    logger.warning("Failed to decode image data")
                    return False

            except Exception as e:
                logger.error(f"Error decoding image: {e}")
                return False

            # Use content manager to store optimized image
            image_path, thumbnail_path, optimized_image_data, thumbnail_data = (
                content_manager.store_image(pixmap)
            )

            if not image_path:
                return False

            # Parse old metadata
            old_metadata = {}
            if old_item.get("metadata"):
                try:
                    old_metadata = json.loads(old_item["metadata"])
                except Exception:
                    pass

            # Create new metadata
            new_metadata = {
                "migrated_from": "v1",
                "original_id": old_item.get("id"),
                "migration_date": "2024-01-01",
                "original_base64_size": len(content),
                "optimized_size": len(optimized_image_data),
                **old_metadata,
            }

            # Add image item
            item_id = new_db.add_image_item(
                image_data=optimized_image_data,
                thumbnail_data=thumbnail_data,
                width=pixmap.width(),
                height=pixmap.height(),
                image_format="PNG",
                metadata=new_metadata,
            )

            if item_id > 0:
                # Set pinned status
                if old_item.get("is_pinned"):
                    new_db.pin_item(item_id, True)

                return True

            return False

        except Exception as e:
            logger.error(f"Error migrating image item: {e}")
            return False
