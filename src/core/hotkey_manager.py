# clipboard_manager/src/core/hotkey_manager.py
"""
Global hotkey management using pynput
"""
import logging
from typing import Callable, Optional

from pynput import keyboard
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as pyqtSignal

logger = logging.getLogger(__name__)


class HotkeyManager(QObject):
    """Global hotkey manager with thread-safe callback handling"""

    hotkey_triggered = pyqtSignal()

    def __init__(self, callback: Callable[[], None]):
        super().__init__()
        self.callback = callback
        self.listener: Optional[keyboard.Listener] = None
        self.running = False

        # Define hotkey combination (Super/Windows + C)
        self.hotkey_combination = {keyboard.Key.cmd, keyboard.KeyCode.from_char("c")}

        # Cross-platform Super key detection
        try:
            # Try to use super_l for Linux
            super_key = getattr(keyboard.Key, "super_l", keyboard.Key.cmd)
            self.hotkey_combination = {super_key, keyboard.KeyCode.from_char("c")}
        except AttributeError:
            # Fallback to cmd for macOS/Windows
            self.hotkey_combination = {
                keyboard.Key.cmd,
                keyboard.KeyCode.from_char("c"),
            }

        self.pressed_keys = set()

        # Connect signal to callback
        self.hotkey_triggered.connect(self.callback)

    def start(self):
        """Start global hotkey listener"""
        if self.running:
            return

        try:
            self.running = True
            self.listener = keyboard.Listener(
                on_press=self.on_key_press, on_release=self.on_key_release
            )
            self.listener.start()
            logger.info("Hotkey manager started (Super+C)")

        except Exception as e:
            logger.error(f"Failed to start hotkey manager: {e}")
            self.running = False

    def stop(self):
        """Stop global hotkey listener"""
        if not self.running:
            return

        self.running = False
        if self.listener:
            self.listener.stop()
            self.listener = None

        logger.info("Hotkey manager stopped")

    def on_key_press(self, key):
        """Handle key press events"""
        if not self.running:
            return

        try:
            self.pressed_keys.add(key)

            # Check if hotkey combination is pressed
            if self.hotkey_combination.issubset(self.pressed_keys):
                self.trigger_callback()

        except Exception as e:
            logger.error(f"Error in key press handler: {e}")

    def on_key_release(self, key):
        """Handle key release events"""
        if not self.running:
            return

        try:
            self.pressed_keys.discard(key)
        except Exception as e:
            logger.error(f"Error in key release handler: {e}")

    def trigger_callback(self):
        """Trigger the callback in the main thread using Qt signal"""
        try:
            # Emit signal which will be handled in main thread
            self.hotkey_triggered.emit()
        except Exception as e:
            logger.error(f"Error triggering callback: {e}")
