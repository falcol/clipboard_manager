# clipboard_manager/setup.py
"""
Legacy setup script for Clipboard Manager (for compatibility)
Modern packaging should use pyproject.toml
"""
import sys
from pathlib import Path

from setuptools import find_packages, setup


def _assert_min_py():
    if sys.version_info < (3, 9):
        raise SystemExit("clipboard-manager requires Python 3.9 or higher")

_assert_min_py()

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = (
    readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
)

# Read requirements from pyproject.toml or fallback to requirements files
def read_requirements():
    """Read requirements from various sources"""
    requirements = []

    # Try to read from requirements/base.txt
    base_req_path = Path(__file__).parent / "requirements" / "base.txt"
    if base_req_path.exists():
        with open(base_req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-r'):
                    requirements.append(line)

    return requirements

# Platform-specific requirements
def get_platform_requirements():
    """Get platform-specific requirements"""
    import platform
    extras = {}

    if platform.system().lower() == 'linux':
        extras['linux'] = ['evdev>=1.9.0', 'python-xlib>=0.33']

    extras['dev'] = [
        'pytest>=7.0.0',
        'pytest-qt>=4.0.0',
        'black>=23.0.0',
        'flake8>=6.0.0',
        'mypy>=1.0.0',
        'pre-commit>=3.0.0',
    ]

    return extras

setup(
    name="clipboard-manager",
    version="1.0.0",
    author="ClipboardManager Team",
    author_email="contact@clipboardmanager.dev",
    description="A modern cross-platform clipboard history manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clipboard-manager/clipboard-manager",
    project_urls={
        "Bug Tracker": "https://github.com/clipboard-manager/clipboard-manager/issues",
        "Documentation": "https://clipboard-manager.readthedocs.io/",
        "Source Code": "https://github.com/clipboard-manager/clipboard-manager",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment",
        "Topic :: Utilities",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require=get_platform_requirements(),
    entry_points={
        "console_scripts": [
            "clipboard-manager=main:main",
        ],
        "gui_scripts": [
            "clipboard-manager-gui=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.qss", "*.png", "*.ico", "*.svg", "*.json"],
        "resources": ["styles/*.qss", "styles/themes/*.qss", "icons/*"],
    },
    zip_safe=False,
    keywords="clipboard history manager cross-platform desktop qt pyside6",
    platforms=["any"],
)
