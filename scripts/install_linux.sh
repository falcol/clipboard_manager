#!/bin/bash
# clipboard_manager/scripts/install_linux.sh
# Linux installation script with comprehensive validation and error handling

set -e

# Configuration
APP_NAME="B1Clip"
APP_VERSION="1.0.0"
INSTALL_DIR="/opt/$APP_NAME"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/48x48/apps"
SYSTEMD_DIR="/etc/systemd/user"
CONFIG_DIR="~/.config/$APP_NAME"

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

# validation functions
check_python_version() {
    log_info "Checking Python version..."
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        REQUIRED_VERSION="3.9"

        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            log_success "Python $PYTHON_VERSION found (>= $REQUIRED_VERSION required)"
        else
            log_error "Python $PYTHON_VERSION found, but >= $REQUIRED_VERSION required"
        fi
    else
        log_error "Python 3 not found. Please install Python 3.9 or higher"
    fi
}

check_disk_space() {
    log_info "Checking disk space..."

    # Check available space in /opt (need at least 100MB)
    AVAILABLE_KB=$(df /opt | tail -1 | awk '{print $4}')
    REQUIRED_KB=102400  # 100MB

    if [ "$AVAILABLE_KB" -lt "$REQUIRED_KB" ]; then
        log_error "Insufficient disk space. Need at least 100MB in /opt"
    else
        log_success "Sufficient disk space available"
    fi
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

# system dependencies installation
install_system_deps() {
    local distro=$(detect_distro)
    log_info "Detected distribution: $distro"

    case "$distro" in
        ubuntu|debian)
            log_info "Installing system dependencies for Ubuntu/Debian..."
            apt update || log_error "Failed to update package list"
            apt install -y \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                build-essential \
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
                libxcb-xinput0 \
                libglib2.0-0t64 \
                libfontconfig1 \
                libdbus-1-3 \
                xdotool \
                || log_error "Failed to install system dependencies"
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
                git \
                || log_error "Failed to install system dependencies"
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
                git \
                || log_error "Failed to install system dependencies"
            ;;
        *)
            log_warning "Unsupported distribution: $distro"
            log_warning "Please install Python 3.9+, pip, and Qt/XCB libraries manually"
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
}

# Create installation directories with proper permissions
create_directories() {
    log_info "Creating installation directories..."
    mkdir -p "$INSTALL_DIR" || log_error "Failed to create $INSTALL_DIR"
    mkdir -p "$BIN_DIR" || log_error "Failed to create $BIN_DIR"
    mkdir -p "$DESKTOP_DIR" || log_error "Failed to create $DESKTOP_DIR"
    mkdir -p "$ICON_DIR" || log_error "Failed to create $ICON_DIR"
    mkdir -p "$SYSTEMD_DIR" || log_error "Failed to create $SYSTEMD_DIR"
}

# file copying with validation
copy_files() {
    log_info "Copying application files..."

    # Get script directory (project root)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

    # Copy source code with validation
    if [ -d "$PROJECT_ROOT/src" ]; then
        cp -r "$PROJECT_ROOT/src" "$INSTALL_DIR/" || log_error "Failed to copy source files"

        # Set proper ownership and permissions
        chown -R root:root "$INSTALL_DIR/src"
        find "$INSTALL_DIR/src" -type f -name "*.py" -exec chmod 644 {} \;
        chmod 755 "$INSTALL_DIR/src/main.py"
    else
        log_error "Source directory not found: $PROJECT_ROOT/src"
    fi

    # Copy resources
    if [ -d "$PROJECT_ROOT/resources" ]; then
        cp -r "$PROJECT_ROOT/resources" "$INSTALL_DIR/" || log_warning "Failed to copy resources"
        chown -R root:root "$INSTALL_DIR/resources" 2>/dev/null || true
    fi

    # Copy requirements with validation
    if [ -d "$PROJECT_ROOT/requirements" ]; then
        cp -r "$PROJECT_ROOT/requirements" "$INSTALL_DIR/" || log_error "Failed to copy requirements"

        # Validate requirements files exist
        if [ ! -f "$INSTALL_DIR/requirements/linux.txt" ] && [ ! -f "$INSTALL_DIR/requirements/base.txt" ]; then
            log_error "No valid requirements file found"
        fi
    elif [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        cp "$PROJECT_ROOT/requirements.txt" "$INSTALL_DIR/" || log_error "Failed to copy requirements.txt"
    else
        log_error "No requirements files found"
    fi

    # Copy additional files
    [ -f "$PROJECT_ROOT/pyproject.toml" ] && cp "$PROJECT_ROOT/pyproject.toml" "$INSTALL_DIR/"
    [ -f "$PROJECT_ROOT/README.md" ] && cp "$PROJECT_ROOT/README.md" "$INSTALL_DIR/"
    [ -f "$PROJECT_ROOT/LICENSE" ] && cp "$PROJECT_ROOT/LICENSE" "$INSTALL_DIR/"
}

# Python dependencies installation
install_python_deps() {
    log_info "Installing Python dependencies..."

    cd "$INSTALL_DIR" || log_error "Failed to change to install directory"

    # Create virtual environment with error handling
    python3 -m venv venv || log_error "Failed to create virtual environment"

    # Activate virtual environment
    source venv/bin/activate || log_error "Failed to activate virtual environment"

    # Upgrade pip and essential tools
    pip install --upgrade pip setuptools wheel || log_error "Failed to upgrade pip"

    # Install dependencies with proper error handling
    if [ -f "requirements/linux.txt" ]; then
        log_info "Installing from requirements/linux.txt..."
        pip install -r requirements/linux.txt || log_error "Failed to install Linux requirements"
    elif [ -f "requirements/base.txt" ]; then
        log_info "Installing from requirements/base.txt..."
        pip install -r requirements/base.txt || log_error "Failed to install base requirements"

        # Install Linux-specific packages
        log_info "Installing Linux-specific packages..."
        pip install evdev python-xlib || log_warning "Failed to install some Linux packages"
    elif [ -f "requirements.txt" ]; then
        log_info "Installing from requirements.txt..."
        pip install -r requirements.txt || log_error "Failed to install requirements"
    elif [ -f "pyproject.toml" ]; then
        log_info "Installing from pyproject.toml..."
        pip install -e ".[linux]" || log_error "Failed to install from pyproject.toml"
    else
        log_error "No requirements file found"
    fi

    # Validate critical packages are installed
    python3 -c "import PySide6; print('✅ PySide6 installed successfully')" || log_error "PySide6 installation failed"
    python3 -c "import pynput; print('✅ pynput installed successfully')" || log_error "pynput installation failed"

    deactivate
}

# launcher script with robust error handling
create_launcher() {
    log_info "Creating launcher script..."

    cat > "$BIN_DIR/$APP_NAME" << 'EOF'
#!/bin/bash
# B1Clip launcher script

set -e

APP_DIR="/opt/B1Clip"
VENV_PATH="$APP_DIR/venv"
MAIN_SCRIPT="$APP_DIR/src/main.py"

# Color output functions
log_error() {
    echo -e "\033[0;31m❌ $1\033[0m" >&2
    exit 1
}

# Validate installation
if [ ! -d "$APP_DIR" ]; then
    log_error "Application not found. Please reinstall B1Clip."
fi

if [ ! -f "$VENV_PATH/bin/activate" ]; then
    log_error "Virtual environment not found. Please reinstall B1Clip."
fi

if [ ! -f "$MAIN_SCRIPT" ]; then
    log_error "Main script not found. Please reinstall B1Clip."
fi

# Change to application directory
cd "$APP_DIR" || log_error "Failed to change to application directory"

# Activate virtual environment
source "$VENV_PATH/bin/activate" || log_error "Failed to activate virtual environment"

# Set up Python path
export PYTHONPATH="$APP_DIR/src:$APP_DIR:$PYTHONPATH"

# Run application with proper error handling
if [ -t 0 ]; then
    # Running in terminal
    python3 "$MAIN_SCRIPT" "$@"
else
    # Running in background (from desktop/systemd)
    python3 "$MAIN_SCRIPT" "$@" 2>/dev/null || {
        # If fails, try to log error
        echo "$(date): B1Clip failed to start" >> ~/.local/share/clipboard-manager-errors.log
        exit 1
    }
fi
EOF

    chmod +x "$BIN_DIR/$APP_NAME" || log_error "Failed to make launcher executable"
}

# desktop entry
create_desktop_entry() {
    log_info "Creating desktop entry..."

    cat > "$DESKTOP_DIR/$APP_NAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=B1Clip
GenericName=Clipboard History Manager
Comment=A modern clipboard history manager with global hotkey support
Exec=$APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Utility;System;Qt;AccessX;
Keywords=clipboard;history;manager;copy;paste;productivity;
StartupWMClass=B1Clip
StartupNotify=true
MimeType=text/plain;text/html;text/rtf;image/png;image/jpeg;
X-GNOME-Autostart-enabled=false
X-KDE-autostart-after=panel
X-Desktop-File-Install-Version=0.26
EOF

    chmod 644 "$DESKTOP_DIR/$APP_NAME.desktop" || log_error "Failed to set desktop entry permissions"
}

# Create application icon
create_icon() {
    log_info "Creating application icon..."

    # Check if icon exists in resources
    if [ -f "$INSTALL_DIR/resources/icons/app_icon.png" ]; then
        cp "$INSTALL_DIR/resources/icons/app_icon.png" "$ICON_DIR/$APP_NAME.png"
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

# systemd service with better configuration
create_systemd_service() {
    log_info "Creating systemd user service..."

    cat > "$SYSTEMD_DIR/$APP_NAME.service" << EOF
[Unit]
Description=B1Clip - Modern clipboard history manager
Documentation=https://github.com/falcol/clipboard_manager
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=$BIN_DIR/$APP_NAME
ExecReload=/bin/kill -HUP \$MAINPID
Restart=on-failure
RestartSec=5
TimeoutStartSec=30
TimeoutStopSec=15

# Environment
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/%i
Environment=QT_QPA_PLATFORM=xcb

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=%h/.local/share/B1Clip

# Process settings
KillMode=mixed
KillSignal=SIGTERM

[Install]
WantedBy=default.target
EOF

    chmod 644 "$SYSTEMD_DIR/$APP_NAME.service" || log_error "Failed to set systemd service permissions"
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
# B1Clip uninstall script

echo "🗑️  Uninstalling B1Clip..."

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
rm -rf "$CONFIG_DIR"

# Update databases
if command -v update-desktop-database > /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

if command -v gtk-update-icon-cache > /dev/null; then
    gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
fi

echo "✅ B1Clip uninstalled successfully!"
EOF

    chmod +x "$BIN_DIR/${APP_NAME}-uninstall"
}

enable_autostart() {
    log_info "=== Autostart ==="

    REAL_USER="${SUDO_USER:-$USER}"

    if loginctl show-user "$REAL_USER" >/dev/null 2>&1; then
        log_info "Detected active systemd session for user: $REAL_USER"

        sudo -u "$REAL_USER" XDG_RUNTIME_DIR="/run/user/$(id -u $REAL_USER)" \
            systemctl --user enable $APP_NAME || log_warning "Failed to enable autostart"

        sudo -u "$REAL_USER" XDG_RUNTIME_DIR="/run/user/$(id -u $REAL_USER)" \
            systemctl --user start $APP_NAME || log_warning "Failed to start user service"
    else
        log_warning "No active systemd user session found for $REAL_USER"
        log_warning "Skipping autostart. You can enable it manually:"
        echo "   systemctl --user enable $APP_NAME"
        echo "   systemctl --user start $APP_NAME"
    fi
}


# main installation function with comprehensive validation
main() {
    echo "🚀 Installing B1Clip v$APP_VERSION..."
    echo "📦 installation with comprehensive validation"
    echo ""

    # Pre-installation checks
    log_info "=== Pre-installation Validation ==="
    check_root
    check_python_version
    check_disk_space

    # System preparation
    log_info "=== System Preparation ==="
    install_system_deps
    create_directories

    # Application installation
    log_info "=== Application Installation ==="
    copy_files
    install_python_deps

    # System integration
    log_info "=== System Integration ==="
    create_launcher
    create_desktop_entry
    create_icon
    create_systemd_service
    update_databases
    create_uninstall_script

    # Post-installation validation
    log_info "=== Post-installation Validation ==="
    if [ -x "$BIN_DIR/$APP_NAME" ]; then
        log_success "Launcher script created successfully"
    else
        log_error "Launcher script creation failed"
    fi

    if [ -f "$DESKTOP_DIR/$APP_NAME.desktop" ]; then
        log_success "Desktop entry created successfully"
    else
        log_warning "Desktop entry creation failed"
    fi

    # Enable autostart
    log_info "=== Autostart ==="
    enable_autostart

    log_success "Installation completed successfully!"
    echo ""
    echo "📋 You can now:"
    echo "   • Run from terminal: $APP_NAME"
    echo "   • Find in applications menu: B1Clip"
    echo "   • Use global hotkey: Super+C"
    echo "   • Enable autostart: systemctl --user enable $APP_NAME"
    echo "   • Start service now: systemctl --user start $APP_NAME"
    echo ""
    echo "🗑️  To uninstall, run: sudo ${APP_NAME}-uninstall"
    echo ""
    echo "🔧 For troubleshooting:"
    echo "   • Test launcher: $APP_NAME --help"
    echo "   • Check logs: journalctl --user -u $APP_NAME -f"
    echo "   • Manual test: cd $INSTALL_DIR && source venv/bin/activate && python3 src/main.py"
    echo "   • Config location: ~/.config/$APP_NAME"
    echo ""
}

# Run installation
main "$@"
