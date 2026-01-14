from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import  current_user, login_user, logout_user, login_required
from ..utilities.auth import _login_user, register_user, reset_link, reset_password, verify_token, get_user_by_email, create_user
from app.logger import logger
from ..forms.forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from app import oauth
import os



auth = Blueprint('auth', __name__, url_prefix='/auth', subdomain="auth")

# Google OAuth
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    access_token_params=None,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    authorize_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v2/",
    client_kwargs={"scope": "openid email profile"},
)

# GitHub OAuth
github = oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)





@auth.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))
    if request.method == "POST":
        user = _login_user(request) #returns user or None
        if user:
            login_user(user)
            logger.info({"event": "login", "user": user.email})
            flash("Logged in successfully.", "success")
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
            if not user:
                flash("Account with this email already exist, login instead?.", "danger")
                return redirect(url_for("auth.register"))
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
    # Verify token before allowing password reset
    if not verify_token(token):
        flash("Invalid or expired reset link", "danger")
        return redirect(url_for("auth.forgot"))

    if request.method == "POST":
        if reset_password(request,token):
            return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", token=token)

@auth.route("/logout")
# @login_required
def logout():
    email = current_user.email
    logout_user()
    logger.info({"event": "logout", "user": email})
    return redirect(url_for("auth.login"))




@auth.route("/login/google")
def login_google():
    redirect_uri = url_for("auth.authorize_google", _external=True)
    return google.authorize_redirect(redirect_uri)

@auth.route("/authorize/google")
def authorize_google():
    token = google.authorize_access_token()
    resp = google.get("userinfo").json()
    email = resp["email"]
    username = resp.get("name") or email.split("@")[0]

    user = get_user_by_email(email)
    if not user:
       user =  create_user(email,username)

    login_user(user)
    return redirect(url_for("dashboard.home"))


@auth.route("/login/github")
def login_github():
    redirect_uri = url_for("auth.authorize_github", _external=True)
    return github.authorize_redirect(redirect_uri)

@auth.route("/authorize/github")
def authorize_github():
    token = github.authorize_access_token()
    resp = github.get("user").json()

    email = resp.get("email")
    if not email:
        # GitHub sometimes hides email — get primary email
        emails = github.get("user/emails").json()
        email = next((e["email"] for e in emails if e["primary"]), None)

    username = resp["login"]

    user = get_user_by_email(email)
    if not user:
        user = create_user(email, username, method="GitHub")

    login_user(user)
    return redirect(url_for("dashboard.home"))
