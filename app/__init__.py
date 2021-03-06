from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask_mail import Mail
from config import config
from flask import Flask
from flask_login import LoginManager
from flask_pagedown import PageDown

bootstrap = Bootstrap()
db = SQLAlchemy()
moment = Moment()
mail = Mail()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
pagedown = PageDown()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    #init_app
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    #视图蓝本注册
    from .main import main
    app.register_blueprint(main)
    from .auth import auth
    app.register_blueprint(auth,url_prefix='/auth')

    return app