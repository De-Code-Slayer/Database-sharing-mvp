from app.database.models import Subscription, Plan, Invoice, PaymentProof
from flask import flash
from app.database.firebase import bucket
from flask_login import current_user
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from app import db


UPLOAD_FOLDER = "static/uploads/proofs"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS




def create_subscription(plan,name):
 # find the database plan
    db_plan = Plan.query.filter_by(name=plan).first()

    # create a subscription (postpaid by default)
    sub = Subscription(
        user_id=current_user.id,
        plan_id=db_plan.id,
        sub_for=name,
        start_date=date.today(),
        billing_type="postpaid"
    )
    db.session.add(sub)
    db.session.commit()
    

    return sub

def generate_monthly_invoices():
    today = date.today()
    first_day = date(today.year, today.month, 1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    active_subs = Subscription.query.filter_by(billing_type="postpaid", status="active").all()

    for sub in active_subs:
        plan = sub.plan

        # create invoice for the month
        invoice = Invoice(
            user_id=sub.user_id,
            subscription_id=sub.id,
            amount=plan.price,
            status="unpaid",
            period_start=first_day,
            period_end=last_day
        )
        db.session.add(invoice)

    db.session.commit()

def prepaid_subscription(plan,name, months_paid):
    db_plan = Plan.query.filter_by(name=plan).first()

    start = date.today()
    end = start + timedelta(days=30 * months_paid)
     

    sub = Subscription.query.filter_by(sub_for=name).first()
    if sub:
        if isinstance(sub.end_date, str):
            sub.end_date = datetime.strptime(sub.end_date, "%Y-%m-%d").date()
        # Update existing subscription
    
        sub.end_date = sub.end_date + timedelta(days=30 * months_paid)
        sub.billing_type = "prepaid"

    else:

        sub = Subscription(
            user_id=current_user.id,
            plan_id=db_plan.id,
            sub_for=name,
            start_date=start,
            end_date=start + timedelta(days=30 * months_paid),
            billing_type="prepaid"
        )
        db.session.add(sub)

    # Create a paid invoice immediately
    invoice = Invoice(
        user_id=current_user.id,
        subscription_id=sub.id,
        amount=db_plan.price * months_paid,
        status="paid",
        period_start=start,
        period_end=end
    )
    db.session.add(invoice)
    db.session.commit()

    return sub, invoice

def proccess_proof(request, invoice_id):
    file = request.files["screenshot"]
    tx_hash = request.form.get("tx_hash")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # save in bucket and reveal public url
        blob = bucket.blob(f"proofs/{current_user.id}/{filename}")
        blob.upload_from_file(file)
        blob.make_public()
        filepath = blob.public_url
    

        proof = PaymentProof(
            invoice_id=invoice_id,
            user_id=current_user.id,
            tx_hash=tx_hash,
            screenshot_url=filepath,
        )
        db.session.add(proof)
        db.session.commit()

        flash("Proof of payment submitted successfully.", "success")

        return proof







