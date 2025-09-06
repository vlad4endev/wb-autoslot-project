import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.tasks import tasks_bp
from src.routes.wb_accounts import wb_accounts_bp
from src.routes.worker import worker_bp
from src.routes.notifications import notifications_bp
from src.routes.health import health_bp
from src.routes.api_docs import api_docs_bp
from src.routes.backup import backup_bp
from src.services.task_worker import task_worker
from src.services.notification_service import notification_service
from src.services.monitoring_service import monitoring_service
from src.services.backup_service import backup_service
from src.config import config
from src.logging_config import setup_logging

# Get configuration
config_name = os.environ.get('FLASK_ENV', 'default')
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Load configuration
app.config.from_object(config[config_name])

# Setup logging
setup_logging(app)

# Enable CORS for all routes
CORS(app, origins=app.config['CORS_ORIGINS'], allow_headers=["Content-Type", "Authorization"])

# Initialize extensions
jwt = JWTManager(app)
migrate = Migrate(app, db)

# JWT configuration for string identity
@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return str(identity)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tasks_bp, url_prefix='/api')
app.register_blueprint(wb_accounts_bp, url_prefix='/api')
app.register_blueprint(worker_bp, url_prefix='/api')
app.register_blueprint(notifications_bp, url_prefix='/api')
app.register_blueprint(health_bp, url_prefix='/api')
app.register_blueprint(api_docs_bp, url_prefix='/api/docs')
app.register_blueprint(backup_bp, url_prefix='/api/backup')

# Database configuration
if not app.config.get('SQLALCHEMY_DATABASE_URI'):
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"

db.init_app(app)

with app.app_context():
    # Initialize database migrations
    from flask_migrate import init, migrate, upgrade
    import os
    
    # Check if migrations directory exists, if not initialize it
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    if not os.path.exists(migrations_dir):
        print("Initializing database migrations...")
        init()
        print("Creating initial migration...")
        migrate(message='Initial migration')
    
    # Apply migrations
    try:
        upgrade()
        print("Database migrations applied successfully")
    except Exception as e:
        print(f"Warning: Failed to apply migrations: {e}")
        # Fallback to create_all for development
        db.create_all()
    
    # Initialize services
    notification_service.init_app(app)
    monitoring_service.init_app(app)
    backup_service.init_app(app)
    
    # Auto-start worker after app context is available
    try:
        if not task_worker.running:
            # Pass app context to worker
            task_worker.app = app
            task_worker.start()
            print("Task worker started successfully")
    except Exception as e:
        print(f"Warning: Failed to start worker: {e}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
