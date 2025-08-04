# clipboard_manager/src/ui/system_tray.py
"""
Enhanced system tray integration with modern menu design
"""
import logging

from PySide6.QtCore import QObject, QTimer
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ui.styles import Styles

logger = logging.getLogger(__name__)


class SystemTray(QObject):
    """Enhanced system tray icon and menu with modern design"""

    quit_requested = pyqtSignal()

    def __init__(self, popup_window, settings_window):
        super().__init__()
        self.popup_window = popup_window
        self.settings_window = settings_window

        # Create enhanced tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self.create_modern_icon())
        self.tray_icon.setToolTip("Clipboard Manager - Click to open")

        # Create modern context menu
        self.create_modern_menu()

        # Connect signals
        self.tray_icon.activated.connect(self.on_tray_activated)

        # Animation timer for icon updates
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_icon)

    def create_modern_icon(self, active=False):
        """Create modern tray icon with optional active state"""
        # Create higher resolution icon
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Modern clipboard design
        if active:
            # Active state - blue accent
            clipboard_color = QColor(0, 120, 212)  # Blue
            clip_color = QColor(0, 86, 154)  # Darker blue
        else:
            # Normal state - white/gray
            clipboard_color = QColor(255, 255, 255, 220)
            clip_color = QColor(180, 180, 180, 200)

        # Draw main clipboard body
        painter.setBrush(QBrush(clipboard_color))
        painter.setPen(clipboard_color)

        # Rounded rectangle for modern look
        # flake8: noqa: E501
        clipboard_rect = painter.drawRoundedRect(6, 4, 20, 26, 2, 2)

        # Draw clip at top
        painter.setBrush(QBrush(clip_color))
        painter.setPen(clip_color)
        painter.drawRoundedRect(10, 2, 12, 6, 2, 2)

        # Draw content lines for detail
        content_color = (
            QColor(100, 100, 100, 150) if not active else QColor(255, 255, 255, 200)
        )
        painter.setPen(content_color)
        painter.drawLine(10, 12, 22, 12)
        painter.drawLine(10, 16, 20, 16)
        painter.drawLine(10, 20, 18, 20)

        painter.end()

        return QIcon(pixmap)

    def create_modern_menu(self):
        """Create modern context menu with enhanced styling"""
        menu = QMenu()
        menu.setStyleSheet(Styles.get_system_tray_menu_style())

        # Show clipboard action with icon
        show_action = menu.addAction("📋  Show Clipboard History")
        show_action.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        show_action.triggered.connect(self.show_clipboard)

        # Quick stats action (informational)
        stats_action = menu.addAction("📊  Quick Stats")
        stats_action.setFont(QFont("Segoe UI", 9))
        stats_action.triggered.connect(self.show_quick_stats)

        menu.addSeparator()

        # Settings action
        settings_action = menu.addAction("⚙️  Settings")
        settings_action.setFont(QFont("Segoe UI", 9))
        settings_action.triggered.connect(self.show_settings)

        # About action
        about_action = menu.addAction("ℹ️  About")
        about_action.setFont(QFont("Segoe UI", 9))
        about_action.triggered.connect(self.show_about)

        menu.addSeparator()

        # Quit action
        quit_action = menu.addAction("❌  Quit Clipboard Manager")
        quit_action.setFont(QFont("Segoe UI", 9))
        quit_action.triggered.connect(self.quit_requested.emit)

        self.tray_icon.setContextMenu(menu)

    def show(self):
        """Show tray icon with enhanced features"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.error("System tray is not available")
            return False

        self.tray_icon.show()
        logger.info("Enhanced system tray icon shown")
        return True

    def hide(self):
        """Hide tray icon"""
        self.tray_icon.hide()
        self.animation_timer.stop()

    def on_tray_activated(self, reason):
        """Handle tray icon activation with enhanced feedback"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_clipboard()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:  # Single click
            # Show brief active state
            self.show_active_feedback()

    def show_active_feedback(self):
        """Show brief visual feedback when icon is clicked"""
        # Switch to active icon
        self.tray_icon.setIcon(self.create_modern_icon(active=True))

        # Switch back after 200ms
        QTimer.singleShot(
            200, lambda: self.tray_icon.setIcon(self.create_modern_icon(active=False))
        )

    def show_clipboard(self):
        """Show clipboard popup with enhanced positioning"""
        # Show active state
        self.tray_icon.setIcon(self.create_modern_icon(active=True))

        # Show the popup
        self.popup_window.show_at_cursor()

        # Return to normal state after popup is shown
        QTimer.singleShot(
            500, lambda: self.tray_icon.setIcon(self.create_modern_icon(active=False))
        )

    def show_settings(self):
        """Show settings window with enhanced presentation"""
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def show_quick_stats(self):
        """Show quick statistics in a tray message"""
        try:
            # Get database stats
            if hasattr(self.popup_window, "database"):
                stats = self.popup_window.database.get_stats()
                total = stats.get("total_items", 0)
                pinned = stats.get("pinned_items", 0)

                message = f"📊 Clipboard Stats\n\n"
                message += f"Total items: {total}\n"
                message += f"Pinned items: {pinned}\n"
                message += f"Regular items: {total - pinned}"

                self.tray_icon.showMessage(
                    "Clipboard Manager",
                    message,
                    QSystemTrayIcon.MessageIcon.Information,
                    3000,  # 3 seconds
                )
            else:
                self.tray_icon.showMessage(
                    "Clipboard Manager",
                    "📊 Stats not available",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )

        except Exception as e:
            logger.error(f"Error showing quick stats: {e}")
            self.tray_icon.showMessage(
                "Clipboard Manager",
                "📊 Unable to load stats",
                QSystemTrayIcon.MessageIcon.Warning,
                2000,
            )

    def show_about(self):
        """Show about information"""
        about_message = """🔷 Clipboard Manager v2.0
            A modern clipboard history manager with:
            • Windows 11-style interface
            • Smart content detection
            • Search and filtering
            • Pin important items
            • Cross-platform support

            Hotkey: Super+V"""

        self.tray_icon.showMessage(
            "About Clipboard Manager",
            about_message,
            QSystemTrayIcon.MessageIcon.Information,
            5000,  # 5 seconds
        )

    def update_icon(self):
        """Update icon based on current state (for future animations)"""
        # Placeholder for future animated states
        pass

    def show_notification(self, title, message, duration=3000):
        """Show system notification"""
        self.tray_icon.showMessage(
            title, message, QSystemTrayIcon.MessageIcon.Information, duration
        )

    def show_new_item_notification(self, item_type, preview=""):
        """Show notification for new clipboard item"""
        icon_map = {"text": "📝", "image": "🖼️", "url": "🔗", "code": "💻", "json": "📄"}

        icon = icon_map.get(item_type, "📋")
        title = f"{icon} New {item_type.title()} Copied"

        # Limit preview length
        if preview and len(preview) > 50:
            preview = preview[:47] + "..."

        message = (
            preview
            if preview
            else f"{item_type.title()} content added to clipboard history"
        )

        self.tray_icon.showMessage(
            title, message, QSystemTrayIcon.MessageIcon.Information, 2000  # 2 seconds
        )
