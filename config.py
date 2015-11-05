import os


class Config(object):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'landcharges')
    DATABASE_USER = os.getenv('DATABASE_USER', 'landcharges')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'lcalpha')
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}/{}".format(DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME)
    MQ_USERNAME = 'mquser'
    MQ_PASSWORD = 'mqpassword'
    MQ_HOSTNAME = 'localhost'
    MQ_PORT = '5672'


class PreviewConfig(Config):
    DEBUG = False
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'landcharges')
    DATABASE_USER = os.getenv('DATABASE_USER', 'landcharges')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'lcalpha')
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}/{}".format(DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME)
    MQ_USERNAME = 'mquser'
    MQ_PASSWORD = 'mqpassword'
    MQ_HOSTNAME = 'localhost'
    MQ_PORT = '5672'
