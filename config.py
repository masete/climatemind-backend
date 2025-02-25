import os
import urllib
from datetime import timedelta

from sqlalchemy.pool import NullPool

from app.network_x_tools.network_x_processor import network_x_processor


class BaseConfig(object):
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = True

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "DEFAULT_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=120)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)
    JWT_ACCESS_COOKIE_NAME = "access_token"
    JWT_REFRESH_COOKIE_NAME = "refresh_token"
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_REFRESH_COOKIE_PATH = "/refresh"
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = None
    CACHE_TYPE = "simple"

    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
    SENDGRID_DEFAULT_FROM = os.environ.get("MAIL_DEFAULT_SENDER")

    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    SENTRY_ENVIRONMENT = os.environ.get("SENTRY_ENVIRONMENT")
    SENTRY_TRACES_SAMPLE_RATE = os.environ.get("SENTRY_TRACES_SAMPLE_RATE", 0.1)

    DB_CREDENTIALS = os.environ.get("DATABASE_PARAMS")
    SQLALCHEMY_DATABASE_URI = (
        "mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(DB_CREDENTIALS)
    )

    CURRENT_DIR = os.getcwd()
    SCHWARTZ_QUESTIONS_PATH = os.path.join(CURRENT_DIR, "app/questions/static")
    SCHWARTZ_QUESTIONS_SCHEMA = (
        f"{SCHWARTZ_QUESTIONS_PATH}/schwartz_questions.schema.json"
    )
    SCHWARTZ_QUESTIONS_FILE = f"{SCHWARTZ_QUESTIONS_PATH}/schwartz_questions.json"

    VALUE_DESCRIPTIONS_PATH = os.path.join(CURRENT_DIR, "app/personal_values/static")
    VALUE_DESCRIPTIONS_SCHEMA = (
        f"{VALUE_DESCRIPTIONS_PATH}/value_descriptions.schema.json"
    )
    VALUE_DESCRIPTIONS_FILE = f"{VALUE_DESCRIPTIONS_PATH}/value_descriptions.json"

    GRAPH_FILE_PATH = os.path.join(CURRENT_DIR, "app/ontology/output")
    GRAPH_FILE_EXT = "gpickle"
    GRAPH_FILE_NAME = "Climate_Mind_DiGraph"
    GRAPH_FILE = f"{GRAPH_FILE_PATH}/{GRAPH_FILE_NAME}.{GRAPH_FILE_EXT}"
    GRAPH_FILE_BACKUP = f"{GRAPH_FILE_PATH}/{GRAPH_FILE_NAME}_backup.{GRAPH_FILE_EXT}"
    nx_processor = network_x_processor(GRAPH_FILE)
    G = nx_processor.get_graph()
    IRI_PREFIX = "webprotege.stanford.edu."


class TestingConfig(DevelopmentConfig):
    DEBUG = False
    TESTING = True

    DB_NAME = "sqldb-web-pytest-001"
    DB_CREDENTIALS = os.environ.get("TEST_DATABASE_PARAMS", "") + f"Database={DB_NAME};"
    SQLALCHEMY_DATABASE_URI = (
        "mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(DB_CREDENTIALS)
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": NullPool,
    }
