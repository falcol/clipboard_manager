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
        self.app_name = "B1Clip"

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

        # Determine executable path
        exe_path = sys.executable
        if not hasattr(sys, "frozen"):  # Running as script
            main_path = Path(__file__).parent.parent / "main.py"
            exe_path = f"{sys.executable} {main_path}"

        # Determine icon path (if exists)
        icon_path = ""
        icon_dir = Path(__file__).parent.parent.parent / "resources" / "icons"

        # Try specific icon first, then fallback to any available
        specific_icon = icon_dir / "app.png"
        if specific_icon.exists():
            icon_path = str(specific_icon)
        else:
            # Fallback: find any available icon
            icon_files = list(icon_dir.glob("*.png")) + list(icon_dir.glob("*.svg"))
            if icon_files:
                icon_path = str(icon_files[0])

        # Add this for debugging
        if icon_path:
            logger.info(f"Using icon: {icon_path}")
        else:
            logger.warning(f"No icon found in: {icon_dir}")

        # Create standard desktop entry
        content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={self.app_name}
Comment=Clipboard Manager Application
Exec={exe_path}
Terminal=false
Categories=Utility;
StartupNotify=true
X-GNOME-Autostart-enabled=true
"""

        if icon_path:
            content += f"Icon={icon_path}\n"

        # Write file and set permissions
        with open(desktop_file, "w") as f:
            f.write(content)

        # Set executable permission for desktop file
        desktop_file.chmod(0o755)

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

    def _validate_linux_autostart(self):
        """Validate Linux autostart configuration"""
        autostart_dir = Path.home() / ".config" / "autostart"
        desktop_file = autostart_dir / f"{self.app_name}.desktop"

        if not desktop_file.exists():
            return False

        # Check executable permission
        if not desktop_file.stat().st_mode & 0o111:
            return False

        # Check file content
        try:
            with open(desktop_file, "r") as f:
                content = f.read()
                return "[Desktop Entry]" in content and "Exec=" in content
        except Exception as e:
            logger.error(f"Error validating Linux autostart: {e}")
            return False
