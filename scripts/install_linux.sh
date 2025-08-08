# clipboard_manager/scripts/install_linux.sh
#!/bin/bash
# clipboard_manager/scripts/install_linux.sh
# Modern Linux installation script with proper dependency management

set -e

# Configuration
APP_NAME="clipboard-manager"
APP_VERSION="1.0.0"
INSTALL_DIR="/opt/$APP_NAME"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/48x48/apps"
SYSTEMD_DIR="/etc/systemd/user"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run as root (use sudo)"
    fi
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif type lsb_release >/dev/null 2>&1; then
        lsb_release -si | tr '[:upper:]' '[:lower:]'
    else
        echo "unknown"
    fi
}

# Install system dependencies
install_system_deps() {
    local distro=$(detect_distro)
    log_info "Detected distribution: $distro"

    case "$distro" in
        ubuntu|debian)
            log_info "Installing system dependencies for Ubuntu/Debian..."
            apt update
            apt install -y \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                libxcb-cursor0 \
                libxcb1 \
                libxcb-icccm4 \
                libxcb-image0 \
                libxcb-keysyms1 \
                libxcb-randr0 \
                libxcb-render-util0 \
                libxcb-shape0 \
                libxcb-sync1 \
                libxcb-xfixes0 \
                libxcb-xinerama0 \
                libxcb-xkb1 \
                libgl1-mesa-glx \
                libglib2.0-0 \
                xdotool \
                git
            ;;
        fedora|centos|rhel)
            log_info "Installing system dependencies for Fedora/CentOS/RHEL..."
            dnf install -y \
                python3 \
                python3-pip \
                python3-devel \
                libxcb \
                libxcb-devel \
                xcb-util-cursor \
                xcb-util-image \
                xcb-util-keysyms \
                xcb-util-renderutil \
                xcb-util-wm \
                mesa-libGL \
                glib2 \
                xdotool \
                git
            ;;
        arch)
            log_info "Installing system dependencies for Arch Linux..."
            pacman -Sy --noconfirm \
                python \
                python-pip \
                libxcb \
                xcb-util-cursor \
                xcb-util-image \
                xcb-util-keysyms \
                xcb-util-renderutil \
                xcb-util-wm \
                mesa \
                glib2 \
                xdotool \
                git
            ;;
        *)
            log_warning "Unsupported distribution: $distro"
            log_warning "Please install Python 3.9+, pip, and Qt/XCB libraries manually"
            ;;
    esac
}

# Create installation directories
create_directories() {
    log_info "Creating installation directories..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICON_DIR"
    mkdir -p "$SYSTEMD_DIR"
}

# Copy application files
copy_files() {
    log_info "Copying application files..."

    # Get script directory (project root)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

    # Copy source code
    if [ -d "$PROJECT_ROOT/src" ]; then
        cp -r "$PROJECT_ROOT/src" "$INSTALL_DIR/"
    else
        log_error "Source directory not found: $PROJECT_ROOT/src"
    fi

    # Copy resources
    if [ -d "$PROJECT_ROOT/resources" ]; then
        cp -r "$PROJECT_ROOT/resources" "$INSTALL_DIR/"
    fi

    # Copy requirements
    if [ -d "$PROJECT_ROOT/requirements" ]; then
        cp -r "$PROJECT_ROOT/requirements" "$INSTALL_DIR/"
    elif [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        cp "$PROJECT_ROOT/requirements.txt" "$INSTALL_DIR/"
    fi

    # Copy pyproject.toml if exists
    if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
        cp "$PROJECT_ROOT/pyproject.toml" "$INSTALL_DIR/"
    fi

    # Copy README and LICENSE
    [ -f "$PROJECT_ROOT/README.md" ] && cp "$PROJECT_ROOT/README.md" "$INSTALL_DIR/"
    [ -f "$PROJECT_ROOT/LICENSE" ] && cp "$PROJECT_ROOT/LICENSE" "$INSTALL_DIR/"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."

    cd "$INSTALL_DIR"

    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip setuptools wheel

    # Install dependencies
    if [ -f "requirements/linux.txt" ]; then
        pip install -r requirements/linux.txt
    elif [ -f "requirements/base.txt" ]; then
        pip install -r requirements/base.txt
        # Install Linux-specific packages
        pip install evdev python-xlib
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    elif [ -f "pyproject.toml" ]; then
        pip install -e ".[linux]"
    else
        log_error "No requirements file found"
    fi

    deactivate
}

# Create launcher script
create_launcher() {
    log_info "Creating launcher script..."

    cat > "$BIN_DIR/$APP_NAME" << EOF
#!/bin/bash
# Clipboard Manager launcher script

cd "$INSTALL_DIR"
source venv/bin/activate
export PYTHONPATH="$INSTALL_DIR/src:\$PYTHONPATH"
exec python3 src/main.py "\$@"
EOF

    chmod +x "$BIN_DIR/$APP_NAME"
}

# Create desktop entry
create_desktop_entry() {
    log_info "Creating desktop entry..."

    cat > "$DESKTOP_DIR/$APP_NAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Clipboard Manager
GenericName=Clipboard History Manager
Comment=A modern clipboard history manager with global hotkey support
Exec=$APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Utility;System;Qt;
Keywords=clipboard;history;manager;copy;paste;
StartupWMClass=clipboard-manager
StartupNotify=true
MimeType=text/plain;
X-GNOME-Autostart-enabled=false
X-KDE-autostart-after=panel
EOF

    chmod 644 "$DESKTOP_DIR/$APP_NAME.desktop"
}

# Create application icon
create_icon() {
    log_info "Creating application icon..."

    # Check if icon exists in resources
    if [ -f "$INSTALL_DIR/resources/icons/app.png" ]; then
        cp "$INSTALL_DIR/resources/icons/app.png" "$ICON_DIR/$APP_NAME.png"
    else
        # Create a simple SVG icon
        cat > "/tmp/$APP_NAME.svg" << 'EOF'
<svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#4A90E2;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#357ABD;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect width="36" height="42" x="6" y="3" rx="3" ry="3" fill="url(#grad1)" stroke="#2C5F93" stroke-width="1"/>
    <rect width="20" height="8" x="14" y="0" rx="2" ry="2" fill="#E8E8E8" stroke="#CCCCCC" stroke-width="1"/>
    <rect width="28" height="2" x="10" y="12" fill="#FFFFFF" opacity="0.8"/>
    <rect width="24" height="2" x="10" y="18" fill="#FFFFFF" opacity="0.6"/>
    <rect width="20" height="2" x="10" y="24" fill="#FFFFFF" opacity="0.6"/>
    <rect width="16" height="2" x="10" y="30" fill="#FFFFFF" opacity="0.4"/>
    <circle cx="38" cy="38" r="8" fill="#FF6B6B" stroke="#E74C3C" stroke-width="1"/>
    <text x="38" y="42" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">📋</text>
</svg>
EOF

        # Convert SVG to PNG if possible
        if command -v convert > /dev/null; then
            convert "/tmp/$APP_NAME.svg" "$ICON_DIR/$APP_NAME.png"
        elif command -v rsvg-convert > /dev/null; then
            rsvg-convert -w 48 -h 48 "/tmp/$APP_NAME.svg" -o "$ICON_DIR/$APP_NAME.png"
        else
            # Copy SVG as fallback
            cp "/tmp/$APP_NAME.svg" "$ICON_DIR/$APP_NAME.svg"
        fi

        rm -f "/tmp/$APP_NAME.svg"
    fi
}

# Create systemd user service (optional)
create_systemd_service() {
    log_info "Creating systemd user service..."

    cat > "$SYSTEMD_DIR/$APP_NAME.service" << EOF
[Unit]
Description=Clipboard Manager
After=graphical-session.target

[Service]
Type=simple
ExecStart=$BIN_DIR/$APP_NAME
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/%i

[Install]
WantedBy=default.target
EOF

    chmod 644 "$SYSTEMD_DIR/$APP_NAME.service"
}

# Update system databases
update_databases() {
    log_info "Updating system databases..."

    # Update desktop database
    if command -v update-desktop-database > /dev/null; then
        update-desktop-database "$DESKTOP_DIR"
    fi

    # Update icon cache
    if command -v gtk-update-icon-cache > /dev/null; then
        gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
    fi

    # Update mime database
    if command -v update-mime-database > /dev/null; then
        update-mime-database /usr/share/mime 2>/dev/null || true
    fi
}

# Create uninstall script
create_uninstall_script() {
    log_info "Creating uninstall script..."

    cat > "$BIN_DIR/${APP_NAME}-uninstall" << EOF
#!/bin/bash
# Clipboard Manager uninstall script

echo "🗑️  Uninstalling Clipboard Manager..."

# Stop service if running
systemctl --user stop $APP_NAME 2>/dev/null || true
systemctl --user disable $APP_NAME 2>/dev/null || true

# Remove files
rm -rf "$INSTALL_DIR"
rm -f "$BIN_DIR/$APP_NAME"
rm -f "$BIN_DIR/${APP_NAME}-uninstall"
rm -f "$DESKTOP_DIR/$APP_NAME.desktop"
rm -f "$ICON_DIR/$APP_NAME.png"
rm -f "$ICON_DIR/$APP_NAME.svg"
rm -f "$SYSTEMD_DIR/$APP_NAME.service"

# Update databases
if command -v update-desktop-database > /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

if command -v gtk-update-icon-cache > /dev/null; then
    gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
fi

echo "✅ Clipboard Manager uninstalled successfully!"
EOF

    chmod +x "$BIN_DIR/${APP_NAME}-uninstall"
}

# Main installation function
main() {
    echo "🚀 Installing Clipboard Manager v$APP_VERSION..."
    echo ""

    check_root
    install_system_deps
    create_directories
    copy_files
    install_python_deps
    create_launcher
    create_desktop_entry
    create_icon
    create_systemd_service
    update_databases
    create_uninstall_script

    log_success "Installation completed successfully!"
    echo ""
    echo "📋 You can now:"
    echo "   • Run from terminal: $APP_NAME"
    echo "   • Find in applications menu: Clipboard Manager"
    echo "   • Use global hotkey: Super+C"
    echo "   • Enable autostart: systemctl --user enable $APP_NAME"
    echo ""
    echo "🗑️  To uninstall, run: sudo ${APP_NAME}-uninstall"
    echo ""
    echo "🔧 For troubleshooting, check:"
    echo "   • Logs: journalctl --user -u $APP_NAME"
    echo "   • Config: ~/.local/share/ClipboardManager/"
    echo ""
}

# Run installation
main "$@"
