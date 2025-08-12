# clipboard_manager/src/ui/settings_window.py
"""
Settings window for configuration - macOS-like layout and spacing
"""
import logging

from PySide6.QtCore import Qt
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ui.settings_window.compact_combo_box import CompactComboBox
from utils.config import Config

logger = logging.getLogger(__name__)


class SettingsWindow(QDialog):
    """Settings configuration window"""

    settings_changed = pyqtSignal()

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.setObjectName("settingsDialog")
        # macOS-like: resizable, min-size instead of fixed-size
        self.setMinimumSize(820, 620)
        self.setWindowTitle("Preferences")

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup the UI (macOS-like)"""
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # General
        general_group = QGroupBox("General")
        general_group.setObjectName("preferencesSection")
        general_group.setFlat(True)
        general_layout = QFormLayout(general_group)
        general_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        general_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        general_layout.setContentsMargins(8, 8, 8, 8)
        general_layout.setHorizontalSpacing(12)
        general_layout.setVerticalSpacing(10)

        # Max items
        self.max_items_spin = QSpinBox()
        self.max_items_spin.setObjectName("formControl")
        self.max_items_spin.setRange(10, 100)
        self.max_items_spin.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        general_layout.addRow("Max clipboard items:", self.max_items_spin)

        # Max text length
        self.max_text_spin = QSpinBox()
        self.max_text_spin.setObjectName("formControl")
        self.max_text_spin.setRange(1000, 2_000_000)
        self.max_text_spin.setSingleStep(1000)
        general_layout.addRow("Max text length:", self.max_text_spin)

        # Global hotkey (simple picker: modifiers + key)
        hotkey_row = QHBoxLayout()
        hotkey_row.setSpacing(8)

        # Modifiers
        self.chk_ctrl = QCheckBox("Ctrl")
        self.chk_alt = QCheckBox("Alt")
        self.chk_shift = QCheckBox("Shift")
        # Cross-platform label for Super/Win
        import sys as _sys
        super_label = "Win" if _sys.platform.startswith("win") else "Super"
        self.chk_super = QCheckBox(super_label)

        for cb in (self.chk_ctrl, self.chk_alt, self.chk_shift, self.chk_super):
            cb.setObjectName("formCheck")
            hotkey_row.addWidget(cb)

        # Key selector
        self.key_combo = CompactComboBox()
        self.key_combo.setObjectName("compactKeyCombo")  # Unique object name
        # Aggressive height limiting
        self.key_combo.setMaxVisibleItems(15)
        self.key_combo.setMinimumContentsLength(10)
        self.key_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.key_combo.setFixedHeight(28)

        # Use very specific CSS selector with !important
        self._populate_key_combo()
        hotkey_row.addWidget(self.key_combo)

        # Clear button
        self.hotkey_clear_btn = QPushButton("Clear")
        self.hotkey_clear_btn.setObjectName("secondaryButton")
        hotkey_row.addWidget(self.hotkey_clear_btn)

        # Preview label
        self.hotkey_preview = QLabel("")
        self.hotkey_preview.setObjectName("settingsLabel")
        hotkey_row.addWidget(self.hotkey_preview)

        # Container for row
        hotkey_container = QWidget()
        hotkey_container.setLayout(hotkey_row)
        general_layout.addRow("Global hotkey:", hotkey_container)

        # (Optional fallback hidden text input)
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setObjectName("formControl")
        self.hotkey_input.setPlaceholderText("e.g., ctrl+alt+v")
        self.hotkey_input.setVisible(False)

        # Wire events to update preview
        for cb in (self.chk_ctrl, self.chk_alt, self.chk_shift, self.chk_super):
            cb.stateChanged.connect(self._update_hotkey_preview)
        self.key_combo.currentIndexChanged.connect(self._update_hotkey_preview)
        self.hotkey_clear_btn.clicked.connect(self._clear_hotkey_selection)

        # Autostart
        self.autostart_check = QCheckBox("Start with system")
        self.autostart_check.setObjectName("formCheck")
        general_layout.addRow(QWidget(), self.autostart_check)  # align like macOS
        root.addWidget(general_group)

        # Appearance
        appearance_group = QGroupBox("Appearance")
        appearance_group.setObjectName("preferencesSection")
        appearance_group.setFlat(True)
        appearance_layout = QFormLayout(appearance_group)
        appearance_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        appearance_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        appearance_layout.setContentsMargins(8, 8, 8, 8)
        appearance_layout.setHorizontalSpacing(12)
        appearance_layout.setVerticalSpacing(10)

        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("formControl")
        self.theme_map = {
            "Dark Amoled": "dark_amoled",
            "Dark Solarized": "dark_solarized",
            "Dark Win11": "dark_win11",
            "Nord": "nord",
            "Vespera": "vespera",
        }
        self.theme_combo.addItems(list(self.theme_map.keys()))
        appearance_layout.addRow("Theme:", self.theme_combo)
        root.addWidget(appearance_group)

        # Performance
        performance_group = QGroupBox("Performance & RAM")
        performance_group.setObjectName("preferencesSection")
        performance_group.setFlat(True)
        performance_layout = QFormLayout(performance_group)
        performance_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        performance_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        performance_layout.setContentsMargins(8, 8, 8, 8)
        performance_layout.setHorizontalSpacing(12)
        performance_layout.setVerticalSpacing(10)

        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setObjectName("formControl")
        self.cache_size_spin.setRange(10, 100)
        self.cache_size_spin.setSuffix(" MB")
        performance_layout.addRow("Cache size:", self.cache_size_spin)

        self.thumbnail_size_spin = QSpinBox()
        self.thumbnail_size_spin.setObjectName("formControl")
        self.thumbnail_size_spin.setRange(32, 128)
        self.thumbnail_size_spin.setSuffix(" px")
        performance_layout.addRow("Thumbnail size:", self.thumbnail_size_spin)

        self.image_quality_spin = QSpinBox()
        self.image_quality_spin.setObjectName("formControl")
        self.image_quality_spin.setRange(50, 95)
        self.image_quality_spin.setSuffix("%")
        performance_layout.addRow("Image quality:", self.image_quality_spin)

        self.cleanup_interval_spin = QSpinBox()
        self.cleanup_interval_spin.setObjectName("formControl")
        self.cleanup_interval_spin.setRange(1, 48)
        self.cleanup_interval_spin.setSuffix(" hours")
        performance_layout.addRow("Cleanup interval:", self.cleanup_interval_spin)

        root.addWidget(performance_group)
        root.addStretch()

        # Footer buttons - right aligned, flat macOS style
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(8)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("dangerButton")
        reset_btn.clicked.connect(self.reset_settings)

        footer.addWidget(reset_btn)
        footer.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_settings)

        footer.addWidget(cancel_btn)
        footer.addWidget(save_btn)

        root.addLayout(footer)

    def load_settings(self):
        """Load settings from original config"""
        self.max_items_spin.setValue(self.config.get("max_items", 25))
        self.max_text_spin.setValue(self.config.get("max_text_length", 1_000_000))
        self.autostart_check.setChecked(self.config.get("autostart", False))

        # Hotkey → parse to UI
        self._apply_hotkey_to_ui(str(self.config.get("hotkey", "super+c")))
        self._update_hotkey_preview()

        self.cache_size_spin.setValue(self.config.get("cache_size_mb", 25))
        self.thumbnail_size_spin.setValue(self.config.get("thumbnail_size", 64))
        self.image_quality_spin.setValue(self.config.get("image_quality", 85))
        self.cleanup_interval_spin.setValue(
            self.config.get("cleanup_interval_hours", 12)
        )

        current_theme = self.config.get("theme", "dark_win11")
        try:
            key = next(k for k, v in self.theme_map.items() if v == current_theme)
            self.theme_combo.setCurrentText(key)
        except StopIteration:
            self.theme_combo.setCurrentText("Dark Win11")

    def save_settings(self):
        """Save settings only when Save button is clicked"""
        try:
            # Collect hotkey from UI (modifiers + key)
            hotkey_value = self._collect_hotkey_from_ui()
            if not hotkey_value:
                # Fallback to hidden text input if user insists
                hotkey_value = self.hotkey_input.text().strip()
            if hotkey_value and not self._is_valid_hotkey(hotkey_value):
                QMessageBox.warning(
                    self,
                    "Invalid Hotkey",
                    "Hotkey format is invalid. Use patterns like 'super+c' or 'ctrl+shift+v'.",
                )
                return

            # Basic conflict detection with in-app shortcuts (example: Ctrl+F)
            if hotkey_value.lower() == "ctrl+f":
                reply = QMessageBox.question(
                    self,
                    "Conflict",
                    "This hotkey conflicts with in-app shortcut (Ctrl+F). Override?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            self.config.set("max_items", self.max_items_spin.value())
            self.config.set("max_text_length", self.max_text_spin.value())
            self.config.set("autostart", self.autostart_check.isChecked())

            # Save hotkey
            if hotkey_value:
                self.config.set("hotkey", hotkey_value.lower())

            self.config.set("cache_size_mb", self.cache_size_spin.value())
            self.config.set("thumbnail_size", self.thumbnail_size_spin.value())
            self.config.set("image_quality", self.image_quality_spin.value())
            self.config.set(
                "cleanup_interval_hours", self.cleanup_interval_spin.value()
            )

            # Theme
            theme_key = self.theme_combo.currentText()
            self.config.set("theme", self.theme_map.get(theme_key, "dark_win11"))

            self.config.save()
            self.settings_changed.emit()

            # Handle autostart
            from utils.autostart import AutostartManager

            autostart_manager = AutostartManager()
            if self.autostart_check.isChecked():
                autostart_manager.enable()
            else:
                autostart_manager.disable()

            self.accept()

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    # --- Hotkey UI helpers ---
    def _populate_key_combo(self):
        """Populate key combo with A-Z, 0-9, F1-12 and common special keys."""
        keys: list[tuple[str, str]] = []
        # Letters
        for code in range(ord('A'), ord('Z') + 1):
            ch = chr(code)
            keys.append((ch, ch.lower()))
        # Digits
        for d in "0123456789":
            keys.append((d, d))
        # Function keys
        for i in range(1, 13):
            disp = f"F{i}"
            keys.append((disp, disp.lower()))
        # Specials
        specials = [
            ("Esc", "esc"), ("Tab", "tab"), ("Space", "space"),
            ("Enter", "enter"), ("Backspace", "backspace"),
            ("Insert", "insert"), ("Delete", "delete"),
            ("Home", "home"), ("End", "end"),
            ("PageUp", "pageup"), ("PageDown", "pagedown"),
            ("Up", "up"), ("Down", "down"), ("Left", "left"), ("Right", "right"),
        ]
        keys.extend(specials)

        self.key_combo.clear()
        for disp, token in keys:
            self.key_combo.addItem(disp, userData=token)

    def _clear_hotkey_selection(self):
        for cb in (self.chk_ctrl, self.chk_alt, self.chk_shift, self.chk_super):
            cb.setChecked(False)
        self.key_combo.setCurrentIndex(-1)
        self._update_hotkey_preview()

    def _collect_hotkey_from_ui(self) -> str:
        """Build normalized hotkey string from UI selections."""
        parts: list[str] = []
        if self.chk_ctrl.isChecked():
            parts.append("ctrl")
        if self.chk_alt.isChecked():
            parts.append("alt")
        if self.chk_shift.isChecked():
            parts.append("shift")
        if self.chk_super.isChecked():
            parts.append("super")

        idx = self.key_combo.currentIndex()
        key = self.key_combo.itemData(idx) if idx >= 0 else None
        if key:
            parts.append(str(key))
        return "+".join(parts)

    def _apply_hotkey_to_ui(self, hotkey: str):
        """Parse existing hotkey string to UI selections."""
        # Reset first
        self._clear_hotkey_selection()
        tokens = [t.strip().lower() for t in hotkey.split("+") if t.strip()]
        for t in tokens:
            if t == "ctrl":
                self.chk_ctrl.setChecked(True)
            elif t == "alt":
                self.chk_alt.setChecked(True)
            elif t == "shift":
                self.chk_shift.setChecked(True)
            elif t in ("super", "win", "cmd"):
                self.chk_super.setChecked(True)
        # Key selection
        key_token = None
        for t in tokens:
            if t not in ("ctrl", "alt", "shift", "super", "win", "cmd"):
                key_token = t
                break
        if key_token:
            # Find matching token in combo
            for i in range(self.key_combo.count()):
                if self.key_combo.itemData(i) == key_token:
                    self.key_combo.setCurrentIndex(i)
                    break
        self._update_hotkey_preview()
        # Keep hidden text in sync as fallback
        self.hotkey_input.setText(self._collect_hotkey_from_ui())

    def _update_hotkey_preview(self):
        """Update preview label with human-readable hotkey."""
        tokens = []
        if self.chk_ctrl.isChecked():
            tokens.append("Ctrl")
        if self.chk_alt.isChecked():
            tokens.append("Alt")
        if self.chk_shift.isChecked():
            tokens.append("Shift")
        import sys as _sys
        if self.chk_super.isChecked():
            tokens.append("Win" if _sys.platform.startswith("win") else "Super")
        idx = self.key_combo.currentIndex()
        if idx >= 0:
            tokens.append(self.key_combo.itemText(idx))
        self.hotkey_preview.setText(" + ".join(tokens))

    # --- Helpers ---
    def _is_valid_hotkey(self, hotkey: str) -> bool:
        """Lightweight validation for hotkey string.

        Accepts tokens like ctrl, alt, shift, super, win, cmd and a key (single char or named).
        """
        try:
            tokens = [t.strip().lower() for t in hotkey.split("+") if t.strip()]
            if not tokens:
                return False

            modifiers = {
                "ctrl",
                "control",
                "alt",
                "shift",
                "super",
                "super_l",
                "win",
                "cmd",
            }
            named_keys = {
                "enter",
                "return",
                "tab",
                "space",
                "esc",
                "escape",
                "backspace",
                "delete",
                "home",
                "end",
                "pageup",
                "pagedown",
                "up",
                "down",
                "left",
                "right",
            }

            valid = True
            for i, token in enumerate(tokens):
                if token in modifiers:
                    continue
                # last (or any) non-modifier token must be key
                if len(token) == 1:
                    # alpha-numeric allowed
                    continue
                if token in named_keys or (token.startswith("f") and token[1:].isdigit()):
                    continue
                valid = False
                break

            return valid
        except Exception:
            return False

    def reset_settings(self):
        """Reset to default settings"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.config.reset_to_defaults()
            self.load_settings()

    def reject(self):
        """Handle when cancel/close window"""
        self.load_settings()
        super().reject()

    def showEvent(self, event):
        """Ensure settings are loaded every time the window is opened"""
        self.load_settings()
        super().showEvent(event)
