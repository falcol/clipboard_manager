# clipboard_manager/src/utils/process_utils.py
"""
Process utilities for cross-platform process name management
"""
import sys

from utils.logging_config import get_logger


def setup_process_name(process_name: str = "B1Clip") -> bool:
    """
    Setup process name for system monitors (Task Manager, htop, ps)

    Args:
        process_name: Name to display in system monitors

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Try using setproctitle if available (optional dependency)
        import setproctitle

        setproctitle.setproctitle(process_name)
        get_logger(__name__).info(f"Process name set to: {process_name}")
        return True
    except ImportError:
        # Fallback: modify sys.argv[0] for basic process name change
        try:
            sys.argv[0] = process_name
            get_logger(__name__).info(
                f"Process name fallback applied: {process_name}"
            )
            return True
        except Exception as e:
            get_logger(__name__).error(f"Failed to set process name: {e}")
            return False
