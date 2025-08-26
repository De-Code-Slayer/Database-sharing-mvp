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


def create_database():
    data = request.json
    name = data.get("name")
    uri = f"sqlite:///{name}.db"  # for demo
    db_instance = DatabaseInstance(name=name, uri=uri)
    db.session.add(db_instance)
    db.session.commit()










