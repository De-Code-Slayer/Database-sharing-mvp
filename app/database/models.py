from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



    # relationship to DatabaseInstance
    instances = db.relationship('DatabaseInstance', backref='owner', lazy=True)
    

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
#     owner = db.relationship("User", backref=db.backref("tenants", lazy=True))


class DatabaseInstance(db.Model):
    # Represents a database instance owned by a user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    uri = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)