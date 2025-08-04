#!/bin/bash
# clipboard_manager/scripts/install_linux.sh
# Enhanced Linux installation script with better security and error handling

set -euo pipefail  # Strict error handling

# Configuration
APP_NAME="clipboard-manager"
VERSION="2.0.0"
INSTALL_DIR="/opt/$APP_NAME"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/48x48/apps"
USER_DATA_DIR="$HOME/.config/clipboard-manager"

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
}

# Error handling
cleanup() {
    log_warning "Cleaning up..."
    rm -f "/tmp/$APP_NAME.svg" 2>/dev/null || true
}

trap cleanup EXIT

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run as root (use sudo)"
        exit 1
    fi

    # Check if we're in the right directory
    if [ ! -f "src/main.py" ]; then
        log_error "Please run this script from the project root directory"
        exit 1
    fi

    # Check Python version
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi

    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    required_version="3.8"

    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        log_error "Python 3.8 or higher is required. Found: $python_version"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Backup existing installation
backup_existing() {
    if [ -d "$INSTALL_DIR" ]; then
        log_warning "Existing installation found at $INSTALL_DIR"
        backup_dir="$INSTALL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "Creating backup at $backup_dir"
        mv "$INSTALL_DIR" "$backup_dir"
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."

    # Create virtual environment for better isolation
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"

    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    if ! pip install -r requirements.txt; then
        log_error "Failed to install dependencies"
        exit 1
    fi

    log_success "Dependencies installed successfully"
}

# Copy application files
copy_files() {
    log_info "Copying application files..."

    # Create directories
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$ICON_DIR"
    mkdir -p "$USER_DATA_DIR"

    # Copy source files with validation
    if ! cp -r src/ "$INSTALL_DIR/"; then
        log_error "Failed to copy source files"
        exit 1
    fi

    # Copy requirements
    if ! cp requirements.txt "$INSTALL_DIR/"; then
        log_error "Failed to copy requirements.txt"
        exit 1
    fi

    # Set proper permissions
    chmod -R 755 "$INSTALL_DIR"
    chown -R root:root "$INSTALL_DIR"

    log_success "Files copied successfully"
}

# Create launcher script
create_launcher() {
    log_info "Creating launcher script..."

    launcher_content="#!/bin/bash
    # Clipboard Manager Launcher
    # Version: $VERSION

    # Set application directory
    APP_DIR=\"$INSTALL_DIR\"
    VENV_DIR=\"\$APP_DIR/venv\"

    # Check if application directory exists
    if [ ! -d \"\$APP_DIR\" ]; then
        echo \"Error: Application not found at \$APP_DIR\" >&2
        exit 1
    fi

    # Check if virtual environment exists
    if [ ! -d \"\$VENV_DIR\" ]; then
        echo \"Error: Virtual environment not found at \$VENV_DIR\" >&2
        exit 1
    fi

    # Activate virtual environment and run
    cd \"\$APP_DIR\"
    source \"\$VENV_DIR/bin/activate\"
    exec python3 src/main.py \"\$@\"
    "

    if ! echo "$launcher_content" > "$BIN_DIR/$APP_NAME"; then
        log_error "Failed to create launcher script"
        exit 1
    fi

    chmod +x "$BIN_DIR/$APP_NAME"
    log_success "Launcher script created"
}

# Create desktop entry
create_desktop_entry() {
    log_info "Creating desktop entry..."

    desktop_content="[Desktop Entry]
        Version=1.0
        Type=Application
        Name=Clipboard Manager
        Comment=Modern clipboard history manager
        GenericName=Clipboard Manager
        Exec=$APP_NAME
        Icon=$APP_NAME
        Terminal=false
        NoDisplay=false
        Categories=Utility;System;Office;
        Keywords=clipboard;history;manager;copy;paste;
        StartupWMClass=clipboard-manager
        StartupNotify=true
        MimeType=text/plain;image/png;image/jpeg;
        "

    if ! echo "$desktop_content" > "$DESKTOP_DIR/$APP_NAME.desktop"; then
        log_error "Failed to create desktop entry"
        exit 1
    fi

    log_success "Desktop entry created"
}

# Create icon
create_icon() {
    log_info "Creating application icon..."

    # Create improved SVG icon
    icon_content='<svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
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
</svg>'

    # Create temporary SVG
    echo "$icon_content" > "/tmp/$APP_NAME.svg"

    # Convert to PNG if ImageMagick is available
    if command -v convert >/dev/null 2>&1; then
        if convert "/tmp/$APP_NAME.svg" "$ICON_DIR/$APP_NAME.png"; then
            log_success "Icon created (PNG)"
        else
            log_warning "Failed to convert SVG to PNG, using SVG"
            cp "/tmp/$APP_NAME.svg" "$ICON_DIR/$APP_NAME.svg"
        fi
    else
        log_warning "ImageMagick not found, using SVG icon"
        cp "/tmp/$APP_NAME.svg" "$ICON_DIR/$APP_NAME.svg"
    fi

    # Clean up temporary file
    rm -f "/tmp/$APP_NAME.svg"
}

# Update system databases
update_system_dbs() {
    log_info "Updating system databases..."

    # Update desktop database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$DESKTOP_DIR"
        log_success "Desktop database updated"
    else
        log_warning "update-desktop-database not found"
    fi

    # Update icon cache
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache /usr/share/icons/hicolor
        log_success "Icon cache updated"
    else
        log_warning "gtk-update-icon-cache not found"
    fi
}

# Create uninstall script
create_uninstall_script() {
    log_info "Creating uninstall script..."

    uninstall_script="$INSTALL_DIR/uninstall.sh"

    uninstall_content="#!/bin/bash
    # Clipboard Manager Uninstaller

    set -e

    echo \"🗑️  Uninstalling Clipboard Manager...\"

    # Stop running instances
    pkill -f \"clipboard-manager\" || true
    pkill -f \"python3.*main.py\" || true

    # Remove application files
    rm -rf \"$INSTALL_DIR\"

    # Remove launcher
    rm -f \"$BIN_DIR/$APP_NAME\"

    # Remove desktop entry
    rm -f \"$DESKTOP_DIR/$APP_NAME.desktop\"

    # Remove icon
    rm -f \"$ICON_DIR/$APP_NAME.png\"
    rm -f \"$ICON_DIR/$APP_NAME.svg\"

    # Update system databases
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database \"$DESKTOP_DIR\"
    fi

    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache /usr/share/icons/hicolor
    fi

    echo \"✅ Clipboard Manager uninstalled successfully!\"
    "

    echo "$uninstall_content" > "$uninstall_script"
    chmod +x "$uninstall_script"

    log_success "Uninstall script created at $uninstall_script"
}

# Main installation function
main() {
    echo "🚀 Installing Clipboard Manager v$VERSION..."
    echo "=========================================="

    check_prerequisites
    backup_existing
    copy_files
    install_dependencies
    create_launcher
    create_desktop_entry
    create_icon
    update_system_dbs
    create_uninstall_script

    echo ""
    echo "=========================================="
    log_success "Installation completed successfully!"
    echo ""
    echo "📋 You can now:"
    echo "   • Run from terminal: $APP_NAME"
    echo "   • Find in applications menu: Clipboard Manager"
    echo "   • Use global hotkey: Super+C"
    echo ""
    echo "⚙️  User data directory: $USER_DATA_DIR"
    echo ""
    echo "🗑️  To uninstall, run:"
    echo "   sudo $INSTALL_DIR/uninstall.sh"
    echo ""
    echo "📖 For more information, check the documentation."
}

# Run main function
main "$@"
