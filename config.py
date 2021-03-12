import os
import pymysql

base_dir = os.path.abspath(os.path.dirname(__file__))
pymysql.install_as_MySQLdb()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY','太阳黑子')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME','1692279896')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD','thlgzgkyqvlefdbj')
    #启用传输层安全
    MAIL_USE_TLS = True
    MAIL_PORT = os.environ.get('MAIL_PORT',25)
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_ADMIN = '1692279896@qq.com'
    MAIL_SENDER = 'Sweet home ADMIN <1692279896@qq.com>'
    MAIL_SUBJECT_PREFIX = os.environ.get('MAIL_SUBJECT_PREFIX','[Sweet home]')
    POST_PER_PAGE = os.environ.get('POST_PER_PAGE',10)
    ALLOW_PHOTO_FMT = set(['png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF'])
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_DIR = 'upload/photo/'
    ALL_UPLOAD_DIR = base_dir + '/app/static/upload/photo/'
    LOCAL_IMG_PATH = base_dir + '/app/static/'
    BASE_PHOTO_PATH = 'upload/photo/default.gif'
    FOLLOW_PER_PAGE = os.environ.get('FOLLOW_PER_PAGE',8)
    COMMENT_PER_PAGE = os.environ.get('COMMENT_PER_PAGE',10)

    @staticmethod
    def init_app(app):
        pass

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
                              'sqlite:///' + os.path.join(base_dir,'data.sqlite')

class TestingConfig(Config):
    Testing = True
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI_TEST') or \
                              'sqlite://'

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI_DEV') or \
                              'mysql://root:cats@127.0.0.1:3306/sweet_home?charset=utf8'

config = {
    'default': DevelopmentConfig,

    'dev': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

