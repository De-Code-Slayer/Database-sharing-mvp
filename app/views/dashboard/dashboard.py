from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from ..forms.forms import CreateTenantForm
from ..utilities.database import create_database_tenant

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
    return redirect(url_for("dashboard.home"))
    
