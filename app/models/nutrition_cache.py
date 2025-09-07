# app/models/nutrition_cache.py
from app.extensions import db
from datetime import datetime

class NutritionCache(db.Model):
    __tablename__ = 'nutrition_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    food_name = db.Column(db.String(200), nullable=False)
    nutrition_data = db.Column(db.JSON, nullable=False)  # PostgreSQL JSON column
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NutritionCache {self.food_name}>'