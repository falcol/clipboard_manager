# 📋 B1Clip

A modern, cross-platform clipboard history manager built with Python and PySide6/Qt6.

[![Python](https://img.shields.io/badge/Ubuntu-24-orange)](https://ubuntu.com/download/desktop)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.9+-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)](https://github.com/falcol/clipboard_manager)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


## ✨ Features

- **📝 Rich Clipboard History**: Automatically saves text, image
- **📌 Pin Important Items**: Pin frequently used items to prevent deletion
- **🔥 Global Hotkey**: Press `Super+C` (Linux) to show clipboard history
- **💾 Efficient Storage**: SQLite-based storage with optimized memory usage
- **🚀 System Integration**: System tray, auto-start, and native platform integration
- **⚙️ Highly Configurable**: Customize items limit, text length, themes, and performance settings
- **🔍 Smart Search**: Fast search and filtering through clipboard history
- **🔒 Privacy-First**: All data stored locally, no network connections

## 🚀 Quick Start

### Requirements

- **Python**: 3.9 or higher
- **Operating System**: Ubuntu 24 for best
- **Display Server**: X11 or Wayland (Linux)

### Installation

#### Option 1: Run from Source (Development)

```bash
# Clone the repository
git clone https://github.com/falcol/clipboard_manager.git
cd clipboard_manager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/base.txt

# For Linux, install platform-specific dependencies
pip install -r requirements/linux.txt

# Run the application
python src/main.py
```

#### Option 2: System Installation (Linux)

```bash
# Download and install system-wide
chmod -u+x scripts/install_linux.sh
sudo ./scripts/install_linux.sh

# Or create and install .deb package
python scripts/create_deb.py
sudo dpkg -i B1Clip_1.0.0_all.deb
```

### First Run

1. **Start the application** - it will appear in your system tray
2. **Copy something** - text or images will be automatically saved
3. **Press `Super+C`** (or `Windows+C` on Windows) to show clipboard history
4. **Click any item** to paste it into the active application
5. **Pin important items** with 📌 to keep them permanently
6. **Right-click tray icon** → Settings to configure preferences

## 🐛 Troubleshooting

### Common Issues

#### Qt Platform Plugin Issues (Linux)

```bash
# Error: qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
# Solution: Install XCB libraries
sudo apt install -y \
    libxcb-cursor0 libxcb1 libxcb-icccm4 libxcb-image0 \
    libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
    libxcb-shape0 libxcb-sync1 libxcb-xfixes0 \
    libxcb-xinerama0 libxcb-xkb1 libglib2.0-0t64 \
    xdotool
```

#### Permission Issues (Linux)

```bash
# If hotkeys don't work, ensure input device access
sudo usermod -a -G input $USER
# Log out and back in
```

#### High DPI Displays

The application automatically handles high DPI displays. If issues persist:

```bash
# Force DPI scaling
export QT_SCALE_FACTOR=1.5
B1Clip
```

### Debugging

```bash
# Enable debug logging
B1Clip --debug

# View logs (Linux)
journalctl --user -u B1Clip -f

# View logs (systemd journal)
journalctl --user -xe
```

## 🛡️ Privacy & Security

- **Local Storage**: All data stored locally in SQLite database
- **No Network Access**: Application never connects to the internet
- **Encrypted Storage**: Optional encryption for sensitive clipboard data
- **Memory Protection**: Secure memory handling for clipboard content
- **User Control**: Full control over data retention and deletion

### Data Locations

- **Database**: `~/.config/B1Clip/clipboard.db`
- **Images**: `~/.config/B1Clip/images/`
- **Thumbnails**: `~/.config/B1Clip/thumbnails/`
- **Configuration**: `~/.config/B1Clip/config.json`
- **Logs**: `~/.config/B1Clip/logs/`

## 🚀 Performance & Technical Details

### Architecture

- **GUI Framework**: PySide6 (Qt6)
- **Database**: SQLite
- **Storage**: Optimized BLOB storage for images with compression
- **Hotkeys**: Cross-platform global hotkey handling with pynput
- **Threading**: Async clipboard monitoring with thread-safe operations
- **Memory**: Intelligent caching with configurable memory limits
- **Search**: Fast full-text search with SQLite FTS5

### System Requirements

- **RAM**: 50-100MB typical usage, configurable cache size
- **Storage**: 10-500MB depending on clipboard history size
- **CPU**: Minimal impact, background monitoring only
- **Graphics**: Hardware acceleration supported, fallback available

---
