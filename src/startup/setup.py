# clipboard_manager/src/startup/setup.py
"""
Application setup utilities
"""
from utils.logging_config import get_logger, setup_logging
from utils.single_instance import CrossPlatformSingleInstance


def setup_enhanced_logging():
    """Setup enhanced logging configuration"""
    setup_logging(level="INFO", log_to_file=True, log_to_console=True)
    return get_logger(__name__)


def check_single_instance():
    """Check if another instance is already running"""
    single_instance = CrossPlatformSingleInstance()

    if not single_instance.acquire_lock():
        logger = get_logger(__name__)
        logger.error("Another instance of Clipboard Manager is already running")
        return None

    return single_instance


def create_clipboard_manager():
    """Create and initialize the clipboard manager instance"""
    from core.application import EnhancedClipboardManager

    logger = get_logger(__name__)

    try:
        manager = EnhancedClipboardManager()
        logger.info("Clipboard Manager created successfully")
        return manager
    except Exception as e:
        logger.error(f"Failed to create Clipboard Manager: {e}")
        raise
