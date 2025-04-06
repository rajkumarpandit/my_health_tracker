from flask import Flask, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure the instance folder exists
    db_dir = os.path.dirname(app.config['SQLITE_DB_PATH'])
    try:
        os.makedirs(db_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating database directory: {e}")
        pass

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    with app.app_context():
        # Import routes
        from .routes import auth, main, meal
        
        # Register blueprints
        app.register_blueprint(auth.bp)
        app.register_blueprint(main.bp)
        app.register_blueprint(meal.bp)
        
        # Create database tables
        db.create_all()
        
        return app
