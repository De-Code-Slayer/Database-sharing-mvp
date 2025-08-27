from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import  current_user, login_user, logout_user, login_required
from ..utilities.auth import _login_user, register_user
from app.logger import logger
from ..forms.forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm




auth = Blueprint('auth', __name__, url_prefix='/auth')







@auth.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))
    if request.method == "POST":
        user = _login_user(request)
        if user:
            flash("Logged in successfully.", "success")
            logger.info({"event": "login", "user": user.email})
            login_user(user)
            return redirect(url_for("dashboard.home"))
   
    return  render_template("auth/login.html", form=form)

@auth.route("/register", methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))
    
    if request.method == "POST":
        if form.validate_on_submit():
            user = register_user(form)
            login_user(user)
            return redirect(url_for("dashboard.home"))
        # else:
        #     flash(f"Please correct the errors below. {form.email.errors}", "danger")
    return render_template("auth/register.html", form=form)


@auth.get("/forgot")
def forgot():
    return render_template("auth/forgot.html")

# @auth.post("/forgot")
# def forgot_post():
    # email = request.form.get("email","").strip().lower()
    # user = User.query.filter_by(email=email).first()
    # if not user:
    #     flash("If that account exists, a reset link has been generated below.", "info")
    #     return redirect(url_for("auth.forgot"))
    # token = _ts().dumps({"uid": user.id})
    # # In real life, email this. For demo, show on page.
    # reset_link = url_for("auth.reset", token=token, _external=True)
    # flash(f"Reset link: {reset_link}", "info")
    # logger.info({"event": "password_reset_requested", "user": email})
    # return redirect(url_for("auth.forgot"))


# @auth.post("/reset/<token>")
# def reset_post(token):
#     password = request.form.get("password","")
#     try:
#         data = _ts().loads(token, max_age=3600)
#         user = User.query.get(data["uid"])
#         if not user:
#             raise BadSignature("no user")
#         user.set_password(password)
#         db.session.commit()
#         flash("Password updated. Please log in.", "success")
#         logger.info({"event": "password_reset", "user": user.email})
#         return redirect(url_for("auth.login"))
#     except SignatureExpired:
#         flash("Reset link expired", "danger")
#     except BadSignature:
#         flash("Invalid reset link", "danger")
#     return redirect(url_for("auth.forgot"))

@auth.route("/logout")
@login_required
def logout():
    email = current_user.email
    logout_user()
    logger.info({"event": "logout", "user": email})
    return redirect(url_for("auth.login"))
