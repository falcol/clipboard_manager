# clipboard_manager/src/core/hotkey_manager.py
"""
Global hotkey management using pynput with enhanced Windows support
"""
import logging
import platform
from typing import Callable, Optional

from pynput import keyboard
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as pyqtSignal

logger = logging.getLogger(__name__)


class HotkeyManager(QObject):
    """Enhanced global hotkey manager with cross-platform support"""

    hotkey_triggered = pyqtSignal()

    def __init__(self, callback: Callable[[], None]):
        super().__init__()
        self.callback = callback
        self.listener: Optional[keyboard.Listener] = None
        self.running = False
        self.current_platform = platform.system().lower()

        # Enhanced cross-platform hotkey detection
        self.setup_hotkey_combination()

        self.pressed_keys = set()
        self.last_trigger_time = 0  # Prevent double triggers

        # Connect signal to callback
        self.hotkey_triggered.connect(self.callback)

    def setup_hotkey_combination(self):
        """Setup hotkey combination based on platform"""
        if self.current_platform == "windows":
            # Windows: Use Windows key + C (avoid conflict with Windows+C)
            try:
                # Try Windows key first
                windows_key = getattr(
                    keyboard.Key, "cmd", keyboard.Key.cmd
                )  # Windows key
                if windows_key:
                    self.hotkey_combination = {
                        windows_key,
                        keyboard.KeyCode.from_char("c"),
                    }
                    logger.info("Windows: Using Windows+C hotkey")
                else:
                    # Fallback to cmd (Command key on Windows)
                    self.hotkey_combination = {
                        keyboard.Key.cmd,
                        keyboard.KeyCode.from_char("c"),
                    }
                    logger.info("Windows: Using Cmd+C hotkey (fallback)")
            except Exception as e:
                logger.error(f"Windows hotkey setup error: {e}")
                # Final fallback
                self.hotkey_combination = {
                    keyboard.Key.cmd,
                    keyboard.KeyCode.from_char("c"),
                }

        elif self.current_platform == "linux":
            # Linux: Use Super key + V (keep original)
            try:
                super_key = getattr(keyboard.Key, "super_l", keyboard.Key.cmd)
                self.hotkey_combination = {super_key, keyboard.KeyCode.from_char("c")}
                logger.info("Linux: Using Super+C hotkey")
            except Exception as e:
                logger.error(f"Linux hotkey setup error: {e}")
                self.hotkey_combination = {
                    keyboard.Key.cmd,
                    keyboard.KeyCode.from_char("c"),
                }

        else:
            # macOS and others: Use Cmd + C
            self.hotkey_combination = {
                keyboard.Key.cmd,
                keyboard.KeyCode.from_char("c"),
            }
            logger.info(f"{self.current_platform}: Using Cmd+C hotkey")

        logger.info(f"Hotkey combination: {self.hotkey_combination}")

    def start(self):
        """Start global hotkey listener with enhanced error handling"""
        if self.running:
            return

        try:
            self.running = True
            self.listener = keyboard.Listener(
                on_press=self.on_key_press, on_release=self.on_key_release
            )
            self.listener.start()

            # Log current pressed keys for debugging
            logger.info(f"Hotkey manager started on {self.current_platform}")
            logger.info(f"Listening for: {self.hotkey_combination}")

            # Test key detection
            self.test_key_detection()

        except Exception as e:
            logger.error(f"Failed to start hotkey manager: {e}")
            self.running = False

    def test_key_detection(self):
        """Test key detection for debugging"""
        try:
            logger.info("Testing key detection...")
            available_keys = [k for k in dir(keyboard.Key) if not k.startswith("_")]
            logger.info(f"Available keys: {available_keys}")
        except Exception as e:
            logger.error(f"Key detection test failed: {e}")

    def stop(self):
        """Stop global hotkey listener"""
        if not self.running:
            return

        self.running = False
        if self.listener:
            try:
                self.listener.stop()
                # Join underlying thread to ensure listener fully stops
                if hasattr(self.listener, "join"):
                    try:
                        self.listener.join(timeout=0.5)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error stopping hotkey listener: {e}")
            self.listener = None

        logger.info("Hotkey manager stopped")

    def on_key_press(self, key):
        """Enhanced key press handler with detailed logging"""
        if not self.running:
            return

        try:
            # Log key press for debugging
            key_str = str(key)
            logger.debug(f"Key pressed: {key_str}")

            self.pressed_keys.add(key)
            logger.debug(f"Current pressed keys: {[str(k) for k in self.pressed_keys]}")

            # Check if hotkey combination is pressed
            if self.hotkey_combination.issubset(self.pressed_keys):
                import time

                current_time = time.time()

                # Prevent double triggers (within 500ms)
                if current_time - self.last_trigger_time > 0.5:
                    logger.info(
                        f"Hotkey triggered! Keys: {[str(k) for k in self.pressed_keys]}"
                    )
                    self.trigger_callback()
                    self.last_trigger_time = current_time
                else:
                    logger.debug("Hotkey ignored (too soon after last trigger)")

        except Exception as e:
            logger.error(f"Error in key press handler: {e}")

    def on_key_release(self, key):
        """Enhanced key release handler"""
        if not self.running:
            return

        try:
            self.pressed_keys.discard(key)
            logger.debug(
                f"Key released: {key}, remaining: {[str(k) for k in self.pressed_keys]}"
            )
        except Exception as e:
            logger.error(f"Error in key release handler: {e}")

    def trigger_callback(self):
        """Trigger the callback in the main thread using Qt signal"""
        try:
            logger.info("Emitting hotkey signal")
            self.hotkey_triggered.emit()
        except Exception as e:
            logger.error(f"Error triggering callback: {e}")

    def get_hotkey_info(self):
        """Get current hotkey information for debugging"""
        return {
            "platform": self.current_platform,
            "combination": [str(k) for k in self.hotkey_combination],
            "running": self.running,
            "pressed_keys": [str(k) for k in self.pressed_keys],
        }
