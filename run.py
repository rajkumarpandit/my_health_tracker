from app import create_app
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = create_app()

if __name__ == '__main__':
    app.run(
        host=os.getenv('HOST_IP', '127.0.0.1'),
        port=int(os.getenv('PORT', 5000)),
        debug=True
    )
