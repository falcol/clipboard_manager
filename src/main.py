# clipboard_manager/src/main.py
#!/usr/bin/env python3
"""
Enhanced main entry point for Clipboard Manager with modern UI and auto-hide focus
"""
import logging
import os
import platform
import signal
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
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

# Import enhanced UI components
from ui.popup_window import PopupWindow
from ui.settings_window import SettingsWindow
from ui.system_tray import SystemTray
from utils.config import Config

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / ".clipboard_manager.log"),
    ],
)
logger = logging.getLogger(__name__)


def setup_qt_environment():
    """Setup Qt environment with cross-platform enhancements"""
    # Detect platform and set appropriate Qt settings
    current_platform = platform.system().lower()

    if current_platform == "windows":
        # Windows-specific Qt settings
        os.environ["QT_QPA_PLATFORM"] = "windows"
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"

        # Windows-specific plugin path
        possible_windows_paths = [
            str(
                Path.home()
                / "AppData/Local/Programs/Python/Lib/site-packages/PySide6/plugins"
            ),
            str(
                Path.home()
                / "AppData/Local/Programs/Python/Lib/site-packages/PySide6/Qt6/plugins"
            ),
            "C:/Program Files/Python*/Lib/site-packages/PySide6/plugins",
        ]

        for path in possible_windows_paths:
            if Path(path).exists():
                os.environ["QT_PLUGIN_PATH"] = path
                logger.info(f"Set Windows QT_PLUGIN_PATH to {path}")
                break

    else:
        # Linux/macOS settings
        os.environ["QT_QPA_PLATFORM"] = "xcb:fallback=wayland:fallback=offscreen"
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"

        # Linux plugin paths
        possible_paths = [
            "/usr/lib/x86_64-linux-gnu/qt6/plugins",
            "/usr/lib/qt6/plugins",
            "/usr/local/lib/qt6/plugins",
            str(Path.home() / ".local/lib/qt6/plugins"),
        ]

        for path in possible_paths:
            if Path(path).exists():
                os.environ["QT_PLUGIN_PATH"] = path
                logger.info(f"Set Linux QT_PLUGIN_PATH to {path}")
                break

    # Enable smooth rendering
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"


class CrossPlatformSingleInstance:
    """Cross-platform single instance checker"""

    def __init__(self, lock_name: str = "clipboard_manager.lock"):
        self.lock_name = lock_name
        self.platform = platform.system().lower()
        self.lock_file = None
        self.lock_fd = None
        self.is_locked = False

        # Determine lock file location based on platform
        if self.platform == "windows":
            self.lock_path = Path(tempfile.gettempdir()) / f"{lock_name}"
        else:
            # Linux/macOS
            self.lock_path = Path.home() / f".{lock_name}"

    def acquire_lock(self) -> bool:
        """Acquire lock for single instance check"""
        try:
            if self.platform == "windows":
                return self._acquire_lock_windows()
            else:
                return self._acquire_lock_unix()
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    def _acquire_lock_windows(self) -> bool:
        """Windows-specific lock acquisition using file locking"""
        try:
            # Create lock file
            self.lock_file = open(self.lock_path, "w")

            # Try to acquire exclusive lock
            import msvcrt

            msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)

            # Write PID to lock file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()

            self.is_locked = True
            logger.info(f"Windows lock acquired: {self.lock_path}")
            return True

        except (IOError, OSError) as e:
            # Another instance is running
            logger.warning(f"Windows lock failed: {e}")
            if self.lock_file:
                self.lock_file.close()
            return False
        except ImportError:
            # Fallback for Windows without msvcrt
            return self._acquire_lock_fallback()

    def _acquire_lock_unix(self) -> bool:
        """Unix/Linux lock acquisition using fcntl"""
        try:
            import fcntl

            self.lock_file = open(self.lock_path, "w")

            # Try to acquire exclusive lock using getattr for better compatibility
            lock_ex = getattr(fcntl, "LOCK_EX", 1)
            lock_nb = getattr(fcntl, "LOCK_NB", 2)
            flock_func = getattr(fcntl, "flock", None)

            if flock_func:
                flock_func(self.lock_file.fileno(), lock_ex | lock_nb)
            else:
                # Fallback if flock is not available
                return self._acquire_lock_fallback()

            # Write PID to lock file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()

            self.is_locked = True
            logger.info(f"Unix lock acquired: {self.lock_path}")
            return True

        except ImportError:
            # Fallback for systems without fcntl
            logger.warning("fcntl not available, using fallback method")
            return self._acquire_lock_fallback()
        except (IOError, OSError) as e:
            # Another instance is running
            logger.warning(f"Unix lock failed: {e}")
            if self.lock_file:
                self.lock_file.close()
            return False

    def _acquire_lock_fallback(self) -> bool:
        """Fallback lock method using file existence check"""
        try:
            # Check if lock file exists and is recent (within 30 seconds)
            if self.lock_path.exists():
                # Check if lock file is stale (older than 30 seconds)
                lock_age = time.time() - self.lock_path.stat().st_mtime
                if lock_age < 30:
                    # Lock file is recent, another instance is running
                    logger.warning(f"Lock file exists and recent: {self.lock_path}")
                    return False
                else:
                    # Stale lock file, remove it
                    logger.info(f"Removing stale lock file: {self.lock_path}")
                    self.lock_path.unlink()

            # Create new lock file
            self.lock_file = open(self.lock_path, "w")
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()

            self.is_locked = True
            logger.info(f"Fallback lock acquired: {self.lock_path}")
            return True

        except Exception as e:
            logger.error(f"Fallback lock failed: {e}")
            return False

    def release_lock(self):
        """Release the lock"""
        try:
            if self.lock_file:
                self.lock_file.close()

            if self.is_locked and self.lock_path.exists():
                self.lock_path.unlink()
                logger.info(f"Lock released: {self.lock_path}")

        except Exception as e:
            logger.error(f"Error releasing lock: {e}")


class EnhancedClipboardManager:
    """Enhanced Clipboard Manager with modern UI and auto-hide focus"""

    def __init__(self):
        # Setup Qt environment
        setup_qt_environment()

        try:
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)

            # Set application properties
            self.app.setApplicationName("Clipboard Manager")
            self.app.setApplicationVersion("2.0")
            self.app.setOrganizationName("Falcol")

            # Set default font for modern UI
            font = QFont("Segoe UI", 9)
            font.setStyleHint(self.app.font().styleHint())
            self.app.setFont(font)

        except Exception as e:
            logger.error(f"Failed to create QApplication: {e}")
            self._handle_qt_error(e)

        # Initialize enhanced configuration
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

        # Initialize enhanced UI components
        self.popup_window = PopupWindow(self.database, self.config)
        self.settings_window = SettingsWindow(self.config)
        self.system_tray = SystemTray(self.popup_window, self.settings_window)

        # Set system_tray reference in popup_window
        self.popup_window.system_tray = self.system_tray

        # Initialize hotkey manager with Super+V
        self.hotkey_manager = HotkeyManager(self.show_popup)

        # Setup enhanced connections
        self.setup_connections()

        # Check system tray availability
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(
                None,
                "System Tray",
                "System tray is not available on this system.\n"
                "The application will run in background mode.",
            )

        # Setup performance monitoring
        self.setup_performance_monitoring()

    def _handle_qt_error(self, error):
        """Handle Qt initialization errors with fallbacks"""
        fallback_platforms = ["wayland", "offscreen"]

        for platform in fallback_platforms:
            os.environ["QT_QPA_PLATFORM"] = platform
            try:
                self.app = QApplication(sys.argv)
                self.app.setQuitOnLastWindowClosed(False)
                logger.warning(f"Using {platform} platform as fallback")
                return
            except Exception as e2:
                logger.error(f"Failed to create QApplication with {platform}: {e2}")
                continue

        # If all fallbacks fail
        QMessageBox.critical(
            None,
            "Qt Error",
            f"Failed to initialize Qt application:\n{error}\n\n"
            "Please ensure Qt6 libraries are properly installed.",
        )
        sys.exit(1)

    def _handle_migration(self):
        """Handle database migration with enhanced error handling"""
        if self.old_db_path.exists() and not self.new_db_path.exists():
            logger.info("Detected old database format, starting migration...")

            migration_manager = MigrationManager(
                self.old_db_path, self.new_db_path, self.data_dir
            )

            try:
                if migration_manager.migrate():
                    logger.info("Database migration completed successfully")
                    # Show success notification when UI is ready
                    QTimer.singleShot(2000, self._show_migration_success)
                else:
                    logger.error("Database migration failed, using new database")
                    QTimer.singleShot(2000, self._show_migration_failure)
            except Exception as e:
                logger.error(f"Migration error: {e}")
                QTimer.singleShot(2000, self._show_migration_failure)

    def _show_migration_success(self):
        """Show migration success notification"""
        if hasattr(self, "system_tray"):
            self.system_tray.show_notification(
                "Migration Complete",
                "Your clipboard history has been successfully upgraded to v2.0!",
                4000,
            )

    def _show_migration_failure(self):
        """Show migration failure notification"""
        if hasattr(self, "system_tray"):
            self.system_tray.show_notification(
                "Migration Notice",
                "Started with new database. Old data preserved as backup.",
                4000,
            )

    def setup_connections(self):
        """Setup enhanced signal connections between components"""
        # Settings changes
        self.settings_window.settings_changed.connect(self.on_settings_changed)

        # System tray
        self.system_tray.quit_requested.connect(self.quit_application)

        # Enhanced clipboard watcher with notifications
        self.clipboard_watcher.content_changed.connect(self.on_content_changed)

        # Popup window focus management
        # if hasattr(self.popup_window, "hidden"):
        #     self.popup_window.hidden.connect(self.on_popup_hidden)

    def setup_performance_monitoring(self):
        """Setup performance monitoring and cleanup"""
        # Periodic cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.perform_maintenance)

        cleanup_interval = (
            self.config.get("cleanup_interval_hours", 24) * 3600000
        )  # Convert to ms
        self.cleanup_timer.start(cleanup_interval)

        logger.info(
            f"Performance monitoring enabled, cleanup every {cleanup_interval//3600000} hours"
        )

    def perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        try:
            logger.info("Performing scheduled maintenance...")

            # Cleanup orphaned files
            active_file_paths = set()
            items = self.database.get_items(limit=1000)
            for item in items:
                if item.get("file_path"):
                    active_file_paths.add(item["file_path"])
                if item.get("thumbnail_path"):
                    active_file_paths.add(item["thumbnail_path"])

            self.content_manager.cleanup_orphaned_files(active_file_paths)

            # Database cleanup
            stats_before = self.database.get_stats()
            # The database cleanup is handled automatically in the database class
            stats_after = self.database.get_stats()

            logger.info(
                # flake8: noqa: E501
                f"Maintenance complete. Items: {stats_before.get('total_items', 0)} -> {stats_after.get('total_items', 0)}"
            )

        except Exception as e:
            logger.error(f"Error during maintenance: {e}")

    def on_content_changed(self, content_type: str, item_data: dict):
        """Handle new clipboard content with enhanced features and notifications"""
        logger.info(f"New {content_type} content detected: {item_data.get('id')}")

        # Show notification for new content (if enabled)
        if self.config.get("show_notifications", False):
            preview = ""
            if content_type == "text":
                preview = item_data.get("preview", "")
            elif content_type == "image":
                width = item_data.get("width", 0)
                height = item_data.get("height", 0)
                preview = f"{width}×{height} pixels"

            self.system_tray.show_new_item_notification(content_type, preview)

        # Update popup if visible
        if self.popup_window.isVisible():
            QTimer.singleShot(100, self.popup_window.load_items)

    def on_popup_hidden(self):
        """Handle popup window hidden event"""
        logger.debug("Popup window hidden")
        # Could add analytics or cleanup here

    def show_popup(self):
        """Show the enhanced clipboard popup window"""
        try:
            self.popup_window.show_at_cursor()
            logger.debug("Clipboard popup shown")
        except Exception as e:
            logger.error(f"Error showing popup: {e}")
            # Fallback notification
            self.system_tray.show_notification(
                "Error", "Failed to show clipboard popup. Check logs for details.", 3000
            )

    def on_settings_changed(self):
        """Handle settings changes with enhanced updates"""
        logger.info("Settings changed, updating components...")

        try:
            # Update all components
            self.clipboard_watcher.update_config()
            self.popup_window.update_config()

            # Update cleanup timer if interval changed
            cleanup_interval = self.config.get("cleanup_interval_hours", 24) * 3600000
            self.cleanup_timer.start(cleanup_interval)

            # Update hotkey if changed (would need hotkey manager enhancement)
            # self.hotkey_manager.update_hotkey(self.config.get("hotkey", "super+v"))

            logger.info("All components updated with new settings")

        except Exception as e:
            logger.error(f"Error updating settings: {e}")

    def start(self):
        """Start the enhanced application with error handling"""
        try:
            # Start enhanced clipboard monitoring
            self.clipboard_watcher.start()

            # Start hotkey listener
            self.hotkey_manager.start()

            # Show enhanced system tray
            if self.system_tray.show():
                # Show startup notification with platform-specific hotkey
                hotkey_info = self.hotkey_manager.get_hotkey_info()
                platform_name = hotkey_info["platform"]

                if platform_name == "windows":
                    hotkey_display = "Windows+C"
                elif platform_name == "linux":
                    hotkey_display = "Super+V"
                else:
                    hotkey_display = "Cmd+C"

                QTimer.singleShot(
                    1000,
                    lambda: self.system_tray.show_notification(
                        "Clipboard Manager Started",
                        f"Press {hotkey_display} to open clipboard history",
                        3000,
                    ),
                )

            logger.info("Enhanced Clipboard Manager started successfully")

            # Setup graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            # Start the Qt event loop
            return self.app.exec()

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            return 0
        except Exception as e:
            logger.error(f"Failed to start enhanced application: {e}")
            return 1

    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        QTimer.singleShot(0, self.quit_application)

    def quit_application(self):
        """Quit the application gracefully with enhanced cleanup"""
        try:
            logger.info("Starting graceful shutdown...")

            # Stop timers
            if hasattr(self, "cleanup_timer"):
                self.cleanup_timer.stop()

            # Stop core components
            self.hotkey_manager.stop()
            self.clipboard_watcher.stop()

            # Hide UI components
            self.system_tray.hide()
            if self.popup_window.isVisible():
                self.popup_window.hide()
            if self.settings_window.isVisible():
                self.settings_window.hide()

            # Final cleanup
            active_file_paths = set()
            try:
                items = self.database.get_items(limit=1000)
                for item in items:
                    if item.get("file_path"):
                        active_file_paths.add(item["file_path"])
                    if item.get("thumbnail_path"):
                        active_file_paths.add(item["thumbnail_path"])

                self.content_manager.cleanup_orphaned_files(active_file_paths)
            except Exception as e:
                logger.error(f"Error during final cleanup: {e}")

            # Close database
            self.database.close()

            logger.info("Graceful shutdown completed")
            self.app.quit()

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            # Force quit if graceful shutdown fails
            self.app.quit()

    def get_status_info(self):
        """Get current application status for debugging"""
        try:
            stats = self.database.get_stats()
            return {
                "version": "2.0-enhanced",
                "database_items": stats.get("total_items", 0),
                "pinned_items": stats.get("pinned_items", 0),
                "clipboard_watching": self.clipboard_watcher.running,
                "hotkey_active": self.hotkey_manager.running,
                "popup_visible": self.popup_window.isVisible(),
                "settings_visible": self.settings_window.isVisible(),
            }
        except Exception as e:
            logger.error(f"Error getting status info: {e}")
            return {"error": str(e)}


def main():
    """Enhanced main function with cross-platform single instance check"""
    single_instance = None

    try:
        # Cross-platform single instance check
        single_instance = CrossPlatformSingleInstance()

        if not single_instance.acquire_lock():
            logger.error("Another instance of Clipboard Manager is already running")
            return 1

        # Create and start the enhanced manager
        manager = EnhancedClipboardManager()
        return manager.start()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return 1
    finally:
        # Cleanup lock file
        if single_instance:
            single_instance.release_lock()


if __name__ == "__main__":
    sys.exit(main())
