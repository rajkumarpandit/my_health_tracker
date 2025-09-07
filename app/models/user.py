from datetime import datetime
from flask_login import UserMixin
from app import login_manager
from app.extensions import db


class RegisteredUser(UserMixin, db.Model):  # ✅ Changed from User to RegisteredUser
    __tablename__ = 'registered_user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)  # Increased length to 100
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(1055), nullable=False)  # ✅ Increased from 128 to 255
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
        
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(id):
    return RegisteredUser.query.get(int(id))  # ✅ Changed from User to RegisteredUser
