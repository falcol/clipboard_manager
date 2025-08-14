# clipboard_manager/src/utils/single_instance.py
"""
Cross-platform single instance checker
"""
import os
import platform
import tempfile
import time
from pathlib import Path

from utils.logging_config import get_logger

logger = get_logger(__name__)

class CrossPlatformSingleInstance:
    """Cross-platform single instance checker"""

    def __init__(self, lock_name: str = "clipboard_manager.lock"):
        self.lock_name = lock_name
        self.platform = platform.system().lower()
        self.lock_file = None
        self.lock_fd = None
        self.is_locked = False

        # Determine lock file location based on platform
        if self.platform == "windows":
            self.lock_path = Path(tempfile.gettempdir()) / f"{lock_name}"
        else:
            # Linux/macOS
            self.lock_path = Path.home() / f".{lock_name}"

    def acquire_lock(self) -> bool:
        """Acquire lock for single instance check"""
        try:
            if self.platform == "windows":
                return self._acquire_lock_windows()
            else:
                return self._acquire_lock_unix()
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    def _acquire_lock_windows(self) -> bool:
        """Windows-specific lock acquisition using file locking"""
        try:
            # Create lock file
            self.lock_file = open(self.lock_path, "w")

            # Try to acquire exclusive lock
            import msvcrt

            msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)

            # Write PID to lock file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()

            self.is_locked = True

            logger.info(f"Windows lock acquired: {self.lock_path}")
            return True

        except (IOError, OSError) as e:
            # Another instance is running
            logger.warning(f"Windows lock failed: {e}")
            if self.lock_file:
                self.lock_file.close()
            return False
        except ImportError:
            # Fallback for Windows without msvcrt
            return self._acquire_lock_fallback()

    def _acquire_lock_unix(self) -> bool:
        """Unix/Linux lock acquisition using fcntl"""
        try:
            import fcntl

            self.lock_file = open(self.lock_path, "w")

            # Try to acquire exclusive lock using getattr for better compatibility
            lock_ex = getattr(fcntl, "LOCK_EX", 1)
            lock_nb = getattr(fcntl, "LOCK_NB", 2)
            flock_func = getattr(fcntl, "flock", None)

            if flock_func:
                flock_func(self.lock_file.fileno(), lock_ex | lock_nb)
            else:
                # Fallback if flock is not available
                return self._acquire_lock_fallback()

            # Write PID to lock file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()

            self.is_locked = True
            logger.info(f"Unix lock acquired: {self.lock_path}")
            return True

        except ImportError:
            # Fallback for systems without fcntl
            logger.warning("fcntl not available, using fallback method")
            return self._acquire_lock_fallback()
        except (IOError, OSError) as e:
            # Another instance is running
            logger.warning(f"Unix lock failed: {e}")
            if self.lock_file:
                self.lock_file.close()
            return False

    def _acquire_lock_fallback(self) -> bool:
        """Fallback lock method using file existence check"""
        try:
            # Check if lock file exists and is recent (within 30 seconds)
            if self.lock_path.exists():
                # Check if lock file is stale (older than 30 seconds)
                lock_age = time.time() - self.lock_path.stat().st_mtime
                if lock_age < 30:
                    # Lock file is recent, another instance is running
                    logger.warning(f"Lock file exists and recent: {self.lock_path}")
                    return False
                else:
                    # Stale lock file, remove it
                    logger.info(f"Removing stale lock file: {self.lock_path}")
                    self.lock_path.unlink()

            # Create new lock file
            self.lock_file = open(self.lock_path, "w")
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()

            self.is_locked = True

            logger.info(f"Fallback lock acquired: {self.lock_path}")
            return True

        except Exception as e:
            logger.error(f"Fallback lock failed: {e}")
            return False

    def release_lock(self):
        """Release the lock"""
        try:
            if self.lock_file:
                self.lock_file.close()

            if self.is_locked and self.lock_path.exists():
                self.lock_path.unlink()
                logger.info(f"Lock released: {self.lock_path}")

        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
