from app.database.models import MyUser, ApiKey
import os
from app.logger import logger
from flask import flash, url_for, request
import hashlib
from flask_login import current_user
from app import db
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from .smtp import send_password_reset_email, send_welcome_email

def _ts():
    return URLSafeTimedSerializer(os.getenv("SECRET_KEY"), salt="iTzComPlic-atedToDAy")

def _login_user(request):
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user = MyUser.query.filter_by(email=email).first()

    # 1️⃣ No user found
    if not user:
        flash("Invalid credentials", "danger")
        return False

    # 2️⃣ No authentication method set
    if not user.authentication_method:
        flash("This account has no authentication method configured.", "warning")
        return False

    # 3️⃣ If the user uses an external auth method (e.g., Google, GitHub)
    if user.authentication_method != "Email/Password":
        flash(f"Please log in using {user.authentication_method}.", "info")
        return user

    # 4️⃣ If using Email/Password, verify password
    if not user.check_password(password):
        flash("Invalid credentials", "danger")
        return False

    # 5️⃣ Success
    return user

def get_user_by_email(email):
    return MyUser.query.filter_by(email=email).first()

def register_user(form):
    email = form.email.data.strip().lower()
    password = form.password.data
    username = form.username.data.strip()
    if MyUser.query.filter_by(email=email).first():
        flash("Email already registered", "warning")
        return False
    user = MyUser(email=email, username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Send welcome email
    send_welcome_email(user.email, user.username)

    logger.info({"event": "register", "user": email})
    return user

def create_user(email,username,method="Google"): 
        user = MyUser(email=email, username=username, authentication_method=method)
        db.session.add(user)
        db.session.commit()
        return user


def reset_link(request):
    email = request.form.get("email","").strip().lower()
    user = MyUser.query.filter_by(email=email).first()
    if not user:
        flash("If that account exists, a reset link has been sent.", "info")
        return

    token = _ts().dumps({"uid": user.id})

    # Send password reset email
    email_sent = send_password_reset_email(
        user_email=email,
        reset_token=token,
        username=user.username
    )

    if email_sent:
        flash("Password reset link has been sent to your email.", "success")
        logger.info({"event": "password_reset_requested", "user": email, "email_sent": True})
    else:
        flash("Failed to send reset email. Please try again later.", "danger")
        logger.error({"event": "password_reset_requested", "user": email, "email_sent": False})
        # Don't raise exception - just log the error and return
    return user



def reset_password(request,token):
    password = request.form.get("password","")
    try:
        data = _ts().loads(token, max_age=3600)
        user = MyUser.query.get(data["uid"])
        if not user:
            raise BadSignature("no user")
        user.set_password(password)
        db.session.commit()
        flash("Password updated. Please log in.", "success")
        logger.info({"event": "password_reset", "user": user.email})
        return True
    except SignatureExpired:
        flash("Reset link expired", "danger")
    except BadSignature:
        flash("Invalid reset link", "danger")


def verify_token(token):
    """Verify password reset token and return user if valid"""
    try:
        data = _ts().loads(token, max_age=3600)
        user = MyUser.query.get(data["uid"])
        if not user:
            raise BadSignature("no user")
        return user
    except (SignatureExpired, BadSignature):
        return None


def generate_api_key():
    api_key = ApiKey.generate_for_user(current_user.id)
    flash("API key generated", "success")
    flash(f"Your new API key: {api_key} . Please copy it now. You won't see it again!", "info")
    logger.info({"event": "api_key_created", "user": current_user.email})
    return api_key

def api_key_auth():
    """Authenticate API key from Authorization header and set current_user"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning({"event": "api_key_missing", "detail": "No Authorization header"})
        return None

    raw_key = auth_header.split(" ")[1]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key = ApiKey.query.filter_by(key_hash=key_hash, revoked=False).first()

    if api_key:
        return api_key.user
    return None

def revoke(key_id):
    
    api_key = next((i for i in current_user.api_key if i.id == key_id), None)
    if api_key:
        api_key.revoke()
        flash("API key revoked", "success")
        logger.info({"event": "api_key_revoked", "user": current_user.email, "key_id": key_id})
    else:
        flash("API key not found", "warning")














