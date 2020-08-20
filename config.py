import os

basedir = os.path.abspath(os.path.dirname(__file__))
ROTATION_NUMBERS = [1, 2, 3, 4, 5]
MAX_ALLOCATION_POINTS = 100
MAIL_CONFIG = {
    "update_subj": "Lottery System: Points Allocation Update",
    "welcome_subj": "Welcome to the Lottery System"
}


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'SuperRandomLongStringToPreventDecryptionWithNumbers123456789'
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
