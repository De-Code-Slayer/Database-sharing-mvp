from datetime import date, timedelta, datetime
from app import db
from app.database.models import Subscription, Invoice, Plan, BillingLog
from app.views.utilities.smtp import send_invoice_email


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
    created_invoices = []

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
        created_invoices.append(invoice)
        log_action("invoice_created", f"Invoice {invoice.amount} for sub {sub.id}")

    db.session.commit()

    # Send notification email for newly created invoices
    for invoice in created_invoices:
        if invoice.user and invoice.user.email:
            invoice_data = {
                'id': invoice.id,
                'user_name': invoice.user.username,
                'amount': invoice.amount,
                'period_start': invoice.period_start,
                'period_end': invoice.period_end,
                'due_date': invoice.due_date,
                'status': invoice.status,
                'subscription_name': invoice.subscription.sub_for if invoice.subscription else ''
            }
            success = send_invoice_email(invoice.user.email, invoice_data)
            log_action("invoice_email_sent", f"Invoice {invoice.id} email send status={success}")


def send_due_reminders():
    """Send reminder email for unpaid invoices about to be due or overdue"""
    today = date.today()

    # Notify 2 days before due
    due_soon = Invoice.query.filter(
        Invoice.status == "unpaid",
        Invoice.due_date == today + timedelta(days=2)
    ).all()

    # Notify 1 day overdue
    overdue = Invoice.query.filter(
        Invoice.status == "unpaid",
        Invoice.due_date == today - timedelta(days=1)
    ).all()

    for inv in due_soon + overdue:
        if inv.user and inv.user.email:
            deadline = "due soon" if inv.due_date > today else "overdue"
            invoice_data = {
                'id': inv.id,
                'user_name': inv.user.username,
                'amount': inv.amount,
                'period_start': inv.period_start,
                'period_end': inv.period_end,
                'due_date': inv.due_date,
                'status': deadline,
                'subscription_name': inv.subscription.sub_for if inv.subscription else ''
            }
            send_invoice_email(inv.user.email, invoice_data)
            log_action("invoice_reminder_sent", f"Invoice {inv.id} {deadline} reminder")



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
    # with app.app_context():
        try:
            create_invoices()
            send_due_reminders()
            suspend_overdue_subscriptions()
            delete_long_suspended()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Billing cron failed:", e)