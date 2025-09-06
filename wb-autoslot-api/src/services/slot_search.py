"""
Slot search service for WB AutoSlot
Handles slot searching and booking functionality
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.models.user import db, Task, Event, User
from src.services.wb_service import wb_service
from src.services.notification_service import notification_service
import json

logger = logging.getLogger(__name__)

class SlotSearchService:
    """Service for searching and managing WB slots"""
    
    def __init__(self):
        self.active_searches = {}
    
    async def start_slot_search(self, task_id: int) -> bool:
        """Start slot search for a task"""
        try:
            task = Task.query.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            # Update task status
            task.status = 'active'
            task.last_check = datetime.utcnow()
            db.session.commit()
            
            # Create start event
            event = Event(
                task_id=task.id,
                user_id=task.user_id,
                event_type='info',
                message=f'Поиск слотов запущен для задачи "{task.name}"'
            )
            db.session.add(event)
            db.session.commit()
            
            # Start background search (mock implementation)
            asyncio.create_task(self._search_slots_background(task_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start slot search for task {task_id}: {e}")
            return False
    
    async def _search_slots_background(self, task_id: int):
        """Background slot search process using real WB service"""
        try:
            task = Task.query.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            logger.info(f"Starting slot search for task {task_id}: {task.name}")
            
            # Use real WB service to search for slots
            found_slots = await wb_service.search_slots(task)
            
            # Update task with results
            task.found_slots = len(found_slots)
            task.last_check = datetime.utcnow()
            
            if found_slots:
                task.status = 'completed'
                event_type = 'success'
                message = f'Найдено {len(found_slots)} слотов для задачи "{task.name}"'
                
                # If auto-booking is enabled, try to book slots
                if task.auto_book and found_slots:
                    booked_count = 0
                    for slot in found_slots[:3]:  # Limit to 3 slots for auto-booking
                        try:
                            if await wb_service.book_slot(task, slot):
                                booked_count += 1
                        except Exception as booking_error:
                            logger.error(f"Failed to book slot {slot['id']}: {booking_error}")
                    
                    if booked_count > 0:
                        message += f'. Автоматически забронировано: {booked_count}'
                
                # Send notification for found slots
                try:
                    user = User.query.get(task.user_id)
                    if user:
                        await notification_service.send_slot_found_notification(user, task, found_slots)
                except Exception as notify_error:
                    logger.error(f"Failed to send slot found notification: {notify_error}")
            else:
                event_type = 'info'
                message = f'Слоты не найдены для задачи "{task.name}". Поиск завершен.'
                task.status = 'completed'  # Mark as completed even if no slots found
                
                # Send task completed notification
                try:
                    user = User.query.get(task.user_id)
                    if user:
                        await notification_service.send_task_completed_notification(user, task)
                except Exception as notify_error:
                    logger.error(f"Failed to send task completed notification: {notify_error}")
            
            # Create result event
            event = Event(
                task_id=task.id,
                user_id=task.user_id,
                event_type=event_type,
                message=message,
                details=json.dumps(found_slots) if found_slots else None
            )
            db.session.add(event)
            db.session.commit()
            
            logger.info(f"Slot search completed for task {task_id}: {len(found_slots)} slots found")
            
        except Exception as e:
            logger.error(f"Background slot search failed for task {task_id}: {e}")
            
            # Update task status to error
            try:
                task = Task.query.get(task_id)
                if task:
                    task.status = 'error'
                    task.last_check = datetime.utcnow()
                    
                    event = Event(
                        task_id=task.id,
                        user_id=task.user_id,
                        event_type='error',
                        message=f'Ошибка поиска слотов для задачи "{task.name}": {str(e)}'
                    )
                    db.session.add(event)
                    db.session.commit()
                    
                    # Send error notification
                    try:
                        user = User.query.get(task.user_id)
                        if user:
                            await notification_service.send_task_error_notification(user, task, str(e))
                    except Exception as notify_error:
                        logger.error(f"Failed to send error notification: {notify_error}")
            except Exception as commit_error:
                logger.error(f"Failed to update task status after error: {commit_error}")
    
    def _mock_slot_search(self, task: Task) -> List[Dict]:
        """Mock slot search implementation"""
        # Simulate slot search based on task parameters
        slots = []
        
        # Mock logic: higher coefficient = more likely to find slots
        if task.coefficient <= 1.0:
            slot_probability = 0.8
        elif task.coefficient <= 1.5:
            slot_probability = 0.6
        elif task.coefficient <= 2.0:
            slot_probability = 0.4
        else:
            slot_probability = 0.2
        
        # Generate mock slots
        import random
        if random.random() < slot_probability:
            num_slots = random.randint(1, 5)
            for i in range(num_slots):
                slot_date = task.date_from + timedelta(days=random.randint(0, (task.date_to - task.date_from).days))
                slots.append({
                    'id': f"slot_{task.id}_{i}",
                    'date': slot_date.isoformat(),
                    'warehouse': task.warehouse,
                    'coefficient': round(task.coefficient + random.uniform(0, 0.5), 2),
                    'packaging': task.packaging,
                    'available_boxes': random.randint(10, 100) if task.packaging == 'boxes' else random.randint(1, 10)
                })
        
        return slots
    
    def stop_slot_search(self, task_id: int) -> bool:
        """Stop slot search for a task"""
        try:
            task = Task.query.get(task_id)
            if not task:
                return False
            
            task.status = 'paused'
            task.last_check = datetime.utcnow()
            
            event = Event(
                task_id=task.id,
                user_id=task.user_id,
                event_type='info',
                message=f'Поиск слотов остановлен для задачи "{task.name}"'
            )
            db.session.add(event)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop slot search for task {task_id}: {e}")
            return False

# Global instance
slot_search_service = SlotSearchService()

