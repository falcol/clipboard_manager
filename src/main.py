#!/usr/bin/env python3
"""
Main entry point for Clipboard Manager
"""
import logging
import os
import signal
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.clipboard_watcher import ClipboardWatcher
from core.database import ClipboardDatabase
from core.hotkey_manager import HotkeyManager
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
        # Try to find Qt plugins in common locations
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

    # Disable high DPI scaling if causing issues
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"


class ClipboardManager:
    def __init__(self):
        # Setup Qt environment before creating QApplication
        setup_qt_environment()

        try:
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)
        except Exception as e:
            logger.error(f"Failed to create QApplication: {e}")
            # Try with different platform
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
                    f"Failed to initialize Qt application:\n{e}\n\n{e2}\n\n"
                    "Please ensure Qt6 and XCB libraries are installed.",
                )
                sys.exit(1)

        # Initialize components
        self.config = Config()
        self.database = ClipboardDatabase()
        self.clipboard_watcher = ClipboardWatcher(self.database, self.config)
        self.popup_window = PopupWindow(self.database, self.config)
        self.settings_window = SettingsWindow(self.config)
        self.system_tray = SystemTray(self.popup_window, self.settings_window)
        self.hotkey_manager = HotkeyManager(self.show_popup)

        # Setup connections
        self.setup_connections()

        # Check system tray availability
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(
                None, "System Tray", "System tray is not available on this system."
            )
            sys.exit(1)

    def setup_connections(self):
        """Setup signal connections between components"""
        self.settings_window.settings_changed.connect(self.on_settings_changed)
        self.system_tray.quit_requested.connect(self.quit_application)

    def show_popup(self):
        """Show the clipboard popup window"""
        self.popup_window.show_at_cursor()

    def on_settings_changed(self):
        """Handle settings changes"""
        self.clipboard_watcher.update_config()
        self.popup_window.update_config()

    def start(self):
        """Start the application"""
        try:
            # Start clipboard monitoring
            self.clipboard_watcher.start()

            # Start hotkey listener
            self.hotkey_manager.start()

            # Show system tray
            self.system_tray.show()

            logger.info("Clipboard Manager started successfully")

            # Setup graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            return self.app.exec()

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
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
            self.database.close()
            self.app.quit()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Main function"""
    try:
        manager = ClipboardManager()
        return manager.start()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
