from flask import Blueprint
from ..utilities.storage import upload_file





api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/status', methods=['GET'])
def status():
    return {"status": "API is running"}, 200    


@api_bp.route("/upload/<int:user_id>", methods=["POST"])
def save_object(user_id):
    # handle file upload and save object metadata
    pass






