#!/usr/bin/env python3
"""
Script to set up complete test data for Unit Coordinator auto assignment testing
"""

import sys
import os
from datetime import datetime, timedelta, time
from werkzeug.security import generate_password_hash

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application import app, db
from models import (
    User, UserRole, Unit, Module, Session, Assignment, 
    UnitFacilitator, FacilitatorSkill, SkillLevel, Availability
)

def setup_test_data():
    """Set up complete test data for auto assignment testing"""
    
    with app.app_context():
        print("Setting up test data for Unit Coordinator auto assignment...")
        
        # 1. Get or create Unit Coordinator
        uc = User.query.filter_by(email="uc@test.com").first()
        if not uc:
            print("Unit Coordinator not found. Please run add_uc.py first.")
            return
        
        print(f"✓ Found Unit Coordinator: {uc.email}")
        
        # 2. Create a test unit
        unit = Unit.query.filter_by(unit_code="TEST101", created_by=uc.id).first()
        if not unit:
            unit = Unit(
                unit_code="TEST101",
                unit_name="Test Unit for Auto Assignment",
                year=2024,
                semester="Semester 1",
                description="Test unit for auto assignment functionality",
                start_date=datetime.now().date(),
                end_date=(datetime.now() + timedelta(days=90)).date(),
                created_by=uc.id
            )
            db.session.add(unit)
            db.session.flush()
            print(f"✓ Created unit: {unit.unit_code}")
        else:
            print(f"✓ Found existing unit: {unit.unit_code}")
        
        # 3. Create modules for the unit
        modules = []
        module_names = ["Lab 1", "Lab 2", "Tutorial 1", "Tutorial 2", "Workshop"]
        
        for name in module_names:
            module = Module.query.filter_by(unit_id=unit.id, module_name=name).first()
            if not module:
                module = Module(
                    unit_id=unit.id,
                    module_name=name,
                    module_type="lab" if "Lab" in name else "tutorial" if "Tutorial" in name else "workshop"
                )
                db.session.add(module)
                modules.append(module)
            else:
                modules.append(module)
        
        db.session.flush()
        print(f"✓ Created/found {len(modules)} modules")
        
        # 4. Get facilitators and link them to the unit
        facilitators = User.query.filter_by(role=UserRole.FACILITATOR).all()
        if not facilitators:
            print("No facilitators found. Please run create_sample_facilitators.py first.")
            return
        
        # Link facilitators to unit
        linked_count = 0
        for facilitator in facilitators:
            link = UnitFacilitator.query.filter_by(unit_id=unit.id, user_id=facilitator.id).first()
            if not link:
                link = UnitFacilitator(unit_id=unit.id, user_id=facilitator.id)
                db.session.add(link)
                linked_count += 1
        
        print(f"✓ Linked {linked_count} new facilitators to unit (total: {len(facilitators)})")
        
        # 5. Create skills for facilitators
        for i, facilitator in enumerate(facilitators):
            for j, module in enumerate(modules):
                skill = FacilitatorSkill.query.filter_by(
                    facilitator_id=facilitator.id, 
                    module_id=module.id
                ).first()
                
                if not skill:
                    # Give different skill levels to create variety
                    if j <= i % 3:
                        skill_level = SkillLevel.PROFICIENT
                    elif j <= i % 2:
                        skill_level = SkillLevel.INTERESTED
                    else:
                        skill_level = SkillLevel.UNINTERESTED
                    
                    skill = FacilitatorSkill(
                        facilitator_id=facilitator.id,
                        module_id=module.id,
                        skill_level=skill_level
                    )
                    db.session.add(skill)
        
        print("✓ Created facilitator skills")
        
        # 6. Create availability for facilitators (make them available)
        for facilitator in facilitators:
            # Check if availability already exists
            existing_avail = Availability.query.filter_by(user_id=facilitator.id).first()
            if not existing_avail:
                # Create availability for weekdays 9-17
                for day in range(5):  # Monday to Friday
                    for hour in range(9, 17):  # 9 AM to 5 PM
                        availability = Availability(
                            user_id=facilitator.id,
                            day_of_week=day,
                            start_time=time(hour, 0),
                            end_time=time(hour+1, 0)
                        )
                        db.session.add(availability)
        
        print("✓ Created facilitator availability")
        
        # 7. Create test sessions
        # Clear existing sessions for this unit
        existing_sessions = db.session.query(Session).join(Module).filter(Module.unit_id == unit.id).all()
        for session in existing_sessions:
            # Clear assignments first
            Assignment.query.filter_by(session_id=session.id).delete()
            db.session.delete(session)
        
        # Create new sessions
        base_date = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        sessions_created = 0
        
        for i, module in enumerate(modules):
            # Create 2 sessions per module
            for j in range(2):
                session_start = base_date + timedelta(days=i*2 + j, hours=j*2)
                session = Session(
                    module_id=module.id,
                    start_time=session_start,
                    end_time=session_start + timedelta(hours=2),
                    day_of_week=session_start.weekday(),
                    location=f"Room {100 + i*10 + j}",
                    max_facilitators=1,
                    lead_staff_required=1,
                    support_staff_required=0
                )
                db.session.add(session)
                sessions_created += 1
        
        print(f"✓ Created {sessions_created} test sessions")
        
        # Commit all changes
        db.session.commit()
        
        print("\n=== Test Data Setup Complete ===")
        print(f"Unit: {unit.unit_code} - {unit.unit_name}")
        print(f"Modules: {len(modules)}")
        print(f"Facilitators: {len(facilitators)}")
        print(f"Sessions: {sessions_created}")
        print("\nYou can now:")
        print("1. Login as Unit Coordinator: uc@test.com / uc123")
        print("2. Navigate to the unit dashboard")
        print("3. Click 'Auto-Assign Facilitators' to test the functionality")
        print("\nThe auto assignment will assign facilitators to sessions based on:")
        print("- Facilitator skills and availability")
        print("- Session requirements")
        print("- Conflict avoidance")

if __name__ == '__main__':
    setup_test_data()