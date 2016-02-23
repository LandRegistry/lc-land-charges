import os


class Config(object):
    DEBUG = os.getenv('DEBUG', True)
    MQ_USERNAME = os.getenv("MQ_USERNAME", "mquser")
    MQ_PASSWORD = os.getenv("MQ_PASSWORD", "mqpassword")
    MQ_HOSTNAME = os.getenv("MQ_HOST", "localhost")
    MQ_PORT = os.getenv("MQ_PORT", "5672")
    LEGACY_ADAPTER_URI = os.getenv('LEGACY_ADAPTER_URL', 'http://localhost:5007')
    APPLICATION_NAME = "lc-land-charges"
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'landcharges')
    DATABASE_USER = os.getenv('DATABASE_USER', 'landcharges')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'lcalpha')
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}/{}".format(DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME)
    ALLOW_DEV_ROUTES = os.getenv('ALLOW_DEV_ROUTES', True)

