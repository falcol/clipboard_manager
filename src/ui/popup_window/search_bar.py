# clipboard_manager/src/ui/popup_window/search_bar.py
"""
Windows 10 Dark Mode B1Clip Popup Window Search Bar - FIXED
"""
import logging

from PySide6.QtCore import Qt, QTimer
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton

logger = logging.getLogger(__name__)


class SearchBar(QFrame):
    """Windows 10 dark mode search bar widget with debounced search"""

    search_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Add debounce timer to prevent excessive search calls
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._emit_search)
        self.search_timer.setInterval(200)  # 200ms debounce delay

        self.pending_search = ""
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(36)
        self.setObjectName("searchBar")
        self.setFrameShape(QFrame.Shape.NoFrame)  # flat bar
        self.setLineWidth(0)

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
        self.search_input.setObjectName("searchInput")

        # FIXED: Use multiple signals for reliable search triggering
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.returnPressed.connect(self.on_return_pressed)  # Enter key
        self.search_input.textEdited.connect(self.on_text_edited)  # Direct typing

        layout.addWidget(self.search_input)

        # Clear button
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(16, 16)
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setFlat(True)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_search)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)

    def on_search_changed(self, text):
        """Handle search text changes with debouncing"""
        self.pending_search = text.strip()

        # Show/hide clear button
        if self.pending_search:
            self.clear_btn.show()
        else:
            self.clear_btn.hide()

        # Debounced search - restart timer on each change
        self.search_timer.stop()
        self.search_timer.start()

    def on_return_pressed(self):
        """Handle Enter key - immediate search without debounce"""
        text = self.search_input.text().strip()
        self.search_timer.stop()  # Cancel pending debounced search
        self.search_requested.emit(text)
        logger.debug(f"Immediate search triggered (Enter): '{text}'")

    def on_text_edited(self, text):
        """Handle direct text editing - backup trigger"""
        # This acts as a backup trigger for textChanged
        self.on_search_changed(text)

    def _emit_search(self):
        """Emit the debounced search request"""
        self.search_requested.emit(self.pending_search)
        logger.debug(f"Debounced search triggered: '{self.pending_search}'")

    def clear_search(self):
        """Clear search with immediate trigger"""
        self.search_input.clear()
        self.clear_btn.hide()
        self.search_timer.stop()  # Cancel any pending search
        self.search_requested.emit("")  # Immediate clear
        logger.debug("Search cleared")

    def focus_search(self):
        """Focus search input"""
        self.search_input.setFocus()
        self.search_input.selectAll()  # Select all text for easy replacement
