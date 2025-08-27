import os
import shutil
from logger import logger



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
    pass
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
        "postgres":create_postgres_tenant,
        "mysql":create_mysql_tenant,
        "mongodb":create_mongodb_tenant,
        "sqlite":create_sqlite_tenant,
        "firebase":create_firebase_tenant,
    }

    create = tenants[selected]
    create()



    pass

def create_database(name: str):

    # create a new database instance


    # save instance env var name to main db

    # return url
    pass
    










