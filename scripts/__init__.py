# clipboard_manager/scripts/__init__.py
"""
Build and installation scripts
"""

# clipboard_manager/scripts/build.py
"""
Build script for creating executables
"""
import shutil
import subprocess
import sys
from pathlib import Path


def build_executable():
    """Build standalone executable using PyInstaller"""

    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Get project root
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    main_py = src_path / "main.py"

    # Build command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name",
        "B1Clip",
        "--icon",
        (
            str(project_root / "resources" / "icons" / "app.ico")
            if (project_root / "resources" / "icons" / "app.ico").exists()
            else None
        ),
        "--add-data",
        f"{src_path};src",
        "--hidden-import",
        "PySide6.QtCore",
        "--hidden-import",
        "PySide6.QtGui",
        "--hidden-import",
        "PySide6.QtWidgets",
        "--hidden-import",
        "pynput",
        str(main_py),
    ]

    # Remove None values
    cmd = [arg for arg in cmd if arg is not None]

    print("Building executable...")
    print(" ".join(cmd))

    try:
        subprocess.check_call(cmd, cwd=project_root)
        print("✅ Build successful! Executable created in dist/ folder")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

    return True


def build_installer():
    """Build installer (Windows only)"""
    if sys.platform != "win32":
        print("Installer creation is only supported on Windows")
        return False

    try:
        # You would use NSIS or Inno Setup here
        print("Installer creation not implemented yet")
        return False
    except Exception as e:
        print(f"❌ Installer creation failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "installer":
        build_installer()
    else:
        build_executable()
