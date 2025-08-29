from datetime import date, timedelta, datetime
from app import db
from app.database.models import Subscription, Invoice, Plan, BillingLog


def log_action(action, details=""):
    """Helper to log billing actions"""
    log = BillingLog(action=action, details=details)
    db.session.add(log)


def create_invoices():
    """Create invoices for active postpaid subscriptions"""
    today = date.today()
    first_day = date(today.year, today.month, 1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    subs = Subscription.query.filter_by(billing_type="postpaid", status="active").all()
    for sub in subs:
        plan = Plan.query.get(sub.plan_id)

        existing = Invoice.query.filter_by(
            subscription_id=sub.id,
            period_start=first_day,
            period_end=last_day
        ).first()
        if existing:
            continue

        invoice = Invoice(
            user_id=sub.user_id,
            subscription_id=sub.id,
            amount=plan.price,
            status="unpaid",
            period_start=first_day,
            period_end=last_day,
            created_at=datetime.utcnow(),
            due_date=last_day + timedelta(days=7)
        )
        db.session.add(invoice)
        log_action("invoice_created", f"Invoice {invoice.amount} for sub {sub.id}")

    db.session.commit()


def suspend_overdue_subscriptions():
    """Suspend subscriptions with invoices overdue by more than 7 days"""
    today = date.today()
    overdue_invoices = Invoice.query.filter(
        Invoice.status == "unpaid",
        Invoice.due_date < today - timedelta(days=7)
    ).all()

    for inv in overdue_invoices:
        sub = inv.subscription
        if sub.status == "active":
            sub.status = "suspended"
            db.session.add(sub)
            log_action("subscription_suspended", f"Sub {sub.id} suspended for unpaid invoice {inv.id}")

    db.session.commit()


def delete_long_suspended():
    """Delete subscriptions suspended for more than 7 days"""
    today = date.today()
    suspended_subs = Subscription.query.filter_by(status="suspended").all()
    for sub in suspended_subs:
        last_invoice = Invoice.query.filter_by(subscription_id=sub.id).order_by(Invoice.created_at.desc()).first()
        if last_invoice and last_invoice.due_date < today - timedelta(days=14):
            db.session.delete(sub)
            log_action("subscription_deleted", f"Sub {sub.id} deleted after long suspension")

    db.session.commit()


def run_billing_cron():
    """Wrapper to run all billing tasks in order"""
    create_invoices()
    suspend_overdue_subscriptions()
    delete_long_suspended()
