import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database Configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


    # Check if running on App Engine
    if os.getenv('GAE_ENV', '').startswith('standard'):
        # Use Cloud SQL for Google App Engine
        CLOUDSQL_USER = os.getenv('CLOUDSQL_USER')
        CLOUDSQL_PASSWORD = os.getenv('CLOUDSQL_PASSWORD')
        CLOUDSQL_DATABASE = os.getenv('CLOUDSQL_DATABASE')
        CLOUDSQL_CONNECTION_NAME = os.getenv('CLOUDSQL_CONNECTION_NAME')
        
        SQLALCHEMY_DATABASE_URI = (
            'mysql+pymysql://{user}:{password}@/{database}'
            '?unix_socket=/cloudsql/{connection_name}').format(
                user=CLOUDSQL_USER,
                password=CLOUDSQL_PASSWORD,
                database=CLOUDSQL_DATABASE,
                connection_name=CLOUDSQL_CONNECTION_NAME)
    
    elif os.getenv('DATABASE_URL'):
        # For Render.com and other PaaS providers
        database_url = os.getenv('DATABASE_URL')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        
        SQLALCHEMY_DATABASE_URI = database_url
    
    elif os.getenv('USE_POSTGRESQL', 'false').lower() == 'true':
        # Local PostgreSQL configuration
        DB_USER = os.getenv('DB_USER', 'postgres')
        DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = os.getenv('DB_PORT', '5432')
        DB_NAME = os.getenv('DB_NAME', 'health_tracker_dev')
        
        SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    else:
        # Use SQLite for local development (fallback)
        SQLITE_DB_PATH = os.path.join(basedir, os.getenv('SQLITE_DB_PATH', 'instance/health_tracker.db'))
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLITE_DB_PATH}'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Vector DB Configuration - FIX THIS
    CHROMA_DB_PATH = os.path.join(basedir, 'instance', 'chromadb')  # ✅ Fixed path
    CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'food_nutrients')
    
    # Create ChromaDB directory
    try:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    except OSError as e:
        print(f"Warning: Could not create ChromaDB directory: {e}")
