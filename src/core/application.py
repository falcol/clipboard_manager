# clipboard_manager/src/core/application.py
"""
B1Clip main application class
"""

import contextlib
import os
import signal
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QMessageBox, QStyleFactory, QSystemTrayIcon

from core.clipboard_watcher import ClipboardWatcher
from core.content_manager import ContentManager
from core.database import ClipboardDatabase
from core.hotkey_manager import HotkeyManager
from core.search_engine import SearchEngine
from ui.popup_window import PopupWindow
from ui.settings_window import SettingsWindow
from ui.system_tray import SystemTray
from utils.config import Config
from utils.logging_config import get_logger
from utils.qss_loader import QSSLoader
from utils.qt_setup import setup_qt_environment
from utils.single_instance import CrossPlatformSingleInstance

logger = get_logger(__name__)


class ClipboardManager:
    """B1Clip with modern UI and auto-hide focus"""

    def __init__(self):
        # Setup Qt environment
        setup_qt_environment()

        try:
            # Enable HiDPI pixmaps and use rounding policy that reduces blur on fractional scaling
            QApplication.setAttribute(
                Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True
            )
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor
            )

            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)

            # Set application properties
            self.app.setApplicationName("B1Clip")
            self.app.setApplicationVersion("1.0")
            self.app.setOrganizationName("Falcol")

            # Use a neutral, cross-platform base style (then QSS will skin it)
            self.app.setStyle(QStyleFactory.create("Fusion"))

            # Set default font with cross-platform family fallbacks (prefer Noto Sans on Linux)
            self.app.setFont(self._choose_system_ui_font())

        except Exception as e:

            logger.error(f"Failed to create QApplication: {e}")
            self._handle_qt_error(e)

        # Initialize configuration
        self.config = Config()
        self._single_instance: CrossPlatformSingleInstance | None = None

        # Initialize data directory (only 1 database)
        self.data_dir = Path(self.config.config_path.parent)
        self.db_path = self.data_dir / "clipboard.db"  # Only 1 file

        # Initialize core components (migration automatically in database)
        self.database = ClipboardDatabase(self.db_path)
        self.content_manager = ContentManager(self.data_dir)
        self.search_engine = SearchEngine(self.database)

        # Initialize clipboard watcher
        self.clipboard_watcher = ClipboardWatcher(
            self.database, self.content_manager, self.config
        )

        # Initialize UI components
        self.popup_window = PopupWindow(self.database, self.config)
        self.settings_window = SettingsWindow(self.config)
        self.system_tray = SystemTray(self.popup_window, self.settings_window)

        # Set system_tray reference in popup_window
        self.popup_window.system_tray = self.system_tray

        # Initialize hotkey manager driven by Config
        self.hotkey_manager = HotkeyManager(self.show_popup, self.config)

        # Initialize QSS loader
        self.qss_loader = QSSLoader()

        # Setup connections
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

    def setup_connections(self):
        """Setup signal connections between components"""
        # Settings changes
        self.settings_window.settings_changed.connect(self.on_settings_changed)

        # System tray
        self.system_tray.quit_requested.connect(self.quit_application)

        # clipboard watcher with notifications
        self.clipboard_watcher.content_changed.connect(self.on_content_changed)

        # Apply QSS to all components
        self._apply_qss_styles()

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
            f"Performance monitoring enabled, cleanup every {cleanup_interval // 3600000} hours"
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
                f"Maintenance complete. Items: {stats_before.get('total_items', 0)} -> {stats_after.get('total_items', 0)}"
            )

        except Exception as e:

            logger.error(f"Error during maintenance: {e}")

    def on_content_changed(self, content_type: str, item_data: dict):
        """Handle new clipboard content with features and notifications"""

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

    def show_popup(self):
        """Show the clipboard popup window"""
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
        """Handle settings changes with updates"""

        logger.info("Settings changed, updating components...")

        try:
            # Update all components
            self.clipboard_watcher.update_config()
            self.popup_window.update_config()

            # Update cleanup timer if interval changed
            cleanup_interval = self.config.get("cleanup_interval_hours", 24) * 3600000
            self.cleanup_timer.start(cleanup_interval)

            # Apply theme immediately, no need to restart
            self._apply_qss_styles()

            # Update hotkey manager from config (if hotkey changed)
            with contextlib.suppress(Exception):
                if getattr(self, "hotkey_manager", None):
                    self.hotkey_manager.update_from_config()

            logger.info("All components updated with new settings")

        except Exception as e:
            logger.error(f"Error updating settings: {e}")

    def _apply_qss_styles(self):
        """Apply QSS stylesheets to entire app (global)"""
        try:
            # Validate theme against available theme files and fallback safely
            available_themes = {
                "dark_win11": "themes/dark_win11.qss",
                "dark_amoled": "themes/dark_amoled.qss",
                "dark_solarized": "themes/dark_solarized.qss",
                "nord": "themes/nord.qss",
                "vespera": "themes/vespera.qss",
                "dracula": "themes/dracula.qss",
                "onedark_pro": "themes/onedark_pro.qss",
                "gruvbox": "themes/gruvbox.qss",
            }

            theme_name = self.config.get("theme", "dark_win11")
            theme_file = available_themes.get(theme_name, available_themes["dark_win11"])

            # Apply globally: main + theme
            self.qss_loader.apply_app_stylesheet(["main.qss", theme_file])

            # QMenu (tray menu) also receives global stylesheet; ensure menu exists
            if getattr(self.system_tray, "menu", None):
                # No-op; global stylesheet is enough, but if needed force polish:
                try:
                    self.system_tray.menu.ensurePolished()
                except Exception:
                    pass

            logger.info(f"Applied global theme: {theme_name}")
        except Exception as e:

            logger.error(f"Error applying global QSS: {e}")

    def start(self):
        """Start the application with error handling"""
        try:
            # Start clipboard monitoring
            self.clipboard_watcher.start()

            # Start hotkey listener
            self.hotkey_manager.start()

            # Show system tray
            if self.system_tray.show():
                # Show startup notification with platform-specific hotkey
                hotkey_info = self.hotkey_manager.get_hotkey_info()
                platform_name = hotkey_info["platform"]

                if platform_name == "windows":
                    hotkey_display = "Windows+C"
                elif platform_name == "linux":
                    hotkey_display = "Super+C"
                else:
                    hotkey_display = "Cmd+C"

                QTimer.singleShot(
                    1000,
                    lambda: self.system_tray.show_notification(
                        "B1Clip Started",
                        f"Press {hotkey_display} to open clipboard history",
                        3000,
                    ),
                )

            logger.info("B1Clip started successfully")

            # Setup graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            # Start the Qt event loop
            return self.app.exec()

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            return 0
        except Exception as e:

            logger.error(f"Failed to start application: {e}")
            return 1

    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""

        logger.info(f"Received signal {signum}, shutting down gracefully...")
        QTimer.singleShot(0, self.quit_application)

    def quit_application(self):
        """Quit the application gracefully with cleanup"""
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

            # Release single-instance lock if we own it (when started via main)
            with contextlib.suppress(Exception):
                single = getattr(self, "_single_instance", None)
                if single is not None:
                    # Method exists on CrossPlatformSingleInstance
                    single.release_lock()  # type: ignore[attr-defined]
            logger.info("Graceful shutdown completed")
            self.app.quit()

        except Exception as e:

            logger.error(f"Error during shutdown: {e}")
            # Force quit if graceful shutdown fails
            self.app.quit()

    def _choose_system_ui_font(self) -> QFont:
        """Choose a readable, cross-platform UI font with sensible fallbacks.

        - Windows: Segoe UI
        - macOS: .SF NS Text / Helvetica Neue
        - Linux: Noto Sans (preferred), Ubuntu, DejaVu Sans
        """
        try:
            families_by_platform = []
            if sys.platform.startswith("win"):
                families_by_platform = ["Segoe UI", "Noto Sans", "Arial", "Sans Serif"]
                point_size = 9
            elif sys.platform.startswith("darwin"):
                families_by_platform = [
                    "Ubuntu",
                    "DejaVu Sans",
                    ".SF NS Text",
                    "Helvetica Neue",
                    "Noto Sans",
                    "Arial",
                    "Sans Serif",
                ]
                point_size = 12  # macOS default UI size is larger
            else:
                # Linux
                families_by_platform = [
                    "Noto Sans",
                    "Ubuntu",
                    "DejaVu Sans",
                    "Segoe UI",
                    "Arial",
                    "Sans Serif",
                ]
                point_size = 10

            db = QFontDatabase()
            for family in families_by_platform:
                if family in db.families():
                    return QFont(family, point_size)

            # Fallback to current app font but adjust size for readability
            return QFont(self.app.font().family(), point_size)
        except Exception:
            # Absolute fallback
            return QFont("Sans Serif", 10)

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
