from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import timedelta, date, datetime
from app import db
from ..forms.forms import CreateTenantForm
from ..utilities.database import create_database_tenant, delete_database_tenant, delete_storage_instances
from ..utilities.payment import proccess_proof
from ..utilities.storage import create_storage, get_objects_by_id
from ..utilities.auth import generate_api_key, revoke
from ..utilities.migration import migrate_database

from app.database.models import Subscription, Invoice, BillingLog

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/', subdomain="dashboard")



@dashboard_bp.route('/')
def landing():
    return render_template("landing.html")


@dashboard_bp.route('/home')
@login_required
def home():
    import os
    form = CreateTenantForm()
    return render_template("dashboard.html", form=form, host=os.getenv("DB_HOST"))




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
    today = date.today()

    invoices = current_user.invoices
    subscriptions = current_user.subscriptions

    # attach calculated due fields
    for inv in invoices:
        if inv.due_date:
            inv.days_to_due = (inv.due_date - today).days
            inv.is_overdue = inv.days_to_due < 0
        else:
            inv.days_to_due = None
            inv.is_overdue = False

    for sub in subscriptions:
        if sub.end_date:
            days_past = (today - sub.end_date).days
            sub.months_overdue = max(0, days_past // 30)
            sub.days_past_due = max(0, days_past)
        else:
            sub.months_overdue = 0
            sub.days_past_due = 0

    billing_logs = BillingLog.query.order_by(BillingLog.created_at.desc()).limit(50).all()

    return render_template('billing.html', invoices=invoices, subscriptions=subscriptions, billing_logs=billing_logs)


@dashboard_bp.route("/admin/subscriptions", methods=["GET", "POST"])
@login_required
def admin_subscriptions():
    if not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        sub_id = request.form.get("subscription_id")
        extend_months = request.form.get("extend_months")
        status = request.form.get("status")

        if sub_id:
            sub = Subscription.query.get(int(sub_id))
            if not sub:
                flash("Subscription not found.", "danger")
                return redirect(url_for('dashboard.admin_subscriptions'))

            if extend_months:
                try:
                    months = int(extend_months)
                    sub.end_date = sub.end_date + timedelta(days=30 * months)
                    sub.status = status or sub.status
                    db.session.commit()
                    flash(f"Subscription {sub.id} extended by {months} month(s).", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Unable to extend subscription: {str(e)}", "danger")

            if status and status in ["active", "suspended"]:
                sub.status = status
                db.session.commit()
                flash(f"Subscription {sub.id} status updated to {status}.", "success")

        return redirect(url_for('dashboard.admin_subscriptions'))

    subscriptions = Subscription.query.order_by(Subscription.id.desc()).all()
    today = date.today()
    for sub in subscriptions:
        if sub.start_date:
            # Calculate uptime: how long service has been running
            uptime_days = (today - sub.start_date).days
            sub.uptime_months = uptime_days // 30
            sub.uptime_days = uptime_days % 30
        else:
            sub.uptime_months = 0
            sub.uptime_days = 0
    return render_template('admin_subscriptions.html', subscriptions=subscriptions)


@dashboard_bp.route("/admin/reconcile-subscriptions", methods=["POST"])
@login_required
def reconcile_subscriptions():
    if not current_user.is_admin:
        abort(403)
    
    try:
        today = date.today()
        active_subscriptions = Subscription.query.filter_by(status="active").all()
        
        invoices_created = 0
        skipped = 0
        
        for sub in active_subscriptions:
            # Check if an invoice already exists for this subscription
            existing_invoice = Invoice.query.filter_by(subscription_id=sub.id).first()
            
            if existing_invoice:
                skipped += 1
                continue
            
            # Create new invoice for the subscription
            # Use subscription's renewal date or today as period end
            period_end = sub.end_date if sub.end_date else today
            
            # Calculate period start (roughly a month before end)
            period_start = today - timedelta(days=30) if not sub.end_date else (sub.end_date - timedelta(days=30))
            
            new_invoice = Invoice(
                user_id=sub.user_id,
                subscription_id=sub.id,
                amount=sub.plan.price if sub.plan else 0,
                status="unpaid",
                period_start=period_start,
                period_end=period_end,
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_invoice)
            invoices_created += 1
        
        db.session.commit()
        flash(f"Reconciliation complete: {invoices_created} invoice(s) created, {skipped} subscription(s) already have invoice(s).", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Reconciliation failed: {str(e)}", "danger")
    
    return redirect(url_for('dashboard.admin_subscriptions'))


@dashboard_bp.route("/admin/unpaid-invoices", methods=["GET"])
@login_required
def admin_unpaid_invoices():
    if not current_user.is_admin:
        abort(403)
    
    # Get all unpaid invoices with related data
    unpaid_invoices = Invoice.query.filter_by(status="unpaid").order_by(Invoice.period_end.asc()).all()
    today = date.today()
    
    for invoice in unpaid_invoices:
        if invoice.period_end:
            days_overdue = (today - invoice.period_end).days
            invoice.days_overdue = max(0, days_overdue)
        else:
            invoice.days_overdue = 0
    
    return render_template('admin_unpaid_invoices.html', invoices=unpaid_invoices)


@dashboard_bp.route("/admin/send-custom-email/<int:sub_id>", methods=["POST"])
@login_required
def send_custom_email(sub_id):
    if not current_user.is_admin:
        abort(403)
    
    sub = Subscription.query.get_or_404(sub_id)
    custom_text = request.form.get("custom_text")
    
    if not custom_text:
        flash("Custom text is required", "danger")
        return redirect(url_for('dashboard.admin_subscriptions'))
    
    from ..utilities.smtp import send_mail
    success = send_mail(
        to_email=sub.user.email,
        subject="Custom Message from SmallShardz Admin",
        body=custom_text
    )
    
    if success:
        flash(f"Custom email sent to {sub.user.email}", "success")
    else:
        flash("Failed to send email", "danger")
    
    return redirect(url_for('dashboard.admin_subscriptions'))


@dashboard_bp.route("/admin/send-invoice-email/<int:user_id>", methods=["POST"])
@login_required
def send_invoice_email(user_id):
    if not current_user.is_admin:
        abort(403)
    
    from app.database.models import MyUser
    user = MyUser.query.get_or_404(user_id)
    
    # Get unpaid invoices for this user
    unpaid_invoices = Invoice.query.filter_by(user_id=user_id, status="unpaid").all()
    
    if not unpaid_invoices:
        flash("No unpaid invoices for this user", "warning")
        return redirect(url_for('dashboard.admin_unpaid_invoices'))
    
    
    
    # Calculate total amount owed (for each Calculate total amount owed (invoice amount × full months overdue, derived from days overdue ÷ 30, rounded down)
    today = date.today()
    total_amount = sum(
    inv.amount * ((today - inv.period_end).days // 30)
    for inv in unpaid_invoices
    if inv.period_end and (today - inv.period_end).days > 0
)
    
    from ..utilities.smtp import send_mail
    success = send_mail(
        to_email=user.email,
        subject="Payment Reminder - Unpaid Invoices",
        template="invoice",
        template_vars={
            "id": f"INVOICE-{user_id}",
            "period_start": min(inv.period_start for inv in unpaid_invoices),
            "period_end": max(inv.period_end for inv in unpaid_invoices),
            "status": "unpaid",
            "amount": total_amount,
            "description": f"Total amount due for {len(unpaid_invoices)} unpaid invoice(s)"
        }
    )
    
    if success:
        flash(f"Invoice reminder sent to {user.email}", "success")
    else:
        flash("Failed to send invoice email", "danger")
    
    return redirect(url_for('dashboard.admin_unpaid_invoices'))


@dashboard_bp.route("/submit-proof", methods=["POST"])
def submit_proof():
    if request.method == "POST":
        # handle file upload and save proof of payment
        proccess_proof(request)
        return redirect(url_for("dashboard.billing"))
    return redirect(url_for("dashboard.billing"))

@dashboard_bp.get("/instance/storage/create")
def create_storage_instance():
   create_storage()
   return redirect(url_for("dashboard.home"))

@dashboard_bp.post("/instance/database/migrate")
def migrate_database_instance():
    # handle idempotency at a higher level if needed



    return migrate_database(request.get_json())
    

@dashboard_bp.route("/instance/storage/<int:storage_id>")
@login_required
def view_storage(storage_id):
    files = get_objects_by_id(storage_id)
    return render_template("view_storage.html", files=files)

@dashboard_bp.post("/delete/instance")
@login_required
def delete_storage_instance():
    delete_storage_instances()
    return redirect(url_for("dashboard.home"))
    


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

@dashboard_bp.route("/revoke/api-key/<int:key_id>")
@login_required
def revoke_api_key(key_id):
    revoke(key_id)
    return redirect(url_for("dashboard.settings"))

@dashboard_bp.route("/api/docs")
@login_required
def api_docs():
    
    return render_template("api-docs2.html")










