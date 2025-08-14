# clipboard_manager/setup.py
"""
Legacy setup script for B1Clip (for compatibility)
Modern packaging should use pyproject.toml
"""
import sys
from pathlib import Path

from setuptools import find_packages, setup


def _assert_min_py():
    if sys.version_info < (3, 9):
        raise SystemExit("B1Clip requires Python 3.9 or higher")

_assert_min_py()

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = (
    readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
)

# Read requirements from pyproject.toml or fallback to requirements files
def read_requirements():
    """Read base requirements for all platforms"""
    requirements = []

    # Read from requirements/base.txt (cross-platform)
    base_req_path = Path(__file__).parent / "requirements" / "base.txt"
    if base_req_path.exists():
        with open(base_req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-r'):
                    requirements.append(line)
    else:
        # Fallback to minimal requirements if base.txt not found
        requirements = [
            "PySide6>=6.9.0",
            "appdirs>=1.4.0",
            "setproctitle>=1.3.0",
            "pynput>=1.8.0",
            "pillow>=11.0.0",
            "psutil>=7.0.0"
        ]

    return requirements

# Platform-specific requirements
def get_platform_requirements():
    """Get platform-specific requirements"""
    extras = {}

    # Linux-specific requirements (from requirements/linux.txt)
    extras['linux'] = [
        'keyboard>=0.13.5',
        'evdev>=1.9.2',
        'python-xlib>=0.33',
        'plyer>=2.1.0'
    ]

    # Windows-specific requirements (from requirements/windows.txt)
    extras['windows'] = [
        'keyboard>=0.13.5',
        'pywin32>=306',
        'wmi>=1.5.1'
    ]

    # Development requirements (sync with requirements/test.txt)
    extras['dev'] = [
        'pytest>=8.4.1',
        'pytest-qt>=4.5.0',
        'black>=23.0.0',
        'flake8>=6.0.0',
        'mypy>=1.0.0',
        'pre-commit>=3.0.0',
    ]

    # Test requirements (match requirements/test.txt)
    extras['test'] = [
        'pytest>=8.4.1',
        'pytest-qt>=4.5.0',
        'iniconfig>=2.1.0',
        'pluggy>=1.6.0'
    ]

    return extras

setup(
    name="B1Clip",
    version="1.0.0",
    author="Falcol",
    author_email="contact@clipboardmanager.dev",
    description="A modern cross-platform clipboard history manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/falcol/clipboard_manager",
    project_urls={
        "Source Code": "https://github.com/falcol/clipboard_manager",
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
            "b1clip=src.main:main",
            "clipboard-manager=src.main:main",  # Legacy alias
        ],
        "gui_scripts": [
            "b1clip-gui=src.main:main",
            "clipboard-manager-gui=src.main:main",  # Legacy alias
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.qss", "*.json"],
        # Resources handled by MANIFEST.in since they're in project root
    },
    zip_safe=False,
    keywords="clipboard history manager cross-platform desktop qt pyside6",
    platforms=["any"],
)
