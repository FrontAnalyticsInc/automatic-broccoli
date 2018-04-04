#!/usr/bin/env python

import os


BASE_FOLDER = os.path.dirname(__file__)


class Config:
    BASE_DIR = os.path.abspath(BASE_FOLDER)
    VERBOSE = True
    WRITE_TO_DB = False
    DB_WRITE_MODE = 'replace'


class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    WRITE_TO_DB = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(Config.BASE_DIR, "insights.db")


class TestConfig(Config):
    """Testing configuration."""

    ENV = 'testing'
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class ProdConfig(Config):
    """Production configuration"""

    ENV = 'prod'
    VERBOSE = False
    DB_WRITE_MODE = 'append'
    WRITE_TO_DB = True
    SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://{0}:{1}@{2}/{3}".format(os.environ.get('BROCCOLI_AWS_USERNAME'),
                                                                       os.environ.get('BROCCOLI_AWS_PASSWORD'),
                                                                       os.environ.get('BROCCOLI_AWS_URL'),
                                                                       os.environ.get('BROCCOLI_AWS_DB_NAME'))

# Set the configuration you would like to operate on
TEST_ENV = TestConfig()
IN_USE = DevConfig()
