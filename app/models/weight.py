from datetime import datetime
# from app.models import db
from app.extensions import db

class UserWeight(db.Model):
    __tablename__ = 'user_weights'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('registered_user.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    date_recorded = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<UserWeight {self.weight}kg on {self.date_recorded}>'