# clipboard_manager/src/ui/styles.py
"""
Modern stylesheet definitions with enhanced visual design - System compatible
"""


class Styles:
    """Modern CSS-like stylesheets for Qt widgets with system compatibility"""

    @staticmethod
    def get_modern_popup_style():
        """Get modern popup window stylesheet - compatible with all Linux systems"""
        return """
        QFrame {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1a1a2e, stop:1 #16213e);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        """

    @staticmethod
    def get_search_bar_style():
        """Get enhanced search bar stylesheet - system compatible"""
        return """
        QFrame {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.1), stop:1 rgba(255, 255, 255, 0.05));
            border: none;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        """

    @staticmethod
    def get_modern_clipboard_item_style(hovered=False):
        """Get enhanced clipboard item stylesheet - system compatible"""
        if hovered:
            return """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.15), stop:1 rgba(255, 255, 255, 0.08));
                border: 2px solid #4facfe;
                border-radius: 16px;
                margin: 6px;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
                font-weight: 500;
            }
            """
        else:
            return """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.08), stop:1 rgba(255, 255, 255, 0.03));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                margin: 6px;
            }
            QFrame:hover {
                border: 2px solid #4facfe;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.12), stop:1 rgba(255, 255, 255, 0.06));
            }
            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
                font-weight: 400;
            }
            """

    @staticmethod
    def get_action_button_style(button_type="normal"):
        """Get enhanced action button stylesheet - system compatible"""
        base_style = """
            QPushButton {
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 600;
                background: rgba(255, 255, 255, 0.1);
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
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
                    color: #a0a0a0;
                }
                QPushButton:hover {
                    color: #4facfe;
                    background: rgba(79, 172, 254, 0.2);
                }
            """
            )
        elif button_type == "pin_active":
            return (
                base_style
                + """
                QPushButton {
                    color: #4facfe;
                    background: rgba(79, 172, 254, 0.2);
                }
                QPushButton:hover {
                    color: #ffffff;
                    background: rgba(79, 172, 254, 0.3);
                }
            """
            )
        elif button_type == "delete":
            return (
                base_style
                + """
                QPushButton {
                    color: #a0a0a0;
                }
                QPushButton:hover {
                    color: #ff6b6b;
                    background: rgba(255, 107, 107, 0.2);
                }
            """
            )

        return base_style

    @staticmethod
    def get_modern_scrollbar_style():
        """Get enhanced scrollbar stylesheet - system compatible"""
        return """
        QScrollArea {
            border: none;
            background: transparent;
        }

        QScrollBar:vertical {
            background: transparent;
            width: 12px;
            border: none;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            min-height: 40px;
            margin: 4px;
        }

        QScrollBar::handle:vertical:hover {
            background: rgba(255, 255, 255, 0.4);
        }

        QScrollBar::handle:vertical:pressed {
            background: rgba(79, 172, 254, 0.8);
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
    def get_enhanced_settings_window_style():
        """Get enhanced settings window stylesheet with better layout"""
        return """
        QDialog {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1a1a2e, stop:1 #16213e);
            color: #ffffff;
            border-radius: 20px;
            font-size: 12px;
        }

        QGroupBox {
            font-weight: 600;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            margin-top: 16px;
            padding-top: 16px;
            background: rgba(255, 255, 255, 0.05);
            font-size: 13px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 20px;
            padding: 0 12px 0 12px;
            color: #4facfe;
            font-size: 14px;
            font-weight: 600;
        }

        QLabel {
            color: #ffffff;
            background: transparent;
            font-size: 12px;
            font-weight: 500;
        }

        QSpinBox {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 10px;
            color: #ffffff;
            font-size: 12px;
            font-weight: 500;
            min-height: 20px;
        }

        QSpinBox:focus {
            border: 2px solid #4facfe;
            background: rgba(255, 255, 255, 0.15);
        }

        QSpinBox::up-button, QSpinBox::down-button {
            background: rgba(255, 255, 255, 0.1);
            border: none;
            width: 20px;
            border-radius: 4px;
        }

        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background: #4facfe;
        }

        QCheckBox {
            color: #ffffff;
            spacing: 12px;
            font-size: 12px;
            font-weight: 500;
            padding: 4px 0px;
        }

        QCheckBox::indicator {
            width: 24px;
            height: 24px;
            border-radius: 6px;
        }

        QCheckBox::indicator:unchecked {
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.3);
        }

        QCheckBox::indicator:unchecked:hover {
            background: rgba(255, 255, 255, 0.15);
            border: 2px solid #4facfe;
        }

        QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4facfe, stop:1 #00f2fe);
            border: 2px solid #4facfe;
        }

        QCheckBox::indicator:checked:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5fb8ff, stop:1 #1af8ff);
        }

        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.1), stop:1 rgba(255, 255, 255, 0.05));
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 12px 20px;
            color: #ffffff;
            min-width: 100px;
            font-size: 12px;
            font-weight: 600;
        }

        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.15), stop:1 rgba(255, 255, 255, 0.08));
            border: 1px solid #4facfe;
        }

        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.05), stop:1 rgba(255, 255, 255, 0.02));
            border: 1px solid #4facfe;
        }

        QPushButton:default {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4facfe, stop:1 #00f2fe);
            border: 1px solid #4facfe;
        }

        QPushButton:default:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5fb8ff, stop:1 #1af8ff);
        }
        """

    @staticmethod
    def get_system_tray_menu_style():
        """Get enhanced system tray menu stylesheet - system compatible"""
        return """
        QMenu {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1a1a2e, stop:1 #16213e);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 12px 0px;
            font-size: 12px;
            font-weight: 500;
        }

        QMenu::item {
            padding: 12px 24px;
            margin: 2px 6px;
            border-radius: 6px;
        }

        QMenu::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4facfe, stop:1 #00f2fe);
        }

        QMenu::item:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3a9bff, stop:1 #00e6f0);
        }

        QMenu::separator {
            height: 1px;
            background: rgba(255, 255, 255, 0.1);
            margin: 6px 12px;
        }
        """

    # Legacy styles for backward compatibility
    @staticmethod
    def get_popup_window_style():
        return Styles.get_modern_popup_style()

    @staticmethod
    def get_clipboard_item_style(hovered=False):
        return Styles.get_modern_clipboard_item_style(hovered)

    @staticmethod
    def get_settings_window_style():
        return Styles.get_enhanced_settings_window_style()
