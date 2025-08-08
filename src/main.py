#!/usr/bin/env python3
# clipboard_manager/src/main.py
"""
Enhanced main entry point for Clipboard Manager - Modular version
"""
import sys
from pathlib import Path

from startup import (
    check_single_instance,
    cleanup_resources,
    create_clipboard_manager,
    setup_enhanced_logging,
    start_application,
)
from utils.process_utils import setup_process_name

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Enhanced main function with refactored modular approach"""
    single_instance = None
    logger = None

    try:
        # Phase 1: Setup process and logging
        setup_process_name()
        logger = setup_enhanced_logging()
        logger.info("Starting Clipboard Manager application...")

        # Phase 2: Check single instance
        single_instance = check_single_instance()
        if single_instance is None:
            return 1

        # Phase 3: Create and start application
        manager = create_clipboard_manager()
        return start_application(manager)

    except KeyboardInterrupt:
        if logger:
            logger.info("Application interrupted by user")
        else:
            print("Application interrupted by user")
        return 0
    except Exception as e:
        if logger:
            logger.error(f"Unexpected error in main: {e}")
        else:
            print(f"Unexpected error in main: {e}")
        return 1
    finally:
        # Phase 4: Cleanup
        cleanup_resources(single_instance)


if __name__ == "__main__":
    sys.exit(main())
