# clipboard_manager/src/ui/system_tray.py
"""
System tray integration
"""
import logging

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

logger = logging.getLogger(__name__)


class SystemTray(QObject):
    """System tray icon and menu"""

    quit_requested = pyqtSignal()

    def __init__(self, popup_window, settings_window):
        super().__init__()
        self.popup_window = popup_window
        self.settings_window = settings_window

        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self.create_icon())
        self.tray_icon.setToolTip("Clipboard Manager")

        # Create context menu
        self.create_menu()

        # Connect signals
        self.tray_icon.activated.connect(self.on_tray_activated)

    def create_icon(self):
        """Create tray icon"""
        # Create simple clipboard icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw clipboard
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRect(2, 1, 10, 12)

        # Draw clip
        painter.setBrush(QBrush(QColor(128, 128, 128)))
        painter.drawRect(4, 0, 6, 3)

        painter.end()

        return QIcon(pixmap)

    def create_menu(self):
        """Create context menu"""
        menu = QMenu()

        # Show clipboard action
        show_action = menu.addAction("📋 Show Clipboard")
        show_action.triggered.connect(self.show_clipboard)

        menu.addSeparator()

        # Settings action
        settings_action = menu.addAction("⚙️ Settings")
        settings_action.triggered.connect(self.show_settings)

        menu.addSeparator()

        # Quit action
        quit_action = menu.addAction("❌ Quit")
        quit_action.triggered.connect(self.quit_requested.emit)

        self.tray_icon.setContextMenu(menu)

    def show(self):
        """Show tray icon"""
        self.tray_icon.show()
        logger.info("System tray icon shown")

    def hide(self):
        """Hide tray icon"""
        self.tray_icon.hide()

    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_clipboard()

    def show_clipboard(self):
        """Show clipboard popup"""
        self.popup_window.show_at_cursor()

    def show_settings(self):
        """Show settings window"""
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
