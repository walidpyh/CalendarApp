from flask import request, Response, g
from functools import wraps
import re
import time

class SecurityMiddleware:
    """
    Middleware to add security headers and other protections to Flask app
    """
    def __init__(self, app=None):
        if app:
            self.init_app(app)
            
    def init_app(self, app):
        """
        Initialize the middleware with a Flask app
        """
        # Apply security headers to all responses
        @app.after_request
        def add_security_headers(response):
            # Content Security Policy (CSP)
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data:; "  # Allow data: for QR codes
                "frame-ancestors 'none'; "
                "form-action 'self';"
            )
            
            # Additional security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            
            return response
            
        # Track request timing for suspicious behavior
        @app.before_request
        def track_request_start():
            g.start_time = time.time()
            
        @app.after_request
        def track_request_end(response):
            if hasattr(g, 'start_time'):
                # Log very fast requests (potential automated attacks)
                elapsed = time.time() - g.start_time
                if elapsed < 0.01 and request.path != '/static':
                    app.logger.warning(f"Suspiciously fast request: {request.path} ({elapsed:.5f}s) from {request.remote_addr}")
                    
            return response

        # Add CSRF token validation for all state-changing requests
        @app.before_request
        def validate_csrf_token():
            # Only check for state-changing methods
            if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
                # Skip check for API endpoints that use token auth
                if not request.path.startswith('/api/'):
                    csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
                    if not csrf_token:
                        app.logger.warning(f"CSRF token missing in request to {request.path} from {request.remote_addr}")
                        # CSRF error will be handled by Flask-WTF

def sanitize_input(input_str):
    """
    Sanitize user input to prevent XSS and other injection attacks
    
    :param input_str: String to sanitize
    :return: Sanitized string
    """
    if not input_str or not isinstance(input_str, str):
        return input_str
        
    # Remove potentially dangerous HTML tags and attributes
    input_str = re.sub(r'<script.*?>.*?</script>', '', input_str, flags=re.IGNORECASE | re.DOTALL)
    input_str = re.sub(r'<.*?javascript:.*?>', '', input_str, flags=re.IGNORECASE | re.DOTALL)
    input_str = re.sub(r'<.*?on\w+=".*?>', '', input_str, flags=re.IGNORECASE | re.DOTALL)
    
    return input_str

def rate_limit(max_requests=10, per_seconds=60):
    """
    Decorator for rate limiting specific routes
    
    :param max_requests: Maximum number of requests allowed
    :param per_seconds: Time period in seconds
    :return: Decorated function
    """
    request_history = {}
    
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get client IP
            client_ip = request.remote_addr
            
            # Initialize tracking for this IP if not exists
            if client_ip not in request_history:
                request_history[client_ip] = []
                
            # Clean old requests
            current_time = time.time()
            request_history[client_ip] = [req_time for req_time in request_history[client_ip] 
                                         if current_time - req_time < per_seconds]
                                         
            # Check if limit exceeded
            if len(request_history[client_ip]) >= max_requests:
                # Log rate limit violation
                from .audit_logger import log_auth_event
                log_auth_event(
                    event_type="rate_limit_exceeded",
                    details={
                        "path": request.path,
                        "limit": max_requests,
                        "period": per_seconds
                    }
                )
                return Response("Rate limit exceeded. Please try again later.", 429)
                
            # Add current request time
            request_history[client_ip].append(current_time)
            
            # Process the request
            return f(*args, **kwargs)
        return wrapped
    return decorator 