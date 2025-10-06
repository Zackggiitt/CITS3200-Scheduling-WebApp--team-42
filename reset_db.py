"""
Script to reset the development database with the new schema.
This will drop the existing database and recreate it with the updated models.
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Flask app and database
from flask import Flask
from models import db, User, UserRole, Unit, Module, FacilitatorSkill, Session, Unavailability, Assignment, SwapRequest

app = Flask(__name__)
app.secret_key = "dev-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all tables.")
        
        # Recreate all tables with new schema
        db.create_all()
        print("Created all tables with new schema.")
        
        print("Database reset complete!")

if __name__ == '__main__':
    reset_database()
