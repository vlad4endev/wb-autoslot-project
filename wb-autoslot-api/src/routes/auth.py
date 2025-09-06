from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from src.models.user import db, User
from src.middleware.rate_limiter import rate_limit_auth
from datetime import timedelta
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@rate_limit_auth(max_requests=3, window_seconds=300)  # 3 attempts per 5 minutes
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        # Validation
        if not phone or not password:
            return jsonify({'error': 'Phone and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Email validation if provided
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user already exists by phone or email
        exists, field = User.user_exists(phone=phone, email=email)
        if exists:
            if field == 'phone':
                return jsonify({
                    'error': 'Пользователь с таким номером телефона уже существует',
                    'error_code': 'USER_EXISTS',
                    'field': 'phone',
                    'message': 'Пользователь с таким номером телефона уже зарегистрирован. Переходим к авторизации...'
                }), 409
            elif field == 'email':
                return jsonify({
                    'error': 'Пользователь с таким email уже существует',
                    'error_code': 'USER_EXISTS',
                    'field': 'email',
                    'message': 'Пользователь с таким email уже зарегистрирован. Переходим к авторизации...'
                }), 409
        
        # Create new user
        try:
            user = User(phone=phone, password=password, email=email)
            db.session.add(user)
            db.session.commit()
            
            # Create tokens
            access_token = create_access_token(
                identity=str(user.id),
                expires_delta=timedelta(hours=24)
            )
            refresh_token = create_refresh_token(
                identity=str(user.id),
                expires_delta=timedelta(days=30)
            )
            
            return jsonify({
                'message': 'User registered successfully',
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Registration failed'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/login', methods=['POST'])
@rate_limit_auth(max_requests=5, window_seconds=300)  # 5 attempts per 5 minutes
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        if not phone and not email:
            return jsonify({'error': 'Phone or email is required'}), 400
        
        # Find user by phone or email
        user = None
        if phone:
            user = User.find_by_phone(phone)
        elif email:
            user = User.find_by_email(email)
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Create tokens
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30)
        )
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        # Convert to int since we store as string but need int for query
        user = User.query.get(int(current_user_id))
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 404
        
        new_token = create_access_token(
            identity=str(current_user_id),
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'access_token': new_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    try:
        current_user_id = get_jwt_identity()
        # Convert to int since we store as string but need int for query
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get user info'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client-side token removal)"""
    return jsonify({'message': 'Logout successful'}), 200

