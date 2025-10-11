"""
Script to add 8 sample facilitators with realistic data including:
- Names and emails
- Passwords matching email prefix
- Varied availability schedules
- Different module skills
"""

import os
import sys
from datetime import datetime, time
from werkzeug.security import generate_password_hash

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User, UserRole, Module, FacilitatorSkill, SkillLevel, Availability
from flask import Flask

# Create a minimal app for database operations
def create_minimal_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def add_sample_facilitators():
    app = create_minimal_app()
    
    with app.app_context():
        # Sample facilitator data - now with skill patterns instead of specific modules
        facilitators_data = [
            {
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email': 'alice.johnson@gmail.com',
                'min_hours': 8,
                'max_hours': 16,
                'availability_days': [0, 1, 2],  # Mon, Tue, Wed
                'availability_hours': ['09:00', '10:00', '11:00', '14:00', '15:00'],
                'skill_pattern': [SkillLevel.PROFICIENT, SkillLevel.INTERESTED, SkillLevel.LEADER, SkillLevel.UNINTERESTED, SkillLevel.INTERESTED]
            },
            {
                'first_name': 'Bob',
                'last_name': 'Smith',
                'email': 'bob.smith@gmail.com',
                'min_hours': 6,
                'max_hours': 20,
                'availability_days': [1, 2, 3, 4],  # Tue, Wed, Thu, Fri
                'availability_hours': ['10:00', '11:00', '12:00', '13:00', '16:00'],
                'skill_pattern': [SkillLevel.INTERESTED, SkillLevel.PROFICIENT, SkillLevel.UNINTERESTED, SkillLevel.PROFICIENT, SkillLevel.LEADER]
            },
            {
                'first_name': 'Carol',
                'last_name': 'Davis',
                'email': 'carol.davis@gmail.com',
                'min_hours': 10,
                'max_hours': 18,
                'availability_days': [0, 2, 4],  # Mon, Wed, Fri
                'availability_hours': ['09:00', '11:00', '13:00', '14:00', '15:00', '16:00'],
                'skill_pattern': [SkillLevel.LEADER, SkillLevel.UNINTERESTED, SkillLevel.PROFICIENT, SkillLevel.INTERESTED, SkillLevel.PROFICIENT]
            },
            {
                'first_name': 'David',
                'last_name': 'Wilson',
                'email': 'david.wilson@gmail.com',
                'min_hours': 4,
                'max_hours': 15,
                'availability_days': [0, 1, 3],  # Mon, Tue, Thu
                'availability_hours': ['08:00', '09:00', '10:00', '15:00', '16:00', '17:00'],
                'skill_pattern': [SkillLevel.UNINTERESTED, SkillLevel.LEADER, SkillLevel.INTERESTED, SkillLevel.INTERESTED, SkillLevel.PROFICIENT]
            },
            {
                'first_name': 'Emma',
                'last_name': 'Brown',
                'email': 'emma.brown@gmail.com',
                'min_hours': 12,
                'max_hours': 20,
                'availability_days': [1, 2, 3, 4],  # Tue, Wed, Thu, Fri
                'availability_hours': ['10:00', '11:00', '12:00', '14:00', '15:00'],
                'skill_pattern': [SkillLevel.LEADER, SkillLevel.PROFICIENT, SkillLevel.PROFICIENT, SkillLevel.INTERESTED, SkillLevel.LEADER]
            },
            {
                'first_name': 'Frank',
                'last_name': 'Miller',
                'email': 'frank.miller@gmail.com',
                'min_hours': 8,
                'max_hours': 16,
                'availability_days': [0, 2, 3, 4],  # Mon, Wed, Thu, Fri
                'availability_hours': ['09:00', '10:00', '13:00', '14:00', '16:00'],
                'skill_pattern': [SkillLevel.INTERESTED, SkillLevel.UNINTERESTED, SkillLevel.LEADER, SkillLevel.PROFICIENT, SkillLevel.INTERESTED]
            },
            {
                'first_name': 'Grace',
                'last_name': 'Taylor',
                'email': 'grace.taylor@gmail.com',
                'min_hours': 6,
                'max_hours': 14,
                'availability_days': [0, 1, 4],  # Mon, Tue, Fri
                'availability_hours': ['11:00', '12:00', '13:00', '15:00', '16:00', '17:00'],
                'skill_pattern': [SkillLevel.INTERESTED, SkillLevel.INTERESTED, SkillLevel.UNINTERESTED, SkillLevel.LEADER, SkillLevel.PROFICIENT]
            },
            {
                'first_name': 'Henry',
                'last_name': 'Anderson',
                'email': 'henry.anderson@gmail.com',
                'min_hours': 10,
                'max_hours': 18,
                'availability_days': [1, 2, 3],  # Tue, Wed, Thu
                'availability_hours': ['08:00', '09:00', '12:00', '13:00', '14:00', '17:00'],
                'skill_pattern': [SkillLevel.PROFICIENT, SkillLevel.LEADER, SkillLevel.PROFICIENT, SkillLevel.PROFICIENT, SkillLevel.UNINTERESTED]
            }
        ]
        
        # Get all modules to assign skills
        modules = Module.query.all()
        module_dict = {module.module_name: module for module in modules}
        
        created_count = 0
        
        for facilitator_data in facilitators_data:
            # Extract password from email (part before @gmail.com)
            password = facilitator_data['email'].split('@')[0]
            
            # Check if facilitator already exists
            existing_user = User.query.filter_by(email=facilitator_data['email']).first()
            if existing_user:
                print(f"Facilitator {facilitator_data['email']} already exists, skipping...")
                continue
            
            # Create facilitator
            facilitator = User(
                email=facilitator_data['email'],
                first_name=facilitator_data['first_name'],
                last_name=facilitator_data['last_name'],
                role=UserRole.FACILITATOR,
                password_hash=generate_password_hash(password),
                min_hours=facilitator_data['min_hours'],
                max_hours=facilitator_data['max_hours']
            )
            
            db.session.add(facilitator)
            db.session.flush()  # Get the ID without committing
            
            # Add availability
            for day in facilitator_data['availability_days']:
                for hour_str in facilitator_data['availability_hours']:
                    hour, minute = map(int, hour_str.split(':'))
                    start_time = time(hour, minute)
                    end_time = time(hour, minute)  # Same as start for slot-based availability
                    
                    availability = Availability(
                        user_id=facilitator.id,
                        day_of_week=day,
                        start_time=start_time,
                        end_time=end_time,
                        is_available=True
                    )
                    db.session.add(availability)
            
            # Add module skills for ALL modules using skill pattern
            skill_assignments = []
            for i, module in enumerate(modules):
                # Use skill pattern cyclically if there are more modules than pattern entries
                skill_level = facilitator_data['skill_pattern'][i % len(facilitator_data['skill_pattern'])]
                
                facilitator_skill = FacilitatorSkill(
                    facilitator_id=facilitator.id,
                    module_id=module.id,
                    skill_level=skill_level
                )
                db.session.add(facilitator_skill)
                skill_assignments.append(f"{module.module_name}: {skill_level.value}")
            
            created_count += 1
            print(f"Created facilitator: {facilitator_data['first_name']} {facilitator_data['last_name']} ({facilitator_data['email']})")
            print(f"  Password: {password}")
            print(f"  Skills assigned for {len(modules)} modules:")
            for skill_assignment in skill_assignments:
                print(f"    - {skill_assignment}")
            print(f"  Available: {len(facilitator_data['availability_days'])} days, {len(facilitator_data['availability_hours'])} hours per day")
            print()
        
        db.session.commit()
        print(f"Successfully created {created_count} facilitators!")
        
        if created_count == 0:
            print("No new facilitators were created (all already exist).")

if __name__ == '__main__':
    add_sample_facilitators()
