from werkzeug.utils import secure_filename
from app import db, engine
from flask_login import current_user
from flask import flash
from ...database.models import StorageInstance,Objects
from .payment import create_subscription
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
        url=file_url,
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

        instance = current_user.storage_instances

        # Create user-specific folder if not exists
        user_dir = current_user.storage_instances.folder_path
        os.makedirs(user_dir, exist_ok=True)

        path = os.path.join(user_dir, filename)

        # Get uploaded file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        # Get existing file size (if file already exists)
        old_size = os.path.getsize(path) if os.path.exists(path) else 0

        # Calculate new used space after replacement
        new_used_space = instance.used_space - old_size + size

        # Check quota BEFORE saving
        if new_used_space > instance.quota:
            return {"status":"failed", "error": "Storage quota exceeded"}, 400

        # Save file
        file.save(path)

        # Save metadata
        file_url = f"{user_dir}/{filename}"
        mime_type = file.mimetype
        file_id = save_metadata(filename, file_url, size, mime_type)

        # Update quota
        instance.used_space = new_used_space
        db.session.commit()

    except Exception as e:
        return {"status":"failed", "error": str(e)}, 500

    return {"status": "ok", "file_id": file_id, "url": file_url}


def create_storage():
    if current_user.storage_instances:
           flash("Storage instance already exists.", "warning")
           return
    

        # Create user-specific folder
    name = f"storage_user_{current_user.id}"
    storage = StorageInstance(
    name=name,
    user_id=current_user.id,
    folder_path=f"{STORAGE_ROOT}/user_{current_user.id}",
    quota=2 * 1024 * 1024 * 1024  # 2GB
                                )
    
    db.session.add(storage)
    db.session.commit()
    flash("Storage instance created successfully.", "success")

    # create subscription
    create_subscription("storage", name)
    return storage


def get_objects_by_id(storage_id):
    storage = StorageInstance.query.filter_by(id=storage_id, user_id=current_user.id).first()
    if not storage:
        flash("Storage instance not found.", "danger")
        return []
    
    files = Objects.query.filter_by(storage_id=storage.id).all()
    return files







