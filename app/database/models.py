from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)



    # relationship to DatabaseInstance
    instances = db.relationship('DatabaseInstance', backref='owner', lazy=True)
    



class DatabaseInstance(db.Model):
    # Represents a database instance owned by a user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    uri = db.Column(db.String(255), nullable=False)