from app import create_app
import os

# # Load environment variables
# load_dotenv()

app = create_app()

# debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
#     app.run(
#         host=os.getenv('HOST_IP', '0.0.0.0'),
#         port=int(os.getenv('PORT', 5000)),
#         debug=debug_mode 
#     )

if __name__ == '__main__':
    # For local development only
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
