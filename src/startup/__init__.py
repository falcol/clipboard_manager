# clipboard_manager/src/startup/__init__.py
"""
Startup utilities and lifecycle management
"""

from .lifecycle import cleanup_resources, start_application
from .setup import (
    check_single_instance,
    create_clipboard_manager,
    setup_enhanced_logging,
)

__all__ = [
    "setup_enhanced_logging",
    "check_single_instance",
    "create_clipboard_manager",
    "start_application",
    "cleanup_resources",
]
