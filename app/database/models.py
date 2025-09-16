from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash



class MyUser(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



    # relationship to DatabaseInstance
    instances = db.relationship('DatabaseInstance', backref='owner', lazy=True)
    storage_instances = db.relationship('StorageInstance', backref='owner', lazy=True)
    subscriptions = db.relationship("Subscription", backref="user", lazy=True)
    invoices = db.relationship("Invoice", backref="user", lazy=True)
    objects = db.relationship("Objects", backref="user", lazy=True)
    

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)



# class Tenant(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
#     tenant_key = db.Column(db.String(32), unique=True, nullable=False)
#     role = db.Column(db.String(80), nullable=False)
#     schema = db.Column(db.String(80), nullable=False)
#     last_env_url = db.Column(db.Text, nullable=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     owner = db.relationship("MyUser", backref=db.backref("tenants", lazy=True))


class DatabaseInstance(db.Model):
    # Represents a database instance owned by a user
    user_id = db.Column(db.Integer, db.ForeignKey('my_user.id'), nullable=False)
    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    database_name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    uri = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# to be able to update database prices from database
class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))  # "Database"
    price = db.Column(db.Float)  # monthly price
    description = db.Column(db.String(255))

    # Relationships
    subscriptions = db.relationship("Subscription", backref="plan", lazy=True)


# subscription model to track user subscriptions
class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("my_user.id"))
    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"))
    sub_for = db.Column(db.String(50), unique=True)  # e.g., "databasename"
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)  # prepaid until this date
    billing_type = db.Column(db.String(10), default="postpaid")  # prepaid or postpaid
    status = db.Column(db.String(20), default="active") #active, suspended

    # Relationships
    invoices = db.relationship("Invoice", backref="subscription", lazy=True)



class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("my_user.id"))
    subscription_id = db.Column(db.Integer, db.ForeignKey("subscription.id"))
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default="unpaid")  # unpaid, paid
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class BillingLog(db.Model):
    __tablename__ = "billing_log"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)  # e.g. "invoice_created"
    details = db.Column(db.Text, nullable=True)  # description of what happened
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PaymentProof(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("my_user.id"), nullable=False)

    tx_hash = db.Column(db.String(200), nullable=True)   # optional
    screenshot_url = db.Column(db.String(500), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    feedback = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected


class StorageInstance(db.Model):
   
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("my_user.id"))   # owner of the instance
    folder_path = db.Column(db.String(512), nullable=False, unique=True)  # e.g. /var/www/storage/user_42
    quota = db.Column(db.BigInteger, default=1073741824)   # default 1GB in bytes
    used_space = db.Column(db.BigInteger, default=0)       # how much user has consumed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: one storage instance can have many files
    files = db.relationship("Objects", backref="storage", lazy=True)

    def __repr__(self):
        return f"<StorageInstance id={self.id} user_id={self.user_id} quota={self.quota} used={self.used_space}>"

class Objects(db.Model):


    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("my_user.id") )   # owner of the file
    storage_id = db.Column(db.Integer, db.ForeignKey("storage_instances.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)          # original filename
    url = db.Column(db.String(512), nullable=False)               # path or external URL
    size = db.Column(db.BigInteger)                               # file size in bytes
    mime_type = db.Column(db.String(128))                         # image/png, application/pdf, etc.
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow) # upload timestamp

    def __repr__(self):
        return f"<File id={self.id} user_id={self.user_id} filename={self.filename}>"
    









