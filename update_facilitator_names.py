"""
Script to update facilitator names with realistic names.
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User, UserRole
from flask import Flask

# Create a minimal app for database operations
def create_minimal_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def update_facilitator_names():
    app = create_minimal_app()
    
    with app.app_context():
        # Get all facilitators
        facilitators = User.query.filter_by(role=UserRole.FACILITATOR).all()
        
        # Fix the name-email mismatches by updating emails to match names
        name_updates = [
            # Current mismatches - update emails to match the names
            ("Sarah", "Johnson", "sarah.johnson@university.edu"),
            ("Michael", "Chen", "michael.chen@university.edu"),
            ("Emma", "Williams", "emma.williams@university.edu"),
            ("David", "Rodriguez", "david.rodriguez@university.edu"),
            ("Jessica", "Thompson", "jessica.thompson@university.edu"),
            ("Alex", "Kumar", "alex.kumar@university.edu"),
            ("Rachel", "Brown", "rachel.brown@university.edu"),
            ("James", "Wilson", "james.wilson@university.edu"),
            ("Lisa", "Garcia", "lisa.garcia@university.edu"),
            ("Ryan", "Davis", "ryan.davis@university.edu")
        ]
        
        print(f"Found {len(facilitators)} facilitators to update:")
        
        # Update first 10 facilitators with proper name-email matching
        for i, facilitator in enumerate(facilitators[:10]):
            if i < len(name_updates):
                old_info = f"{facilitator.first_name} {facilitator.last_name} ({facilitator.email})"
                
                first_name, last_name, new_email = name_updates[i]
                facilitator.first_name = first_name
                facilitator.last_name = last_name
                facilitator.email = new_email
                
                print(f"  Updated: {old_info} → {facilitator.first_name} {facilitator.last_name} ({facilitator.email})")
        
        # Keep any remaining facilitators as test accounts
        for facilitator in facilitators[10:]:
            print(f"  Kept: {facilitator.first_name} {facilitator.last_name} ({facilitator.email})")
        
        db.session.commit()
        print("\n✅ All facilitator names and emails updated successfully!")
        
        # Show final list
        print("\nCurrent facilitators:")
        for facilitator in facilitators:
            print(f"  - {facilitator.first_name} {facilitator.last_name} ({facilitator.email})")

if __name__ == '__main__':
    update_facilitator_names()
