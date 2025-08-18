# clipboard_manager/src/core/hotkey_manager.py
"""
Global hotkey management using pynput with cross-platform support.

Reads the hotkey combination from Config (e.g. "super+c", "ctrl+shift+v").
Falls back to a reasonable per-platform default if parsing fails.
"""
import logging
import platform
from typing import TYPE_CHECKING, Callable, Optional, Set

from pynput import keyboard
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as pyqtSignal

if TYPE_CHECKING:
    # Imported only for type checking to avoid runtime dependency cycle
    from utils.config import Config

logger = logging.getLogger(__name__)


class HotkeyManager(QObject):
    """global hotkey manager with cross-platform support"""

    hotkey_triggered = pyqtSignal()

    def __init__(self, callback: Callable[[], None], config: Optional["Config"] = None):
        super().__init__()
        self.callback = callback
        self.listener: Optional[keyboard.Listener] = None
        self.running = False
        self.current_platform = platform.system().lower()
        self.config = config

        # cross-platform hotkey detection
        self.setup_hotkey_combination()

        self.pressed_keys = set()
        self.last_trigger_time = 0  # Prevent double triggers

        # Connect signal to callback
        self.hotkey_triggered.connect(self.callback)

    def setup_hotkey_combination(self):
        """Setup hotkey combination based on config or platform defaults."""
        # Try from config first
        hotkey_str = None
        if self.config is not None:
            try:
                hotkey_str = self.config.get("hotkey")
            except Exception:
                hotkey_str = None

        combination: Optional[Set[object]] = None
        if isinstance(hotkey_str, str) and hotkey_str.strip():
            combination = self._parse_hotkey(hotkey_str)

        # Fallback per platform
        if not combination:
            if self.current_platform == "windows":
                # Avoid default Windows+C conflict by using Windows+Shift+V
                combination = self._parse_hotkey("win+shift+v") or {
                    keyboard.Key.cmd,
                    keyboard.Key.shift,
                    keyboard.KeyCode.from_char("v"),
                }
            elif self.current_platform == "linux":
                combination = self._parse_hotkey("super+c") or {
                    getattr(keyboard.Key, "super_l", keyboard.Key.cmd),
                    keyboard.KeyCode.from_char("c"),
                }
            else:
                combination = self._parse_hotkey("cmd+c") or {
                    keyboard.Key.cmd,
                    keyboard.KeyCode.from_char("c"),
                }

        self.hotkey_combination = combination
        logger.info(f"Hotkey combination: {self._display_hotkey()} -> {self.hotkey_combination}")

    def _parse_hotkey(self, hotkey: str) -> Optional[Set[object]]:
        """Parse a hotkey string like 'ctrl+alt+h' to a set of pynput keys.

        Returns None if parsing fails.
        """
        try:
            parts = [p.strip().lower() for p in hotkey.split("+") if p.strip()]
            if not parts:
                return None

            keyset: Set[object] = set()
            modmap = {
                "ctrl": keyboard.Key.ctrl,
                "control": keyboard.Key.ctrl,
                "alt": keyboard.Key.alt,
                "shift": keyboard.Key.shift,
                "cmd": keyboard.Key.cmd,
                "win": getattr(keyboard.Key, "cmd", keyboard.Key.cmd),
                "super": getattr(keyboard.Key, "super_l", keyboard.Key.cmd),
                "super_l": getattr(keyboard.Key, "super_l", keyboard.Key.cmd),
            }
            for token in parts:
                if token in modmap:
                    keyset.add(modmap[token])
                else:
                    # Assume last token is the main key
                    if len(token) == 1:
                        keyset.add(keyboard.KeyCode.from_char(token))
                    else:
                        # Named special key (e.g., 'enter', 'tab')
                        special = getattr(keyboard.Key, token, None)
                        if special is None:
                            return None
                        keyset.add(special)

            return keyset if keyset else None
        except Exception as e:
            logger.error(f"Failed to parse hotkey '{hotkey}': {e}")
            return None

    def _display_hotkey(self) -> str:
        """Return a human-readable string for current hotkey from config if available."""
        if self.config is not None:
            try:
                hk = self.config.get("hotkey")
                if isinstance(hk, str) and hk:
                    return hk
            except Exception:
                pass
        # Fallback
        if self.current_platform == "windows":
            return "win+shift+v"
        if self.current_platform == "linux":
            return "super+c"
        return "cmd+c"

    def start(self):
        """Start global hotkey listener with error handling"""
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
            # self.test_key_detection()

        except Exception as e:
            logger.error(f"Failed to start hotkey manager: {e}")
            self.running = False

    def update_from_config(self):
        """Re-setup the hotkey based on (possibly updated) config."""
        try:
            # Stop existing listener
            if self.listener is not None and self.running:
                self.stop()
            # Recompute combination
            self.setup_hotkey_combination()
            # Restart if previously running
            self.start()
        except Exception as e:
            logger.error(f"Failed to update hotkey from config: {e}")

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
        """key press handler with detailed logging"""
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
        """key release handler"""
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
            "display": self._display_hotkey(),
            "running": self.running,
            "pressed_keys": [str(k) for k in self.pressed_keys],
        }
