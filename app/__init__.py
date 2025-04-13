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

    # Ensure the instance folder exists
    db_dir = os.path.dirname(app.config['SQLITE_DB_PATH'])
    try:
        os.makedirs(db_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating database directory: {e}")

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    with app.app_context():
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
