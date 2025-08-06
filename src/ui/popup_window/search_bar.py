# clipboard_manager/src/ui/popup_window/search_bar.py
"""
Windows 10 Dark Mode Clipboard Manager Popup Window Search Bar
"""
import logging

from PySide6.QtCore import Qt
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton

from ui.styles import Styles

logger = logging.getLogger(__name__)


class SearchBar(QFrame):
    """Windows 10 dark mode search bar widget"""

    search_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(36)
        self.setStyleSheet(Styles.get_search_bar_style())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)

        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setFixedSize(16, 16)
        search_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(search_icon)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clipboard history...")
        self.search_input.setStyleSheet(
            "border: none; background: transparent; color: #ffffff; font-size: 11px;"
        )
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)

        # Clear button
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(16, 16)
        self.clear_btn.setStyleSheet(
            """
            QPushButton {
                border: none;
                background: transparent;
                color: #888888;
                border-radius: 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background: #3d3d3d;
                color: #ffffff;
            }
        """
        )
        self.clear_btn.clicked.connect(self.clear_search)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)

    def on_search_changed(self, text):
        """Handle search text changes"""
        if text.strip():
            self.clear_btn.show()
        else:
            self.clear_btn.hide()
        self.search_requested.emit(text)

    def clear_search(self):
        """Clear search with proper signal emission"""
        self.search_input.clear()
        self.clear_btn.hide()
        self.search_requested.emit("")

    def focus_search(self):
        """Focus search input"""
        self.search_input.setFocus()
