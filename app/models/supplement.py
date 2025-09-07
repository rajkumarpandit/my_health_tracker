from datetime import datetime
# from app import db
from app.extensions import db

class UserSupplement(db.Model):
    __tablename__ = 'user_supplements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('registered_user.id'), nullable=False)
    supplement_name = db.Column(db.String(50), nullable=False)
    date_taken = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<UserSupplement {self.supplement_name} for user {self.user_id} on {self.date_taken}>'