from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Task, Event, WBAccount
from src.services.slot_search import slot_search_service
from src.services.task_worker import task_worker
from src.middleware.rate_limiter import rate_limit, rate_limit_by_endpoint
from datetime import datetime, date
import json
import asyncio

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get user's tasks"""
    try:
        current_user_id = get_jwt_identity()
        # Convert to int since we store as string but need int for query
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        tasks = [task.to_dict() for task in user.tasks]
        
        return jsonify({
            'tasks': tasks,
            'count': len(tasks)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get tasks'}), 500

@tasks_bp.route('/tasks', methods=['POST'])
@jwt_required()
@rate_limit_by_endpoint(max_requests=10, window_seconds=60)  # 10 task creations per minute
def create_task():
    """Create a new task"""
    try:
        current_user_id = get_jwt_identity()
        # Convert to int since we store as string but need int for query
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validation
        required_fields = ['name', 'warehouse', 'date_from', 'date_to', 'coefficient', 'packaging']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse dates
        try:
            date_from = datetime.strptime(data['date_from'], '%Y-%m-%d').date()
            date_to = datetime.strptime(data['date_to'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if date_from > date_to:
            return jsonify({'error': 'Start date cannot be after end date'}), 400
        
        if date_from < date.today():
            return jsonify({'error': 'Start date cannot be in the past'}), 400
        
        # Validate coefficient
        try:
            coefficient = float(data['coefficient'])
            if coefficient <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({'error': 'Coefficient must be a positive number'}), 400
        
        # Validate WB account if provided
        wb_account_id = data.get('wb_account_id')
        if wb_account_id:
            wb_account = WBAccount.query.filter_by(
                id=wb_account_id,
                user_id=int(current_user_id),
                is_active=True
            ).first()
            if not wb_account:
                return jsonify({'error': 'Invalid or inactive WB account'}), 400
        
        # Create new task
        new_task = Task(
            user_id=int(current_user_id),
            wb_account_id=wb_account_id,
            name=data['name'].strip(),
            warehouse=data['warehouse'].strip(),
            date_from=date_from,
            date_to=date_to,
            coefficient=coefficient,
            packaging=data['packaging'].strip(),
            shipment_number=data.get('shipment_number', '').strip() or None,
            auto_book=bool(data.get('auto_book', False))
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        # Create event
        event = Event(
            user_id=int(current_user_id),
            task_id=new_task.id,
            event_type='task_created',
            message=f'Task "{new_task.name}" created successfully'
        )
        db.session.add(event)
        db.session.commit()
        
        # Add task to worker for periodic execution
        try:
            task_worker.add_task(new_task.id, interval_minutes=30)
            print(f"Task {new_task.id} added to worker")
        except Exception as e:
            print(f"Failed to add task to worker: {e}")
        
        # Start slot search immediately
        try:
            import threading
            def start_search():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(slot_search_service.start_slot_search(new_task.id))
                loop.close()
            
            search_thread = threading.Thread(target=start_search)
            search_thread.daemon = True
            search_thread.start()
        except Exception as e:
            # Log error but don't fail task creation
            print(f"Failed to start slot search: {e}")
        
        return jsonify({
            'message': 'Task created successfully and slot search started',
            'task': new_task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create task'}), 500

@tasks_bp.route('/tasks/<int:task_id>/<action>', methods=['POST'])
@jwt_required()
def task_action(task_id, action):
    """Perform action on task (start, pause, stop)"""
    try:
        current_user_id = get_jwt_identity()
        
        task = Task.query.filter_by(
            id=task_id,
            user_id=int(current_user_id)
        ).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        if action == 'start':
            if task.status in ['paused', 'error']:
                # Update task status
                task.status = 'active'
                db.session.commit()
                
                # Add to worker
                try:
                    task_worker.add_task(task_id, interval_minutes=30)
                    
                    # Start immediate search
                    import threading
                    def start_search():
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(slot_search_service.start_slot_search(task_id))
                        loop.close()
                    
                    search_thread = threading.Thread(target=start_search)
                    search_thread.daemon = True
                    search_thread.start()
                    
                    return jsonify({'message': 'Task started successfully'}), 200
                except Exception as e:
                    return jsonify({'error': f'Failed to start task: {str(e)}'}), 500
            else:
                return jsonify({'error': 'Task is already active'}), 400
                
        elif action == 'pause':
            if task.status == 'active':
                # Update task status
                task.status = 'paused'
                db.session.commit()
                
                # Remove from worker
                task_worker.remove_task(task_id)
                
                return jsonify({'message': 'Task paused successfully'}), 200
            else:
                return jsonify({'error': 'Task is not active'}), 400
                
        elif action == 'stop':
            # Update task status
            task.status = 'completed'
            db.session.commit()
            
            # Remove from worker
            task_worker.remove_task(task_id)
            
            return jsonify({'message': 'Task stopped successfully'}), 200
        else:
            return jsonify({'error': 'Invalid action'}), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to perform task action'}), 500

@tasks_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update task"""
    try:
        current_user_id = get_jwt_identity()
        
        task = Task.query.filter_by(
            id=task_id,
            user_id=int(current_user_id)
        ).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update status
        if 'status' in data:
            new_status = data['status']
            if new_status in ['active', 'paused', 'completed', 'error']:
                old_status = task.status
                task.status = new_status
                task.updated_at = datetime.utcnow()
                
                # Create event for status change
                if old_status != new_status:
                    status_messages = {
                        'active': 'Задача запущена',
                        'paused': 'Задача остановлена',
                        'completed': 'Задача завершена',
                        'error': 'Задача остановлена из-за ошибки'
                    }
                    
                    event = Event(
                        task_id=task.id,
                        user_id=int(current_user_id),
                        event_type='info',
                        message=status_messages.get(new_status, f'Статус изменен на {new_status}')
                    )
                    db.session.add(event)
        
        # Update other fields if provided
        updatable_fields = ['name', 'warehouse', 'coefficient', 'packaging', 'shipment_number', 'auto_book']
        for field in updatable_fields:
            if field in data:
                setattr(task, field, data[field])
                task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update task'}), 500

@tasks_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete a task"""
    try:
        current_user_id = get_jwt_identity()
        
        task = Task.query.filter_by(
            id=task_id,
            user_id=int(current_user_id)
        ).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Remove from worker if active
        task_worker.remove_task(task_id)
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': 'Task deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete task'}), 500

@tasks_bp.route('/events', methods=['GET'])
@jwt_required()
def get_events():
    """Get user's events"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get recent events (last 100)
        events = Event.query.filter_by(user_id=int(current_user_id))\
                           .order_by(Event.created_at.desc())\
                           .limit(100)\
                           .all()
        
        events_data = [event.to_dict() for event in events]
        
        return jsonify({
            'events': events_data,
            'count': len(events_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get events'}), 500

@tasks_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get dashboard statistics"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate stats
        active_tasks = len([task for task in user.tasks if task.status == 'active'])
        found_slots = sum(task.found_slots for task in user.tasks)
        total_events = len(user.events)
        
        return jsonify({
            'activeTasks': active_tasks,
            'foundSlots': found_slots,
            'notifications': total_events,
            'totalTasks': len(user.tasks),
            'wbAccounts': len(user.wb_accounts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get stats'}), 500

