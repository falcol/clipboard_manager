# clipboard_manager/src/ui/styles.py
"""
Windows 10 Dark Mode Clipboard Manager Styles
"""


class Styles:
    """Windows 10 Dark Mode CSS-like stylesheets for Qt widgets"""

    @staticmethod
    def get_modern_popup_style():
        """Get Windows 10 dark mode popup window stylesheet"""
        return """
        QFrame {
            background: #1f1f1f;
            border-radius: 6px;
            border: 1px solid #3d3d3d;
        }
        """

    @staticmethod
    def get_search_bar_style():
        """Get Windows 10 dark mode search bar stylesheet"""
        return """
        QFrame {
            background: #2d2d2d;
            border: none;
            border-top: 1px solid #3d3d3d;
            border-bottom: 1px solid #3d3d3d;
        }
        """

    @staticmethod
    def get_modern_clipboard_item_style(hovered=False):
        """Get Windows 10 dark mode clipboard item stylesheet"""
        if hovered:
            return """
            QFrame {
                background: #3d3d3d;
                border: 1px solid #0078d4;
                border-radius: 4px;
                margin: 1px;
                padding: 3px;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
            }
            """
        else:
            return """
            QFrame {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin: 1px;
                padding: 3px;
            }
            QFrame:hover {
                background: #3d3d3d;
                border: 1px solid #0078d4;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
            }
            """

    @staticmethod
    def get_action_button_style(button_type="normal"):
        """Get Windows 10 dark mode action button stylesheet"""
        base_style = """
            QPushButton {
                border: none;
                border-radius: 12px;
                font-size: 11px;
                font-weight: normal;
                background: transparent;
                color: #cccccc;
            }
            QPushButton:hover {
                background: #3d3d3d;
                color: #ffffff;
            }
            QPushButton:pressed {
                background: #2d2d2d;
            }
        """

        if button_type == "pin":
            return (
                base_style
                + """
                QPushButton {
                    color: #888888;
                }
                QPushButton:hover {
                    color: #0078d4;
                    background: rgba(0, 120, 212, 0.1);
                }
            """
            )
        elif button_type == "pin_active":
            return (
                base_style
                + """
                QPushButton {
                    color: #0078d4;
                    background: rgba(0, 120, 212, 0.1);
                }
                QPushButton:hover {
                    color: #ffffff;
                    background: rgba(0, 120, 212, 0.2);
                }
            """
            )
        elif button_type == "delete":
            return (
                base_style
                + """
                QPushButton {
                    color: #888888;
                }
                QPushButton:hover {
                    color: #ff4444;
                    background: rgba(255, 68, 68, 0.1);
                }
            """
            )

        return base_style

    @staticmethod
    def get_modern_scrollbar_style():
        """Get Windows 10 dark mode scrollbar stylesheet"""
        return """
        QScrollArea {
            border: none;
            background: transparent;
        }

        QScrollBar:vertical {
            background: transparent;
            width: 6px;
            border: none;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background: #5a5a5a;
            border-radius: 3px;
            min-height: 20px;
            margin: 1px;
        }

        QScrollBar::handle:vertical:hover {
            background: #7a7a7a;
        }

        QScrollBar::handle:vertical:pressed {
            background: #0078d4;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
            border: none;
            background: none;
        }

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: none;
        }
        """

    @staticmethod
    def get_popup_window_style():
        """Get Windows 10 dark mode popup window stylesheet for backward compatibility"""
        return """
        QWidget {
            background-color: #1f1f1f;
            color: #ffffff;
            border-radius: 6px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }

        QScrollArea {
            border: none;
            background-color: transparent;
        }

        QScrollBar:vertical {
            background-color: transparent;
            width: 6px;
            border-radius: 3px;
        }

        QScrollBar::handle:vertical {
            background-color: #5a5a5a;
            border-radius: 3px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #7a7a7a;
        }

        QPushButton {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 4px 8px;
            color: #ffffff;
        }

        QPushButton:hover {
            background-color: #3d3d3d;
        }

        QPushButton:pressed {
            background-color: #1f1f1f;
        }
        """

    @staticmethod
    def get_clipboard_item_style(hovered=False):
        """Get Windows 10 dark mode clipboard item stylesheet for backward compatibility"""
        bg_color = "#3d3d3d" if hovered else "#2d2d2d"
        return f"""
        QFrame {{
            background-color: {bg_color};
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            margin: 1px;
        }}

        QLabel {{
            color: #ffffff;
            background-color: transparent;
            border: none;
        }}

        QPushButton {{
            background-color: transparent;
            border: none;
            border-radius: 12px;
            color: #cccccc;
            font-size: 11px;
        }}

        QPushButton:hover {{
            background-color: #3d3d3d;
            color: #ffffff;
        }}
        """

    @staticmethod
    def get_settings_window_style():
        """Get Windows 10 dark mode settings window stylesheet"""
        return """
        QDialog {
            background-color: #1f1f1f;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
        }

        QGroupBox {
            font-weight: bold;
            border: 1px solid #3d3d3d;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
            background: #2d2d2d;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px 0 8px;
            color: #0078d4;
            font-size: 12px;
            font-weight: bold;
        }

        QLabel {
            color: #ffffff;
            background: transparent;
        }

        QSpinBox {
            background: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 6px;
            color: #ffffff;
            font-size: 11px;
        }

        QSpinBox:focus {
            border: 1px solid #0078d4;
            background: #3d3d3d;
        }

        QSpinBox::up-button, QSpinBox::down-button {
            background: #3d3d3d;
            border: none;
            width: 16px;
            border-radius: 2px;
        }

        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background: #0078d4;
        }

        QCheckBox {
            color: #ffffff;
            spacing: 8px;
            font-size: 11px;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 3px;
        }

        QCheckBox::indicator:unchecked {
            background: #2d2d2d;
            border: 1px solid #3d3d3d;
        }

        QCheckBox::indicator:unchecked:hover {
            background: #3d3d3d;
            border: 1px solid #0078d4;
        }

        QCheckBox::indicator:checked {
            background: #0078d4;
            border: 1px solid #0078d4;
        }

        QCheckBox::indicator:checked:hover {
            background: #0086f0;
        }

        QPushButton {
            background: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 8px 16px;
            color: #ffffff;
            min-width: 90px;
            font-size: 11px;
            font-weight: 500;
        }

        QPushButton:hover {
            background: #3d3d3d;
            border: 1px solid #0078d4;
        }

        QPushButton:pressed {
            background: #1f1f1f;
            border: 1px solid #005a9e;
        }

        QPushButton:default {
            background: #0078d4;
            border: 1px solid #0078d4;
        }

        QPushButton:default:hover {
            background: #0086f0;
        }
        """

    @staticmethod
    def get_system_tray_menu_style():
        """Get Windows 10 dark mode system tray menu stylesheet"""
        return """
        QMenu {
            background-color: #1f1f1f;
            color: #ffffff;
            border: 1px solid #3d3d3d;
            border-radius: 6px;
            padding: 8px 0px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }

        QMenu::item {
            padding: 8px 20px;
            margin: 1px 4px;
            border-radius: 3px;
        }

        QMenu::item:selected {
            background: #0078d4;
        }

        QMenu::item:pressed {
            background: #005a9e;
        }

        QMenu::separator {
            height: 1px;
            background: #3d3d3d;
            margin: 4px 10px;
        }
        """
