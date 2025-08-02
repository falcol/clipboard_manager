# clipboard_manager/src/utils/autostart.py
"""
Auto-start functionality for different platforms
"""
import logging
import platform
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class AutostartManager:
    """Manage application auto-start"""

    def __init__(self):
        self.system = platform.system().lower()
        self.app_name = "ClipboardManager"

    def enable(self):
        """Enable auto-start"""
        try:
            if self.system == "windows":
                self._enable_windows()
            elif self.system == "linux":
                self._enable_linux()
            elif self.system == "darwin":  # macOS
                self._enable_macos()

            logger.info("Auto-start enabled")
            return True

        except Exception as e:
            logger.error(f"Failed to enable auto-start: {e}")
            return False

    def disable(self):
        """Disable auto-start"""
        try:
            if self.system == "windows":
                self._disable_windows()
            elif self.system == "linux":
                self._disable_linux()
            elif self.system == "darwin":  # macOS
                self._disable_macos()

            logger.info("Auto-start disabled")
            return True

        except Exception as e:
            logger.error(f"Failed to disable auto-start: {e}")
            return False

    def _enable_windows(self):
        """Enable auto-start on Windows"""
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_ALL_ACCESS,
        )

        exe_path = sys.executable
        if hasattr(sys, "frozen"):  # Running as executable
            exe_path = sys.executable
        else:  # Running as script
            main_path = Path(__file__).parent.parent / "main.py"
            exe_path = f'"{sys.executable}" "{main_path}"'

        winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)

    def _disable_windows(self):
        """Disable auto-start on Windows"""
        import winreg

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_ALL_ACCESS,
            )
            winreg.DeleteValue(key, self.app_name)
            winreg.CloseKey(key)
        except FileNotFoundError:
            pass  # Key doesn't exist

    def _enable_linux(self):
        """Enable auto-start on Linux"""
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)

        desktop_file = autostart_dir / f"{self.app_name}.desktop"

        exe_path = sys.executable
        if not hasattr(sys, "frozen"):  # Running as script
            main_path = Path(__file__).parent.parent / "main.py"
            exe_path = f"{sys.executable} {main_path}"

        content = f"""[Desktop Entry]
                Type=Application
                Name={self.app_name}
                Exec={exe_path}
                Hidden=false
                NoDisplay=false
                X-GNOME-Autostart-enabled=true
                """

        with open(desktop_file, "w") as f:
            f.write(content)

    def _disable_linux(self):
        """Disable auto-start on Linux"""
        autostart_dir = Path.home() / ".config" / "autostart"
        desktop_file = autostart_dir / f"{self.app_name}.desktop"

        if desktop_file.exists():
            desktop_file.unlink()

    def _enable_macos(self):
        """Enable auto-start on macOS"""
        # macOS implementation would require creating a launch agent
        # This is a placeholder for future implementation
        logger.warning("macOS auto-start not implemented yet")

    def _disable_macos(self):
        """Disable auto-start on macOS"""
        # macOS implementation would require removing launch agent
        # This is a placeholder for future implementation
        logger.warning("macOS auto-start not implemented yet")
