from app.database.models import Subscription, Plan, Invoice, PaymentProof, Payment
from flask import flash, url_for, jsonify
from app.database.firebase import bucket
from flask_login import current_user
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from app import db
import secrets
import requests
import os
from app.logger import logger
import logging


UPLOAD_FOLDER = "static/uploads/proofs"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}


PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_INIT_URL = "https://api.paystack.co/transaction/initialize"
PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/"



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
        end_date = date.today() + timedelta(days=30),
        billing_type="postpaid"
    )
    db.session.add(sub)
    db.session.commit()
    

    return sub

def delete_subscription(database_name):
    # find the database sub
    db_plan = Subscription.query.filter_by(sub_for=database_name).first()

    if db_plan:  # Only delete if it exists
        db.session.delete(db_plan)
        db.session.commit()
    else:
        logger.warning(f"No subscription found for database {database_name}")
        raise ValueError(f"No subscription found for database {database_name}")

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

def proccess_proof(request):
    invoice_id = request.form.get('invoice-id')
    subscription_id = request.form.get('subscription-id')
    file = request.files["proof"]
    tx_hash = request.form.get("tx_hash")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # save in bucket and reveal public url
        blob = bucket.blob(f"proofs/{current_user.id}/{filename}")
        blob.upload_from_file(file)
        blob.make_public()
        filepath = blob.public_url
    

        proof = PaymentProof(
            user_id=current_user.id,
            invoice_id = invoice_id,
            subscription_id = subscription_id,
            tx_hash=tx_hash,
            screenshot_url=filepath,
        )

        

        db.session.add(proof)
        db.session.commit()

        flash("Proof of payment submitted successfully.", "success")

        return proof

def pay_invoice(invoice_id):
    invoice = get_invoice(invoice_id)
    if not invoice:
        return None

    if invoice.status == "paid":
        flash("Invoice is already paid.", "info")
        return None

    # Mark invoice as paid
    invoice.status = "paid"
    db.session.commit()

    # update subscription end date if postpaid
    sub = invoice.subscription
    if sub.billing_type == "postpaid":
        if isinstance(sub.end_date, str):
            sub.end_date = datetime.strptime(sub.end_date, "%Y-%m-%d").date()
        sub.end_date = sub.end_date + timedelta(days=30)
        db.session.commit()

    flash("Invoice paid successfully.", "success")
    return invoice

def get_subscription(sub_id):
    sub = Subscription.query.get(sub_id)
    if not sub:
        flash("Subscription does not exist.", "danger")
        return None
    if sub.user_id != current_user.id:
        flash("You are not authorized to view this subscription.", "danger")
        return None
    return sub

def get_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        flash("Invoice does not exist.", "danger")
        return None
    if invoice.user_id != current_user.id:
        flash("You are not authorized to view this invoice.", "danger")
        return None
    return invoice

def get_payment(payment_reference):
    payment = Payment.query.filter_by(reference=payment_reference).first()
    if not payment:
        flash("Payment record does not exist.", "danger")
        return None
    if payment.user_id != current_user.id:
        flash("You are not authorized to view this payment record.", "danger")
        return None
    return payment

def proccess_payment(invoice_id):
    
    invoice = get_invoice(invoice_id)
    reference = secrets.token_hex(8)
    payment = Payment(invoice_id=invoice.id, reference=reference, amount=invoice.amount, user_id=invoice.user_id)
    db.session.add(payment)
    db.session.commit()

    payload = {
        "email": invoice.user.email,
        "amount": int(invoice.amount * 100),
        "reference": reference,
        "callback_url": url_for("payment.verify_payment", reference=reference, _external=True)
    }

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    response = requests.post(PAYSTACK_INIT_URL, json=payload, headers=headers).json()
    return response

def paystack_verify_payment(reference):

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    response = requests.get(PAYSTACK_VERIFY_URL + reference, headers=headers).json()

    payment = get_payment(reference)
    if not payment:
        flash("Payment record not found.", "danger")
        return False

    if response["data"]["status"] == "success":
        payment.status = "success"
        payment.invoice.status = "paid"
        db.session.commit()
        flash("Payment successful!", "success")
        pay_invoice(payment.invoice_id)
    else:
        payment.status = "failed"
        db.session.commit()
        flash("Payment failed or incomplete.", "warning")

def verify_amount_naira(amount):
    try:
        amount = int(amount)
        if amount <= 0:
            flash("Amount must be positive.", "danger")
            raise ValueError("Amount must be positive.")
        
        # convert to naira
        amount = (amount * 1450)  # Example conversion rate

        
        return amount
    except ValueError:
        return None

def proccess_extension(sub_id, duration_months):
    reference = secrets.token_hex(8)
    sub = get_subscription(sub_id)
    amount = verify_amount_naira(sub.plan.price * duration_months)
    if not sub:
        return None
    payment = Payment(subscription_id=sub.id, reference=reference, amount=amount, user_id=sub.user_id)
    db.session.add(payment)
    db.session.commit()
    payload = {
        "email": sub.user.email,
        "amount": int(amount * 100),
        "reference": reference,
        "callback_url": url_for("payment.verify_payment_ext", reference=reference, _external=True)
    }
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    response = requests.post(PAYSTACK_INIT_URL, json=payload, headers=headers).json()
    return response





def process_intent(amount, email):
        
     try:   
        # Paystack API endpoint to initialize the transaction
        url = 'https://api.paystack.co/transaction/initialize'
        
        # Headers for authorization
        headers = {
            'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        print(headers)
        # Data to send to Paystack
        data = {
            'email': email,
            'amount': amount,
        }
        
        # Make the request to Paystack API
        response = requests.post(url, json=data, headers=headers)
        
        # Check if the request was successful
        print(response.json())
        if response.status_code == 200:
            payment_data = response.json()
            reference = payment_data['data']['reference']
            
            # Send the payment reference and amount to the client-side
            return jsonify({
                'reference': reference,
                'email': email,
                'amount': amount
            })
        else:
            return jsonify({'error': 'Payment initialization failed'}), 500
     except Exception as e:
        logging.error({'error':e})
        return jsonify({'error': 'Payment initialization failed'}), 500













