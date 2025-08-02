# clipboard_manager/setup.py
"""
Setup script for Clipboard Manager
"""
from pathlib import Path

from setuptools import find_packages, setup

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = (
    readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
)

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split("\n")

setup(
    name="clipboard-manager",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A cross-platform clipboard history manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/clipboard-manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "clipboard-manager=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.qss", "*.png", "*.ico"],
    },
)
