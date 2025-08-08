# clipboard_manager/src/utils/process_utils.py
"""
Process utilities for cross-platform process name management
"""
import sys


def setup_process_name(process_name: str = "ClipboardManager") -> bool:
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
        print(f"Process name set to: {process_name}")
        return True
    except ImportError:
        # Fallback: modify sys.argv[0] for basic process name change
        try:
            sys.argv[0] = process_name
            print(f"Process name fallback applied: {process_name}")
            return True
        except Exception as e:
            print(f"Failed to set process name: {e}")
            return False
