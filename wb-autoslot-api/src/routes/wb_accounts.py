from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, WBAccount
from datetime import datetime
import json

wb_accounts_bp = Blueprint('wb_accounts', __name__)

@wb_accounts_bp.route('/wb-accounts', methods=['GET'])
@jwt_required()
def get_wb_accounts():
    """Get user's WB accounts"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        accounts = [account.to_dict() for account in user.wb_accounts]
        
        return jsonify({
            'accounts': accounts,
            'count': len(accounts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get WB accounts'}), 500


@wb_accounts_bp.route('/wb-accounts', methods=['POST'])
@jwt_required()
def add_wb_account():
    """Add new WB account"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        account_name = data.get('account_name', '').strip()
        cookies = data.get('cookies', '')
        
        if not account_name:
            return jsonify({'error': 'Account name is required'}), 400
        
        # Check if account name already exists for this user
        existing_account = WBAccount.query.filter_by(
            user_id=current_user_id,
            account_name=account_name
        ).first()
        
        if existing_account:
            return jsonify({'error': 'Account with this name already exists'}), 409
        
        # Create new WB account
        wb_account = WBAccount(
            user_id=current_user_id,
            account_name=account_name,
            cookies=cookies,
            last_login=datetime.utcnow() if cookies else None
        )
        
        db.session.add(wb_account)
        db.session.commit()
        
        return jsonify({
            'message': 'WB account added successfully',
            'account': wb_account.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add WB account'}), 500


@wb_accounts_bp.route('/wb-accounts/<int:account_id>', methods=['PUT'])
@jwt_required()
def update_wb_account(account_id):
    """Update WB account"""
    try:
        current_user_id = get_jwt_identity()
        
        wb_account = WBAccount.query.filter_by(
            id=account_id,
            user_id=current_user_id
        ).first()
        
        if not wb_account:
            return jsonify({'error': 'WB account not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields
        if 'account_name' in data:
            account_name = data['account_name'].strip()
            if account_name:
                # Check for duplicate names
                existing = WBAccount.query.filter_by(
                    user_id=current_user_id,
                    account_name=account_name
                ).filter(WBAccount.id != account_id).first()
                
                if existing:
                    return jsonify({'error': 'Account with this name already exists'}), 409
                
                wb_account.account_name = account_name
        
        if 'cookies' in data:
            wb_account.cookies = data['cookies']
            wb_account.last_login = datetime.utcnow()
        
        if 'is_active' in data:
            wb_account.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'WB account updated successfully',
            'account': wb_account.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update WB account'}), 500


@wb_accounts_bp.route('/wb-accounts/<int:account_id>', methods=['DELETE'])
@jwt_required()
def delete_wb_account(account_id):
    """Delete WB account"""
    try:
        current_user_id = get_jwt_identity()
        
        wb_account = WBAccount.query.filter_by(
            id=account_id,
            user_id=current_user_id
        ).first()
        
        if not wb_account:
            return jsonify({'error': 'WB account not found'}), 404
        
        # Check if account is used in any active tasks
        active_tasks = [task for task in wb_account.tasks if task.status == 'active']
        if active_tasks:
            return jsonify({
                'error': f'Cannot delete account. It is used in {len(active_tasks)} active task(s)'
            }), 400
        
        db.session.delete(wb_account)
        db.session.commit()
        
        return jsonify({'message': 'WB account deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete WB account'}), 500


@wb_accounts_bp.route('/wb-accounts/<int:account_id>/test', methods=['POST'])
@jwt_required()
def test_wb_account(account_id):
    """Test WB account connection"""
    try:
        current_user_id = get_jwt_identity()
        
        wb_account = WBAccount.query.filter_by(
            id=account_id,
            user_id=current_user_id
        ).first()
        
        if not wb_account:
            return jsonify({'error': 'WB account not found'}), 404
        
        # TODO: Implement actual WB connection test using Playwright
        # For now, return mock response
        if wb_account.cookies:
            wb_account.last_login = datetime.utcnow()
            wb_account.is_active = True
            db.session.commit()
            
            return jsonify({
                'message': 'WB account connection successful',
                'status': 'connected',
                'last_test': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'message': 'No cookies found for this account',
                'status': 'disconnected'
            }), 400
        
    except Exception as e:
        return jsonify({'error': 'Failed to test WB account'}), 500

