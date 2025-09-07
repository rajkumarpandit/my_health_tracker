#!/usr/bin/env bash
# build.sh
set -o errexit

pip install -r requirements.txt

# Run database migrations
python -c "
from flask_migrate import upgrade
from app import create_app
app = create_app()
with app.app_context():
    upgrade()
"