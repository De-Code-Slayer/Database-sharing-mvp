from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..forms.forms import CreateTenantForm
from ..utilities.database import create_database_tenant, delete_database_tenant
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



















