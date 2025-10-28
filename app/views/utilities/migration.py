
from app.database.models import MigrationRecord,DatabaseInstance
from app import db
from flask import flash
from flask_login import current_user
import os
import logging
import subprocess
import tempfile
import datetime
import shutil

import subprocess

def get_instance(instance_id):
    return DatabaseInstance.query.filter_by(id=instance_id, user_id=current_user.id).first()


def detect_instance_type(instance):
   return instance.name 

def migrate_database(req_data):
    instance_id = req_data.get("instance_id") if req_data else None
    source_url = req_data.get("source_url") if req_data else None
    dest_url = req_data.get("dest_url") if req_data else None

    database = {
        "postgresql":migrate_postgres,
        "mysql":migrate_mysql
    }

    # get database instance
    instance = get_instance(instance_id)

    # get database type
    db_type = detect_instance_type(instance)

    # migrate_db
    if db_type in database:
       return database[db_type](source_url, dest_url)
    
    return {"status":"failed","error":"Unsupported database type"}
  


def migrate_postgres(source_url, dest_url):
    user_id = current_user.id
    """
    Migration procedure (Postgres-focused):
      ✅ Create a compressed dump of the source DB (pg_dump -Fc)
      ✅ Create a snapshot (backup) of the destination DB BEFORE overwriting
      ✅ Restore source dump into destination using pg_restore
      ✅ On failure, attempt to restore destination snapshot
      ✅ Clean up temp files on success
    """

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    temp_dir = tempfile.mkdtemp(prefix=f"migration_{user_id}_")

    snapshot_path = os.path.join(temp_dir, f"dest_snapshot_{timestamp}.dump")
    dump_path = os.path.join(temp_dir, f"source_dump_{timestamp}.dump")

    try:


        PG_DUMP = shutil.which("pg_dump") or "/usr/bin/pg_dump"
        PG_RESTORE = shutil.which("pg_restore") or "/usr/bin/pg_restore"


        print("📦 Step 1: Creating snapshot of destination database...")
        snapshot_cmd = [
            PG_DUMP,
            "-Fc",             # Custom format (compressed)
            "-f", snapshot_path,
            dest_url
        ]
        subprocess.check_call(snapshot_cmd)
        print(f"✅ Destination snapshot saved: {snapshot_path}")

        print("🚀 Step 2: Creating compressed dump of source database...")
        dump_cmd = [
            PG_DUMP,
            "-Fc",
            "-f", dump_path,
            source_url
        ]
        subprocess.check_call(dump_cmd)
        print(f"✅ Source dump saved: {dump_path}")

        print("⚙️ Step 3: Restoring source dump into destination...")
        restore_cmd = [
            PG_RESTORE,
            "--clean",          # Drop existing objects before recreating
            "--if-exists",      # Avoid failing if object doesn’t exist
            "--no-owner",       # Avoid role mismatches
            "-d", dest_url,
            dump_path
        ]

        subprocess.check_call(restore_cmd)
        print("✅ Migration successful.")

        # Clean up dump after success
        if os.path.exists(dump_path):
            os.remove(dump_path)
        # Optional: Keep snapshot for X hours or delete immediately
        print("🧹 Cleaning temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)

        return {"status": "success", "snapshot": snapshot_path}

    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}. Rolling back...")
        logging.error(f"Migration failed for user {user_id}: {e}")
        flash("Migration failed. Attempting rollback...", "danger")

        # Attempt rollback
        try:
            restore_snapshot_cmd = [
                PG_RESTORE,
                "--clean",
                "--if-exists",
                "--no-owner",
                "-d", dest_url,
                snapshot_path
            ]
            subprocess.check_call(restore_snapshot_cmd)
            print("🔁 Rollback completed successfully.")
            logging.info(f"Migration failed for user {user_id}, but rollback succeeded.")
            flash("Migration failed, but rollback succeeded.", "warning")
            return {"status": "rolled_back", "error": str(e)}
        except subprocess.CalledProcessError as rollback_err:
            print(f"⚠️ Rollback failed: {rollback_err}")
            logging.error(f"Critical: Migration and rollback both failed for user {user_id}. Manual intervention required.")
            flash("danger","Critical: Migration and rollback both failed. Manual intervention required.", "danger")
            return {
                "status": "failed",
                "error": str(e),
                "rollback_error": str(rollback_err)
            }
        

    finally:
        # If any files remain, clean up at the end
        if os.path.exists(dump_path):
            os.remove(dump_path)
        # You can choose to keep snapshot for 24h by skipping delete here
        shutil.rmtree(temp_dir, ignore_errors=True)
        


def migrate_mysql(source_url, dest_url):
    
    dump = subprocess.Popen(['mysqldump', source_url], stdout=subprocess.PIPE)
    restore = subprocess.Popen(['mysql', dest_url], stdin=dump.stdout)
    dump.stdout.close()
    restore.communicate()

