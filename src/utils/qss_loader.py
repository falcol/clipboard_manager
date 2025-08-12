# ===============================================
# FILE: src/utils/qss_loader.py
# QSS file loader for clipboard manager
# ===============================================

"""
QSS file loader for clipboard manager
Loads and applies QSS stylesheets from files
"""
import logging
from pathlib import Path
from typing import Optional, cast

from PySide6.QtWidgets import QApplication, QWidget

logger = logging.getLogger(__name__)


class QSSLoader:
    """Load and apply QSS stylesheets"""

    def __init__(self, styles_dir: Optional[Path] = None):
        if styles_dir is None:
            # Default to resources/styles relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.styles_dir = project_root / "resources" / "styles"
        else:
            self.styles_dir = styles_dir

        self.styles_dir.mkdir(parents=True, exist_ok=True)

    def load_stylesheet(self, filename: str) -> str:
        """Load QSS stylesheet from file"""
        file_path = self.styles_dir / filename

        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                logger.debug(f"Loaded QSS from {file_path}")
                return content
            else:
                logger.warning(f"QSS file not found: {file_path}")
                return ""
        except Exception as e:
            logger.error(f"Error loading QSS file {file_path}: {e}")
            return ""

    def load_stylesheets(self, filenames: list[str]) -> str:
        """Load and concatenate multiple QSS files."""
        contents: list[str] = []
        missing: list[str] = []
        for fn in filenames:
            css = self.load_stylesheet(fn)
            if css:
                contents.append(css)
            else:
                missing.append(fn)
        if missing:
            logger.warning(f"Missing QSS files: {missing}")
        return "\n".join(contents)

    def apply_stylesheet(self, widget, filename: str):
        """Apply QSS stylesheet to widget"""
        stylesheet = self.load_stylesheet(filename)
        if stylesheet:
            widget.setStyleSheet(stylesheet)
            logger.debug(f"Applied {filename} to {widget.__class__.__name__}")

    def apply_stylesheet_to_widget_and_children(self, widget, filename: str):
        """Apply QSS to widget and all its children"""
        stylesheet = self.load_stylesheet(filename)
        if stylesheet:
            widget.setStyleSheet(stylesheet)

            # Apply to all child widgets
            for child in widget.findChildren(QWidget):
                if child != widget:  # Avoid infinite recursion
                    child.setStyleSheet(stylesheet)

            logger.debug(
                f"Applied {filename} to {widget.__class__.__name__} and children"
            )

    def apply_app_stylesheet(self, filenames: list[str]):
        """Apply QSS to the entire application."""
        css = self.load_stylesheets(filenames)
        if css:
            app = cast(Optional[QApplication], QApplication.instance())
            if app is not None:
                app.setStyleSheet(css)

    def get_available_stylesheets(self) -> list:
        """Get list of available QSS files"""
        if not self.styles_dir.exists():
            return []

        return [f.name for f in self.styles_dir.glob("*.qss")]
