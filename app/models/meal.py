from datetime import datetime
from app.models import db

class UserMeal(db.Model):
    __tablename__ = 'user_meals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('registered_user.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    measurement_type = db.Column(db.String(20), nullable=False)  # 'weight' or 'count'
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    date_recorded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserMeal {self.food_name} - {self.quantity}{self.unit}>'

class FoodNutrient(db.Model):
    __tablename__ = 'food_nutrients'
    
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(100), nullable=False, unique=True)
    base_quantity = db.Column(db.Float, nullable=False)
    base_unit = db.Column(db.String(20), nullable=False)
    measurement_type = db.Column(db.String(20), nullable=False)  # 'weight' or 'count'
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<FoodNutrient {self.food_name}>'
