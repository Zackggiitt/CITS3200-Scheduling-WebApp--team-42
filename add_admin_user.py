"""
Script to add an admin user to the database.
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User, UserRole
from flask import Flask

# Create a minimal app for database operations
def create_minimal_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def add_admin_user():
    app = create_minimal_app()
    
    with app.app_context():
        # Check if admin user already exists
        existing_admin = User.query.filter_by(email="admin@gmail.com").first()
        
        if existing_admin:
            print("Admin user already exists!")
            return
        
        # Create admin user with password 'admin'
        admin_user = User(
            email="admin@gmail.com",
            first_name="Admin",
            last_name="User",
            password_hash=generate_password_hash("admin"),
            role=UserRole.ADMIN
        )
        
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user added successfully!")

if __name__ == '__main__':
    add_admin_user()
