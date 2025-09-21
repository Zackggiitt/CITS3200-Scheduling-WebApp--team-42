#!/usr/bin/env python3
"""
Script to create comprehensive test data for unavailability system testing.
This script creates:
- Test facilitator user (fac_demo@example.com) - password should be set by existing facilitator creation script
- Sample units with proper date ranges (3 active units, 2 past units)
- Modules for those units
- Sessions for the modules (past sessions for past units, future sessions for active units)
- Unit assignments for the facilitator
- Session assignments for the facilitator

Usage:
    python create_unavailability_test_data.py create  - Create all test data
    python create_unavailability_test_data.py clear   - Clear all test data
    python create_unavailability_test_data.py status  - Show current status
"""

import sys
import os
from werkzeug.security import generate_password_hash
from datetime import datetime, date, time, timedelta

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application import app, db
from models import (
    User, Unit, Module, Session, Assignment, UnitFacilitator, 
    UserRole, Unavailability, RecurringPattern, SwapRequest, SwapStatus
)

def create_test_facilitator():
    """Create the test facilitator user"""
    email = 'fac_demo@example.com'
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print(f"✓ Test facilitator already exists: {email}")
        return existing_user
    
    # Create new facilitator user (password will be set by existing facilitator creation script)
    user = User(
        first_name='Demo',
        last_name='Facilitator',
        email=email,
        phone_number='+61 4 9876 5432',
        staff_number='FAC999',
        password_hash='',  # Empty password - should be set by existing facilitator creation script
        role=UserRole.FACILITATOR
    )
    
    db.session.add(user)
    db.session.commit()
    
    print(f"✓ Created test facilitator: {email}")
    print(f"  Note: Password should be set by existing facilitator creation script")
    return user

def create_sample_units():
    """Create sample units with proper date ranges for testing"""
    
    # Get an admin user for created_by field
    admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
    if not admin_user:
        # Create a basic admin user if none exists
        admin_user = User(
            first_name='Admin',
            last_name='User',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            role=UserRole.ADMIN
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✓ Created admin user for unit creation")
    
    # Define sample units with realistic date ranges
    today = date.today()
    
    sample_units = [
        {
            'unit_code': 'CITS1001',
            'unit_name': 'Computer Science Fundamentals',
            'year': 2025,
            'semester': 'Semester 1',
            'start_date': today - timedelta(days=30),  # Started 30 days ago
            'end_date': today + timedelta(days=60),    # Ends in 60 days
            'description': 'Introduction to computer science concepts and programming'
        },
        {
            'unit_code': 'CITS2002',
            'unit_name': 'Systems Programming',
            'year': 2025,
            'semester': 'Semester 1',
            'start_date': today - timedelta(days=20),  # Started 20 days ago
            'end_date': today + timedelta(days=70),    # Ends in 70 days
            'description': 'Systems programming and low-level software development'
        },
        # Past Units
        {
            'unit_code': 'CITS2200',
            'unit_name': 'Algorithms and Data Structures',
            'year': 2024,
            'semester': 'Semester 2',
            'start_date': today - timedelta(days=200),  # Started 200 days ago
            'end_date': today - timedelta(days=50),    # Ended 50 days ago
            'description': 'Advanced algorithms and data structure implementations'
        },
        {
            'unit_code': 'CITS3000',
            'unit_name': 'Software Engineering Project',
            'year': 2025,
            'semester': 'Semester 1',
            'start_date': today - timedelta(days=300),  # Started 300 days ago
            'end_date': today - timedelta(days=100),   # Ended 100 days ago
            'description': 'Large-scale software development project management'
        }
    ]
    
    created_units = []
    
    for unit_data in sample_units:
        # Check if unit already exists
        existing_unit = Unit.query.filter_by(
            unit_code=unit_data['unit_code'],
            year=unit_data['year'],
            semester=unit_data['semester']
        ).first()
        
        if existing_unit:
            print(f"✓ Unit already exists: {unit_data['unit_code']}")
            created_units.append(existing_unit)
            continue
        
        # Create new unit
        unit = Unit(
            unit_code=unit_data['unit_code'],
            unit_name=unit_data['unit_name'],
            year=unit_data['year'],
            semester=unit_data['semester'],
            description=unit_data['description'],
            created_by=admin_user.id,
            start_date=unit_data['start_date'],
            end_date=unit_data['end_date']
        )
        
        db.session.add(unit)
        db.session.commit()
        
        print(f"✓ Created unit: {unit_data['unit_code']} - {unit_data['unit_name']}")
        print(f"  Date range: {unit_data['start_date']} to {unit_data['end_date']}")
        created_units.append(unit)
    
    return created_units

def create_sample_modules(units):
    """Create sample modules for the units"""
    
    module_templates = {
        'CITS1001': [
            {'name': 'Programming Lab A', 'type': 'lab'},
            {'name': 'Programming Lab B', 'type': 'lab'},
            {'name': 'Tutorial Group 1', 'type': 'tutorial'},
            {'name': 'Tutorial Group 2', 'type': 'tutorial'},
            {'name': 'Lecture Series', 'type': 'lecture'}
        ],
        'CITS2002': [
            {'name': 'Systems Lab 1', 'type': 'lab'},
            {'name': 'Systems Lab 2', 'type': 'lab'},
            {'name': 'Workshop A', 'type': 'workshop'},
            {'name': 'Workshop B', 'type': 'workshop'},
            {'name': 'Core Lectures', 'type': 'lecture'}
        ],
        'CITS2200': [
            {'name': 'Algorithm Lab 1', 'type': 'lab'},
            {'name': 'Algorithm Lab 2', 'type': 'lab'},
            {'name': 'Data Structures Workshop', 'type': 'workshop'},
            {'name': 'Complexity Analysis Tutorial', 'type': 'tutorial'},
            {'name': 'Algorithm Theory', 'type': 'lecture'}
        ],
        'CITS3000': [
            {'name': 'Project Lab 1', 'type': 'lab'},
            {'name': 'Project Lab 2', 'type': 'lab'},
            {'name': 'Software Design Workshop', 'type': 'workshop'},
            {'name': 'Project Management Tutorial', 'type': 'tutorial'},
            {'name': 'Software Engineering Principles', 'type': 'lecture'}
        ]
    }
    
    created_modules = []
    
    for unit in units:
        unit_code = unit.unit_code
        if unit_code not in module_templates:
            continue
        
        for module_data in module_templates[unit_code]:
            # Check if module already exists
            existing_module = Module.query.filter_by(
                unit_id=unit.id,
                module_name=module_data['name']
            ).first()
            
            if existing_module:
                print(f"✓ Module already exists: {unit_code} - {module_data['name']}")
                created_modules.append(existing_module)
                continue
            
            # Create new module
            module = Module(
                unit_id=unit.id,
                module_name=module_data['name'],
                module_type=module_data['type']
            )
            
            db.session.add(module)
            db.session.commit()
            
            print(f"✓ Created module: {unit_code} - {module_data['name']} ({module_data['type']})")
            created_modules.append(module)
    
    return created_modules

def create_sample_sessions(modules):
    """Create sample sessions for the modules"""
    
    # Clear existing sessions first
    Session.query.delete()
    
    created_sessions = []
    today = datetime.now()
    
    for module in modules:
        # Get the unit for this module to determine if it's past or current/future
        unit = db.session.get(Unit, module.unit_id)
        is_past_unit = unit.end_date and unit.end_date < today.date()
        
        # Create 4-5 sessions per module for better testing
        sessions_per_module = 2 if module.module_type == 'lecture' else 4
        
        for i in range(sessions_per_module):
            if is_past_unit:
                # For past units, create sessions in the past
                session_date = unit.end_date - timedelta(days=(sessions_per_module - i) * 7)
            else:
                # For current/future units, create sessions across different weeks
                if i < 2:
                    # First 2 sessions: this week (tomorrow and day after)
                    session_date = today.date() + timedelta(days=1 + i)
                elif i == 2:
                    # Third session: next week
                    session_date = today.date() + timedelta(days=7 + i)
                else:
                    # Fourth session: week after next
                    session_date = today.date() + timedelta(days=14 + i)
            
            # Different time slots based on module type
            if module.module_type == 'lab':
                base_start = datetime.combine(date.today(), time(9, 0))
                start_time = (base_start + timedelta(hours=i)).time()
                end_time = (base_start + timedelta(hours=i+2)).time()
            elif module.module_type == 'workshop':
                base_start = datetime.combine(date.today(), time(14, 0))
                start_time = (base_start + timedelta(hours=i)).time()
                end_time = (base_start + timedelta(hours=i+1, minutes=30)).time()
            elif module.module_type == 'tutorial':
                base_start = datetime.combine(date.today(), time(11, 0))
                start_time = (base_start + timedelta(hours=i)).time()
                end_time = (base_start + timedelta(hours=i+1)).time()
            else:  # lecture
                base_start = datetime.combine(date.today(), time(10, 0))
                start_time = (base_start + timedelta(hours=i)).time()
                end_time = (base_start + timedelta(hours=i+1)).time()
            
            session = Session(
                module_id=module.id,
                day_of_week=session_date.weekday(),
                start_time=datetime.combine(session_date, start_time),
                end_time=datetime.combine(session_date, end_time),
                max_facilitators=2 if module.module_type == 'lab' else 1,
                location=f"Room {100 + i}" if module.module_type != 'lecture' else "Lecture Theatre A"
            )
            
            db.session.add(session)
            created_sessions.append(session)
    
    db.session.commit()
    
    print(f"✓ Created {len(created_sessions)} sessions")
    return created_sessions

def assign_facilitator_to_units(facilitator, units):
    """Assign the facilitator to the units"""
    
    assignments_created = 0
    
    for unit in units:
        # Check if assignment already exists
        existing_assignment = UnitFacilitator.query.filter_by(
            user_id=facilitator.id,
            unit_id=unit.id
        ).first()
        
        if existing_assignment:
            print(f"✓ Facilitator already assigned to: {unit.unit_code}")
            continue
        
        # Create new assignment
        assignment = UnitFacilitator(
            user_id=facilitator.id,
            unit_id=unit.id
        )
        
        db.session.add(assignment)
        assignments_created += 1
        
        print(f"✓ Assigned facilitator to unit: {unit.unit_code}")
    
    db.session.commit()
    return assignments_created

def assign_facilitator_to_sessions(facilitator, sessions):
    """Assign the facilitator to some sessions"""
    
    # Clear existing assignments
    Assignment.query.filter_by(facilitator_id=facilitator.id).delete()
    
    assignments_created = 0
    
    # Assign to every other session to create a realistic schedule
    for i, session in enumerate(sessions):
        if i % 2 == 0:  # Assign to every other session
            assignment = Assignment(
                facilitator_id=facilitator.id,
                session_id=session.id,
                is_confirmed=True
            )
            
            db.session.add(assignment)
            assignments_created += 1
    
    db.session.commit()
    
    print(f"✓ Created {assignments_created} session assignments")
    return assignments_created

def create_sample_unavailability(facilitator, units):
    """Create some sample unavailability records for testing"""
    
    # Clear existing unavailability for this facilitator
    Unavailability.query.filter_by(user_id=facilitator.id).delete()
    
    unavailability_created = 0
    today = date.today()
    
    for unit in units:
        # Only create unavailability for units that are currently active
        if unit.start_date <= today <= unit.end_date:
            # Create a few sample unavailability records
            sample_dates = [
                today + timedelta(days=1),   # Tomorrow
                today + timedelta(days=3),   # Day after tomorrow
                today + timedelta(days=7),   # Next week
            ]
            
            for i, unav_date in enumerate(sample_dates):
                if unav_date <= unit.end_date:  # Only if within unit period
                    unavailability = Unavailability(
                        user_id=facilitator.id,
                        unit_id=unit.id,
                        date=unav_date,
                        is_full_day=(i % 2 == 0),  # Alternate between full day and partial
                        start_time=time(9, 0) if i % 2 == 1 else None,
                        end_time=time(17, 0) if i % 2 == 1 else None,
                        reason=f"Sample unavailability {i+1} for {unit.unit_code}"
                    )
                    
                    db.session.add(unavailability)
                    unavailability_created += 1
    
    db.session.commit()
    
    print(f"✓ Created {unavailability_created} sample unavailability records")
    return unavailability_created

def create_all_test_data():
    """Create all test data for unavailability system testing"""
    
    print("🚀 Creating comprehensive test data for unavailability system...")
    print("=" * 60)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # 1. Create test facilitator
        print("\n📝 Step 1: Creating test facilitator...")
        facilitator = create_test_facilitator()
        
        # 2. Create sample units
        print("\n📚 Step 2: Creating sample units...")
        units = create_sample_units()
        
        # 3. Create modules for units
        print("\n📖 Step 3: Creating modules...")
        modules = create_sample_modules(units)
        
        # 4. Create sessions for modules
        print("\n📅 Step 4: Creating sessions...")
        sessions = create_sample_sessions(modules)
        
        # 5. Assign facilitator to units
        print("\n👤 Step 5: Assigning facilitator to units...")
        unit_assignments = assign_facilitator_to_units(facilitator, units)
        
        # 6. Assign facilitator to sessions
        print("\n📋 Step 6: Assigning facilitator to sessions...")
        session_assignments = assign_facilitator_to_sessions(facilitator, sessions)
        
        # 7. Create sample unavailability
        print("\n🚫 Step 7: Creating sample unavailability...")
        unavailability_count = create_sample_unavailability(facilitator, units)
        
        print("\n" + "=" * 60)
        print("✅ Test data creation completed successfully!")
        print(f"📊 Summary:")
        print(f"   • Facilitator: {facilitator.email}")
        print(f"   • Units: {len(units)}")
        print(f"   • Modules: {len(modules)}")
        print(f"   • Sessions: {len(sessions)}")
        print(f"   • Unit assignments: {unit_assignments}")
        print(f"   • Session assignments: {session_assignments}")
        print(f"   • Sample unavailability: {unavailability_count}")
        
        # 8. Create additional facilitators for swap testing
        print("\n👥 Step 8: Creating additional facilitators for swap testing...")
        additional_facilitators = create_additional_facilitators()
        
        # 9. Assign additional facilitators to units and sessions
        print("\n📋 Step 9: Assigning additional facilitators to sessions...")
        additional_assignments = assign_additional_facilitators_to_sessions(additional_facilitators, sessions)
        
        # 10. Create sample swap requests
        print("\n🔄 Step 10: Creating sample swap requests...")
        swap_requests_count = create_sample_swap_requests(facilitator, additional_facilitators, sessions)
        
        print("\n" + "=" * 60)
        print("✅ Test data creation completed successfully!")
        print(f"📊 Summary:")
        print(f"   • Facilitator: {facilitator.email}")
        print(f"   • Additional facilitators: {len(additional_facilitators)}")
        print(f"   • Units: {len(units)}")
        print(f"   • Modules: {len(modules)}")
        print(f"   • Sessions: {len(sessions)}")
        print(f"   • Unit assignments: {unit_assignments}")
        print(f"   • Session assignments: {session_assignments}")
        print(f"   • Additional session assignments: {additional_assignments}")
        print(f"   • Sample unavailability: {unavailability_count}")
        print(f"   • Sample swap requests: {swap_requests_count}")
        print("\n🎯 You can now test the unavailability and swap systems!")
        print(f"   Login with: {facilitator.email}")
        print(f"   Note: Password should be set by existing facilitator creation script")

def create_additional_facilitators():
    """Create additional facilitators for swap testing"""
    
    additional_facilitators_data = [
        {
            'email': 'fac_sarah@example.com',
            'first_name': 'Sarah',
            'last_name': 'Chen',
            'phone_number': '+61 4 1111 2222',
            'staff_number': 'FAC101',
            'password': 'password123'
        },
        {
            'email': 'fac_michael@example.com',
            'first_name': 'Michael',
            'last_name': 'Torres',
            'phone_number': '+61 4 3333 4444',
            'staff_number': 'FAC102',
            'password': 'password123'
        },
        {
            'email': 'fac_emily@example.com',
            'first_name': 'Emily',
            'last_name': 'Johnson',
            'phone_number': '+61 4 5555 6666',
            'staff_number': 'FAC103',
            'password': 'password123'
        }
    ]
    
    created_facilitators = []
    
    for fac_data in additional_facilitators_data:
        # Check if facilitator already exists
        existing_facilitator = User.query.filter_by(email=fac_data['email']).first()
        if existing_facilitator:
            print(f"✓ Additional facilitator already exists: {fac_data['email']}")
            created_facilitators.append(existing_facilitator)
            continue
        
        # Create new facilitator
        facilitator = User(
            first_name=fac_data['first_name'],
            last_name=fac_data['last_name'],
            email=fac_data['email'],
            phone_number=fac_data['phone_number'],
            staff_number=fac_data['staff_number'],
            password_hash=generate_password_hash(fac_data['password']),
            role=UserRole.FACILITATOR
        )
        
        db.session.add(facilitator)
        db.session.commit()
        
        print(f"✓ Created additional facilitator: {fac_data['email']}")
        created_facilitators.append(facilitator)
    
    return created_facilitators

def assign_additional_facilitators_to_sessions(additional_facilitators, sessions):
    """Assign additional facilitators to some sessions for swap testing"""
    
    assignment_count = 0
    
    # Get active units for assignment
    active_units = [unit for unit in Unit.query.all() if unit.end_date and unit.end_date > date.today()]
    
    for i, facilitator in enumerate(additional_facilitators):
        # Assign facilitator to active units
        for unit in active_units[:2]:  # Assign to first 2 active units
            # Check if already assigned
            existing_assignment = UnitFacilitator.query.filter_by(
                unit_id=unit.id, 
                user_id=facilitator.id
            ).first()
            
            if not existing_assignment:
                unit_assignment = UnitFacilitator(
                    unit_id=unit.id,
                    user_id=facilitator.id
                )
                db.session.add(unit_assignment)
                assignment_count += 1
        
        # Assign facilitator to some sessions (every 3rd session starting from index i)
        for j, session in enumerate(sessions):
            if j % 3 == i and session.start_time > datetime.utcnow():
                # Check if already assigned
                existing_assignment = Assignment.query.filter_by(
                    session_id=session.id,
                    facilitator_id=facilitator.id
                ).first()
                
                if not existing_assignment:
                    session_assignment = Assignment(
                        session_id=session.id,
                        facilitator_id=facilitator.id,
                        is_confirmed=True
                    )
                    db.session.add(session_assignment)
                    assignment_count += 1
    
    db.session.commit()
    print(f"✓ Created {assignment_count} additional facilitator assignments")
    return assignment_count

def create_sample_swap_requests(main_facilitator, additional_facilitators, sessions):
    """Create sample swap requests for testing"""
    
    swap_requests_count = 0
    
    # Get future sessions assigned to main facilitator
    main_facilitator_assignments = Assignment.query.filter_by(
        facilitator_id=main_facilitator.id
    ).join(Session).filter(Session.start_time > datetime.utcnow()).all()
    
    # Get future sessions assigned to additional facilitators
    additional_facilitator_assignments = []
    for facilitator in additional_facilitators:
        assignments = Assignment.query.filter_by(
            facilitator_id=facilitator.id
        ).join(Session).filter(Session.start_time > datetime.utcnow()).all()
        additional_facilitator_assignments.extend(assignments)
    
    # Create sample swap requests
    sample_swap_requests = [
        {
            'requester_assignment': main_facilitator_assignments[0] if main_facilitator_assignments else None,
            'target_assignment': additional_facilitator_assignments[0] if additional_facilitator_assignments else None,
            'status': SwapStatus.FACILITATOR_PENDING,
            'reason': 'Medical appointment that cannot be rescheduled'
        },
        {
            'requester_assignment': main_facilitator_assignments[1] if len(main_facilitator_assignments) > 1 else None,
            'target_assignment': additional_facilitator_assignments[1] if len(additional_facilitator_assignments) > 1 else None,
            'status': SwapStatus.COORDINATOR_PENDING,
            'reason': 'Conference presentation',
            'facilitator_confirmed': True,
            'facilitator_confirmed_at': datetime.utcnow() - timedelta(days=1)
        },
        {
            'requester_assignment': main_facilitator_assignments[2] if len(main_facilitator_assignments) > 2 else None,
            'target_assignment': additional_facilitator_assignments[2] if len(additional_facilitator_assignments) > 2 else None,
            'status': SwapStatus.APPROVED,
            'reason': 'Family emergency',
            'facilitator_confirmed': True,
            'facilitator_confirmed_at': datetime.utcnow() - timedelta(days=2),
            'reviewed_at': datetime.utcnow() - timedelta(days=1),
            'reviewed_by': User.query.filter_by(role=UserRole.UNIT_COORDINATOR).first().id if User.query.filter_by(role=UserRole.UNIT_COORDINATOR).first() else None
        },
        {
            'requester_assignment': main_facilitator_assignments[3] if len(main_facilitator_assignments) > 3 else None,
            'target_assignment': additional_facilitator_assignments[3] if len(additional_facilitator_assignments) > 3 else None,
            'status': SwapStatus.FACILITATOR_DECLINED,
            'reason': 'Personal commitment',
            'facilitator_confirmed': False,
            'facilitator_confirmed_at': datetime.utcnow() - timedelta(days=1),
            'facilitator_decline_reason': 'Not available due to other commitments'
        }
    ]
    
    for swap_data in sample_swap_requests:
        if not swap_data['requester_assignment'] or not swap_data['target_assignment']:
            continue
            
        # Check if swap request already exists
        existing_request = SwapRequest.query.filter_by(
            requester_id=swap_data['requester_assignment'].facilitator_id,
            requester_assignment_id=swap_data['requester_assignment'].id,
            target_assignment_id=swap_data['target_assignment'].id
        ).first()
        
        if existing_request:
            continue
        
        # Create swap request
        swap_request = SwapRequest(
            requester_id=swap_data['requester_assignment'].facilitator_id,
            target_id=swap_data['target_assignment'].facilitator_id,
            requester_assignment_id=swap_data['requester_assignment'].id,
            target_assignment_id=swap_data['target_assignment'].id,
            reason=swap_data['reason'],
            status=swap_data['status'],
            facilitator_confirmed=swap_data.get('facilitator_confirmed', False),
            facilitator_confirmed_at=swap_data.get('facilitator_confirmed_at'),
            facilitator_decline_reason=swap_data.get('facilitator_decline_reason'),
            reviewed_at=swap_data.get('reviewed_at'),
            reviewed_by=swap_data.get('reviewed_by')
        )
        
        db.session.add(swap_request)
        swap_requests_count += 1
    
    db.session.commit()
    print(f"✓ Created {swap_requests_count} sample swap requests")
    return swap_requests_count

def clear_test_data():
    """Clear all test data"""
    
    print("🗑️ Clearing test data...")
    
    with app.app_context():
        try:
            # Clear in reverse order to avoid foreign key constraints
            # Clear swap requests first
            SwapRequest.query.delete()
            
            # Clear assignments
            Assignment.query.filter_by(facilitator_id=User.query.filter_by(email='fac_demo@example.com').first().id).delete()
            
            # Clear additional facilitator assignments
            additional_facilitator_emails = ['fac_sarah@example.com', 'fac_michael@example.com', 'fac_emily@example.com']
            for email in additional_facilitator_emails:
                facilitator = User.query.filter_by(email=email).first()
                if facilitator:
                    Assignment.query.filter_by(facilitator_id=facilitator.id).delete()
                    UnitFacilitator.query.filter_by(user_id=facilitator.id).delete()
            
            # Clear main facilitator data
            Unavailability.query.filter_by(user_id=User.query.filter_by(email='fac_demo@example.com').first().id).delete()
            UnitFacilitator.query.filter_by(user_id=User.query.filter_by(email='fac_demo@example.com').first().id).delete()
            
            # Clear sessions, modules, units
            Session.query.delete()
            Module.query.delete()
            Unit.query.delete()
            
            # Clear all test facilitators
            User.query.filter_by(email='fac_demo@example.com').delete()
            for email in additional_facilitator_emails:
                User.query.filter_by(email=email).delete()
            
            db.session.commit()
            print("✅ Test data cleared successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing test data: {e}")

def show_status():
    """Show current status of test data"""
    
    print("📊 Current test data status:")
    print("=" * 40)
    
    with app.app_context():
        # Check facilitator
        facilitator = User.query.filter_by(email='fac_demo@example.com').first()
        if facilitator:
            print(f"✅ Test facilitator: {facilitator.email}")
            
            # Check units
            unit_assignments = UnitFacilitator.query.filter_by(user_id=facilitator.id).all()
            print(f"📚 Units assigned: {len(unit_assignments)}")
            for assignment in unit_assignments:
                unit = Unit.query.get(assignment.unit_id)
                print(f"   • {unit.unit_code} - {unit.unit_name}")
                print(f"     Date range: {unit.start_date} to {unit.end_date}")
            
            # Check sessions
            session_assignments = Assignment.query.filter_by(facilitator_id=facilitator.id).all()
            print(f"📅 Session assignments: {len(session_assignments)}")
            
            # Check unavailability
            unavailability_count = Unavailability.query.filter_by(user_id=facilitator.id).count()
            print(f"🚫 Unavailability records: {unavailability_count}")
            
            # Check additional facilitators
            additional_facilitator_emails = ['fac_sarah@example.com', 'fac_michael@example.com', 'fac_emily@example.com']
            additional_count = 0
            for email in additional_facilitator_emails:
                if User.query.filter_by(email=email).first():
                    additional_count += 1
            print(f"👥 Additional facilitators: {additional_count}")
            
            # Check swap requests
            swap_requests_count = SwapRequest.query.count()
            print(f"🔄 Swap requests: {swap_requests_count}")
            
            if swap_requests_count > 0:
                # Show breakdown by status
                for status in SwapStatus:
                    count = SwapRequest.query.filter_by(status=status).count()
                    if count > 0:
                        print(f"   • {status.value}: {count}")
            
        else:
            print("❌ Test facilitator not found")
            print("   Run: python create_unavailability_test_data.py create")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "create":
            create_all_test_data()
        elif command == "clear":
            confirm = input("Are you sure you want to clear ALL test data? (yes/no): ")
            if confirm.lower() == "yes":
                clear_test_data()
            else:
                print("Operation cancelled.")
        elif command == "status":
            show_status()
        else:
            print("Unknown command. Use: create, clear, or status")
    else:
        print("Available commands:")
        print("  python create_unavailability_test_data.py create  - Create all test data")
        print("  python create_unavailability_test_data.py clear   - Clear all test data")
        print("  python create_unavailability_test_data.py status - Show current status")

if __name__ == "__main__":
    main()
