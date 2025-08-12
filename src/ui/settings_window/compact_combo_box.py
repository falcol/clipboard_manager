from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox


class CompactComboBox(QComboBox):
    """QComboBox with fixed popup size/position."""

    def showPopup(self) -> None:  # type: ignore[override]
        super().showPopup()
        try:
            view = self.view()
            view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            try:
                example_row_height = max(20, view.sizeHintForRow(0))
            except Exception:
                example_row_height = 22

            max_visible = max(1, min(self.maxVisibleItems(), 20))
            popup_height = min(350, example_row_height * max_visible + 8)

            view.setMinimumHeight(popup_height)
            view.setMaximumHeight(popup_height)

            container = view.window()
            if container is not None:
                try:
                    # Minimum width = width of combobox
                    popup_width = max(container.width(), self.width())
                    container.setMinimumHeight(popup_height)
                    container.setMaximumHeight(popup_height)
                    container.resize(popup_width, popup_height)

                    # Calculate the position of the combobox (bottom, left like HTML select)
                    below_left = self.mapToGlobal(self.rect().bottomLeft())
                    above_left = self.mapToGlobal(self.rect().topLeft())

                    screen = (self.window().screen().availableGeometry()
                              if self.window() and self.window().screen()
                              else QApplication.primaryScreen().availableGeometry())

                    x = max(screen.left(), min(below_left.x(), screen.right() - popup_width))
                    y = below_left.y()

                    # If there is not enough space below, show above the combobox
                    if y + popup_height > screen.bottom():
                        y = above_left.y() - popup_height

                    container.move(x, y)
                except Exception:
                    pass
        except Exception:
            pass
