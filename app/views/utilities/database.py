import os
import shutil
from app.logger import logger
from app import db
from sqlalchemy import text
from flask import flash
from app.database.models import DatabaseInstance
from flask_login import current_user


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
    schema = credentials.get("schema", "")

    if db_type == "postgresql":
        uri = f"postgresql://{user}:{password}@{host}:{port}/{schema}"
    elif db_type == "mysql":
        uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{schema}"
    elif db_type == "sqlite":
        uri = f"sqlite:///{schema}.db"
    else:
        uri = ""

    instance = DatabaseInstance(
        user_id=current_user.id,
        name=db_type,
        uri=uri
    )
    db.session.add(instance)
    db.session.commit()
    flash(f"Database instance '{instance.name}' created and saved.")
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
    
    """
    Create a new schema and optionally a new user in Postgres.
    """

    try:
        
        schema_name = create_unique_schema_name()
        password = create_unique_password()
        username = current_user.username if current_user else "default_user"


        # 1️⃣ Optionally create a new user
        if username and password:
            db.session.execute(
                text(f"CREATE USER {username} WITH PASSWORD :password"),
                {"password": password}
            )
        
        # 2️⃣ Create the schema
        owner_clause = f"AUTHORIZATION {username}" if username else ""
        db.session.execute(
            text(f"CREATE SCHEMA {schema_name} {owner_clause}")
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating Postgres tenant: {e}")
        flash(f"Error creating Postgres tenant: {e}", "danger")
        return None    
    # 3️⃣ Commit changes
    db.session.commit()
    flash(f"Schema '{schema_name}' created successfully!")
    return {"schema": schema_name, "username": username, "password": password, "db_type": "postgresql"}

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
    










