
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from ..utilities.payment import proccess_payment, paystack_verify_payment,paystack_verify_payment_ext, proccess_extension, process_intent, prepaid_subscription
from app.logger import logger



payment_bp = Blueprint('payment', __name__, url_prefix='/pay', subdomain="dashboard")

@payment_bp.route("/pay_invoice/<int:invoice_id>")
@login_required
def pay_invoice(invoice_id):
    response = proccess_payment(invoice_id)
    logger.info(f"Payment initiation response: {response}")
    if response.get("status"):
        return redirect(response["data"]["authorization_url"])
    else:
        flash("Payment initialization failed.", "danger")
        return redirect(url_for("dashboard.billing"))

@payment_bp.route("/verify_payment/<reference>")
def verify_payment(reference):
     if paystack_verify_payment(reference):
        flash("Payment successful!", "success")
     return redirect(url_for("dashboard.billing"))

@payment_bp.route("/ext/<plan>/<name>/<months>/verify_payment/<reference>")
def verify_payment_ext(plan,name,months,reference):
     if paystack_verify_payment_ext(reference):
        flash("Payment successful!", "success")       
        prepaid_subscription(plan,name,months)
     return redirect(url_for("dashboard.billing"))

@payment_bp.route("/extend/<int:sub_id>/<int:duration_months>")
@login_required
def extend(sub_id,duration_months):
    response = proccess_extension(sub_id,duration_months)
    logger.info(f"Payment initiation response: {response}")
    if response.get("status"):
        return redirect(response["data"]["authorization_url"])
    else:
        flash("Payment initialization failed.", "danger")
        return redirect(url_for("dashboard.billing"))

@payment_bp.route("/intent/paystack", methods=["POST"])
@login_required
def create_payment_intent():
    return process_intent(request.get_json().get('amount'), request.get_json().get('email'))


@payment_bp.route("/api/verify_payment/<reference>", methods=["GET"])
@login_required
def verify_payment_intent(reference):
    return verify_payment

   









