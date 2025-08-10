# clipboard_manager/src/startup/lifecycle.py
"""
Application lifecycle management
"""

import contextlib

from utils.logging_config import get_logger


def start_application(manager):
    """Start the clipboard manager application"""
    logger = get_logger(__name__)

    try:
        return manager.start()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        with contextlib.suppress(Exception):
            manager.quit_application()
        return 0
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        with contextlib.suppress(Exception):
            manager.quit_application()
        return 1


def cleanup_resources(single_instance):
    """Clean up resources before application exit"""
    if single_instance:
        single_instance.release_lock()
