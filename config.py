import os

class Config(object):
    DEBUG = False

class DevelopmentConfig(object):
    DEBUG = True
    DATABASE_NAME = 'landcharges'
    DATABASE_USER = 'landcharges'
    DATABASE_PASSWORD = 'lcalpha'
    DATABASE_HOST = 'localhost'