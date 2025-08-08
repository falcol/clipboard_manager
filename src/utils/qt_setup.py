# clipboard_manager/src/utils/qt_setup.py
"""
Qt environment setup utilities for cross-platform compatibility
"""
import os
import platform
from pathlib import Path

from utils.logging_config import get_logger


def setup_qt_environment():
    """Setup Qt environment with cross-platform enhancements"""
    current_platform = platform.system().lower()
    logger = get_logger(__name__)

    if current_platform == "windows":
        _setup_windows_qt_environment(logger)
    else:
        _setup_linux_qt_environment(logger)

    # Enable smooth rendering
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"


def _setup_windows_qt_environment(logger):
    """Setup Windows-specific Qt environment"""
    # Windows-specific Qt settings
    os.environ["QT_QPA_PLATFORM"] = "windows"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    # Windows-specific plugin path
    possible_windows_paths = [
        str(
            Path.home()
            / "AppData/Local/Programs/Python/Lib/site-packages/PySide6/plugins"
        ),
        str(
            Path.home()
            / "AppData/Local/Programs/Python/Lib/site-packages/PySide6/Qt6/plugins"
        ),
        "C:/Program Files/Python*/Lib/site-packages/PySide6/plugins",
    ]

    for path in possible_windows_paths:
        if Path(path).exists():
            os.environ["QT_PLUGIN_PATH"] = path
            logger.info(f"Set Windows QT_PLUGIN_PATH to {path}")
            break


def _setup_linux_qt_environment(logger):
    """Setup Linux/macOS Qt environment"""
    # Linux/macOS settings
    os.environ["QT_QPA_PLATFORM"] = "xcb:fallback=wayland:fallback=offscreen"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    # Linux plugin paths
    possible_paths = [
        "/usr/lib/x86_64-linux-gnu/qt6/plugins",
        "/usr/lib/qt6/plugins",
        "/usr/local/lib/qt6/plugins",
        str(Path.home() / ".local/lib/qt6/plugins"),
    ]

    for path in possible_paths:
        if Path(path).exists():
            os.environ["QT_PLUGIN_PATH"] = path
            logger.info(f"Set Linux QT_PLUGIN_PATH to {path}")
            break
