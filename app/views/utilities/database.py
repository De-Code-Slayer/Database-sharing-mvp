import os
import shutil
from app.logger import logger
from app import db, engine
from sqlalchemy import text
from flask import flash
from app.database.models import DatabaseInstance, StorageInstance, MyUser
from flask_login import current_user
import secrets
import subprocess
import shlex
from .payment import create_subscription,delete_subscription
from .storage import create_storage


HOST = os.getenv('DB_HOST')


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
    host = HOST
    port = "[PORT]"
    schema = credentials.get("database", "")

    uri = credentials.get("uri", f"{db_type}://{user}:{password}@{host}:{port}/{schema}")

    instance = DatabaseInstance(
        user_id=current_user.id,
        username = user,
        password = password,
        database_name = schema,
        name=db_type,
        uri=uri
    )
    db.session.add(instance)
    db.session.commit()
    flash(f"Database instance '{instance.name}' created")
    return instance

def get_db_instance_by_id(id):
    return DatabaseInstance.query.filter_by(id=id).first()

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

def sanitize_username(name):
    # Allow only letters, digits, and underscores
    safe = "".join(c if c.isalnum() else "_" for c in name)
    return safe.lower()

def create_postgres_tenant():
   

    try : 
        

        # Auto-generate username/password 
        
        username = sanitize_username(f"user_{current_user.username}_{secrets.token_hex(4)}")
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

def delete_postgres_tenant(instance):
    try:
        username = instance.username
        database_name = instance.database_name

        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")

            # 1️⃣ Drop the database (must happen before dropping the user if user owns it)
            conn.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))

            # 2️⃣ Drop the user
            conn.execute(text(f'DROP USER IF EXISTS "{username}"'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error Deleting Postgres tenant: {e}")
        flash(f"Error Deleting Postgres tenant: {e}", "danger")
        return None    

    # 3️⃣ Commit changes in your app database
    db.session.commit()

    # 4️⃣ Delete subscription metadata (if you manage that separately)
    delete_subscription(database_name)

    return True

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
    
    # check user limits
    limit = current_user.database_limit
    user_dbs = DatabaseInstance.query.filter_by(user_id=current_user.id).count()
    if user_dbs >= limit:
        flash(f"You have reached your database limit of {limit}. Please contact support if you need more limits. This is due to abuse", 'warning')
        return 

     # create

    tenants = {
        "postgresql":create_postgres_tenant,
        "mysql":create_mysql_tenant,
        "mongodb":create_mongodb_tenant,
        "sqlite":create_sqlite_tenant,
        "storage":create_storage,
        "firebase":create_firebase_tenant,
    }

    create = tenants[selected]
    credentials = create()

    # save cred to main db
    save_db_credentials(credentials)




    pass

def delete_database_tenant(form):

    db_id = form.get('id')

    instance = get_db_instance_by_id(db_id)
    db_type = instance.name
    logger.info(f"Deleting tenant for DB type: {db_type}")
    
    # check if user owns db
    if instance.user_id != current_user.id:
        flash('You do not own the database you are trying to delete', 'danger')
        return 


    tenants = {
        "postgresql":delete_postgres_tenant,
        "mysql":create_mysql_tenant,
        "mongodb":create_mongodb_tenant,
        "sqlite":create_sqlite_tenant,
        "firebase":create_firebase_tenant,
    }

    delete_tenant = tenants[db_type]
    credentials = delete_tenant(instance)

    # delete cred to main db
    db.session.delete(instance)
    db.session.commit()


    pass

def delete_storage_instances():
    
    if current_user.storage_instances.delete_instance():
        flash("Storage instance deleted successfully.", "success")
    else:
        flash("Error deleting storage instance.", "danger")


def get_database_instance(id):
    return DatabaseInstance.query.get(id)






def create_database(name: str):

    # create a new database instance


    # save instance env var name to main db

    # return url
    pass
    


def start_psql_session(db_instance: DatabaseInstance):
    """Start psql process for a given DatabaseInstance"""
    psql_cmd = (
        f'psql -U {db_instance.username} '
        f'-d {db_instance.database_name} '
        f'-h {HOST}'
    )

    # Copy current environment and add PGPASSWORD
    env = os.environ.copy()
    env["PGPASSWORD"] = db_instance.password

    return subprocess.Popen(
        shlex.split(psql_cmd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env
    )



def get_counts():
    user_count = MyUser.query.count()
    db_count = DatabaseInstance.query.count()
    storage_count = StorageInstance.query.count()
    return {
        "users": user_count,
        "databases": db_count,
        "storage": storage_count
    }


def get_db_uri(db_name):
    if not current_user.instances or len(current_user.instances) == 0:
        return {"status": "failed", "error": "No database instance found"}, 404

    db_instance = db_instance = next((i for i in current_user.instances if i.database_name == db_name), None)
    if not db_instance:
        return {"status": "failed", "error": "Database instance not found"}, 404

    uri = f"{db_instance.name}://{db_instance.username}:{db_instance.password}@{os.getenv('DB_HOST')}:5432/{db_instance.database_name}"
    return {"status": "ok", "uri": uri}, 200











