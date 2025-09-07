#!/usr/bin/env bash
# filepath: c:\Raj\MyProjects\My_health_tracker\.render-build.sh

# Exit on error
set -o errexit

echo "Starting Render build process..."

# Install Python dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running database migrations..."

# Set FLASK_APP environment variable
export FLASK_APP=run.py

# Initialize migration repository if it doesn't exist
if [ ! -d "migrations" ]; then
    echo "Initializing Flask-Migrate..."
    flask db init
fi

# Create migration if models changed
echo "Creating migration..."
flask db migrate -m "Auto migration during build"

# Apply migrations
echo "📝 Applying migrations..."
flask db upgrade

echo "Build completed successfully!"