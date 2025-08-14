# 📋 Clipboard Manager

A modern, cross-platform clipboard history manager built with Python and PySide6/Qt6.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.9+-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)](https://github.com/clipboard-manager/clipboard-manager)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- **📝 Rich Clipboard History**: Automatically saves text, HTML, RTF, and image clipboard content
- **📌 Pin Important Items**: Pin frequently used items to prevent deletion
- **🔥 Global Hotkey**: Press `Super+C` (Linux) to show clipboard history
- **🎨 Modern UI**: Clean, dark interface with smooth animations and multiple themes
- **💾 Efficient Storage**: SQLite-based storage with optimized memory usage
- **🚀 System Integration**: System tray, auto-start, and native platform integration
- **⚙️ Highly Configurable**: Customize items limit, text length, themes, and performance settings
- **🔍 Smart Search**: Fast search and filtering through clipboard history
- **🌍 Cross-Platform**: Works seamlessly on Linux
- **🔒 Privacy-First**: All data stored locally, no network connections

## 🚀 Quick Start

### Requirements

- **Python**: 3.9 or higher
- **Operating System**: Linux
- **Display Server**: X11 or Wayland (Linux)

### Installation

#### Option 1: Run from Source (Development)

```bash
# Clone the repository
git clone https://github.com/clipboard-manager/clipboard-manager.git
cd clipboard-manager

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
sudo ./scripts/install_linux.sh

# Or create and install .deb package
python scripts/create_deb.py
sudo dpkg -i clipboard-manager_1.0.0_all.deb
```

#### Option 3: PyPI Installation (Future)

```bash
# Install from PyPI (coming soon)
pip install clipboard-manager

# With Linux-specific dependencies
pip install clipboard-manager[linux]
```

### First Run

1. **Start the application** - it will appear in your system tray
2. **Copy something** - text or images will be automatically saved
3. **Press `Super+C`** (or `Windows+C` on Windows) to show clipboard history
4. **Click any item** to paste it into the active application
5. **Pin important items** with 📌 to keep them permanently
6. **Right-click tray icon** → Settings to configure preferences

## 🔧 Configuration

### Settings Window

Access via right-click system tray icon → Settings:

- **General**:
  - Maximum clipboard items (10-100, default: 25)
  - Maximum text length (1KB-2MB, default: 1MB)
  - Auto-start with system

- **Appearance**:
  - Theme selection (Dark Win11, AMOLED, Solarized, Nord, Vespera)

- **Performance & RAM**:
  - Cache size (10-100 MB, default: 25MB)
  - Thumbnail size (32-128px, default: 64px)
  - Image quality (50-95%, default: 85%)
  - Cleanup interval (1-48 hours, default: 12h)

### Configuration Files

- **Linux**: `~/.local/share/B1Clip/`

### Hotkey Customization

Global hotkeys by platform:
- **Linux**: `Super+C` (configurable in settings)

## 🛠️ Development

### Setting up Development Environment

```bash
<code_block_to_apply_changes_from>
```

### Project Dependencies

#### Core Dependencies (requirements/base.txt)
- **PySide6**: Qt6 GUI framework
- **appdirs**: Cross-platform app directories
- **setproctitle**: Process name setting
- **pynput**: Cross-platform input handling
- **keyboard**: Global hotkey support
- **pillow**: Image processing
- **click**: CLI interface (future)

#### Linux-specific (requirements/linux.txt)
- **evdev**: Linux input device access
- **python-xlib**: X11 protocol access

#### Development (dev extra)
- **pytest**: Testing framework
- **pytest-qt**: Qt testing support
- **black**: Code formatting
- **flake8**: Code linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

### Building Packages

```bash
# Build wheel package
python -m build

# Create Linux .deb package
python scripts/create_deb.py

```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest -m "not slow"      # Skip slow tests
pytest -m integration     # Only integration tests

# Run Qt-specific tests
pytest tests/test_ui.py
```

## 📦 Packaging & Distribution

### PyInstaller (Standalone Executable)

```bash
# Install PyInstaller
pip install pyinstaller

# Create standalone executable
pyinstaller --onefile --noconsole --add-data "resources:resources" src/main.py

# The executable will be in dist/
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements/base.txt .
RUN pip install -r base.txt

COPY src/ ./src/
COPY resources/ ./resources/

CMD ["python", "src/main.py"]
```

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
    libxcb-xinerama0 libxcb-xkb1 libgl1-mesa-glx libglib2.0-0
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
clipboard-manager
```

### Debugging

```bash
# Enable debug logging
clipboard-manager --debug

# View logs (Linux)
journalctl --user -u clipboard-manager -f

# View logs (systemd journal)
journalctl --user -xe
```

### Performance Optimization

- Reduce cache size in settings for lower RAM usage
- Decrease thumbnail size for faster loading
- Increase cleanup interval for less frequent maintenance
- Disable image preview for text-only workflows

## 🛡️ Privacy & Security

- **Local Storage**: All data stored locally in SQLite database
- **No Network Access**: Application never connects to the internet
- **Encrypted Storage**: Optional encryption for sensitive clipboard data
- **Memory Protection**: Secure memory handling for clipboard content
- **User Control**: Full control over data retention and deletion

### Data Locations

- **Database**: `~/.local/share/B1Clip/clipboard.db`
- **Images**: `~/.local/share/B1Clip/images/`
- **Thumbnails**: `~/.local/share/B1Clip/thumbnails/`
- **Configuration**: `~/.local/share/B1Clip/config.json`
- **Logs**: `~/.local/share/B1Clip/logs/`

## 🚀 Performance & Technical Details

### Architecture

- **GUI Framework**: PySide6 (Qt6) for native, modern interface
- **Database**: SQLite with WAL mode for concurrent access
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

### Supported Formats

- **Text**: Plain text, Rich Text (RTF), HTML
- **Images**: PNG, JPEG, BMP, TIFF, WebP
- **Files**: File paths and URLs (metadata only)
- **Custom**: Application-specific clipboard formats

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature-name`
3. **Make** your changes with tests
4. **Run** quality checks: `black`, `flake8`, `mypy`, `pytest`
5. **Commit** with conventional commit format
6. **Push** and create a Pull Request

### Code Standards

- **Style**: Black formatting, line length 88
- **Quality**: Flake8 linting, type hints required
- **Testing**: Pytest with >80% coverage
- **Documentation**: Docstrings for all public APIs
- **Commits**: Conventional Commits format

### Bug Reports

Please include:
- Operating system and version
- Python version
- Error messages and traceback
- Steps to reproduce
- Expected vs actual behavior

### Feature Requests

- Check existing issues first
- Describe the use case clearly
- Consider implementation complexity
- Provide mockups/examples if helpful

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **Qt/PySide6**: Excellent cross-platform GUI framework
- **SQLite**: Reliable embedded database
- **Python**: Amazing ecosystem and community
- **Contributors**: All the wonderful people who help improve this project

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/clipboard-manager/clipboard-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/clipboard-manager/clipboard-manager/discussions)
- **Email**: contact@clipboardmanager.dev
- **Documentation**: [ReadTheDocs](https://clipboard-manager.readthedocs.io/)

---

**Happy clipboard managing! 📋✨**

*Made with ❤️ for productive developers and power users everywhere.*
```

Tóm tắt các thay đổi quan trọng:

1. **Cấu trúc project hiện đại**: Sử dụng `pyproject.toml` làm chuẩn, `setup.py` cho tương thích legacy
2. **Scripts cải tiến**: `install_linux.sh` với auto-detect distro, dependency management thông minh
3. **Debian packaging**: `create_deb.py` hoàn toàn mới với proper metadata, systemd service, security
4. **Documentation toàn diện**: README với cấu trúc rõ ràng, troubleshooting chi tiết, development guide
5. **Best practices**: Virtual environments, proper dependency separation, security considerations

Project structure giờ đây tuân theo Python packaging standards hiện đại và sẵn sàng cho production deployment!
