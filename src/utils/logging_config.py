# ===============================================
# FILE: src/utils/logging_config.py
# Enhanced logging configuration with file paths and line numbers
# ===============================================

"""
Enhanced logging configuration with file paths and line numbers
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .config import Config


class EnhancedLogFormatter(logging.Formatter):
    """Enhanced formatter with file path and line number.

    Color output is optional to keep file logs clean on all platforms.
    """

    def __init__(
        self,
        include_path: bool = True,
        include_line: bool = True,
        colorize: bool = True,
    ):
        super().__init__()
        self.include_path = include_path
        self.include_line = include_line
        self.colorize = colorize

    def format(self, record):
        # Add file path and line number to record
        if self.include_path and hasattr(record, "pathname"):
            # Get relative path from project root
            try:
                project_root = Path(__file__).parent.parent.parent
                rel_path = Path(record.pathname).relative_to(project_root)
                filepath = str(rel_path)
            except ValueError:
                filepath = record.pathname
        else:
            filepath = record.filename

        if self.include_line:
            location = f"{filepath}:{record.lineno}"
        else:
            location = filepath

        # Enhanced format with optional colors and structure
        if self.colorize:
            if record.levelno >= logging.ERROR:
                color = "\033[91m"  # Red for errors
            elif record.levelno >= logging.WARNING:
                color = "\033[93m"  # Yellow for warnings
            elif record.levelno >= logging.INFO:
                color = "\033[94m"  # Blue for info
            else:
                color = "\033[90m"  # Gray for debug
            reset = "\033[0m"
            level_part = f"{color}[{record.levelname:3}]{reset} "
        else:
            level_part = f"[{record.levelname:3}] "

        # Format: [LEVEL] [TIME] [FILE:LINE] MESSAGE
        formatted = level_part
        formatted += f"[{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}] "
        formatted += f"[{location}] "
        formatted += f"{record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


class EnhancedLoggingConfig:
    """Enhanced logging configuration manager"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.log_dir = self._get_log_directory()
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_directory(self) -> Path:
        """Get log directory path"""
        if self.config:
            config_dir = self.config.config_path.parent
            return config_dir / "logs"
        else:
            # Fallback to default location
            return Path.home() / ".config" / "B1Clip" / "logs"

    def setup_logging(
        self,
        level: str = "INFO",
        log_to_file: bool = True,
        log_to_console: bool = True,
        max_file_size: int = 5 * 1024 * 1024,  # 5MB
        backup_count: int = 3,
    ):
        """Setup enhanced logging configuration"""

        # Convert string level to logging level
        log_level = getattr(logging, level.upper(), logging.INFO)

        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Create formatters
        detailed_formatter = EnhancedLogFormatter(
            include_path=True, include_line=True, colorize=True
        )
        # File formatter should avoid ANSI color codes for better log readability
        file_formatter = EnhancedLogFormatter(
            include_path=True, include_line=True, colorize=False
        )

        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(console_handler)

        # File handlers
        if log_to_file:
            # Main log file with rotation
            main_log_file = self.log_dir / "clipboard_manager.log"
            file_handler = logging.handlers.RotatingFileHandler(
                main_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

            # Error log file (only errors and critical)
            error_log_file = self.log_dir / "errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            root_logger.addHandler(error_handler)

            # Debug log file (if debug level)
            if log_level <= logging.DEBUG:
                debug_log_file = self.log_dir / "debug.log"
                debug_handler = logging.handlers.RotatingFileHandler(
                    debug_log_file,
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
                debug_handler.setLevel(logging.DEBUG)
                debug_handler.setFormatter(file_formatter)
                root_logger.addHandler(debug_handler)

        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info("Enhanced logging system initialized")
        logger.info(f"Log directory: {self.log_dir}")
        logger.info(f"Log level: {level}")
        logger.info(f"File logging: {log_to_file}")
        logger.info(f"Console logging: {log_to_console}")

    def get_logger(self, name: str) -> logging.Logger:
        """Get logger with enhanced configuration"""
        return logging.getLogger(name)

    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files"""
        import time

        current_time = time.time()
        cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)

        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    logging.getLogger(__name__).info(
                        f"Cleaned up old log file: {log_file}"
                    )
                except Exception as e:
                    logging.getLogger(__name__).error(
                        f"Failed to clean up {log_file}: {e}"
                    )


# Global logging config instance
_logging_config = None


def get_logging_config() -> EnhancedLoggingConfig:
    """Get global logging configuration instance"""
    global _logging_config
    if _logging_config is None:
        _logging_config = EnhancedLoggingConfig()
    return _logging_config


def setup_logging(level: str = "INFO", **kwargs):
    """Setup enhanced logging (convenience function)"""
    config = get_logging_config()
    config.setup_logging(level=level, **kwargs)


def get_logger(name: str) -> logging.Logger:
    """Get logger with enhanced configuration (convenience function)"""
    config = get_logging_config()
    return config.get_logger(name)
