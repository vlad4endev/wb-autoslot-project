"""
API Documentation routes using Flask-RESTX
"""

from flask import Blueprint
from flask_restx import Api, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User

api_docs_bp = Blueprint('api_docs', __name__)

# Create API instance
api = Api(
    api_docs_bp,
    version='2.0.0',
    title='WB AutoSlot API',
    description='API для автоматического поиска слотов Wildberries',
    doc='/',  # Swagger UI will be available at /api/docs/
    prefix='/api/docs'
)

# Namespaces
auth_ns = api.namespace('auth', description='Аутентификация и авторизация')
tasks_ns = api.namespace('tasks', description='Управление задачами')
wb_accounts_ns = api.namespace('wb-accounts', description='Управление аккаунтами WB')
worker_ns = api.namespace('worker', description='Управление воркером')
notifications_ns = api.namespace('notifications', description='Уведомления')
health_ns = api.namespace('health', description='Мониторинг здоровья системы')

# Models for request/response documentation
user_model = api.model('User', {
    'id': fields.Integer(description='ID пользователя'),
    'phone': fields.String(description='Номер телефона'),
    'email': fields.String(description='Email адрес'),
    'created_at': fields.DateTime(description='Дата создания'),
    'is_active': fields.Boolean(description='Активен ли пользователь'),
    'wb_accounts_count': fields.Integer(description='Количество WB аккаунтов'),
    'tasks_count': fields.Integer(description='Количество задач')
})

login_model = api.model('Login', {
    'phone': fields.String(required=True, description='Номер телефона'),
    'email': fields.String(description='Email адрес (альтернатива телефону)'),
    'password': fields.String(required=True, description='Пароль')
})

register_model = api.model('Register', {
    'phone': fields.String(required=True, description='Номер телефона'),
    'email': fields.String(description='Email адрес'),
    'password': fields.String(required=True, description='Пароль (минимум 6 символов)')
})

task_model = api.model('Task', {
    'id': fields.Integer(description='ID задачи'),
    'name': fields.String(description='Название задачи'),
    'warehouse': fields.String(description='Склад'),
    'dateRange': fields.String(description='Период поиска'),
    'coefficient': fields.Float(description='Минимальный коэффициент'),
    'packaging': fields.String(description='Тип упаковки'),
    'shipment_number': fields.String(description='Номер приемки/отгрузки'),
    'auto_book': fields.Boolean(description='Автоматическое бронирование'),
    'status': fields.String(description='Статус задачи'),
    'lastCheck': fields.String(description='Время последней проверки'),
    'found': fields.Boolean(description='Найдены ли слоты'),
    'found_slots': fields.Integer(description='Количество найденных слотов'),
    'created_at': fields.DateTime(description='Дата создания'),
    'wb_account': fields.Raw(description='WB аккаунт')
})

create_task_model = api.model('CreateTask', {
    'name': fields.String(required=True, description='Название задачи'),
    'warehouse': fields.String(required=True, description='Склад'),
    'date_from': fields.String(required=True, description='Дата начала (YYYY-MM-DD)'),
    'date_to': fields.String(required=True, description='Дата окончания (YYYY-MM-DD)'),
    'coefficient': fields.Float(required=True, description='Минимальный коэффициент'),
    'packaging': fields.String(required=True, description='Тип упаковки'),
    'shipment_number': fields.String(description='Номер приемки/отгрузки'),
    'auto_book': fields.Boolean(description='Автоматическое бронирование'),
    'wb_account_id': fields.Integer(description='ID WB аккаунта')
})

wb_account_model = api.model('WBAccount', {
    'id': fields.Integer(description='ID аккаунта'),
    'account_name': fields.String(description='Название аккаунта'),
    'is_active': fields.Boolean(description='Активен ли аккаунт'),
    'last_login': fields.DateTime(description='Последний вход'),
    'created_at': fields.DateTime(description='Дата создания')
})

create_wb_account_model = api.model('CreateWBAccount', {
    'account_name': fields.String(required=True, description='Название аккаунта'),
    'cookies': fields.String(description='Cookies для авторизации')
})

event_model = api.model('Event', {
    'id': fields.Integer(description='ID события'),
    'time': fields.String(description='Время события'),
    'type': fields.String(description='Тип события'),
    'message': fields.String(description='Сообщение'),
    'details': fields.String(description='Детали'),
    'created_at': fields.DateTime(description='Дата создания'),
    'task_name': fields.String(description='Название задачи')
})

health_model = api.model('Health', {
    'status': fields.String(description='Статус системы'),
    'timestamp': fields.DateTime(description='Время проверки'),
    'version': fields.String(description='Версия API'),
    'uptime': fields.Float(description='Время работы в секундах'),
    'components': fields.Raw(description='Статус компонентов')
})

# Auth endpoints documentation
@auth_ns.route('/register')
class Register(Resource):
    @api.expect(register_model)
    @api.marshal_with(user_model)
    @api.doc('register_user', description='Регистрация нового пользователя')
    def post(self):
        """Регистрация нового пользователя"""
        pass

@auth_ns.route('/login')
class Login(Resource):
    @api.expect(login_model)
    @api.doc('login_user', description='Вход пользователя в систему')
    def post(self):
        """Вход пользователя в систему"""
        pass

@auth_ns.route('/me')
class Me(Resource):
    @jwt_required()
    @api.marshal_with(user_model)
    @api.doc('get_current_user', description='Получение информации о текущем пользователе')
    def get(self):
        """Получение информации о текущем пользователе"""
        pass

# Tasks endpoints documentation
@tasks_ns.route('/')
class TaskList(Resource):
    @jwt_required()
    @api.doc('get_tasks', description='Получение списка задач')
    def get(self):
        """Получение списка задач пользователя"""
        pass

    @jwt_required()
    @api.expect(create_task_model)
    @api.marshal_with(task_model)
    @api.doc('create_task', description='Создание новой задачи')
    def post(self):
        """Создание новой задачи"""
        pass

@tasks_ns.route('/<int:task_id>')
class Task(Resource):
    @jwt_required()
    @api.marshal_with(task_model)
    @api.doc('get_task', description='Получение задачи по ID')
    def get(self, task_id):
        """Получение задачи по ID"""
        pass

    @jwt_required()
    @api.expect(create_task_model)
    @api.marshal_with(task_model)
    @api.doc('update_task', description='Обновление задачи')
    def put(self, task_id):
        """Обновление задачи"""
        pass

    @jwt_required()
    @api.doc('delete_task', description='Удаление задачи')
    def delete(self, task_id):
        """Удаление задачи"""
        pass

@tasks_ns.route('/<int:task_id>/start')
class TaskStart(Resource):
    @jwt_required()
    @api.doc('start_task', description='Запуск задачи')
    def post(self, task_id):
        """Запуск задачи"""
        pass

@tasks_ns.route('/<int:task_id>/pause')
class TaskPause(Resource):
    @jwt_required()
    @api.doc('pause_task', description='Приостановка задачи')
    def post(self, task_id):
        """Приостановка задачи"""
        pass

# WB Accounts endpoints documentation
@wb_accounts_ns.route('/')
class WBAccountList(Resource):
    @jwt_required()
    @api.doc('get_wb_accounts', description='Получение списка WB аккаунтов')
    def get(self):
        """Получение списка WB аккаунтов пользователя"""
        pass

    @jwt_required()
    @api.expect(create_wb_account_model)
    @api.marshal_with(wb_account_model)
    @api.doc('create_wb_account', description='Создание нового WB аккаунта')
    def post(self):
        """Создание нового WB аккаунта"""
        pass

@wb_accounts_ns.route('/<int:account_id>')
class WBAccount(Resource):
    @jwt_required()
    @api.marshal_with(wb_account_model)
    @api.doc('get_wb_account', description='Получение WB аккаунта по ID')
    def get(self, account_id):
        """Получение WB аккаунта по ID"""
        pass

    @jwt_required()
    @api.expect(create_wb_account_model)
    @api.marshal_with(wb_account_model)
    @api.doc('update_wb_account', description='Обновление WB аккаунта')
    def put(self, account_id):
        """Обновление WB аккаунта"""
        pass

    @jwt_required()
    @api.doc('delete_wb_account', description='Удаление WB аккаунта')
    def delete(self, account_id):
        """Удаление WB аккаунта"""
        pass

# Worker endpoints documentation
@worker_ns.route('/status')
class WorkerStatus(Resource):
    @jwt_required()
    @api.doc('get_worker_status', description='Получение статуса воркера')
    def get(self):
        """Получение статуса воркера"""
        pass

# Health endpoints documentation
@health_ns.route('/')
class Health(Resource):
    @api.marshal_with(health_model)
    @api.doc('health_check', description='Проверка здоровья системы')
    def get(self):
        """Проверка здоровья системы"""
        pass

@health_ns.route('/detailed')
class HealthDetailed(Resource):
    @api.marshal_with(health_model)
    @api.doc('detailed_health_check', description='Детальная проверка здоровья системы')
    def get(self):
        """Детальная проверка здоровья системы"""
        pass

@health_ns.route('/ready')
class HealthReady(Resource):
    @api.doc('readiness_check', description='Проверка готовности системы (Kubernetes)')
    def get(self):
        """Проверка готовности системы (Kubernetes)"""
        pass

@health_ns.route('/live')
class HealthLive(Resource):
    @api.doc('liveness_check', description='Проверка жизнеспособности системы (Kubernetes)')
    def get(self):
        """Проверка жизнеспособности системы (Kubernetes)"""
        pass
