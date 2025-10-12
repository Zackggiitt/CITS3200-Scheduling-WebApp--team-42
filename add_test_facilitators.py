"""
Script to add test facilitators and their module skills to the database.
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User, UserRole, Module, FacilitatorSkill, SkillLevel
from flask import Flask

# Create a minimal app for database operations
def create_minimal_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def add_test_facilitators():
    app = create_minimal_app()
    
    with app.app_context():
        # Add test facilitators
        facilitator1 = User(
            email="facilitator1@example.com",
            first_name="Facilitator",
            last_name="One",
            role=UserRole.FACILITATOR
        )
        
        facilitator2 = User(
            email="facilitator2@example.com",
            first_name="Facilitator",
            last_name="Two",
            role=UserRole.FACILITATOR
        )
        
        # Check if they already exist
        existing_facilitator1 = User.query.filter_by(email="facilitator1@example.com").first()
        existing_facilitator2 = User.query.filter_by(email="facilitator2@example.com").first()
        
        if not existing_facilitator1:
            db.session.add(facilitator1)
        
        if not existing_facilitator2:
            db.session.add(facilitator2)
        
        db.session.commit()
        
        # Get the facilitators (either newly created or existing)
        facilitator1 = User.query.filter_by(email="facilitator1@example.com").first()
        facilitator2 = User.query.filter_by(email="facilitator2@example.com").first()
        
        # Get all modules
        modules = Module.query.all()
        
        # Clear existing skills for these facilitators
        FacilitatorSkill.query.filter_by(facilitator_id=facilitator1.id).delete()
        FacilitatorSkill.query.filter_by(facilitator_id=facilitator2.id).delete()
        
        # Add skills for facilitator 1
        for i, module in enumerate(modules):
            if i % 2 == 0:  # Assign skills to even-indexed modules
                skill_level = SkillLevel.PROFICIENT if i % 4 == 0 else SkillLevel.INTERESTED
                facilitator_skill = FacilitatorSkill(
                    facilitator_id=facilitator1.id,
                    module_id=module.id,
                    skill_level=skill_level
                )
                db.session.add(facilitator_skill)
        
        # Add skills for facilitator 2
        for i, module in enumerate(modules):
            if i % 2 == 1:  # Assign skills to odd-indexed modules
                skill_level = SkillLevel.LEADER if i % 3 == 0 else SkillLevel.PROFICIENT
                facilitator_skill = FacilitatorSkill(
                    facilitator_id=facilitator2.id,
                    module_id=module.id,
                    skill_level=skill_level
                )
                db.session.add(facilitator_skill)
        
        db.session.commit()
        print("Test facilitators and skills added successfully!")

if __name__ == '__main__':
    add_test_facilitators()
