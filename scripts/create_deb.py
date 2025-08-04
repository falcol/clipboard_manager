# clipboard_manager/scripts/create_deb.py
"""
Create Debian package for Ubuntu/Debian systems
"""
import shutil
import subprocess
import tempfile
from pathlib import Path


def create_debian_package():
    """Create .deb package with improved structure"""

    project_root = Path(__file__).parent.parent
    app_name = "clipboard-manager"
    version = "2.0.0"  # Updated version

    # Create temporary directory for package
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        package_dir = temp_path / f"{app_name}_{version}"

        # Create package structure
        debian_dir = package_dir / "DEBIAN"
        opt_dir = package_dir / "opt" / app_name
        bin_dir = package_dir / "usr" / "local" / "bin"
        desktop_dir = package_dir / "usr" / "share" / "applications"
        icon_dir = (
            package_dir / "usr" / "share" / "icons" / "hicolor" / "48x48" / "apps"
        )

        # Create directories
        for dir_path in [debian_dir, opt_dir, bin_dir, desktop_dir, icon_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Copy application files
        shutil.copytree(project_root / "src", opt_dir / "src")
        shutil.copy2(project_root / "requirements.txt", opt_dir)

        # Create improved control file
        control_content = f"""Package: {app_name}
            Version: {version}
            Section: utils
            Priority: optional
            Architecture: all
            Depends: python3 (>= 3.8), python3-pip, python3-pyside6, python3-pynput
            Recommends: python3-appdirs, python3-evdev
            Maintainer: Clipboard Manager Team <team@clipboard-manager.com>
            Homepage: https://github.com/your-repo/clipboard-manager
            Description: Modern clipboard history manager
            A cross-platform clipboard history manager with global hotkey support,
            pin functionality, and modern UI. Features include:
            .
            * Global hotkey (Super+V) to show clipboard history
            * Pin important items for quick access
            * Search through clipboard history
            * Support for text and image content
            * Modern dark theme UI
            * Cross-platform compatibility
            .
            This package provides the clipboard manager application.
        """

        with open(debian_dir / "control", "w") as f:
            f.write(control_content)

        # Create improved postinst script
        postinst_content = f"""#!/bin/bash
            set -e

            echo "Installing Clipboard Manager dependencies..."

            # Install Python dependencies with user flag
            if command -v pip3 > /dev/null; then
                pip3 install --user -r /opt/{app_name}/requirements.txt
            else
                echo "Warning: pip3 not found, please install dependencies manually"
            fi

            # Update desktop database
            if command -v update-desktop-database > /dev/null; then
                update-desktop-database /usr/share/applications
            fi

            # Update icon cache
            if command -v gtk-update-icon-cache > /dev/null; then
                gtk-update-icon-cache /usr/share/icons/hicolor
            fi

            # Create user data directory
            mkdir -p $HOME/.config/clipboard-manager

            echo "✅ Clipboard Manager installed successfully!"
            echo " Run 'clipboard-manager' to start the application."
            echo "⚙️  Access settings via system tray icon."
        """

        postinst_file = debian_dir / "postinst"
        with open(postinst_file, "w") as f:
            f.write(postinst_content)
        postinst_file.chmod(0o755)

        # Create improved prerm script
        prerm_content = """#!/bin/bash
            set -e

            echo "Stopping Clipboard Manager..."

            # Stop the application if running
            pkill -f "clipboard-manager" || true
            pkill -f "python3.*main.py" || true

            echo "Clipboard Manager stopped."
        """

        prerm_file = debian_dir / "prerm"
        with open(prerm_file, "w") as f:
            f.write(prerm_content)
        prerm_file.chmod(0o755)

        # Create improved launcher script
        launcher_content = f"""#!/bin/bash
            # Clipboard Manager Launcher

            # Set application directory
            APP_DIR="/opt/{app_name}"

            # Check if application directory exists
            if [ ! -d "$APP_DIR" ]; then
                echo "Error: Application not found at $APP_DIR"
                exit 1
            fi

            # Change to application directory
            cd "$APP_DIR"

            # Run the application
            exec python3 src/main.py "$@"
            """

        launcher_file = bin_dir / app_name
        with open(launcher_file, "w") as f:
            f.write(launcher_content)
        launcher_file.chmod(0o755)

        # Create improved desktop entry
        desktop_content = f"""[Desktop Entry]
            Version=1.0
            Type=Application
            Name=Clipboard Manager
            Comment=Modern clipboard history manager with global hotkey support
            GenericName=Clipboard Manager
            Exec={app_name}
            Icon={app_name}
            Terminal=false
            NoDisplay=false
            Categories=Utility;System;Office;
            Keywords=clipboard;history;manager;copy;paste;
            StartupWMClass=clipboard-manager
            StartupNotify=true
            MimeType=text/plain;image/png;image/jpeg;
            """

        with open(desktop_dir / f"{app_name}.desktop", "w") as f:
            f.write(desktop_content)

        # Create improved SVG icon
        icon_content = """<svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#4facfe;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#00f2fe;stop-opacity:1" />
                </linearGradient>
            </defs>
            <rect width="48" height="48" rx="8" fill="url(#bg)"/>
            <rect width="32" height="40" x="8" y="4"
                fill="rgba(255,255,255,0.9)" stroke="rgba(255,255,255,0.3)"
                stroke-width="1" rx="2"/>
            <rect width="16" height="6" x="16" y="0"
                fill="rgba(255,255,255,0.7)" stroke="rgba(255,255,255,0.3)"
                stroke-width="1" rx="1"/>
            <text x="24" y="28" text-anchor="middle"
                font-family="Arial, sans-serif" font-size="16"
                fill="rgba(255,255,255,0.9)">📋</text>
        </svg>"""

        with open(icon_dir / f"{app_name}.svg", "w") as f:
            f.write(icon_content)

        # Build package with improved error handling
        print("📦 Building Debian package...")
        try:
            # flake8: noqa: F841
            result = subprocess.run(
                ["dpkg-deb", "--build", str(package_dir)],
                cwd=temp_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Move package to project root
            package_file = temp_path / f"{app_name}_{version}.deb"
            output_file = project_root / f"{app_name}_{version}_all.deb"
            shutil.move(str(package_file), str(output_file))

            print(f"✅ Package created successfully: {output_file}")
            print(f" Install with: sudo dpkg -i {output_file.name}")
            print(f"🔧 Fix dependencies: sudo apt-get install -f")
            print(f"📋 Package size: {output_file.stat().st_size / 1024:.1f} KB")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Package build failed:")
            print(f"   Command: {e.cmd}")
            print(f"   Return code: {e.returncode}")
            if e.stdout:
                print(f"   stdout: {e.stdout}")
            if e.stderr:
                print(f"   stderr: {e.stderr}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False


if __name__ == "__main__":
    success = create_debian_package()
    exit(0 if success else 1)
