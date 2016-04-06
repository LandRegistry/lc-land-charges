import os


class Config(object):
    DEBUG = os.getenv('DEBUG', True)

    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "postgresql://landcharges:lcalpha@localhost/landcharges")
    AMQP_URI = os.getenv("AMQP_URI", "amqp://mquser:mqpassword@localhost:5672")
    PSQL_CONNECTION = os.getenv("PSQL_CONNECTION", "dbname='landcharges' user='landcharges' host='localhost' password='lcalpha'")

    APPLICATION_NAME = "lc-land-charges"
    ALLOW_DEV_ROUTES = os.getenv('ALLOW_DEV_ROUTES', True)
    AUDIT_LOG_FILENAME = os.getenv("AUDIT_LOG_FILENAME", "/vagrant/logs/land-charges/audit.log")

