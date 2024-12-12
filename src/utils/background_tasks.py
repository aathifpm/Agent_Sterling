import asyncio
from datetime import datetime
import logging

# Get logger for this module
logger = logging.getLogger(__name__)

class BackgroundTasks:
    def __init__(self):
        self.is_running = False
        self.tasks = []

    async def start_task(self, task_func, *args, **kwargs):
        """Start a new background task."""
        if not self.is_running:
            self.is_running = True
            task = asyncio.create_task(self._run_task(task_func, *args, **kwargs))
            self.tasks.append(task)
            logger.info(f"Started background task: {task_func.__name__}")
            return task

    async def _run_task(self, task_func, *args, **kwargs):
        """Run a task and handle any errors."""
        try:
            while self.is_running:
                try:
                    await task_func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in background task {task_func.__name__}: {str(e)}")
                    await asyncio.sleep(60)  # Wait before retrying
        except asyncio.CancelledError:
            logger.info(f"Task {task_func.__name__} was cancelled")
            raise
        finally:
            self.is_running = False

    def stop_all_tasks(self):
        """Stop all running background tasks."""
        self.is_running = False
        for task in self.tasks:
            if not task.done():
                task.cancel()
        self.tasks.clear()
        logger.info("All background tasks stopped")

    @property
    def status(self):
        """Get the current status of background tasks."""
        return {
            "is_running": self.is_running,
            "active_tasks": len([t for t in self.tasks if not t.done()]),
            "total_tasks": len(self.tasks),
            "last_checked": str(datetime.now())
        }
