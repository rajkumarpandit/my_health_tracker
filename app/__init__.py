from flask import Flask
from .config import Config
import os
from dotenv import load_dotenv
from .extensions import db, migrate, login_manager

# Load environment variables
load_dotenv()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Debug: Print which database is being used
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:'):
        print(f"🗃️  Using SQLite database")
    elif db_uri.startswith('postgresql:'):
        print(f"🐘 Using PostgreSQL database")
    elif db_uri.startswith('mysql:'):
        print(f"🐬 Using MySQL database")
    
    with app.app_context():
        # Import ALL models here so Flask-Migrate can detect them
        from app.models import (
            RegisteredUser, 
            UserMeal, 
            UserExercise, 
            DailyTarget, 
            UserSupplement, 
            UserWeight,
            NutritionCache
        )
        
        # Import routes
        from .routes import auth, main, meal, daily_target
        from .routes import weight
        from .routes import exercise
        from .routes import supplement
        
        # Register blueprints
        app.register_blueprint(auth.bp)
        app.register_blueprint(main.bp)
        app.register_blueprint(meal.bp)
        app.register_blueprint(daily_target.bp)
        app.register_blueprint(weight.bp)
        app.register_blueprint(exercise.bp, url_prefix='/exercise')
        app.register_blueprint(supplement.bp, url_prefix='/supplement')
        
        return app
