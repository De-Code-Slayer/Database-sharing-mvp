from flask import Blueprint, request, abort, send_from_directory
from ..utilities.storage import upload_file
from .helper import api_login_required





api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/status', methods=['GET'])
def status():
    return {"status": True}, 200    


@api_bp.post("/upload")
@api_login_required
def save_object():
    return upload_file(request)
    




