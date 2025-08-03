# ===============================================
# FILE: src/main_enhanced.py
# Enhanced main entry point using new architecture
# ===============================================

#!/usr/bin/env python3
"""
Enhanced main entry point for Clipboard Manager with Phase 1 improvements
"""
import logging
import os
import signal
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.clipboard_watcher import EnhancedClipboardWatcher
from core.content_manager import ContentManager

# Import enhanced components
from core.database import EnhancedClipboardDatabase
from core.hotkey_manager import HotkeyManager
from core.migration_manager import MigrationManager
from core.search_engine import SearchEngine

# Import existing UI components (will be enhanced in Phase 2)
from ui.popup_window import PopupWindow
from ui.settings_window import SettingsWindow
from ui.system_tray import SystemTray
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_qt_environment():
    """Setup Qt environment with fallback options"""
    # Set Qt platform plugin path if needed
    qt_plugin_path = os.environ.get("QT_PLUGIN_PATH")
    if not qt_plugin_path:
        possible_paths = [
            "/usr/lib/x86_64-linux-gnu/qt6/plugins",
            "/usr/lib/qt6/plugins",
            "/usr/local/lib/qt6/plugins",
            str(Path.home() / ".local/lib/qt6/plugins"),
        ]

        for path in possible_paths:
            if Path(path).exists():
                os.environ["QT_PLUGIN_PATH"] = path
                logger.info(f"Set QT_PLUGIN_PATH to {path}")
                break

    # Set fallback platform if xcb fails
    os.environ["QT_QPA_PLATFORM"] = "xcb:fallback=wayland"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"


class EnhancedClipboardManager:
    """Enhanced Clipboard Manager with Phase 1 improvements"""

    def __init__(self):
        # Setup Qt environment
        setup_qt_environment()

        try:
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)
        except Exception as e:
            logger.error(f"Failed to create QApplication: {e}")
            self._handle_qt_error(e)

        # Initialize configuration
        self.config = Config()

        # Initialize data directory and check for migration
        self.data_dir = Path(self.config.config_path.parent)
        self.old_db_path = self.data_dir / "clipboard.db"
        self.new_db_path = self.data_dir / "clipboard_v2.db"

        # Handle database migration if needed
        self._handle_migration()

        # Initialize enhanced core components
        self.database = EnhancedClipboardDatabase(self.new_db_path)
        self.content_manager = ContentManager(self.data_dir)
        self.search_engine = SearchEngine(self.database)

        # Initialize enhanced clipboard watcher
        self.clipboard_watcher = EnhancedClipboardWatcher(
            self.database, self.content_manager, self.config
        )

        # Initialize UI components (existing for now, will be enhanced in Phase 2)
        self.popup_window = PopupWindow(self.database, self.config)
        self.settings_window = SettingsWindow(self.config)
        self.system_tray = SystemTray(self.popup_window, self.settings_window)

        # Update hotkey to Super+V (Windows 11 style)
        self.hotkey_manager = HotkeyManager(self.show_popup)
        self.hotkey_manager.hotkey_combination = (
            {
                self.hotkey_manager.hotkey_combination.pop(),  # Remove old key
                self.hotkey_manager.keyboard.KeyCode.from_char("v"),  # Add 'v' key
            }
            if hasattr(self.hotkey_manager, "keyboard")
            else self.hotkey_manager.hotkey_combination
        )

        # Setup connections
        self.setup_connections()

        # Check system tray availability
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(
                None, "System Tray", "System tray is not available on this system."
            )
            sys.exit(1)

    def _handle_qt_error(self, error):
        """Handle Qt initialization errors"""
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        try:
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)
            logger.warning("Using offscreen platform as fallback")
        except Exception as e2:
            logger.error(f"Failed to create QApplication with offscreen: {e2}")
            QMessageBox.critical(
                None,
                "Qt Error",
                f"Failed to initialize Qt application:\n{error}\n\n{e2}\n\n"
                "Please ensure Qt6 and XCB libraries are installed.",
            )
            sys.exit(1)

    def _handle_migration(self):
        """Handle database migration if needed"""
        if self.old_db_path.exists() and not self.new_db_path.exists():
            logger.info("Detected old database format, starting migration...")

            migration_manager = MigrationManager(
                self.old_db_path, self.new_db_path, self.data_dir
            )

            if migration_manager.migrate():
                logger.info("Database migration completed successfully")
            else:
                logger.error("Database migration failed, using new database")

    def setup_connections(self):
        """Setup signal connections between components"""
        self.settings_window.settings_changed.connect(self.on_settings_changed)
        self.system_tray.quit_requested.connect(self.quit_application)

        # Connect enhanced clipboard watcher
        self.clipboard_watcher.content_changed.connect(self.on_content_changed)

    def on_content_changed(self, content_type: str, item_data: dict):
        """Handle new clipboard content with enhanced features"""
        logger.info(f"New {content_type} content detected: {item_data.get('id')}")

        # Future: Add intelligent notifications, auto-categorization, etc.
        # For now, this just logs the event

    def show_popup(self):
        """Show the clipboard popup window"""
        # For Phase 1, we still use the existing popup
        # In Phase 2, this will be replaced with enhanced Windows 11-style popup
        self.popup_window.show_at_cursor()

    def on_settings_changed(self):
        """Handle settings changes"""
        self.clipboard_watcher.update_config()
        self.popup_window.update_config()

    def start(self):
        """Start the enhanced application"""
        try:
            # Start enhanced clipboard monitoring
            self.clipboard_watcher.start()

            # Start hotkey listener
            self.hotkey_manager.start()

            # Show system tray
            self.system_tray.show()

            logger.info("Enhanced Clipboard Manager started successfully")

            # Setup graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            return self.app.exec()

        except Exception as e:
            logger.error(f"Failed to start enhanced application: {e}")
            return 1

    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.quit_application()

    def quit_application(self):
        """Quit the application gracefully"""
        try:
            self.hotkey_manager.stop()
            self.clipboard_watcher.stop()

            # Cleanup orphaned files
            active_file_paths = set()
            items = self.database.get_items(limit=1000)  # Get all items
            for item in items:
                if item.get("file_path"):
                    active_file_paths.add(item["file_path"])
                if item.get("thumbnail_path"):
                    active_file_paths.add(item["thumbnail_path"])

            self.content_manager.cleanup_orphaned_files(active_file_paths)

            self.database.close()
            self.app.quit()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Enhanced main function"""
    try:
        manager = EnhancedClipboardManager()
        return manager.start()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
