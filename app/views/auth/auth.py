from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import  current_user, login_user, logout_user, login_required
from ..utilities.auth import _login_user, register_user, reset_link, reset_password, verify_token
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

@auth.post("/forgot")
def forgot_post():
    reset_link(request)
    return redirect(url_for("auth.forgot"))


@auth.route("/reset/<token>", methods=["GET","POST"])
def reset_post(token):
    # verify token
    if not verify_token(token):
        return(request.referrer)
    if request.method == "POST":
        if reset_password(request,token):
            return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", token=token)

@auth.route("/logout")
@login_required
def logout():
    email = current_user.email
    logout_user()
    logger.info({"event": "logout", "user": email})
    return redirect(url_for("auth.login"))
