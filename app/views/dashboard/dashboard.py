from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..forms.forms import CreateTenantForm
from ..utilities.database import create_database_tenant
from ..utilities.payment import proccess_proof

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')




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
            create_database_tenant(form)
        else:
            flash(f"Form validation failed.{form.errors}", "danger")
    return redirect(url_for("dashboard.home"))
    

@dashboard_bp.route("/submit-proof/<int:invoice_id>", methods=["GET", "POST"])
def submit_proof(invoice_id):
    if request.method == "POST":
        # handle file upload and save proof of payment
        proccess_proof(request, invoice_id)
        return redirect(url_for("dashboard.submit_proof", invoice_id=invoice_id))
    return redirect(url_for("dashboard.home"))



















