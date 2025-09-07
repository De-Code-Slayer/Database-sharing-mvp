from app.database.models import MyUser
import os
from app.logger import logger
from flask import flash, url_for
from app import db
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

def _ts():
    return URLSafeTimedSerializer(os.getenv("SECRET_KEY"), salt="iTzComPlic-atedToDAy")

def _login_user(request):
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user = MyUser.query.filter_by(email=email).first()

    
    if not user or not user.check_password(password):
            flash("Invalid credentials", "danger")
            return False
    return user


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
    logger.info({"event": "register", "user": email})
    return user


def reset_link(request):
    email = request.form.get("email","").strip().lower()
    user = MyUser.query.filter_by(email=email).first()
    if not user:
        flash("If that account exists, a reset link has been generated below.", "info")
    token = _ts().dumps({"uid": user.id})
    # In real life, email this. For demo, show on page.
    reset_link = url_for("auth.reset_post", token=token, _external=True)
    flash(f"Reset link: {reset_link}", "info")
    logger.info({"event": "password_reset_requested", "user": email})

def verify_token(token):
        data = _ts().loads(token, max_age=3600)
        user = MyUser.query.get(data["uid"])
        if not user:
            raise BadSignature("no user")
        else:
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

















