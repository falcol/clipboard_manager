#!/usr/bin/env python3
# clipboard_manager/scripts/create_deb.py
"""
Modern Debian package builder for B1Clip
Creates .deb package with proper dependencies and metadata
"""
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List


class DebianPackageBuilder:
    """Modern Debian package builder with proper metadata handling"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.app_name = "B1Clip"
        self.version = self._get_version()
        self.architecture = "all"

    def _get_version(self) -> str:
        """Get version from pyproject.toml or fallback to default"""
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomllib
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    return data.get("project", {}).get("version", "1.0.0")
            except ImportError:
                # Python < 3.11 fallback
                try:
                    import tomli
                    with open(pyproject_path, "rb") as f:
                        data = tomli.load(f)
                        return data.get("project", {}).get("version", "1.0.0")
                except ImportError:
                    pass
            except Exception as e:
                # Handle any TOML parsing errors
                print(f"Warning: Could not parse pyproject.toml: {e}")
                print("Using default version 1.0.0")
        return "1.0.0"

    def _get_dependencies(self) -> List[str]:
        """Get system dependencies for Debian package"""
        return [
            "python3 (>= 3.9)",
            "python3-pip",
            "python3-venv",
            "python3-dev",
            "libxcb-cursor0",
            "libxcb1",
            "libxcb-icccm4",
            "libxcb-image0",
            "libxcb-keysyms1",
            "libxcb-randr0",
            "libxcb-render-util0",
            "libxcb-shape0",
            "libxcb-sync1",
            "libxcb-xfixes0",
            "libxcb-xinerama0",
            "libxcb-xkb1",
            "libxcb-xinput0",
            "libgl1-mesa-glx",
            "libglib2.0-0",
            "libfontconfig1",
            "libdbus-1-3",
            "xdotool"
        ]

    def _create_control_file(self, debian_dir: Path) -> None:
        """Create DEBIAN/control file with proper metadata"""
        dependencies = ", ".join(self._get_dependencies())

        control_content = f"""Package: {self.app_name}
Version: {self.version}
Section: utils
Priority: optional
Architecture: {self.architecture}
Depends: {dependencies}
Recommends: git
Suggests: imagemagick, librsvg2-bin
Maintainer: B1Clip Team <contact@clipboardmanager.dev>
Homepage: https://github.com/falcol/clipboard_manager
Description: Modern cross-platform clipboard history manager
 A modern clipboard history manager built with PySide6/Qt6 that provides:
 .
 • Automatic clipboard history with text and image support
 • Global hotkey activation (Super+C)
 • Pin functionality for important items
 • Modern dark theme with smooth animations
 • System tray integration and auto-start
 • Cross-platform compatibility (Linux, Windows, macOS)
 • SQLite-based efficient storage
 • Configurable settings and preferences
 .
 This application runs in the background and provides quick access to
 clipboard history through a global hotkey, similar to Windows 10/11
 clipboard manager (Win+V) but with additional features and customization.
"""

        with open(debian_dir / "control", "w", encoding="utf-8") as f:
            f.write(control_content)

    def _create_postinst_script(self, debian_dir: Path) -> None:
        """Create post-installation script"""
        postinst_content = f"""#!/bin/bash
set -e

APP_NAME="{self.app_name}"
INSTALL_DIR="/opt/$APP_NAME"

echo "Setting up B1Clip..."

# Create virtual environment and install Python dependencies
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip setuptools wheel

# Install from requirements or pyproject.toml
if [ -f "requirements/linux.txt" ]; then
    pip install -r requirements/linux.txt
elif [ -f "requirements/base.txt" ]; then
    pip install -r requirements/base.txt
    pip install evdev python-xlib  # Linux-specific
elif [ -f "pyproject.toml" ]; then
    pip install -e ".[linux]"
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: No requirements file found, installing core dependencies..."
    pip install PySide6 appdirs setproctitle pynput keyboard pillow click
    pip install evdev python-xlib  # Linux-specific
fi

deactivate

# Set proper permissions
chmod +x /usr/local/bin/$APP_NAME
chmod -R 755 "$INSTALL_DIR"

# Update desktop database
if command -v update-desktop-database > /dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

# Update icon cache
if command -v gtk-update-icon-cache > /dev/null; then
    gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
fi

# Update mime database
if command -v update-mime-database > /dev/null; then
    update-mime-database /usr/share/mime 2>/dev/null || true
fi

echo "B1Clip installed successfully!"
echo ""
echo "Usage:"
echo "  • Run from terminal: $APP_NAME"
echo "  • Find in applications menu: B1Clip"
echo "  • Use global hotkey: Super+C"
echo ""
echo "To enable autostart: systemctl --user enable $APP_NAME"
"""

        postinst_file = debian_dir / "postinst"
        with open(postinst_file, "w", encoding="utf-8") as f:
            f.write(postinst_content)
        postinst_file.chmod(0o755)

    def _create_prerm_script(self, debian_dir: Path) -> None:
        """Create pre-removal script"""
        prerm_content = f"""#!/bin/bash
set -e

APP_NAME="{self.app_name}"

echo "Stopping B1Clip..."

# Stop user service if running
systemctl --user stop "$APP_NAME" 2>/dev/null || true
systemctl --user disable "$APP_NAME" 2>/dev/null || true

# Kill any running instances
pkill -f "clipboard.manager" 2>/dev/null || true
pkill -f "python.*main.py" 2>/dev/null || true

# Give processes time to exit gracefully
sleep 2

echo "B1Clip stopped."
"""

        prerm_file = debian_dir / "prerm"
        with open(prerm_file, "w", encoding="utf-8") as f:
            f.write(prerm_content)
        prerm_file.chmod(0o755)

    def _create_postrm_script(self, debian_dir: Path) -> None:
        """Create post-removal script with cleanup"""
        postrm_content = f"""#!/bin/bash
set -e

APP_NAME="{self.app_name}"

if [ "$1" = "purge" ]; then
    echo "🧹 Cleaning up B1Clip configuration and user data..."

    # Stop and disable user services for all users
    for user_home in /home/*; do
        if [ -d "$user_home" ]; then
            user=$(basename "$user_home")

            # Skip non-user directories
            [ "$user" = "lost+found" ] && continue

            echo "Cleaning up for user: $user"

            # Stop and disable systemd user service
            sudo -u "$user" systemctl --user stop "$APP_NAME" 2>/dev/null || true
            sudo -u "$user" systemctl --user disable "$APP_NAME" 2>/dev/null || true

            # Remove user configuration directories
            [ -d "$user_home/.local/share/B1Clip" ] && rm -rf "$user_home/.local/share/B1Clip"
            [ -d "$user_home/.config/B1Clip" ] && rm -rf "$user_home/.config/B1Clip"

            # Remove autostart entries
            [ -f "$user_home/.config/autostart/B1Clip.desktop" ] && rm -f "$user_home/.config/autostart/B1Clip.desktop"

            echo "✅ Cleaned up for user: $user"
        fi
    done

    # Remove system-wide configuration remnants
    [ -f "/etc/xdg/autostart/B1Clip.desktop" ] && rm -f "/etc/xdg/autostart/B1Clip.desktop"

    # Clean up any remaining processes
    pkill -f "B1Clip" 2>/dev/null || true
    pkill -f "clipboard.*manager" 2>/dev/null || true

    # Update system databases
    if command -v update-desktop-database > /dev/null; then
        update-desktop-database /usr/share/applications 2>/dev/null || true
    fi

    if command -v gtk-update-icon-cache > /dev/null; then
        gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
    fi

    if command -v update-mime-database > /dev/null; then
        update-mime-database /usr/share/mime 2>/dev/null || true
    fi

    # Reload systemd user daemon for all users
    for user_home in /home/*; do
        if [ -d "$user_home" ]; then
            user=$(basename "$user_home")
            [ "$user" = "lost+found" ] && continue
            sudo -u "$user" systemctl --user daemon-reload 2>/dev/null || true
        fi
    done

    echo "✅ B1Clip completely removed and cleaned up."
fi
"""

        postrm_file = debian_dir / "postrm"
        with open(postrm_file, "w", encoding="utf-8") as f:
            f.write(postrm_content)
        postrm_file.chmod(0o755)

    def _copy_application_files(self, package_dir: Path) -> None:
        """Copy application files to package directory"""
        opt_dir = package_dir / "opt" / self.app_name

        # Copy source code
        if (self.project_root / "src").exists():
            shutil.copytree(self.project_root / "src", opt_dir / "src")
        else:
            raise FileNotFoundError("Source directory not found")

        # Copy resources
        if (self.project_root / "resources").exists():
            shutil.copytree(self.project_root / "resources", opt_dir / "resources")

        # Copy requirements
        if (self.project_root / "requirements").exists():
            shutil.copytree(self.project_root / "requirements", opt_dir / "requirements")
        elif (self.project_root / "requirements.txt").exists():
            shutil.copy2(self.project_root / "requirements.txt", opt_dir)

        # Copy configuration files
        for config_file in ["pyproject.toml", "README.md", "LICENSE"]:
            config_path = self.project_root / config_file
            if config_path.exists():
                shutil.copy2(config_path, opt_dir)

    def _create_launcher_script(self, package_dir: Path) -> None:
        """Create launcher script"""
        bin_dir = package_dir / "usr" / "local" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        launcher_content = f"""#!/bin/bash
# B1Clip launcher script
# This script activates the virtual environment and runs the application

APP_DIR="/opt/{self.app_name}"
VENV_DIR="$APP_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please reinstall the package."
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set Python path
export PYTHONPATH="$APP_DIR/src:$PYTHONPATH"

# Change to app directory
cd "$APP_DIR"

# Run the application
exec python3 src/main.py "$@"
"""

        launcher_file = bin_dir / self.app_name
        with open(launcher_file, "w", encoding="utf-8") as f:
            f.write(launcher_content)
        launcher_file.chmod(0o755)

    def _create_desktop_entry(self, package_dir: Path) -> None:
        """Create desktop entry file"""
        desktop_dir = package_dir / "usr" / "share" / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)

        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=B1Clip
GenericName=Clipboard History Manager
Comment=Modern clipboard history manager with global hotkey support
Exec={self.app_name}
Icon={self.app_name}
Terminal=false
Categories=Utility;System;Qt;Office;
Keywords=clipboard;history;manager;copy;paste;hotkey;
StartupWMClass=B1Clip
StartupNotify=true
MimeType=text/plain;text/html;image/png;image/jpeg;
X-GNOME-Autostart-enabled=false
X-KDE-autostart-after=panel
Actions=Settings;About;

[Desktop Action Settings]
Name=Settings
Exec={self.app_name} --settings
Icon=preferences-system

[Desktop Action About]
Name=About
Exec={self.app_name} --about
Icon=help-about
"""

        with open(desktop_dir / f"{self.app_name}.desktop", "w", encoding="utf-8") as f:
            f.write(desktop_content)

    def _create_icon(self, package_dir: Path) -> None:
        """Create application icon"""
        icon_dir = package_dir / "usr" / "share" / "icons" / "hicolor" / "48x48" / "apps"
        icon_dir.mkdir(parents=True, exist_ok=True)

        # Check if icon exists in resources
        resource_icon = self.project_root / "resources" / "icons" / "app_icon.png"
        if resource_icon.exists():
            shutil.copy2(resource_icon, icon_dir / f"{self.app_name}.png")
            return

        # Create SVG icon as fallback
        icon_svg_content = '''<svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#4A90E2;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#357ABD;stop-opacity:1" />
        </linearGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="1" dy="2" stdDeviation="2" flood-color="black" flood-opacity="0.3"/>
        </filter>
    </defs>

    <!-- Main clipboard body -->
    <rect x="8" y="6" width="32" height="38" rx="3" ry="3"
          fill="url(#gradient)" stroke="#2C5F93" stroke-width="1" filter="url(#shadow)"/>

    <!-- Clip -->
    <rect x="16" y="2" width="16" height="8" rx="2" ry="2"
          fill="#E8E8E8" stroke="#CCCCCC" stroke-width="1"/>

    <!-- Text lines -->
    <rect x="12" y="14" width="24" height="2" fill="#FFFFFF" opacity="0.9"/>
    <rect x="12" y="19" width="20" height="2" fill="#FFFFFF" opacity="0.7"/>
    <rect x="12" y="24" width="22" height="2" fill="#FFFFFF" opacity="0.7"/>
    <rect x="12" y="29" width="18" height="2" fill="#FFFFFF" opacity="0.5"/>
    <rect x="12" y="34" width="16" height="2" fill="#FFFFFF" opacity="0.5"/>

    <!-- Action indicator -->
    <circle cx="36" cy="36" r="6" fill="#FF6B6B" stroke="#E74C3C" stroke-width="1"/>
    <text x="36" y="39" text-anchor="middle" font-family="Arial" font-size="8" fill="white" font-weight="bold">∞</text>
</svg>'''

        with open(icon_dir / f"{self.app_name}.svg", "w", encoding="utf-8") as f:
            f.write(icon_svg_content)

    def _create_systemd_service(self, package_dir: Path) -> None:
        """Create systemd user service file"""
        systemd_dir = package_dir / "etc" / "systemd" / "user"
        systemd_dir.mkdir(parents=True, exist_ok=True)

        service_content = f"""[Unit]
Description=B1Clip - Modern clipboard history manager
Documentation=https://github.com/falcol/clipboard_manager
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/local/bin/{self.app_name}
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/%i
Environment=QT_QPA_PLATFORM=xcb

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.local/share/B1Clip

[Install]
WantedBy=default.target
"""

        with open(systemd_dir / f"{self.app_name}.service", "w", encoding="utf-8") as f:
            f.write(service_content)

    def build_package(self) -> bool:
        """Build the Debian package"""
        print(f"📦 Building Debian package for {self.app_name} v{self.version}...")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / f"{self.app_name}_{self.version}"
            debian_dir = package_dir / "DEBIAN"

            try:
                # Create package structure
                debian_dir.mkdir(parents=True, exist_ok=True)

                # Create DEBIAN files
                self._create_control_file(debian_dir)
                self._create_postinst_script(debian_dir)
                self._create_prerm_script(debian_dir)
                self._create_postrm_script(debian_dir)

                # Copy application files
                self._copy_application_files(package_dir)

                # Create system integration files
                self._create_launcher_script(package_dir)
                self._create_desktop_entry(package_dir)
                self._create_icon(package_dir)
                self._create_systemd_service(package_dir)

                # Build package
                print("🔨 Building .deb package...")
                result = subprocess.run(
                    ["dpkg-deb", "--build", "--root-owner-group", str(package_dir)],
                    cwd=temp_path,
                    check=True,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print("📦 Package built successfully")

                # Move package to project root
                package_file = temp_path / f"{self.app_name}_{self.version}.deb"
                output_file = self.project_root / f"{self.app_name}_{self.version}_all.deb"
                shutil.move(str(package_file), str(output_file))

                print(f"✅ Package created successfully: {output_file.name}")
                print(f"📏 Package size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
                print("")
                print("📥 Installation commands:")
                print(f"   sudo dpkg -i {output_file.name}")
                print("   sudo apt-get install -f  # Fix dependencies if needed")
                print("")
                print("🔍 Package info:")
                print(f"   dpkg -I {output_file.name}")
                print(f"   dpkg -c {output_file.name}")

                return True

            except subprocess.CalledProcessError as e:
                print(f"❌ Package build failed: {e}")
                print(f"stdout: {e.stdout}")
                print(f"stderr: {e.stderr}")
                return False
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                return False


def main():
    """Main function"""
    builder = DebianPackageBuilder()
    success = builder.build_package()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
