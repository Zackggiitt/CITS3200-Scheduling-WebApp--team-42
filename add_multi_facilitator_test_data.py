#!/usr/bin/env python3
"""
Script to add test data with multiple facilitators per session
to verify the multi-facilitator display functionality
"""

import sys
sys.path.append('.')
from application import app
from models import db, User, UserRole, Session, Module, Assignment, Unit
from datetime import datetime, timedelta

def add_multi_facilitator_test_data():
    """Add test sessions with multiple facilitators"""
    with app.app_context():
        # Find a unit to work with
        unit = Unit.query.first()
        if not unit:
            print("No units found. Please create a unit first.")
            return
        
        print(f"Working with unit: {unit.unit_code} - {unit.unit_name}")
        
        # Find facilitators
        facilitators = User.query.filter_by(role=UserRole.FACILITATOR).limit(6).all()
        if len(facilitators) < 3:
            print("Need at least 3 facilitators. Found:", len(facilitators))
            return
        
        print(f"Found {len(facilitators)} facilitators")
        
        # Find or create a module
        module = Module.query.filter_by(unit_id=unit.id).first()
        if not module:
            module = Module(
                unit_id=unit.id,
                module_name="Test Multi-Facilitator Module",
                module_type="workshop"
            )
            db.session.add(module)
            db.session.commit()
            print("Created test module")
        
        # Create test sessions with multiple facilitators
        test_sessions = [
            {
                "name": "Single Lead Session",
                "lead_count": 1,
                "support_count": 0,
                "facilitators": [facilitators[0]]
            },
            {
                "name": "Lead + Support Session", 
                "lead_count": 1,
                "support_count": 1,
                "facilitators": [facilitators[1], facilitators[2]]
            },
            {
                "name": "Multiple Leads Session",
                "lead_count": 2,
                "support_count": 0,
                "facilitators": [facilitators[3], facilitators[4]]
            },
            {
                "name": "Large Team Session",
                "lead_count": 2,
                "support_count": 2,
                "facilitators": [facilitators[0], facilitators[1], facilitators[2], facilitators[3]]
            }
        ]
        
        created_sessions = []
        
        for i, session_data in enumerate(test_sessions):
            # Create session
            start_time = datetime.now() + timedelta(days=i+1, hours=9)
            end_time = start_time + timedelta(hours=3)
            
            session = Session(
                module_id=module.id,
                session_type="workshop",
                start_time=start_time,
                end_time=end_time,
                day_of_week=start_time.weekday(),
                location=f"Test Lab {i+1}",
                required_skills=None,
                max_facilitators=len(session_data["facilitators"]),
                lead_staff_required=session_data["lead_count"],
                support_staff_required=session_data["support_count"]
            )
            
            db.session.add(session)
            db.session.flush()  # Get session ID
            
            # Create assignments
            for j, facilitator in enumerate(session_data["facilitators"]):
                role = "lead" if j < session_data["lead_count"] else "support"
                
                assignment = Assignment(
                    session_id=session.id,
                    facilitator_id=facilitator.id,
                    is_confirmed=True,
                    role=role
                )
                
                db.session.add(assignment)
                print(f"  - Assigned {facilitator.first_name} {facilitator.last_name} as {role}")
            
            created_sessions.append({
                "session": session,
                "name": session_data["name"],
                "facilitator_count": len(session_data["facilitators"])
            })
            
            print(f"Created session: {session_data['name']} with {len(session_data['facilitators'])} facilitators")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully created {len(created_sessions)} test sessions with multi-facilitator assignments!")
            
            # Display summary
            print("\nSession Summary:")
            for session_info in created_sessions:
                session = session_info["session"]
                print(f"  - {session_info['name']}: {session_info['facilitator_count']} facilitators")
                
                # Show assignments
                for assignment in session.assignments:
                    role_badge = "LEAD" if assignment.role == "lead" else "SUPPORT"
                    print(f"    * {assignment.facilitator.first_name} {assignment.facilitator.last_name} ({role_badge})")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating test data: {e}")
            return False
        
        return True

def main():
    """Run the test data creation"""
    print("="*60)
    print("MULTI-FACILITATOR TEST DATA CREATION")
    print("="*60)
    
    success = add_multi_facilitator_test_data()
    
    if success:
        print("\n" + "="*60)
        print("✅ Test data creation completed successfully!")
        print("You can now check the Sessions List to see multi-facilitator display.")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ Test data creation failed.")
        print("="*60)

if __name__ == "__main__":
    main()
