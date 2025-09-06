from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    wb_accounts = db.relationship('WBAccount', backref='user', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, phone, password, email=None):
        self.phone = self.normalize_phone(phone)
        self.email = self.normalize_email(email) if email else None
        self.password_hash = generate_password_hash(password)
    
    @staticmethod
    def normalize_phone(phone):
        """Normalize phone number to +7XXXXXXXXXX format"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]
        elif digits.startswith('7') and len(digits) == 11:
            pass
        elif len(digits) == 10:
            digits = '7' + digits
        else:
            raise ValueError('Invalid phone number format')
        
        return '+' + digits
    
    @staticmethod
    def normalize_email(email):
        """Normalize email address"""
        if not email:
            return None
        return email.strip().lower()
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'wb_accounts_count': len(self.wb_accounts),
            'tasks_count': len(self.tasks)
        }
    
    @staticmethod
    def find_by_phone(phone):
        """Find user by phone number"""
        try:
            normalized_phone = User.normalize_phone(phone)
            return User.query.filter_by(phone=normalized_phone).first()
        except ValueError:
            return None
    
    @staticmethod
    def find_by_email(email):
        """Find user by email address"""
        if not email:
            return None
        try:
            normalized_email = User.normalize_email(email)
            return User.query.filter_by(email=normalized_email).first()
        except Exception:
            return None
    
    @staticmethod
    def user_exists(phone=None, email=None):
        """Check if user exists by phone or email"""
        if phone:
            try:
                normalized_phone = User.normalize_phone(phone)
                if User.query.filter_by(phone=normalized_phone).first():
                    return True, 'phone'
            except ValueError:
                pass
        
        if email:
            try:
                normalized_email = User.normalize_email(email)
                if User.query.filter_by(email=normalized_email).first():
                    return True, 'email'
            except Exception:
                pass
        
        return False, None


class WBAccount(db.Model):
    __tablename__ = 'wb_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    cookies = db.Column(db.Text)  # Encrypted cookies storage
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_name': self.account_name,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    wb_account_id = db.Column(db.Integer, db.ForeignKey('wb_accounts.id'), nullable=True)
    
    name = db.Column(db.String(200), nullable=False)
    warehouse = db.Column(db.String(100), nullable=False)
    date_from = db.Column(db.Date, nullable=False)
    date_to = db.Column(db.Date, nullable=False)
    coefficient = db.Column(db.Float, nullable=False)
    packaging = db.Column(db.String(50), nullable=False)
    shipment_number = db.Column(db.String(50))  # Номер приемки/отгрузки
    auto_book = db.Column(db.Boolean, default=False)
    
    status = db.Column(db.String(20), default='active')  # active, paused, completed, error
    last_check = db.Column(db.DateTime)
    found_slots = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = db.relationship('Event', backref='task', lazy=True, cascade='all, delete-orphan')
    wb_account = db.relationship('WBAccount', backref='tasks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'warehouse': self.warehouse,
            'dateRange': f"{self.date_from.strftime('%d.%m.%Y')} - {self.date_to.strftime('%d.%m.%Y')}",
            'coefficient': self.coefficient,
            'packaging': self.packaging,
            'shipment_number': self.shipment_number,
            'auto_book': self.auto_book,
            'status': self.status,
            'lastCheck': self.last_check.strftime('%H:%M') if self.last_check else None,
            'found': self.found_slots > 0,
            'found_slots': self.found_slots,
            'created_at': self.created_at.isoformat(),
            'wb_account': self.wb_account.to_dict() if self.wb_account else None
        }


class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    event_type = db.Column(db.String(20), nullable=False)  # success, error, info, warning
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text)  # JSON details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='events')
    
    def to_dict(self):
        return {
            'id': self.id,
            'time': self.created_at.strftime('%H:%M'),
            'type': self.event_type,
            'message': self.message,
            'details': self.details,
            'created_at': self.created_at.isoformat(),
            'task_name': self.task.name if self.task else None
        }

