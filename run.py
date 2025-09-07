from app import create_app
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = create_app()

if __name__ == '__main__':
    # Get debug mode from environment (False for production)
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(
        host=os.getenv('HOST_IP', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=debug_mode  # ✅ Don't hardcode debug=True for production
    )
