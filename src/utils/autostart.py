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
        self.app_display_name = "Clipboard Manager"

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
        """Enable auto-start on Linux with proper desktop entry"""
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)

        desktop_file = autostart_dir / f"{self.app_name}.desktop"

        # Get correct executable path
        if hasattr(sys, "frozen"):  # Running as executable
            exe_path = sys.executable
        else:  # Running as script
            main_path = Path(__file__).parent.parent / "main.py"
            # Use absolute path and proper escaping
            exe_path = f"{sys.executable} {main_path.absolute()}"

        # Create proper desktop entry
        content = f"""[Desktop Entry]
            Type=Application
            Name={self.app_display_name}
            Comment=Clipboard history manager with modern UI
            GenericName=Clipboard Manager
            Exec={exe_path}
            Icon=clipboard-manager
            Terminal=false
            NoDisplay=false
            Hidden=false
            X-GNOME-Autostart-enabled=true
            Categories=Utility;System;
            Keywords=clipboard;history;manager;
            StartupNotify=true
            """

        try:
            with open(desktop_file, "w", encoding="utf-8") as f:
                f.write(content)

            # Set proper permissions
            desktop_file.chmod(0o644)

            logger.info(f"Created autostart entry: {desktop_file}")

        except Exception as e:
            logger.error(f"Failed to create desktop entry: {e}")
            raise

    def _disable_linux(self):
        """Disable auto-start on Linux"""
        autostart_dir = Path.home() / ".config" / "autostart"
        desktop_file = autostart_dir / f"{self.app_name}.desktop"

        try:
            if desktop_file.exists():
                desktop_file.unlink()
                logger.info(f"Removed autostart entry: {desktop_file}")
            else:
                logger.info("No autostart entry found to remove")
        except Exception as e:
            logger.error(f"Failed to remove desktop entry: {e}")
            raise

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

    def is_enabled(self):
        """Check if auto-start is currently enabled"""
        try:
            if self.system == "linux":
                autostart_dir = Path.home() / ".config" / "autostart"
                desktop_file = autostart_dir / f"{self.app_name}.desktop"
                return desktop_file.exists()
            elif self.system == "windows":
                import winreg

                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0,
                        winreg.KEY_READ,
                    )
                    winreg.QueryValueEx(key, self.app_name)
                    winreg.CloseKey(key)
                    return True
                except FileNotFoundError:
                    return False
            else:
                return False
        except Exception as e:
            logger.error(f"Error checking autostart status: {e}")
            return False
