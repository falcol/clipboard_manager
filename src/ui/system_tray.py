# clipboard_manager/src/ui/system_tray.py
"""
system tray integration with modern menu design
"""
import logging

from PySide6.QtCore import QObject, QPoint, QTimer
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPixmap, Qt
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from ui.about_popup import show_about_popup

logger = logging.getLogger(__name__)


class SystemTray(QObject):
    """system tray icon and menu with modern design"""

    quit_requested = pyqtSignal()

    def __init__(self, popup_window, settings_window):
        super().__init__()
        self.popup_window = popup_window
        self.settings_window = settings_window

        # Create icon and menu before showing
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self.create_modern_icon())
        self.tray_icon.setToolTip("B1Clip - Click to open")

        # Create menu and preload deeply
        self.menu = self.create_modern_menu()
        self.tray_icon.setContextMenu(self.menu)

        # Preload extremely
        self.force_qt_preload()

        # Connect signal
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
        """Create modern context menu with styling"""
        menu = QMenu()

        # Styling is applied globally to QApplication; avoid redundant menu-specific QSS

        # Show clipboard action with icon
        show_action = menu.addAction("📋  Show Clipboard History")
        show_action.setFont(QFont(QApplication.font().family(), 10, QFont.Weight.Medium))
        show_action.triggered.connect(self.show_clipboard)

        menu.addSeparator()

        # Settings action
        settings_action = menu.addAction("⚙️  Settings")
        settings_action.setFont(QFont(QApplication.font().family(), 9))
        settings_action.triggered.connect(self.show_settings)

        # About action
        about_action = menu.addAction("ℹ️  About")
        about_action.setFont(QFont(QApplication.font().family(), 9))
        about_action.triggered.connect(self.show_about)

        menu.addSeparator()

        # Quit action
        quit_action = menu.addAction("❌  Quit B1Clip")
        quit_action.setFont(QFont(QApplication.font().family(), 9))
        # Ensure tray icon hides before quitting to avoid orphan tray entries
        def _on_quit():
            try:
                self.hide()
            except Exception:
                pass
            self.quit_requested.emit()
        quit_action.triggered.connect(_on_quit)

        # Preload each action
        for action in menu.actions():
            action.icon()  # Force load icon
            action.font()  # Force load font

        return menu

    def force_qt_preload(self):
        """Force Qt to initialize all GUI resources"""
        # 1. Show and hide menu immediately
        self.menu.popup(QPoint(-1000, -1000))  # Show outside screen
        QTimer.singleShot(0, self.menu.hide)

        # 2. Render dummy pixmap to force initialization
        pixmap = QPixmap(1, 1)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.end()

        # 3. Access QApplication style to force initialization
        QApplication.style().polish(self.menu)

    def show(self):
        """Show tray icon with features"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.error("System tray is not available")
            return False

        self.tray_icon.show()
        logger.info("system tray icon shown")
        return True

    def hide(self):
        """Hide tray icon"""
        self.tray_icon.hide()
        self.animation_timer.stop()

    def on_tray_activated(self, reason):
        """Handle tray icon activation with minimal processing"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_clipboard()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:  # Single click
            # Avoid unnecessary visual feedback to prevent delay
            pass
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            # Menu will be shown automatically by Qt, no additional processing needed
            pass

    def show_active_feedback(self):
        """Show brief visual feedback when icon is clicked"""
        # Switch to active icon
        self.tray_icon.setIcon(self.create_modern_icon(active=True))

        # Switch back after 200ms
        QTimer.singleShot(
            200, lambda: self.tray_icon.setIcon(self.create_modern_icon(active=False))
        )

    def show_clipboard(self):
        """Show clipboard popup with positioning"""
        # Show active state
        self.tray_icon.setIcon(self.create_modern_icon(active=True))

        # Show the popup
        self.popup_window.show_at_cursor()

        # Return to normal state after popup is shown
        QTimer.singleShot(
            500, lambda: self.tray_icon.setIcon(self.create_modern_icon(active=False))
        )

    def show_settings(self):
        """Show settings window with presentation"""
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def show_about(self):
        """Show about information with platform-specific hotkey"""
        try:

            # Try to get proper parent window
            parent_window = None
            if hasattr(self, "popup_window") and self.popup_window:
                parent_window = self.popup_window
            elif hasattr(self, "settings_window") and self.settings_window:
                parent_window = self.settings_window
            else:
                # Fallback to tray icon parent
                parent_window = self.tray_icon.parent()

            # Show about popup
            show_about_popup(parent=parent_window)

        except Exception as e:
            logger.error(f"Error showing about popup: {e}")
            # Fallback: show as tray message
            self.tray_icon.showMessage(
                "B1Clip",
                "🔷 B1Clip v1.0\nA modern clipboard history manager",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    def update_icon(self):
        """Update icon based on current state (for future animations)"""
        # Placeholder for future animated states
        pass

    def show_notification(self, title, message, duration=3000):
        """Show system notification with cross-platform support"""
        try:
            import platform

            current_platform = platform.system().lower()

            if current_platform == "linux":
                # Linux: try notify-send first, then fallback to Qt
                if self._show_linux_notification(title, message):
                    return
                else:
                    # Fallback to Qt system tray message
                    self.tray_icon.showMessage(
                        title,
                        message,
                        QSystemTrayIcon.MessageIcon.Information,
                        duration,
                    )
            else:
                # Windows/macOS: use Qt system tray message
                self.tray_icon.showMessage(
                    title, message, QSystemTrayIcon.MessageIcon.Information, duration
                )

        except Exception as e:
            logger.error(f"Error showing notification: {e}")
            # Final fallback: just log the message
            logger.info(f"Notification: {title} - {message}")

    def _show_linux_notification(self, title, message):
        """Show notification on Linux using notify-send"""
        try:
            import subprocess

            # Try notify-send command
            result = subprocess.run(
                ["notify-send", title, message, "--icon=clipboard"],
                capture_output=True,
                timeout=5,
            )

            if result.returncode == 0:
                logger.info(f"Linux notification sent: {title}")
                return True
            else:
                logger.warning(f"notify-send failed: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("notify-send not available on Linux")
            return False
        except Exception as e:
            logger.error(f"Error with Linux notification: {e}")
            return False

    def show_new_item_notification(self, item_type, preview=""):
        """Show notification for new clipboard item with cross-platform support"""
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

        self.show_notification(title, message, 2000)  # Use cross-platform method

    def show_paste_notification(self, content_type: str):
        """Show notification when content is pasted with cross-platform support"""
        try:
            icon_map = {
                "text": "📝",
                "image": "🖼️",
                "url": "🔗",
                "code": "💻",
                "json": "📄",
            }
            icon = icon_map.get(content_type, "📋")

            self.show_notification(
                f"{icon} Content Pasted",
                f"{content_type.title()} content pasted like Windows clipboard",
                2000,
            )
        except Exception as e:
            logger.error(f"Error showing paste notification: {e}")

    def preload_resources(self):
        """Preload resources to avoid delay on first interaction"""
        # Preload icons
        self.create_modern_icon(active=True)
        self.create_modern_icon(active=False)

        # Access menu to force initialization
        menu = self.tray_icon.contextMenu()
        if menu:
            # Trigger a dummy layout or rendering if possible
            menu.actions()  # Access actions to force initialization
            for action in menu.actions():
                action.font()  # Access font to preload it

        logger.info("System tray resources preloaded")
