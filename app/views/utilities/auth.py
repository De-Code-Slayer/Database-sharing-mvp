from app.database.models import MyUser
from app.logger import logger
from flask import flash
from app import db

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


