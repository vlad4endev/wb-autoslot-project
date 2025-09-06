"""
Notification service for WB AutoSlot
Handles email, SMS, and Telegram notifications
"""

import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional
from src.models.user import User, Task, Event

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self, app=None):
        self.app = app
        self.email_enabled = False
        self.telegram_enabled = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize notification service with app context"""
        self.app = app
        self.email_enabled = app.config.get('NOTIFICATIONS_ENABLED', False) and app.config.get('EMAIL_SMTP_SERVER')
        self.telegram_enabled = app.config.get('NOTIFICATIONS_ENABLED', False) and app.config.get('TELEGRAM_BOT_TOKEN')
        
        logger.info(f"Notification service initialized - Email: {self.email_enabled}, Telegram: {self.telegram_enabled}")
    
    async def send_slot_found_notification(self, user: User, task: Task, slots: List[Dict]):
        """Send notification when slots are found"""
        try:
            message = f"🎉 Найдены слоты для задачи '{task.name}'\n\n"
            message += f"📅 Период: {task.date_from.strftime('%d.%m.%Y')} - {task.date_to.strftime('%d.%m.%Y')}\n"
            message += f"🏢 Склад: {task.warehouse}\n"
            message += f"📦 Упаковка: {task.packaging}\n"
            message += f"📊 Найдено слотов: {len(slots)}\n\n"
            
            for i, slot in enumerate(slots[:5], 1):  # Show first 5 slots
                slot_date = datetime.fromisoformat(slot['date']).strftime('%d.%m.%Y')
                message += f"{i}. {slot_date} - Коэффициент: {slot['coefficient']}\n"
            
            if len(slots) > 5:
                message += f"... и еще {len(slots) - 5} слотов\n"
            
            # Send notifications
            await self._send_notifications(user, "Слоты найдены", message, task)
            
        except Exception as e:
            logger.error(f"Error sending slot found notification: {e}")
    
    async def send_task_completed_notification(self, user: User, task: Task):
        """Send notification when task is completed"""
        try:
            message = f"✅ Задача '{task.name}' завершена\n\n"
            message += f"📅 Период: {task.date_from.strftime('%d.%m.%Y')} - {task.date_to.strftime('%d.%m.%Y')}\n"
            message += f"🏢 Склад: {task.warehouse}\n"
            message += f"📊 Найдено слотов: {task.found_slots}\n"
            message += f"⏰ Время завершения: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            
            await self._send_notifications(user, "Задача завершена", message, task)
            
        except Exception as e:
            logger.error(f"Error sending task completed notification: {e}")
    
    async def send_task_error_notification(self, user: User, task: Task, error_message: str):
        """Send notification when task encounters an error"""
        try:
            message = f"❌ Ошибка в задаче '{task.name}'\n\n"
            message += f"📅 Период: {task.date_from.strftime('%d.%m.%Y')} - {task.date_to.strftime('%d.%m.%Y')}\n"
            message += f"🏢 Склад: {task.warehouse}\n"
            message += f"⚠️ Ошибка: {error_message}\n"
            message += f"⏰ Время ошибки: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            
            await self._send_notifications(user, "Ошибка в задаче", message, task)
            
        except Exception as e:
            logger.error(f"Error sending task error notification: {e}")
    
    async def _send_notifications(self, user: User, subject: str, message: str, task: Task):
        """Send notifications via all enabled channels"""
        if self.email_enabled:
            await self._send_email(user, subject, message)
        
        if self.telegram_enabled:
            await self._send_telegram(subject, message)
    
    async def _send_email(self, user: User, subject: str, message: str):
        """Send email notification"""
        try:
            if not self.email_enabled:
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.app.config['EMAIL_FROM']
            msg['To'] = user.phone  # Using phone as email for now
            msg['Subject'] = f"WB AutoSlot - {subject}"
            
            # Create HTML message
            html_message = f"""
            <html>
            <body>
                <h2>WB AutoSlot</h2>
                <h3>{subject}</h3>
                <pre style="font-family: Arial, sans-serif; white-space: pre-wrap;">{message}</pre>
                <hr>
                <p><small>Это автоматическое уведомление от системы WB AutoSlot</small></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_message, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.app.config['EMAIL_SMTP_SERVER'], self.app.config['EMAIL_SMTP_PORT'])
            server.starttls()
            server.login(self.app.config['EMAIL_USERNAME'], self.app.config['EMAIL_PASSWORD'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent to {user.phone}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def _send_telegram(self, subject: str, message: str):
        """Send Telegram notification"""
        try:
            if not self.telegram_enabled:
                return
            
            bot_token = self.app.config['TELEGRAM_BOT_TOKEN']
            chat_id = self.app.config['TELEGRAM_CHAT_ID']
            
            full_message = f"*{subject}*\n\n{message}"
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': full_message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Telegram notification sent to chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
    
    def send_test_notification(self, user: User):
        """Send test notification to verify setup"""
        try:
            message = "🧪 Это тестовое уведомление от WB AutoSlot\n\n"
            message += f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            message += f"👤 Пользователь: {user.phone}\n"
            message += "✅ Уведомления работают корректно!"
            
            # Send via all channels
            if self.email_enabled:
                self._send_email(user, "Тестовое уведомление", message)
            
            if self.telegram_enabled:
                self._send_telegram("Тестовое уведомление", message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return False

# Global notification service instance
notification_service = NotificationService()
