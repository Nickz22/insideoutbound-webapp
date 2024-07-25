from app import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    salesforce_id = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    org_id = db.Column(db.String(255))
    is_sandbox = db.Column(db.Boolean)
