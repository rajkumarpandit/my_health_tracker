import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)  # Session expires after 1 day
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    
    # Database Configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLITE_DB_PATH = os.path.join(basedir, os.getenv('SQLITE_DB_PATH', 'instance/health_tracker.db'))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLITE_DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Vector DB Configuration
    CHROMA_DB_PATH = os.path.join(basedir, os.getenv('CHROMA_DB_PATH', 'instance/chromadb'))
    CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'food_nutrients')
