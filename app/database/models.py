from app import db
from datetime import datetime
from flask_login import UserMixin
import secrets
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash



class MyUser(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    authentication_method = db.Column(db.String(20), default="Email/Password")  # local, google, github
    is_admin = db.Column(db.Boolean, default=False)
    database_limit = db.Column(db.Integer, default=3)  # max number of databases user can create
    storage_limit = db.Column(db.Integer, default=1)   # max number of storage instances
    usdt_payment_address = db.Column(db.String(250), default='TWBhtsqMuDuio2xRmPBadwYAEJ4hh3WT9C', nullable=True)  # optional crypto payment address



    # relationship to DatabaseInstance
    instances = db.relationship('DatabaseInstance', backref='owner', lazy=True)
    storage_instances = db.relationship('StorageInstance', backref='owner', lazy=True, uselist=False)
    subscriptions = db.relationship("Subscription", backref="user", lazy=True)
    invoices = db.relationship("Invoice", backref="user", lazy=True)
    objects = db.relationship("Objects", backref="user", lazy=True)
    api_key = db.relationship("ApiKey", backref="user", lazy=True)  # for API access

    

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)



class DatabaseInstance(db.Model):
    # Represents a database instance owned by a user
    user_id = db.Column(db.Integer, db.ForeignKey('my_user.id'), nullable=False)
    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.String(50), nullable=False) #database name, postgres,mysql,etc
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
    due_date = db.Column(db.Date) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class BillingLog(db.Model):
    __tablename__ = "billing_log"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)  # e.g. "invoice_created"
    details = db.Column(db.Text, nullable=True)  # description of what happened
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PaymentProof(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Either attached to an invoice OR a subscription/prepayment
   
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=True)
    
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
    name = db.Column(db.String(50), nullable=False)
    folder_path = db.Column(db.String(512), nullable=False, unique=True)  # e.g. /var/www/storage/user_42
    quota = db.Column(db.BigInteger, default=1073741824)   # default 1GB in bytes
    used_space = db.Column(db.BigInteger, default=0)       # how much user has consumed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: one storage instance can have many files
    files = db.relationship("Objects", backref="storage", lazy=True)

    def __repr__(self):
        return f"<StorageInstance id={self.id} user_id={self.user_id} quota={self.quota} used={self.used_space}>"
    
    def delete_instance(self):
        import shutil, os
        import logging
        try:
            if os.path.exists(self.folder_path):
                shutil.rmtree(self.folder_path)
            # delete all associated files records
            for file in self.files:
                db.session.delete(file)
            #delete subscription
            if self.owner and self.owner.subscriptions:
                for sub in self.owner.subscriptions:
                    if sub.sub_for == self.name:
                        db.session.delete(sub)
            # delete the storage instance record
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting storage instance: {e}")
            return False


class Objects(db.Model):


    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("my_user.id") )   # owner of the file
    storage_id = db.Column(db.Integer, db.ForeignKey("storage_instance.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)          # original filename
    url = db.Column(db.String(512), nullable=False)               # path to file on disk
    public_url = db.Column(db.String(512), nullable=True)         # public URL 
    size = db.Column(db.BigInteger)                               # file size in bytes
    mime_type = db.Column(db.String(128))                         # image/png, application/pdf, etc.
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow) # upload timestamp

    def __repr__(self):
        return f"<File id={self.id} user_id={self.user_id} filename={self.filename}>"
    
    def delete_object(self):
        import os
        try:
            if os.path.exists(self.url):
                if os.remove(self.url):
                    # update quota
                    if self.size and self.storage:
                        self.storage.used_space = max(0, self.storage.used_space - self.size)
                    # delete db record
                    db.session.delete(self)
                    db.session.commit()
                       
                return True
            else:
                return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
        
    
class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("my_user.id"), nullable=False)
    key_hash = db.Column(db.String(128), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked = db.Column(db.Boolean, default=False)

    @staticmethod
    def generate_for_user(user_id):
        # Generate a random key (like Stripe/Paystack style)
        raw_key = "sk_live_" + secrets.token_urlsafe(32)  # human-usable
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = ApiKey(user_id=user_id, key_hash=key_hash)
        db.session.add(api_key)
        db.session.commit()

        return raw_key  # return plain key ONCE to user
    
    # revoke
    def revoke(self):
        self.revoked = True
        self.delete()
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @property
    def masked(self):
        # Show only the first 6 and last 4 characters
        # Example: sk_live_C4I4pJ...HFI
        return f"{self.key_hash[:6]}...{self.key_hash[-4:]}"


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("my_user.id"), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey("subscription.id"), nullable=True)
    reference = db.Column(db.String(100), unique=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoice = db.relationship("Invoice", backref="payments", lazy=True)
    subscription = db.relationship("Subscription", backref="payments", lazy=True)


class MigrationRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64))
    source_url = db.Column(db.String(512))
    dest_url = db.Column(db.String(512))
    direction = db.Column(db.String(32))  # "to_smallshardz" or "from_smallshardz"
    status = db.Column(db.String(32))     # "pending", "running", "success", "failed"
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    logs = db.Column(db.Text)












