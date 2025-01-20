from flask import Flask, render_template
from data.database import db_session
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError

from blueprints.auth import auth_blueprint
from blueprints.profile import profile_blueprint
from blueprints.event import event_blueprint


def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = False
    app.config['SECRET_KEY'] = 'walid741415'
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # Set CSRF token validity to 1 hour


    db_session.global_init('data/database/app.sqlite')
    login_manager = LoginManager()
    login_manager.init_app(app)

    csrf = CSRFProtect()
    csrf.init_app(app)

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
        return """
        <html>
            <head><title>CSRF Error</title></head>
            <body>
                <h1>Your session has expired or the CSRF token is invalid.</h1>
                <p>Please refresh the page and try again.</p>
            </body>
        </html>
    """, 403

    @app.route('/')
    def main():
        return render_template('homepage.html')
    return app


app = create_app()


def main():
    app.run(port=8000, host='127.0.0.1', debug=True, threaded=True)


if __name__ == '__main__':
    main()
