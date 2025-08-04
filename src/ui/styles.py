# clipboard_manager/src/ui/styles.py
"""
Modern stylesheet definitions inspired by GNOME Clipboard Indicator
"""


class Styles:
    """Modern CSS-like stylesheets for Qt widgets"""

    @staticmethod
    def get_modern_popup_style():
        """Get modern popup window stylesheet"""
        return """
        QFrame {
            background: #2b2b2b;
            border-radius: 12px;
            border: 1px solid #404040;
        }
        """

    @staticmethod
    def get_search_bar_style():
        """Get search bar stylesheet"""
        return """
        QFrame {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #333333, stop:1 #2a2a2a);
            border: none;
            border-top: 1px solid #404040;
            border-bottom: 1px solid #404040;
        }
        """

    @staticmethod
    def get_modern_clipboard_item_style(hovered=False):
        """Get modern clipboard item stylesheet"""
        if hovered:
            return """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #404040, stop:1 #383838);
                border: 1px solid #0078d4;
                border-radius: 8px;
                margin: 2px;
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
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #353535, stop:1 #2e2e2e);
                border: 1px solid #444444;
                border-radius: 8px;
                margin: 2px;
            }
            QFrame:hover {
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
        """Get action button stylesheet"""
        base_style = """
            QPushButton {
                border: none;
                border-radius: 14px;
                font-size: 12px;
                font-weight: bold;
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid #aaa;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """

        if button_type == "pin":
            return (
                base_style
                + """
                QPushButton {
                    color: #888;
                }
                QPushButton:hover {
                    color: #0078d4;
                    background: rgba(0, 120, 212, 0.2);
                }
            """
            )
        elif button_type == "pin_active":
            return (
                base_style
                + """
                QPushButton {
                    color: #0078d4;
                    background: rgba(0, 120, 212, 0.2);
                }
                QPushButton:hover {
                    color: #ffffff;
                    background: rgba(0, 120, 212, 0.3);
                }
            """
            )
        elif button_type == "delete":
            return (
                base_style
                + """
                QPushButton {
                    color: #888;
                }
                QPushButton:hover {
                    color: #ff4444;
                    background: rgba(255, 68, 68, 0.2);
                }
            """
            )

        return base_style

    @staticmethod
    def get_modern_scrollbar_style():
        """Get modern scrollbar stylesheet"""
        return """
        QScrollArea {
            border: none;
            background: transparent;
        }

        QScrollBar:vertical {
            background: transparent;
            width: 8px;
            border: none;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
            min-height: 30px;
            margin: 2px;
        }

        QScrollBar::handle:vertical:hover {
            background: rgba(255, 255, 255, 0.5);
        }

        QScrollBar::handle:vertical:pressed {
            background: rgba(0, 120, 212, 0.8);
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
        """Get legacy popup window stylesheet for backward compatibility"""
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
        """Get legacy clipboard item stylesheet for backward compatibility"""
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
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #333333, stop:1 #2a2a2a);
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
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #404040, stop:1 #353535);
            border: 1px solid #555555;
            border-radius: 6px;
            padding: 6px;
            color: #ffffff;
            font-size: 11px;
        }

        QSpinBox:focus {
            border: 2px solid #0078d4;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #454545, stop:1 #3a3a3a);
        }

        QSpinBox::up-button, QSpinBox::down-button {
            background: #555555;
            border: none;
            width: 16px;
            border-radius: 3px;
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
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }

        QCheckBox::indicator:unchecked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #404040, stop:1 #353535);
            border: 1px solid #555555;
        }

        QCheckBox::indicator:unchecked:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #454545, stop:1 #3a3a3a);
            border: 1px solid #0078d4;
        }

        QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0078d4, stop:1 #005a9e);
            border: 1px solid #0078d4;
        }

        QCheckBox::indicator:checked:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0086f0, stop:1 #0066b8);
        }

        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #404040, stop:1 #353535);
            border: 1px solid #555555;
            border-radius: 6px;
            padding: 8px 16px;
            color: #ffffff;
            min-width: 90px;
            font-size: 11px;
            font-weight: 500;
        }

        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4a4a4a, stop:1 #3f3f3f);
            border: 1px solid #0078d4;
        }

        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #363636, stop:1 #2b2b2b);
            border: 1px solid #005a9e;
        }

        QPushButton:default {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0078d4, stop:1 #005a9e);
            border: 1px solid #0078d4;
        }

        QPushButton:default:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0086f0, stop:1 #0066b8);
        }
        """

    @staticmethod
    def get_system_tray_menu_style():
        """Get system tray menu stylesheet"""
        return """
        QMenu {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #404040;
            border-radius: 8px;
            padding: 8px 0px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }

        QMenu::item {
            padding: 8px 20px;
            margin: 2px 4px;
            border-radius: 4px;
        }

        QMenu::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0078d4, stop:1 #005a9e);
        }

        QMenu::item:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #005a9e, stop:1 #004578);
        }

        QMenu::separator {
            height: 1px;
            background: #404040;
            margin: 4px 10px;
        }
        """
