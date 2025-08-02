# clipboard_manager/src/ui/styles.py
"""
Stylesheet definitions for UI components
"""


class Styles:
    """CSS-like stylesheets for Qt widgets"""

    @staticmethod
    def get_popup_window_style():
        """Get popup window stylesheet"""
        return """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            border-radius: 8px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }

        QScrollArea {
            border: none;
            background-color: transparent;
        }

        QScrollBar:vertical {
            background-color: #3c3c3c;
            width: 8px;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 4px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }

        QPushButton {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px 8px;
            color: #ffffff;
        }

        QPushButton:hover {
            background-color: #4a4a4a;
        }

        QPushButton:pressed {
            background-color: #363636;
        }
        """

    @staticmethod
    def get_clipboard_item_style(hovered=False):
        """Get clipboard item stylesheet"""
        bg_color = "#3a3a3a" if hovered else "#333333"
        return f"""
        QFrame {{
            background-color: {bg_color};
            border: 1px solid #444444;
            border-radius: 4px;
            margin: 2px;
        }}

        QLabel {{
            color: #ffffff;
            background-color: transparent;
            border: none;
        }}

        QPushButton {{
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 2px;
            color: #ffffff;
            font-size: 12px;
        }}

        QPushButton:hover {{
            background-color: #4a4a4a;
        }}
        """

    @staticmethod
    def get_settings_window_style():
        """Get settings window stylesheet"""
        return """
        QDialog {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
        }

        QGroupBox {
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }

        QLabel {
            color: #ffffff;
        }

        QSpinBox {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 2px;
            color: #ffffff;
        }

        QCheckBox {
            color: #ffffff;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }

        QCheckBox::indicator:unchecked {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 3px;
        }

        QCheckBox::indicator:checked {
            background-color: #0078d4;
            border: 1px solid #005a9e;
            border-radius: 3px;
        }

        QPushButton {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 6px 12px;
            color: #ffffff;
            min-width: 80px;
        }

        QPushButton:hover {
            background-color: #4a4a4a;
        }

        QPushButton:pressed {
            background-color: #363636;
        }
        """
