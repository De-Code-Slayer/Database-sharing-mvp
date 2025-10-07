from flask import Blueprint, request, abort, send_from_directory, jsonify
from ..utilities.storage import upload_file
from ..utilities.database import get_counts, get_db_uri
from .helper import api_login_required





api_bp = Blueprint('api', __name__, subdomain='api')

@api_bp.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "ok",
        "message": "API is running"
    }, 200    )


@api_bp.post("/upload")
@api_login_required
def save_object():
    return jsonify(upload_file(request))

@api_bp.get("/database/uri/<db_name>")
@api_login_required
def db_uri(db_name):
    return jsonify(get_db_uri(db_name))


@api_bp.get('/stats')
def stats():
    
    return jsonify(get_counts())
    




