# from app import db
from app.extensions import db
from datetime import datetime

class DailyTarget(db.Model):
    __tablename__ = 'daily_targets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('registered_user.id'), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    date_modified = db.Column(db.DateTime, default=datetime.now)  # Changed from utcnow to now

    user = db.relationship('RegisteredUser', backref='daily_target')