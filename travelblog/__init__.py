import os

from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment

from travelblog.config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
login.login_message_category = 'info'
mail = Mail()
moment = Moment()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.app_context().push()
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)

    from travelblog.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from travelblog.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from travelblog.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app


from travelblog import models