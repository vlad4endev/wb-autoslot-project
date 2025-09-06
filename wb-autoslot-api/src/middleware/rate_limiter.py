"""
Rate limiting middleware for WB AutoSlot API
"""

import time
import logging
from functools import wraps
from flask import request, jsonify, g
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(lambda: deque())
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, key, max_requests, window_seconds):
        """Check if request is allowed"""
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(now)
            self.last_cleanup = now
        
        # Get request history for this key
        request_times = self.requests[key]
        
        # Remove requests outside the window
        cutoff_time = now - window_seconds
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
        
        # Check if under limit
        if len(request_times) < max_requests:
            request_times.append(now)
            return True, max_requests - len(request_times)
        
        return False, 0
    
    def _cleanup_old_entries(self, now):
        """Clean up old entries to prevent memory leaks"""
        cutoff_time = now - 3600  # 1 hour
        keys_to_remove = []
        
        for key, request_times in self.requests.items():
            # Remove old requests
            while request_times and request_times[0] < cutoff_time:
                request_times.popleft()
            
            # Remove empty entries
            if not request_times:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.requests[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_requests=100, window_seconds=3600, per='ip'):
    """
    Rate limiting decorator
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        per: Rate limit per 'ip' or 'user'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine rate limit key
            if per == 'ip':
                key = request.remote_addr
            elif per == 'user':
                # Try to get user ID from JWT token
                from flask_jwt_extended import get_jwt_identity
                user_id = get_jwt_identity()
                if user_id:
                    key = f"user:{user_id}"
                else:
                    key = request.remote_addr
            else:
                key = request.remote_addr
            
            # Check rate limit
            allowed, remaining = rate_limiter.is_allowed(key, max_requests, window_seconds)
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for {key}: {max_requests} requests per {window_seconds}s")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per {window_seconds} seconds',
                    'retry_after': window_seconds
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(int(time.time() + window_seconds))
            
            return response
        
        return decorated_function
    return decorator

def rate_limit_by_endpoint(max_requests=60, window_seconds=60):
    """Rate limit by endpoint"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create key based on endpoint and IP
            endpoint = request.endpoint or 'unknown'
            key = f"{endpoint}:{request.remote_addr}"
            
            allowed, remaining = rate_limiter.is_allowed(key, max_requests, window_seconds)
            
            if not allowed:
                logger.warning(f"Endpoint rate limit exceeded for {key}")
                return jsonify({
                    'error': 'Endpoint rate limit exceeded',
                    'message': f'Too many requests to {endpoint}',
                    'retry_after': window_seconds
                }), 429
            
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
            
            return response
        
        return decorated_function
    return decorator

def rate_limit_auth(max_requests=5, window_seconds=300):
    """Rate limit for authentication endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = f"auth:{request.remote_addr}"
            
            allowed, remaining = rate_limiter.is_allowed(key, max_requests, window_seconds)
            
            if not allowed:
                logger.warning(f"Auth rate limit exceeded for {request.remote_addr}")
                return jsonify({
                    'error': 'Too many authentication attempts',
                    'message': f'Maximum {max_requests} attempts per {window_seconds} seconds',
                    'retry_after': window_seconds
                }), 429
            
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
            
            return response
        
        return decorated_function
    return decorator
