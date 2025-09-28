from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..forms.forms import CreateTenantForm
from ..utilities.database import create_database_tenant, delete_database_tenant
from ..utilities.payment import proccess_proof
from ..utilities.storage import create_storage, get_objects_by_id
from ..utilities.auth import generate_api_key

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')



@dashboard_bp.route('/')
def landing():
    return render_template("landing.html")


@dashboard_bp.route('/home')
@login_required
def home():

    form = CreateTenantForm()
    return render_template("dashboard.html", form=form)




@dashboard_bp.route("/select-db", methods=["GET", "POST"])
@login_required
def select_db():
    form = CreateTenantForm()
    if request.method == "POST":
        if form.validate_on_submit():
            if form.db_type.data == "storage":
                return redirect(url_for("dashboard.create_storage_instance"))
            else:
                create_database_tenant(form)
        else:
            flash(f"Form validation failed.{form.errors}", "danger")
    return redirect(url_for("dashboard.home"))
    

@dashboard_bp.route("/delete", methods=["POST"])
@login_required
def delete_db():
   
    if request.method == "POST":    
        delete_database_tenant(request.form)
    return redirect(url_for('dashboard.home'))


@dashboard_bp.route("/billing", methods=["GET"])
@login_required
def billing():
    
    return render_template('billing.html')


@dashboard_bp.route("/submit-proof", methods=["POST"])
def submit_proof():
    if request.method == "POST":
        # handle file upload and save proof of payment
        proccess_proof(request)
        return redirect(url_for("dashboard.billing"))
    return redirect(url_for("dashboard.billing"))

@dashboard_bp.get("/storage/create")
def create_storage_instance():
   create_storage()
   return redirect(url_for("dashboard.home"))

@dashboard_bp.route("/storage/<int:storage_id>")
@login_required
def view_storage(storage_id):
    files = get_objects_by_id(storage_id)
    return render_template("view_storage.html", files=files)

@dashboard_bp.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@dashboard_bp.route("/2fa")
@login_required
def two_fa():
    return render_template("2fa.html")

@dashboard_bp.post("/create-api-key")
@login_required
def create_api_key():

    generate_api_key()
    return redirect(url_for("dashboard.settings"))













