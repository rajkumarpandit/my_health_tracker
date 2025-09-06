from flask.cli import FlaskGroup
from flask_migrate import upgrade
from app import create_app, db
from app.extensions import db, migrate

app = create_app()
cli = FlaskGroup(app)

with app.app_context():
    upgrade()

if __name__ == '__main__':
    cli()