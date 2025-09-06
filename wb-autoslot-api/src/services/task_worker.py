"""
Task Worker Service for WB AutoSlot
Handles background task processing and scheduling
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Set
from src.models.user import db, Task, Event
from src.services.slot_search import slot_search_service
from src.services.wb_service import wb_service

logger = logging.getLogger(__name__)

class TaskWorker:
    """Background task worker for processing slot search tasks"""
    
    def __init__(self):
        self.running = False
        self.worker_thread = None
        self.active_tasks: Set[int] = set()
        self.task_intervals: Dict[int, int] = {}  # task_id -> interval in minutes
        self.last_run: Dict[int, datetime] = {}
        self.app = None
        
    def start(self):
        """Start the background worker"""
        if self.running:
            logger.warning("Task worker is already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Task worker started")
    
    def stop(self):
        """Stop the background worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Task worker stopped")
    
    def add_task(self, task_id: int, interval_minutes: int = 30):
        """Add a task to the worker queue"""
        self.active_tasks.add(task_id)
        self.task_intervals[task_id] = interval_minutes
        self.last_run[task_id] = datetime.utcnow() - timedelta(minutes=interval_minutes)
        logger.info(f"Added task {task_id} with interval {interval_minutes} minutes")
    
    def remove_task(self, task_id: int):
        """Remove a task from the worker queue"""
        self.active_tasks.discard(task_id)
        self.task_intervals.pop(task_id, None)
        self.last_run.pop(task_id, None)
        logger.info(f"Removed task {task_id} from worker")
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                # Process active tasks
                self._process_tasks()
                
                # Sleep for 1 minute before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(60)
    
    def _process_tasks(self):
        """Process all active tasks"""
        if not self.active_tasks:
            return
        
        current_time = datetime.utcnow()
        
        for task_id in list(self.active_tasks):
            try:
                # Check if task should run
                if self._should_run_task(task_id, current_time):
                    logger.info(f"Running task {task_id}")
                    
                    # Run task in a separate thread to avoid blocking
                    task_thread = threading.Thread(
                        target=self._run_task_async,
                        args=(task_id,),
                        daemon=True
                    )
                    task_thread.start()
                    
                    # Update last run time
                    self.last_run[task_id] = current_time
                    
            except Exception as e:
                logger.error(f"Error processing task {task_id}: {e}")
    
    def _should_run_task(self, task_id: int, current_time: datetime) -> bool:
        """Check if a task should run based on its interval"""
        if task_id not in self.active_tasks:
            return False
        
        if task_id not in self.last_run:
            return True
        
        interval_minutes = self.task_intervals.get(task_id, 30)
        last_run = self.last_run[task_id]
        
        return (current_time - last_run).total_seconds() >= interval_minutes * 60
    
    def _run_task_async(self, task_id: int):
        """Run a task asynchronously"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the task
            loop.run_until_complete(self._execute_task(task_id))
            
        except Exception as e:
            logger.error(f"Error running task {task_id}: {e}")
        finally:
            try:
                loop.close()
            except:
                pass
    
    async def _execute_task(self, task_id: int):
        """Execute a specific task"""
        try:
            # Get task from database
            with self.app.app_context():
                task = Task.query.get(task_id)
                if not task:
                    logger.error(f"Task {task_id} not found")
                    self.remove_task(task_id)
                    return
                
                # Check if task is still active
                if task.status != 'active':
                    logger.info(f"Task {task_id} is not active, removing from worker")
                    self.remove_task(task_id)
                    return
                
                # Check if task has WB account
                if not task.wb_account:
                    logger.warning(f"Task {task_id} has no WB account assigned")
                    return
                
                # Run slot search
                await slot_search_service._search_slots_background(task_id)
                
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
    
    def get_status(self) -> Dict:
        """Get worker status"""
        return {
            'running': self.running,
            'active_tasks': len(self.active_tasks),
            'task_list': list(self.active_tasks),
            'intervals': self.task_intervals.copy(),
            'last_runs': {str(k): v.isoformat() for k, v in self.last_run.items()}
        }
    
    def cleanup_old_tasks(self):
        """Clean up completed or error tasks"""
        try:
            with self.app.app_context():
                # Get all tasks that are not active
                inactive_tasks = Task.query.filter(
                    Task.status.in_(['completed', 'error', 'paused'])
                ).all()
                
                for task in inactive_tasks:
                    if task.id in self.active_tasks:
                        self.remove_task(task.id)
                        logger.info(f"Cleaned up inactive task {task.id}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up tasks: {e}")

# Global worker instance
task_worker = TaskWorker()