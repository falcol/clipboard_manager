# ===============================================
# FILE: src/utils/memory_optimizer.py
# Memory optimization and monitoring utilities
# ===============================================

"""
Memory optimization and monitoring for clipboard manager
"""
import gc
import logging
import tracemalloc
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("psutil not available - memory monitoring will be limited")


class MemoryOptimizer:
    """Runtime memory optimization and monitoring"""

    def __init__(self, enable_profiling: bool = True):
        self.enable_profiling = enable_profiling
        self._baseline_memory = 0
        self._memory_alerts: List[Dict] = []
        self._last_cleanup_time = 0

        # ✅ OPTIMIZATION: Enable memory tracing if requested
        if self.enable_profiling:
            try:
                tracemalloc.start(10)  # Keep 10 frames for debugging
                logger.info("Memory profiling enabled")
            except Exception as e:
                logger.warning(f"Failed to start memory tracing: {e}")

        # ✅ OPTIMIZATION: Tune garbage collection for better performance
        self._setup_gc_optimization()

    def _setup_gc_optimization(self):
        """Setup optimized garbage collection settings"""
        try:
            # More aggressive GC tuning for memory-constrained environments
            gc.set_threshold(500, 8, 8)  # Reduced from default (700, 10, 10)

            # Enable automatic garbage collection
            gc.enable()

            logger.info("Garbage collection optimized for memory efficiency")
        except Exception as e:
            logger.error(f"Failed to optimize GC settings: {e}")

    def monitor_memory_usage(self) -> Dict:
        """Monitor current memory usage with detailed statistics"""
        try:
            stats = {"gc_objects": len(gc.get_objects())}

            # ✅ OPTIMIZATION: Use psutil if available for accurate memory stats
            if HAS_PSUTIL:
                process = psutil.Process()
                memory_info = process.memory_info()

                stats["rss_mb"] = memory_info.rss / 1024 / 1024
                stats["vms_mb"] = memory_info.vms / 1024 / 1024
                stats["percent"] = int(process.memory_percent())
                stats["available_mb"] = int(psutil.virtual_memory().available / 1024 / 1024)

                # ✅ OPTIMIZATION: Trigger cleanup if memory usage is high
                if stats["rss_mb"] > 80:  # 80MB threshold for clipboard manager
                    self._schedule_memory_cleanup(stats["rss_mb"])

            # Add tracemalloc stats if available
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                stats["traced_current_mb"] = int(current / 1024 / 1024)
                stats["traced_peak_mb"] = int(peak / 1024 / 1024)

            return stats

        except Exception as e:
            logger.error(f"Memory monitoring error: {e}")
            return {"error": str(e)}

    def _schedule_memory_cleanup(self, current_mb: float):
        """Schedule memory cleanup if needed"""
        import time
        current_time = time.time()

        # ✅ OPTIMIZATION: Rate limit cleanup to avoid performance impact
        if current_time - self._last_cleanup_time > 30:  # 30 seconds minimum between cleanups
            self._last_cleanup_time = current_time
            self.trigger_memory_cleanup()

            # Log memory alert
            alert = {
                "timestamp": current_time,
                "memory_mb": current_mb,
                "action": "cleanup_triggered"
            }
            self._memory_alerts.append(alert)

            # Keep only last 10 alerts
            self._memory_alerts = self._memory_alerts[-10:]

    def trigger_memory_cleanup(self, force: bool = False) -> Dict:
        """Trigger comprehensive memory cleanup"""
        try:
            cleanup_stats = {"collected": 0, "freed_mb": 0}

            # ✅ OPTIMIZATION: Get memory before cleanup
            memory_before = 0
            if HAS_PSUTIL:
                memory_before = psutil.Process().memory_info().rss

            # ✅ OPTIMIZATION: Force garbage collection with multiple passes
            for generation in range(3):
                collected = gc.collect(generation)
                cleanup_stats["collected"] += collected

            # ✅ OPTIMIZATION: Calculate freed memory
            if HAS_PSUTIL:
                memory_after = psutil.Process().memory_info().rss
                cleanup_stats["freed_mb"] = (memory_before - memory_after) / 1024 / 1024

            logger.info(f"Memory cleanup completed: {cleanup_stats}")
            return cleanup_stats

        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
            return {"error": str(e)}

    def trigger_content_manager_cleanup(self, content_manager):
        """Trigger cleanup on ContentManager"""
        try:
            if hasattr(content_manager, '_cleanup_cache_optimized'):
                content_manager._cleanup_cache_optimized()

            # Get cache stats after cleanup
            if hasattr(content_manager, 'get_cache_stats'):
                cache_stats = content_manager.get_cache_stats()
                logger.info(f"Content manager cache cleaned: {cache_stats}")

        except Exception as e:
            logger.error(f"Error cleaning content manager cache: {e}")

    def trigger_database_cleanup(self, database):
        """Trigger database optimization"""
        try:
            # ✅ OPTIMIZATION: Database vacuum and analyze
            if hasattr(database, 'connection') and database.connection:
                cursor = database.connection.cursor()

                # VACUUM to reclaim space (only if database not too large)
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]

                if db_size < 50 * 1024 * 1024:  # Only vacuum if < 50MB
                    cursor.execute("VACUUM")
                    logger.info("Database vacuumed")

                # ANALYZE to update statistics
                cursor.execute("ANALYZE")
                logger.info("Database analyzed")

        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")

    def get_memory_report(self) -> Dict:
        """Get comprehensive memory usage report"""
        try:
            report = {
                "current_usage": self.monitor_memory_usage(),
                "gc_stats": {
                    "counts": gc.get_count(),
                    "threshold": gc.get_threshold(),
                    "objects": len(gc.get_objects())
                },
                "recent_alerts": self._memory_alerts[-5:],  # Last 5 alerts
            }

            # Add tracemalloc top stats if available
            if tracemalloc.is_tracing():
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')[:10]  # Top 10 memory consumers

                report["top_memory_consumers"] = [
                    {
                        "file": stat.traceback.format()[0],
                        "size_mb": stat.size / 1024 / 1024,
                        "count": stat.count
                    }
                    for stat in top_stats
                ]

            return report

        except Exception as e:
            logger.error(f"Error generating memory report: {e}")
            return {"error": str(e)}

    def optimize_for_low_memory(self) -> bool:
        """Apply aggressive optimizations for low-memory environments"""
        try:
            logger.info("Applying low-memory optimizations...")

            # ✅ OPTIMIZATION: More aggressive GC
            gc.set_threshold(300, 5, 5)  # Very aggressive

            # ✅ OPTIMIZATION: Force immediate cleanup
            collected = sum(gc.collect(i) for i in range(3))

            # ✅ OPTIMIZATION: Disable memory tracing to save memory
            if tracemalloc.is_tracing():
                tracemalloc.stop()
                logger.info("Memory tracing disabled to save memory")

            logger.info(f"Low-memory optimization complete: collected {collected} objects")
            return True

        except Exception as e:
            logger.error(f"Error applying low-memory optimizations: {e}")
            return False

    def __del__(self):
        """Cleanup when optimizer is destroyed"""
        try:
            if tracemalloc.is_tracing():
                tracemalloc.stop()
        except Exception:
            pass


# Global memory optimizer instance
_memory_optimizer: Optional[MemoryOptimizer] = None


def get_memory_optimizer(enable_profiling: bool = True) -> MemoryOptimizer:
    """Get global memory optimizer instance"""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer(enable_profiling)
    return _memory_optimizer


def cleanup_memory(force: bool = False) -> Dict[str, int]:
    """Convenience function for memory cleanup"""
    optimizer = get_memory_optimizer()
    return optimizer.trigger_memory_cleanup(force)


def get_memory_stats() -> Dict:
    """Convenience function for memory statistics"""
    optimizer = get_memory_optimizer()
    return optimizer.monitor_memory_usage()
