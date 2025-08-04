# ===============================================
# FILE: src/utils/enhanced_config.py
# Enhanced configuration with Phase 1 features
# ===============================================

"""
Enhanced configuration management with Phase 1 features
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from appdirs import user_config_dir

logger = logging.getLogger(__name__)


class Config:
    """Enhanced configuration manager with Phase 1 features"""

    DEFAULT_CONFIG = {
        # Basic settings
        "max_items": 50,  # Increased from 25
        "max_text_length": 50000,  # Increased from 10000
        "autostart": False,
        "theme": "dark",
        # Enhanced Phase 1 settings
        "hotkey": "super+c",  # Changed from super+c to match Windows 11
        "search_enabled": True,
        "fuzzy_search_threshold": 0.8,
        "max_search_results": 25,
        # Performance settings
        "cache_size_mb": 50,
        "thumbnail_size": 128,  # Increased from 64
        "image_quality": 95,
        "background_cleanup": True,
        "cleanup_interval_hours": 24,
        # Content management
        "intelligent_deduplication": True,
        "content_analysis": True,
        "auto_categorization": True,
        "preserve_formatting": True,
        # Database settings
        "database_version": "v2",
        "auto_migration": True,
        "backup_before_migration": True,
        "max_database_size_mb": 500,
        # UI settings (for Phase 2)
        "popup_width": 400,
        "popup_height": 500,
        "animation_speed": 150,  # ms
        "show_preview": True,
        "preview_timeout": 2000,  # ms
        # Search settings
        "search_suggestions": True,
        "search_history": True,
        "max_search_suggestions": 5,
        # Privacy settings
        "exclude_passwords": True,
        "exclude_credit_cards": True,
        "exclude_patterns": [],  # List of regex patterns to exclude
    }

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_dir = Path(user_config_dir("ClipboardManager", "YourName"))
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "config_v2.json"

        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """Load enhanced configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    saved_config = json.load(f)

                    # Merge with defaults to ensure all keys exist
                    self.config.update(saved_config)

                    # Handle version migration
                    self._migrate_config_if_needed()

                logger.info(f"Enhanced configuration loaded from {self.config_path}")
            else:
                logger.info("No config file found, using enhanced defaults")
                self.save()  # Create config file with defaults
        except Exception as e:
            logger.error(f"Failed to load enhanced config: {e}")

    def save(self):
        """Save enhanced configuration to file"""
        try:
            # Add metadata
            config_with_metadata = {
                "_metadata": {
                    "version": "2.0",
                    "created": "2025-08-04",  # Current timestamp would be better
                    "phase": "1",
                },
                **self.config,
            }

            with open(self.config_path, "w") as f:
                json.dump(config_with_metadata, f, indent=2)
            logger.info(f"Enhanced configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save enhanced config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with enhanced features"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value with validation"""
        # Validate certain settings
        if key == "max_items" and (value < 10 or value > 1000):
            raise ValueError("max_items must be between 10 and 1000")
        elif key == "cache_size_mb" and (value < 10 or value > 500):
            raise ValueError("cache_size_mb must be between 10 and 500")
        elif key == "fuzzy_search_threshold" and (value < 0.1 or value > 1.0):
            raise ValueError("fuzzy_search_threshold must be between 0.1 and 1.0")

        self.config[key] = value

    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance-related settings"""
        return {
            "cache_size_mb": self.get("cache_size_mb"),
            "thumbnail_size": self.get("thumbnail_size"),
            "image_quality": self.get("image_quality"),
            "background_cleanup": self.get("background_cleanup"),
            "cleanup_interval_hours": self.get("cleanup_interval_hours"),
        }

    def get_search_settings(self) -> Dict[str, Any]:
        """Get search-related settings"""
        return {
            "search_enabled": self.get("search_enabled"),
            "fuzzy_search_threshold": self.get("fuzzy_search_threshold"),
            "max_search_results": self.get("max_search_results"),
            "search_suggestions": self.get("search_suggestions"),
            "max_search_suggestions": self.get("max_search_suggestions"),
        }

    def get_content_settings(self) -> Dict[str, Any]:
        """Get content management settings"""
        return {
            "intelligent_deduplication": self.get("intelligent_deduplication"),
            "content_analysis": self.get("content_analysis"),
            "auto_categorization": self.get("auto_categorization"),
            "preserve_formatting": self.get("preserve_formatting"),
            "exclude_passwords": self.get("exclude_passwords"),
            "exclude_credit_cards": self.get("exclude_credit_cards"),
            "exclude_patterns": self.get("exclude_patterns"),
        }

    def _migrate_config_if_needed(self):
        """Migrate old configuration format to new format"""
        # Check if we need to migrate from old hotkey setting
        if self.config.get("hotkey") == "super+c":
            self.config["hotkey"] = "super+v"
            logger.info("Migrated hotkey from Super+C to Super+V")

        # Add any missing default values
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in self.config:
                self.config[key] = value
                logger.info(f"Added missing config key: {key}")

    def reset_to_defaults(self):
        """Reset configuration to enhanced defaults"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()

    def export_settings(self, export_path: Path) -> bool:
        """Export settings to file"""
        try:
            with open(export_path, "w") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return False

    def import_settings(self, import_path: Path) -> bool:
        """Import settings from file"""
        try:
            with open(import_path, "r") as f:
                imported_config = json.load(f)

            # Validate and merge
            for key, value in imported_config.items():
                if key in self.DEFAULT_CONFIG:
                    self.set(key, value)

            self.save()
            return True
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False
