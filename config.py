import os

basedir = os.path.abspath(os.path.dirname(__file__))

os.environ['DATABASE_URL'] = 'postgresql://localhost:5432/rotations'
ROTATION_NUMBERS = [1, 2, 3, 4, 5]


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'qwerty123456'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
