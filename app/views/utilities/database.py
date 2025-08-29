import os
import shutil
from app.logger import logger
from app import db, engine
from sqlalchemy import text
from flask import flash
from app.database.models import DatabaseInstance
from flask_login import current_user
import secrets
from .payment import create_subscription


def save_db_credentials(credentials: dict):
    
   

    # Example credentials dict:
    # {
    #   "db_type": "postgresql",
    #   "schema": "tenant1",
    #   "username": "user1",
    #   "password": "pass1"
    # }

    db_type = credentials.get("db_type", "postgresql")
    user = credentials.get("username", "")
    password = credentials.get("password", "")
    host = "[HOST]"
    port = "[PORT]"
    schema = credentials.get("database", "")

    uri = credentials.get("uri", f"{db_type}://{user}:{password}@{host}:{port}/{schema}")

    instance = DatabaseInstance(
        user_id=current_user.id,
        name=db_type,
        uri=uri
    )
    db.session.add(instance)
    db.session.commit()
    flash(f"Database instance '{instance.name}' created")
    return instance

def create_unique_schema_name(base="tenant"):
    import random
    import string
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{base}_{suffix}"

def create_unique_password(length=12):
    import random
    import string
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=length))

def create_unique_prefix(base="user_"):
    import random
    import string
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{base}{suffix}_"

def backup_database(db_uri: str, backup_path="backup.db"):
    try:
        if db_uri.startswith("sqlite:///"):
            db_file = db_uri.replace("sqlite:///", "")
            shutil.copy(db_file, backup_path)
            logger.info(f"Database backup created at {backup_path}")
        else:
            logger.warning("Backup currently supported only for SQLite.")
    except Exception as e:
        logger.error(f"Backup failed: {e}")

def migrate_to(uri: str):
    logger.info(f"Migration feature stub: would migrate to {uri}")


def create_postgres_tenant():
   

    try : 
        

        # Auto-generate username/password 
        
        username = f"user_{current_user.username}_{secrets.token_hex(4)}"
        database_name = f"db_{secrets.token_hex(4)}"
        password = secrets.token_urlsafe(16)

        with engine.connect() as conn:
            # Set autocommit because CREATE DATABASE cannot run inside a transaction
            conn.execution_options(isolation_level="AUTOCOMMIT")

            # 1️⃣ Create user 
            conn.execute(text(f"CREATE USER {username} WITH PASSWORD :password"),
                            {"password": password})

            # 2️⃣ Create the database
            conn.execute(text(f"CREATE DATABASE {database_name} OWNER {username}"))

        # 3️⃣ Return connection info for this tenant
        connection_url = f"postgresql://{username}:{password}@{engine.url.host}:{engine.url.port}/{database_name}"

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating Postgres tenant: {e}")
        flash(f"Error creating Postgres tenant: {e}", "danger")
        return None    
    # 3️⃣ Commit changes
    db.session.commit()
    create_subscription('postgres',database_name)
    
    return {"database": database_name, "username": username, "password": password, "db_type": "postgresql", "uri":connection_url}

def create_mysql_tenant():
    pass
def create_mongodb_tenant():
    pass
def create_firebase_tenant():
    pass
def create_sqlite_tenant():
    pass


def create_database_tenant(form):
    selected = form.db_type.data
    logger.info(f"Creating tenant for DB type: {selected}")
    

    tenants = {
        "postgresql":create_postgres_tenant,
        "mysql":create_mysql_tenant,
        "mongodb":create_mongodb_tenant,
        "sqlite":create_sqlite_tenant,
        "firebase":create_firebase_tenant,
    }

    create = tenants[selected]
    credentials = create()

    # save cred to main db
    save_db_credentials(credentials)




    pass

def create_database(name: str):

    # create a new database instance


    # save instance env var name to main db

    # return url
    pass
    










