import os


class Config(object):
    DEBUG = os.getenv('DEBUG', True)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "postgresql://landcharges:lcalpha@localhost/landcharges")

    PSQL_CONNECTION = os.getenv("PSQL_CONNECTION", "dbname='landcharges' user='landcharges' host='192.168.39.229' password='landcharges'")
    #PSQL_CONNECTION = os.getenv("PSQL_CONNECTION", "dbname='landcharges' user='landcharges' host='localhost' password='lcalpha'")

