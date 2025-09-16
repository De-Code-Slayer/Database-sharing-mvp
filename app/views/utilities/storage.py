from werkzeug.utils import secure_filename
from app import db, engine
from flask_login import current_user
from flask import flash
from ...database.models import StorageInstance,Objects
import os


STORAGE_ROOT = os.getenv("STORAGE_ROOT", "storage")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "docx", "xlsx", "txt", "zip", "rar", "mp4", "mp3", "avi", "mkv", "mov", "wmv", "flv", "webm", "csv", "json", "xml", "html", "css", "js"}



def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_metadata(filename, file_url, size, mime_type):
    new_file = Objects(
        user_id=current_user.id,
        storage_id=current_user.storage_instances.id,
        filename=filename,
        furl=file_url,
        size=size,
        mime_type=mime_type
    )
    db.session.add(new_file)
    db.session.commit()
    return new_file.id


def upload_file(request):
    if "file" not in request.files:
        return {"status":"failed", "error": "No file provided"}, 400

    try:
        file = request.files["file"]
        filename = secure_filename(file.filename)

        # Create user-specific folder if not exists
        user_dir = current_user.storage_instances.folder_path
        os.makedirs(user_dir, exist_ok=True)

        # Save file
        path = os.path.join(user_dir, filename)
        file.save(path)

        # Save metadata
        file_url = f"{user_dir}/{filename}"
        size = os.path.getsize(path)
        mime_type = file.mimetype

        file_id = save_metadata(filename, file_url, size, mime_type)
    except Exception as e:
        return {"status":"failed", "error": str(e)}, 500
    
    return {"status": "ok", "file_id": file_id, "url": file_url}


def create_storage():
    if current_user.storage_instances:
           flash("Storage instance already exists.", "warning")
           return
    
        # Create user-specific folder
    storage = StorageInstance(
    user_id=current_user.id,
    folder_path=f"{STORAGE_ROOT}/user_{current_user.id}",
    quota=2 * 1024 * 1024 * 1024  # 2GB
                                )
    
    db.session.add(storage)
    db.session.commit()
    flash("Storage instance created successfully.", "success")
    return storage










