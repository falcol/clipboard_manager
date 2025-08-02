# clipboard_manager/src/utils/config.py
"""
Configuration management
"""
import json
import logging
from pathlib import Path
from typing import Any

from appdirs import user_config_dir

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager"""

    DEFAULT_CONFIG = {
        "max_items": 25,
        "max_text_length": 10000,
        "autostart": False,
        "hotkey": "super+v",
        "theme": "dark",
    }

    def __init__(self, config_path: Path = None):
        if config_path is None:
            config_dir = Path(user_config_dir("ClipboardManager", "YourName"))
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "config.json"

        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.info("No config file found, using defaults")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
