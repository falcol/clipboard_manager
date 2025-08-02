# clipboard_manager/scripts/create_deb.py
"""
Create Debian package for Ubuntu/Debian systems
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def create_debian_package():
    """Create .deb package"""

    project_root = Path(__file__).parent.parent
    app_name = "clipboard-manager"
    version = "1.0.0"

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

        # Create control file
        control_content = f"""Package: {app_name}
Version: {version}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pip
Maintainer: Your Name <your.email@example.com>
Description: Cross-platform clipboard history manager
 A modern clipboard history manager with global hotkey support,
 pin functionality, and cross-platform compatibility.
"""

        with open(debian_dir / "control", "w") as f:
            f.write(control_content)

        # Create postinst script
        postinst_content = f"""#!/bin/bash
set -e

# Install Python dependencies
pip3 install -r /opt/{app_name}/requirements.txt

# Update desktop database
if command -v update-desktop-database > /dev/null; then
    update-desktop-database /usr/share/applications
fi

# Update icon cache
if command -v gtk-update-icon-cache > /dev/null; then
    gtk-update-icon-cache /usr/share/icons/hicolor
fi

echo "Clipboard Manager installed successfully!"
echo "Run 'clipboard-manager' to start the application."
"""

        postinst_file = debian_dir / "postinst"
        with open(postinst_file, "w") as f:
            f.write(postinst_content)
        postinst_file.chmod(0o755)

        # Create prerm script
        prerm_content = """#!/bin/bash
set -e

# Stop the application if running
pkill -f "clipboard-manager" || true
"""

        prerm_file = debian_dir / "prerm"
        with open(prerm_file, "w") as f:
            f.write(prerm_content)
        prerm_file.chmod(0o755)

        # Create launcher script
        launcher_content = f"""#!/bin/bash
cd /opt/{app_name}
python3 src/main.py "$@"
"""

        launcher_file = bin_dir / app_name
        with open(launcher_file, "w") as f:
            f.write(launcher_content)
        launcher_file.chmod(0o755)

        # Create desktop entry
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Clipboard Manager
Comment=Cross-platform clipboard history manager
Exec={app_name}
Icon={app_name}
Terminal=false
Categories=Utility;
StartupWMClass=clipboard-manager
"""

        with open(desktop_dir / f"{app_name}.desktop", "w") as f:
            f.write(desktop_content)

        # Create simple icon
        icon_content = """<svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
    <rect width="32" height="40" x="8" y="4" fill="#ffffff" stroke="#000000" stroke-width="2"/>
    <rect width="16" height="6" x="16" y="0" fill="#cccccc" stroke="#000000" stroke-width="1"/>
    <text x="24" y="28" text-anchor="middle" font-family="Arial" font-size="20">📋</text>
</svg>"""

        with open(icon_dir / f"{app_name}.svg", "w") as f:
            f.write(icon_content)

        # Build package
        print("📦 Building Debian package...")
        try:
            subprocess.run(
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

            print(f"✅ Package created: {output_file}")
            print(f"📥 Install with: sudo dpkg -i {output_file.name}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Package build failed: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False


if __name__ == "__main__":
    create_debian_package()
