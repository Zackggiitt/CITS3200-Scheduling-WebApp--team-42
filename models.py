from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=True)  # Allow null for OAuth users
    
    # OAuth related fields
    oauth_provider = db.Column(db.String(50), nullable=True)  # 'google', 'microsoft', None
    oauth_id = db.Column(db.String(255), nullable=True)  # OAuth provider's user ID
    avatar_url = db.Column(db.String(500), nullable=True)  # User avatar URL
    
    def __repr__(self):
        return f'<User {self.email}>'
