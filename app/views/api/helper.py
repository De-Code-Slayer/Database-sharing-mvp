from functools import wraps
from flask import request, jsonify
from flask_login import current_user, login_user
from ..utilities.auth import api_key_auth

def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_authenticated:
            # already logged in via session (web UI)
            return f(*args, **kwargs)

        user = api_key_auth()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        # Log the user in for this request only
        login_user(user, remember=False, force=True)

        return f(*args, **kwargs)
    return decorated