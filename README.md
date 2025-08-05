# clipboard_manager/README.md
# 📋 Clipboard Manager

A modern, cross-platform clipboard history manager built with Python and PySide6.

## ✨ Features

- **📝 Clipboard History**: Automatically saves text and image clipboard content
- **📌 Pin Important Items**: Pin frequently used items to prevent deletion
- **🔥 Global Hotkey**: Press `Super+C` (Windows+C) to show clipboard history
- **🎨 Modern Dark UI**: Clean, modern interface with smooth animations
- **💾 Persistent Storage**: Uses SQLite for efficient storage (less RAM usage)
- **🚀 System Tray**: Runs in background with system tray integration
- **⚙️ Configurable**: Customize max items, text length, and auto-start
- **🌍 Cross-Platform**: Works on Ubuntu, and other Linux distributions

## 🚀 Quick Start

### Requirements
- Python 3.9 or higher
- PySide6, pynput, Pillow, appdirs

### Installation

1. **Clone/Download** the project
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python src/main.py
   ```

### Usage

1. **Start the app** - it will run in the system tray
2. **Copy anything** - text or images will be automatically saved
3. **Press `Super+C`** (Super+C on Linux) to show history
4. **Click any item** to paste it to clipboard
5. **Pin items** with 📌 to keep them permanently
6. **Delete items** with 🗑 or clear all history

## 🔧 Configuration

Right-click the system tray icon → Settings to configure:
- Maximum number of clipboard items (10-100)
- Maximum text length (1000-50000 characters)
- Auto-start with system

## 🛠️ Troubleshooting

### Qt Platform Plugin Issues (Linux)

If you encounter errors like:
```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
```

**Solution:**
1. Install required XCB libraries:
   ```bash
   sudo apt update
   sudo apt install -y libxcb-cursor0 libxcb1 libxcb-icccm4 libxcb-image0 \
     libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
     libxcb-sync1 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 \
     xdotool \
     libgl1-mesa-glx libglib2.0-0
   ```

2. If the issue persists, the application will automatically try fallback platforms.

### Thread Safety Issues

If you see warnings about QObject threads, the application includes automatic thread-safe handling for hotkey callbacks.

## 📦 Installation as System Application

### Ubuntu/Debian
```bash
# Make install script executable
chmod +x scripts/install_linux.sh

# Install system-wide
sudo ./scripts/install_linux.sh

# Or create .deb package
python scripts/create_deb.py
sudo dpkg -i clipboard-manager_1.0.0_all.deb


# if run error
sudo apt install -y libxcb-cursor0 libxcb1 libxcb-icccm4 libxcb-image0 \
   libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
   libxcb-sync1 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1

sudo apt install libgl1-mesa-glx libglib2.0-0
```
```

## 🏗️ Architecture

```
clipboard_manager/
├── src/
│   ├── main.py              # Application entry point
│   ├── core/                # Core functionality
│   │   ├── clipboard_watcher.py  # Monitor clipboard changes
│   │   ├── database.py           # SQLite operations
│   │   └── hotkey_manager.py     # Global hotkey handling
│   ├── ui/                  # User interface
│   │   ├── popup_window.py       # Main clipboard popup
│   │   ├── settings_window.py    # Settings dialog
│   │   ├── system_tray.py        # System tray integration
│   │   └── styles.py             # UI stylesheets
│   └── utils/               # Utilities
│       ├── config.py             # Configuration management
│       ├── autostart.py          # Auto-start functionality
│       └── image_utils.py        # Image processing
├── resources/               # Icons and assets
├── scripts/                 # Build and installation scripts
└── requirements.txt         # Python dependencies
```

## 🛠️ Technical Details

- **GUI Framework**: PySide6 (Qt6) for modern, native UI
- **Database**: SQLite for persistent, efficient storage
- **Hotkey**: pynput for cross-platform global hotkey support
- **Image Processing**: Pillow for image compression and thumbnails
- **Configuration**: JSON-based configuration with appdirs for proper paths

## 🔒 Privacy & Security

- All data is stored **locally** in SQLite database
- No network connections or data transmission
- Clipboard data never leaves your device
- Database location: `~/.local/share/ClipboardManager/` (Linux)

## 🤝 Contributing

Feel free to:
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation

## 📄 License

MIT License - see LICENSE file for details.

---

**Happy clipboard managing! 📋✨**
