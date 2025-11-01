from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy() # This will be initialized in app.py

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    sso_id = db.Column(db.String(128), unique=True, nullable=True)
    
    daily_api_calls = db.Column(db.Integer, default=0)
    last_api_call_date = db.Column(db.Date, default=lambda: date.today())

    templates = db.relationship('Template', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class IPUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, unique=True)
    last_attempt_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<IPUsage {self.ip_address}>'

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Template {self.name}>'
