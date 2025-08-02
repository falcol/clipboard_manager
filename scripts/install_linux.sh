# clipboard_manager/scripts/install_linux.sh
#!/bin/bash
# Linux installation script

set -e

APP_NAME="clipboard-manager"
INSTALL_DIR="/opt/$APP_NAME"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/48x48/apps"

echo "🚀 Installing Clipboard Manager..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$ICON_DIR"

# Copy application files
echo "📁 Copying files..."
cp -r src/ "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# Install Python dependencies
echo "📦 Installing dependencies..."
pip3 install -r "$INSTALL_DIR/requirements.txt"

# Create launcher script
echo "🔧 Creating launcher..."
cat > "$BIN_DIR/$APP_NAME" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 src/main.py "\$@"
EOF

chmod +x "$BIN_DIR/$APP_NAME"

# Create desktop entry
echo "🖥️ Creating desktop entry..."
cat > "$DESKTOP_DIR/$APP_NAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Clipboard Manager
Comment=Cross-platform clipboard history manager
Exec=$APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Utility;
StartupWMClass=clipboard-manager
EOF

# Create icon (simple text-based icon if none exists)
if [ ! -f "resources/icons/app.png" ]; then
    echo "🎨 Creating default icon..."
    # Create a simple SVG icon and convert to PNG
    cat > "/tmp/$APP_NAME.svg" << EOF
<svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
    <rect width="32" height="40" x="8" y="4" fill="#ffffff" stroke="#000000" stroke-width="2"/>
    <rect width="16" height="6" x="16" y="0" fill="#cccccc" stroke="#000000" stroke-width="1"/>
    <text x="24" y="28" text-anchor="middle" font-family="Arial" font-size="16">📋</text>
</svg>
EOF

    # Convert SVG to PNG (if convert is available)
    if command -v convert > /dev/null; then
        convert "/tmp/$APP_NAME.svg" "$ICON_DIR/$APP_NAME.png"
    else
        # Copy a placeholder if ImageMagick is not available
        cp "/tmp/$APP_NAME.svg" "$ICON_DIR/$APP_NAME.svg"
    fi

    rm "/tmp/$APP_NAME.svg"
else
    cp "resources/icons/app.png" "$ICON_DIR/$APP_NAME.png"
fi

# Update desktop database
if command -v update-desktop-database > /dev/null; then
    update-desktop-database "$DESKTOP_DIR"
fi

# Update icon cache
if command -v gtk-update-icon-cache > /dev/null; then
    gtk-update-icon-cache /usr/share/icons/hicolor
fi

echo "✅ Installation complete!"
echo ""
echo "📋 You can now:"
echo "   • Run from terminal: $APP_NAME"
echo "   • Find in applications menu: Clipboard Manager"
echo "   • Use global hotkey: Super+V"
echo ""
echo "🗑️ To uninstall, run:"
echo "   sudo rm -rf $INSTALL_DIR"
echo "   sudo rm $BIN_DIR/$APP_NAME"
echo "   sudo rm $DESKTOP_DIR/$APP_NAME.desktop"
echo "   sudo rm $ICON_DIR/$APP_NAME.png"
