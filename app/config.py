import os


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 299 # Recycle connections every 30 seconds
    SQLALCHEMY_POOL_SIZE = 10  # Maximum number of connections to keep in the pool
    SQLALCHEMY_POOL_TIMEOUT = 299  # Timeout for acquiring a connection from the pool
    SQLALCHEMY_POOL_PRE_PING = True  # Check the connection before using it   
    SQLALCHEMY_ECHO = True # Log SQL queries for debugging
    LOG_LEVEL = "INFO"

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///mvp.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret") 
    LOG_LEVEL = "DEBUG"

class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    LOG_LEVEL = "INFO"

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}













