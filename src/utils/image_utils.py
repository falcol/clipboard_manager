# clipboard_manager/src/utils/image_utils.py
"""
Image processing utilities
"""
import logging

from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QPixmap

logger = logging.getLogger(__name__)


class ImageUtils:
    """Image processing utilities"""

    @staticmethod
    def pixmap_to_bytes(pixmap: QPixmap, format: str = "PNG") -> bytes:
        """Convert QPixmap to bytes"""
        try:
            byte_array = QBuffer()
            byte_array.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(byte_array, format)
            return byte_array.data().data()
        except Exception as e:
            logger.error(f"Error converting pixmap to bytes: {e}")
            return b""

    @staticmethod
    def bytes_to_pixmap(data: bytes) -> QPixmap:
        """Convert bytes to QPixmap"""
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            return pixmap
        except Exception as e:
            logger.error(f"Error converting bytes to pixmap: {e}")
            return QPixmap()

    @staticmethod
    def create_thumbnail(pixmap: QPixmap, size: tuple) -> QPixmap:
        """Create thumbnail from pixmap"""
        try:
            return pixmap.scaled(
                size[0],
                size[1],
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return QPixmap()
