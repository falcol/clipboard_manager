# clipboard_manager/src/utils/memory_manager.py
"""
Memory management utilities for RAM optimization
"""
import gc
import logging
import os
from typing import Dict

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - memory monitoring disabled")

logger = logging.getLogger(__name__)


class MemoryManager:
    """Centralized memory management for the application"""

    def __init__(self):
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process(os.getpid())
        else:
            self.process = None
        self.memory_threshold_mb = 80
        self.last_cleanup_time = 0
        self.cleanup_interval = 30

    def get_memory_usage(self) -> Dict:
        if not PSUTIL_AVAILABLE:
            return {
                "memory_mb": 0,
                "memory_bytes": 0,
                "virtual_memory_mb": 0,
                "memory_percent": 0,
                "threshold_mb": self.memory_threshold_mb,
                "error": "psutil not available",
            }
        """Get current memory usage statistics"""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            return {
                "memory_mb": round(memory_mb, 2),
                "memory_bytes": memory_info.rss,
                "virtual_memory_mb": round(memory_info.vms / 1024 / 1024, 2),
                "memory_percent": self.process.memory_percent(),
                "threshold_mb": self.memory_threshold_mb,
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {"memory_mb": 0, "error": str(e)}

    def should_cleanup(self) -> bool:
        """Check if memory cleanup is needed"""
        try:
            import time

            current_time = time.time()

            # Check time interval
            if current_time - self.last_cleanup_time < self.cleanup_interval:
                return False

            # Check memory threshold
            memory_usage = self.get_memory_usage()
            return memory_usage.get("memory_mb", 0) > self.memory_threshold_mb

        except Exception as e:
            logger.error(f"Error checking cleanup condition: {e}")
            return False

    def force_garbage_collection(self):
        """Force Python garbage collection"""
        try:
            collected = gc.collect()
            logger.info(f"Garbage collection freed {collected} objects")
            return collected
        except Exception as e:
            logger.error(f"Error in garbage collection: {e}")
            return 0

    def cleanup_memory(self, content_manager=None, qss_loader=None):
        """Perform comprehensive memory cleanup"""
        try:
            import time

            self.last_cleanup_time = time.time()

            logger.info("Starting memory cleanup...")

            # 1. Force garbage collection
            collected = self.force_garbage_collection()

            # 2. Clear content manager cache if provided
            if content_manager and hasattr(content_manager, "clear_cache"):
                content_manager.clear_cache()
                logger.info("Cleared content manager cache")

            # 3. Clear QSS cache if provided
            if qss_loader and hasattr(qss_loader, "clear_cache"):
                qss_loader.clear_cache()
                logger.info("Cleared QSS cache")

            # 4. Get final memory usage
            final_usage = self.get_memory_usage()

            logger.info(
                f"Memory cleanup completed. "
                f"Freed {collected} objects. "
                f"Current RAM: {final_usage.get('memory_mb', 0):.1f}MB"
            )

            return {
                "objects_freed": collected,
                "final_memory_mb": final_usage.get("memory_mb", 0),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in memory cleanup: {e}")
            return {"success": False, "error": str(e)}

    def get_memory_recommendations(self) -> list:
        """Get memory optimization recommendations"""
        memory_usage = self.get_memory_usage()
        memory_mb = memory_usage.get("memory_mb", 0)

        recommendations = []

        if memory_mb > 100:
            recommendations.append(
                "High memory usage detected. Consider reducing cache sizes."
            )
        if memory_mb > 80:
            recommendations.append(
                "Memory usage is elevated. Enable automatic cleanup."
            )
        if memory_mb > 60:
            recommendations.append("Consider using lazy loading for images.")

        return recommendations

    def set_memory_threshold(self, threshold_mb: int):
        """Set memory threshold for automatic cleanup"""
        self.memory_threshold_mb = max(
            50, min(threshold_mb, 200)
        )  # Clamp between 50-200MB
        logger.info(f"Memory threshold set to {self.memory_threshold_mb}MB")

    def get_system_memory_info(self) -> Dict:
        """Get system-wide memory information"""
        try:
            memory = psutil.virtual_memory()
            return {
                "total_mb": round(memory.total / 1024 / 1024, 2),
                "available_mb": round(memory.available / 1024 / 1024, 2),
                "used_mb": round(memory.used / 1024 / 1024, 2),
                "percent_used": memory.percent,
                "app_memory_mb": self.get_memory_usage().get("memory_mb", 0),
            }
        except Exception as e:
            logger.error(f"Error getting system memory info: {e}")
            return {"error": str(e)}


# Global memory manager instance
memory_manager = MemoryManager()
