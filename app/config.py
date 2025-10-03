import os


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "Hyah-Kujsh-12345")  # Change this in production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 299 # Recycle connections every 30 seconds
    SQLALCHEMY_POOL_SIZE = 10  # Maximum number of connections to keep in the pool
    SQLALCHEMY_POOL_TIMEOUT = 299  # Timeout for acquiring a connection from the pool
    SQLALCHEMY_POOL_PRE_PING = True  # Check the connection before using it   
    SQLALCHEMY_ECHO = False # Log SQL queries for debugging
    LOG_LEVEL = "INFO"
    SERVER_NAME = os.environ.get("SERVER_NAME", "smallshardz.com")

    # Server defaults (can be overridden by ENV)
    FLASK_RUN_HOST = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    FLASK_RUN_PORT = int(os.environ.get("FLASK_RUN_PORT", 5000))
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false")
    JWT_SECRET_KEY = "qqq-qqq-qqq-qqq"  # Change this in production


   




class DevelopmentConfig(BaseConfig):
    FLASK_DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///mvp.db").replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret") 
    LOG_LEVEL = "DEBUG"
    JWT_SECRET_KEY = "dev_jwt_secret"

class ProductionConfig(BaseConfig):
    FLASK_DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///mvp.db").replace("postgres://", "postgresql://")
    LOG_LEVEL = "INFO"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret") 
    JWT_SECRET_KEY = "dev_jwt_secret"

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://testuser:testpass@localhost:5432/testdb"
    )
    LOG_LEVEL = "DEBUG"
    JWT_SECRET_KEY = "dev_jwt_secret"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}









