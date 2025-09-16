from flask import Blueprint, request, abort, send_from_directory
from ..utilities.storage import upload_file





api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/status', methods=['GET'])
def status():
    return {"status": "API is running"}, 200    


@api_bp.post("/upload/", methods=["POST"])
def save_object():
    # handle file upload and save object metadata
    return upload_file(request)
    




