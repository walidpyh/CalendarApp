from flask import Flask, render_template, request
from data.database import db_session
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError
import os
import secrets
from datetime import timedelta

from blueprints.auth import auth_blueprint
from blueprints.profile import profile_blueprint
from blueprints.event import event_blueprint
from security import SecurityMiddleware, log_auth_event


def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = False
    
    # Generate a strong secret key or load from environment variable
    if os.environ.get('FLASK_SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
    else:
        # Generate a secure random key (in production, this should be set in env vars)
        app.config['SECRET_KEY'] = secrets.token_hex(32)
    
    # CSRF protection settings
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # Set CSRF token validity to 1 hour
    app.config['WTF_CSRF_SSL_STRICT'] = True  # Reject CSRF tokens from HTTP to HTTPS
    
    # Session security settings
    app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Restrict cookie to same site
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # Session expires after 1 hour

    db_session.global_init('data/database/app.sqlite')
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.session_protection = "strong"  # Enhanced session protection

    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Initialize security middleware
    security = SecurityMiddleware()
    security.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_blueprint, url_prefix='/')
    app.register_blueprint(profile_blueprint, url_prefix='/')
    app.register_blueprint(event_blueprint, url_prefix='/')

    @login_manager.user_loader
    def load_user(user_id):
        from data.database.users import User
        session = db_session.create_session()
        return session.query(User).get(user_id)
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        # Log CSRF violations
        log_auth_event(
            event_type="security_violation",
            username=request.remote_addr,  # We don't know the user yet
            success=False,
            details={
                "violation_type": "csrf",
                "url": request.url,
                "method": request.method
            }
        )
        return """
        <html>
            <head><title>CSRF Error</title></head>
            <body>
                <h1>Your session has expired or the CSRF token is invalid.</h1>
                <p>Please refresh the page and try again.</p>
            </body>
        </html>
    """, 403
    
    @app.errorhandler(403)
    def handle_forbidden(e):
        return """
        <html>
            <head><title>Access Denied</title></head>
            <body>
                <h1>Access Denied</h1>
                <p>You do not have permission to access this resource.</p>
            </body>
        </html>
    """, 403
    
    @app.errorhandler(404)
    def handle_not_found(e):
        return """
        <html>
            <head><title>Page Not Found</title></head>
            <body>
                <h1>Page Not Found</h1>
                <p>The requested page does not exist.</p>
            </body>
        </html>
    """, 404
    
    @app.errorhandler(500)
    def handle_server_error(e):
        return """
        <html>
            <head><title>Server Error</title></head>
            <body>
                <h1>Server Error</h1>
                <p>An unexpected error occurred. Please try again later.</p>
            </body>
        </html>
    """, 500

    @app.route('/')
    def main():
        return render_template('homepage.html')
    return app


app = create_app()


def main():
    app.run(port=8000, host='127.0.0.1', debug=True, threaded=True)


if __name__ == '__main__':
    main()
