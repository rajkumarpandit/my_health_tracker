# from app import db
from app.extensions import db
from datetime import datetime

class UserExercise(db.Model):
    __tablename__ = 'user_exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('registered_user.id'), nullable=False)
    date_recorded = db.Column(db.Date, nullable=False)
    
    # Exercise types
    gym = db.Column(db.Integer, default=0)
    running = db.Column(db.Integer, default=0)
    yoga = db.Column(db.Integer, default=0)
    zumba = db.Column(db.Integer, default=0)
    hiit = db.Column(db.Integer, default=0)
    cardio = db.Column(db.Integer, default=0)
    cycling = db.Column(db.Integer, default=0)
    swimming = db.Column(db.Integer, default=0)
    badminton = db.Column(db.Integer, default=0)
    lawn_tennis = db.Column(db.Integer, default=0)
    table_tennis = db.Column(db.Integer, default=0)
    volleyball = db.Column(db.Integer, default=0)
    basketball = db.Column(db.Integer, default=0)
    cricket = db.Column(db.Integer, default=0)
    football = db.Column(db.Integer, default=0)
    walking = db.Column(db.Integer, default=0)
    other_sports = db.Column(db.Integer, default=0)
    usual_movement = db.Column(db.Integer, default=0)
    step_count = db.Column(db.Integer, default=0)
    
    # Totals
    total_calories = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship with User (will be defined in the User model with backref)
    
    def __repr__(self):
        return f'<UserExercise {self.id} for user {self.user_id} on {self.date_recorded}>'