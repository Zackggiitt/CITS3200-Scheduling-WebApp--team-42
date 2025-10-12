#!/usr/bin/env python3
"""
Integration test for NO_INTEREST constraint with real database

This test creates test data in the database and verifies:
1. Facilitators with NO_INTEREST are not assigned to sessions
2. CSV report correctly shows skill levels for assignments
3. No "No Interest" assignments appear when other facilitators are available
"""

import sys
import os
from datetime import datetime, time, date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and database models
from models import (
    db, User, UserRole, Unit, Module, Session, 
    FacilitatorSkill, SkillLevel, UnitFacilitator, Assignment
)
from optimization_engine import (
    generate_optimal_assignments,
    prepare_facilitator_data,
    generate_schedule_report_csv
)


def setup_test_data(app):
    """Create test data for integration testing"""
    with app.app_context():
        print("\n📊 Setting up test data...")
        
        # Clean up any existing test data
        Assignment.query.filter(
            Assignment.session_id.in_(
                db.session.query(Session.id)
                .join(Module)
                .join(Unit)
                .filter(Unit.unit_code == 'TEST1000')
            )
        ).delete(synchronize_session=False)
        
        FacilitatorSkill.query.filter(
            FacilitatorSkill.facilitator_id.in_(
                db.session.query(User.id)
                .filter(User.email.like('%@test-no-interest.com'))
            )
        ).delete(synchronize_session=False)
        
        UnitFacilitator.query.filter(
            UnitFacilitator.unit_id.in_(
                db.session.query(Unit.id)
                .filter(Unit.unit_code == 'TEST1000')
            )
        ).delete(synchronize_session=False)
        
        Session.query.filter(
            Session.module_id.in_(
                db.session.query(Module.id)
                .join(Unit)
                .filter(Unit.unit_code == 'TEST1000')
            )
        ).delete(synchronize_session=False)
        
        Module.query.filter(
            Module.unit_id.in_(
                db.session.query(Unit.id)
                .filter(Unit.unit_code == 'TEST1000')
            )
        ).delete(synchronize_session=False)
        
        Unit.query.filter_by(unit_code='TEST1000').delete()
        
        User.query.filter(User.email.like('%@test-no-interest.com')).delete()
        
        db.session.commit()
        
        # Create a test Unit Coordinator
        uc = User.query.filter_by(email='uc@test-no-interest.com').first()
        if not uc:
            uc = User(
                email='uc@test-no-interest.com',
                first_name='Test',
                last_name='Coordinator',
                role=UserRole.UNIT_COORDINATOR
            )
            uc.set_password('test123')
            db.session.add(uc)
            db.session.commit()
        
        # Create test unit
        unit = Unit(
            unit_code='TEST1000',
            unit_name='No Interest Test Unit',
            year=2025,
            semester='Semester 1',
            created_by=uc.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90)
        )
        db.session.add(unit)
        db.session.commit()
        print(f"  ✓ Created unit: {unit.unit_code}")
        
        # Create test modules
        module1 = Module(
            unit_id=unit.id,
            module_name='Python Workshop',
            module_type='workshop'
        )
        module2 = Module(
            unit_id=unit.id,
            module_name='Java Lab',
            module_type='lab'
        )
        db.session.add_all([module1, module2])
        db.session.commit()
        print(f"  ✓ Created modules: {module1.module_name}, {module2.module_name}")
        
        # Create sessions
        today = date.today()
        session1 = Session(
            module_id=module1.id,
            session_type='workshop',
            start_time=datetime.combine(today + timedelta(days=1), time(9, 0)),
            end_time=datetime.combine(today + timedelta(days=1), time(11, 0)),
            day_of_week=0,  # Monday
            location='Room 101'
        )
        session2 = Session(
            module_id=module1.id,
            session_type='workshop',
            start_time=datetime.combine(today + timedelta(days=2), time(14, 0)),
            end_time=datetime.combine(today + timedelta(days=2), time(16, 0)),
            day_of_week=1,  # Tuesday
            location='Room 102'
        )
        session3 = Session(
            module_id=module2.id,
            session_type='lab',
            start_time=datetime.combine(today + timedelta(days=3), time(10, 0)),
            end_time=datetime.combine(today + timedelta(days=3), time(12, 0)),
            day_of_week=2,  # Wednesday
            location='Lab A'
        )
        db.session.add_all([session1, session2, session3])
        db.session.commit()
        print(f"  ✓ Created 3 sessions")
        
        # Create test facilitators
        # Facilitator 1: NO_INTEREST in Python Workshop, PROFICIENT in Java Lab
        fac1 = User(
            email='fac1@test-no-interest.com',
            first_name='Alice',
            last_name='NoInterest',
            role=UserRole.FACILITATOR,
            min_hours=0,
            max_hours=20
        )
        fac1.set_password('test123')
        
        # Facilitator 2: PROFICIENT in Python Workshop, NO_INTEREST in Java Lab
        fac2 = User(
            email='fac2@test-no-interest.com',
            first_name='Bob',
            last_name='PythonExpert',
            role=UserRole.FACILITATOR,
            min_hours=0,
            max_hours=20
        )
        fac2.set_password('test123')
        
        # Facilitator 3: HAVE_SOME_SKILL in both (backup option)
        fac3 = User(
            email='fac3@test-no-interest.com',
            first_name='Carol',
            last_name='Generalist',
            role=UserRole.FACILITATOR,
            min_hours=0,
            max_hours=20
        )
        fac3.set_password('test123')
        
        db.session.add_all([fac1, fac2, fac3])
        db.session.commit()
        print(f"  ✓ Created 3 facilitators")
        
        # Add facilitators to unit
        for fac in [fac1, fac2, fac3]:
            uf = UnitFacilitator(unit_id=unit.id, user_id=fac.id)
            db.session.add(uf)
        db.session.commit()
        
        # Set up skills
        # Facilitator 1: NO_INTEREST in module1, PROFICIENT in module2
        skill1_1 = FacilitatorSkill(
            facilitator_id=fac1.id,
            module_id=module1.id,
            skill_level=SkillLevel.NO_INTEREST
        )
        skill1_2 = FacilitatorSkill(
            facilitator_id=fac1.id,
            module_id=module2.id,
            skill_level=SkillLevel.PROFICIENT
        )
        
        # Facilitator 2: PROFICIENT in module1, NO_INTEREST in module2
        skill2_1 = FacilitatorSkill(
            facilitator_id=fac2.id,
            module_id=module1.id,
            skill_level=SkillLevel.PROFICIENT
        )
        skill2_2 = FacilitatorSkill(
            facilitator_id=fac2.id,
            module_id=module2.id,
            skill_level=SkillLevel.NO_INTEREST
        )
        
        # Facilitator 3: HAVE_SOME_SKILL in both
        skill3_1 = FacilitatorSkill(
            facilitator_id=fac3.id,
            module_id=module1.id,
            skill_level=SkillLevel.HAVE_SOME_SKILL
        )
        skill3_2 = FacilitatorSkill(
            facilitator_id=fac3.id,
            module_id=module2.id,
            skill_level=SkillLevel.HAVE_SOME_SKILL
        )
        
        db.session.add_all([skill1_1, skill1_2, skill2_1, skill2_2, skill3_1, skill3_2])
        db.session.commit()
        print(f"  ✓ Created facilitator skills")
        
        print("  ✅ Test data setup complete\n")
        
        return {
            'unit_id': unit.id,
            'module_ids': {'python': module1.id, 'java': module2.id},
            'session_ids': [session1.id, session2.id, session3.id],
            'facilitator_ids': {'fac1': fac1.id, 'fac2': fac2.id, 'fac3': fac3.id}
        }


def run_integration_test(app):
    """Run the integration test"""
    with app.app_context():
        print("\n" + "="*80)
        print("INTEGRATION TEST: NO_INTEREST Constraint with Real Database")
        print("="*80)
        
        # Setup test data
        test_data = setup_test_data(app)
        unit_id = test_data['unit_id']
        module_ids = test_data['module_ids']
        facilitator_ids = test_data['facilitator_ids']
        
        # Fetch the objects we need
        unit = Unit.query.get(unit_id)
        
        print("\n📋 Test Setup:")
        print(f"  - Facilitator 1 (Alice): NO_INTEREST in Python, PROFICIENT in Java")
        print(f"  - Facilitator 2 (Bob): PROFICIENT in Python, NO_INTEREST in Java")
        print(f"  - Facilitator 3 (Carol): HAVE_SOME_SKILL in both")
        print(f"  - Sessions: 2x Python Workshop, 1x Java Lab")
        
        # Get facilitators for this unit
        facilitators_from_db = (
            db.session.query(User)
            .join(UnitFacilitator, User.id == UnitFacilitator.user_id)
            .filter(UnitFacilitator.unit_id == unit_id)
            .filter(User.role == UserRole.FACILITATOR)
            .all()
        )
        
        print(f"\n  ✓ Found {len(facilitators_from_db)} facilitators in database")
        
        # Prepare facilitator data for optimization
        facilitators_prepared = prepare_facilitator_data(facilitators_from_db)
        print(f"  ✓ Prepared facilitator data for optimization")
        
        # Generate assignments
        print("\n🔄 Running optimization engine...")
        assignments, conflicts = generate_optimal_assignments(facilitators_prepared, unit_id)
        
        print(f"\n📊 Results:")
        print(f"  - Assignments created: {len(assignments)}")
        print(f"  - Conflicts: {len(conflicts)}")
        
        if conflicts:
            print("\n  Conflicts:")
            for conflict in conflicts:
                print(f"    - {conflict}")
        
        # Verify NO_INTEREST constraint
        print("\n" + "="*80)
        print("VERIFICATION: Checking NO_INTEREST Constraint")
        print("="*80)
        
        violations = []
        
        for assignment in assignments:
            fac_id = assignment['facilitator']['id']
            module_id = assignment['session']['module_id']
            fac_name = assignment['facilitator']['name']
            module_name = assignment['session']['module_name']
            
            # Check if this facilitator has NO_INTEREST in this module
            skill = FacilitatorSkill.query.filter_by(
                facilitator_id=fac_id,
                module_id=module_id
            ).first()
            
            if skill and skill.skill_level == SkillLevel.NO_INTEREST:
                violations.append({
                    'facilitator': fac_name,
                    'module': module_name,
                    'skill_level': skill.skill_level.value
                })
                print(f"  ❌ VIOLATION: {fac_name} assigned to {module_name} with NO_INTEREST")
        
        if not violations:
            print("  ✅ NO VIOLATIONS FOUND: All assignments respect NO_INTEREST constraint")
        
        # Verify expected assignments
        print("\n" + "="*80)
        print("VERIFICATION: Expected Assignment Pattern")
        print("="*80)
        
        alice_sessions = [a for a in assignments if a['facilitator']['id'] == facilitator_ids['fac1']]
        bob_sessions = [a for a in assignments if a['facilitator']['id'] == facilitator_ids['fac2']]
        carol_sessions = [a for a in assignments if a['facilitator']['id'] == facilitator_ids['fac3']]
        
        print(f"\n  Alice (NO_INTEREST in Python):")
        print(f"    - Python Workshop sessions: {len([s for s in alice_sessions if 'Python' in s['session']['module_name']])}")
        print(f"    - Java Lab sessions: {len([s for s in alice_sessions if 'Java' in s['session']['module_name']])}")
        
        alice_python_count = len([s for s in alice_sessions if 'Python' in s['session']['module_name']])
        if alice_python_count == 0:
            print(f"    ✅ CORRECT: Alice not assigned to Python (has NO_INTEREST)")
        else:
            print(f"    ❌ ERROR: Alice assigned to Python despite NO_INTEREST")
        
        print(f"\n  Bob (NO_INTEREST in Java):")
        print(f"    - Python Workshop sessions: {len([s for s in bob_sessions if 'Python' in s['session']['module_name']])}")
        print(f"    - Java Lab sessions: {len([s for s in bob_sessions if 'Java' in s['session']['module_name']])}")
        
        bob_java_count = len([s for s in bob_sessions if 'Java' in s['session']['module_name']])
        if bob_java_count == 0:
            print(f"    ✅ CORRECT: Bob not assigned to Java (has NO_INTEREST)")
        else:
            print(f"    ❌ ERROR: Bob assigned to Java despite NO_INTEREST")
        
        print(f"\n  Carol (HAVE_SOME_SKILL in both):")
        print(f"    - Python Workshop sessions: {len([s for s in carol_sessions if 'Python' in s['session']['module_name']])}")
        print(f"    - Java Lab sessions: {len([s for s in carol_sessions if 'Java' in s['session']['module_name']])}")
        
        # Generate CSV report
        print("\n" + "="*80)
        print("CSV REPORT VERIFICATION")
        print("="*80)
        
        csv_content = generate_schedule_report_csv(
            assignments,
            f"{unit.unit_code} - {unit.unit_name}",
            total_facilitators_in_pool=len(facilitators_from_db)
        )
        
        print("\n  ✓ Generated CSV report")
        
        # Check CSV content for "No Interest" entries
        csv_lines = csv_content.split('\n')
        
        # Find the skill distribution section
        in_skill_dist = False
        no_interest_count = 0
        
        for i, line in enumerate(csv_lines):
            if 'SKILL LEVEL DISTRIBUTION' in line:
                in_skill_dist = True
            elif in_skill_dist and 'No Interest' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    try:
                        no_interest_count = int(parts[1].strip())
                    except ValueError:
                        pass
                break
        
        print(f"\n  CSV Report - Skill Level Distribution:")
        print(f"    - 'No Interest' assignments in CSV: {no_interest_count}")
        
        if no_interest_count == 0:
            print(f"    ✅ CORRECT: CSV shows 0 'No Interest' assignments")
        else:
            print(f"    ❌ WARNING: CSV shows {no_interest_count} 'No Interest' assignments")
        
        # Final verdict
        print("\n" + "="*80)
        print("FINAL VERDICT")
        print("="*80)
        
        all_passed = (
            len(violations) == 0 and
            alice_python_count == 0 and
            bob_java_count == 0 and
            no_interest_count == 0
        )
        
        if all_passed:
            print("\n✅ ALL TESTS PASSED!")
            print("  - NO_INTEREST constraint is correctly enforced")
            print("  - CSV report accurately reflects skill levels")
            print("  - No facilitators assigned to sessions they're not interested in")
        else:
            print("\n❌ TEST FAILURES DETECTED:")
            if len(violations) > 0:
                print(f"  - {len(violations)} constraint violations found")
            if alice_python_count > 0:
                print(f"  - Alice incorrectly assigned to Python sessions")
            if bob_java_count > 0:
                print(f"  - Bob incorrectly assigned to Java sessions")
            if no_interest_count > 0:
                print(f"  - CSV report shows {no_interest_count} NO_INTEREST assignments")
        
        print("="*80)
        
        return all_passed


def cleanup_test_data(app):
    """Clean up test data after testing"""
    with app.app_context():
        print("\n🧹 Cleaning up test data...")
        
        # Delete in correct order due to foreign key constraints
        Assignment.query.filter(
            Assignment.session_id.in_(
                db.session.query(Session.id)
                .join(Module)
                .join(Unit)
                .filter(Unit.unit_code == 'TEST1000')
            )
        ).delete(synchronize_session=False)
        
        FacilitatorSkill.query.filter(
            FacilitatorSkill.facilitator_id.in_(
                db.session.query(User.id)
                .filter(User.email.like('%@test-no-interest.com'))
            )
        ).delete(synchronize_session=False)
        
        UnitFacilitator.query.filter(
            UnitFacilitator.unit_id.in_(
                db.session.query(Unit.id)
                .filter(Unit.unit_code == 'TEST1000')
            )
        ).delete(synchronize_session=False)
        
        Session.query.filter(
            Session.module_id.in_(
                db.session.query(Module.id)
                .join(Unit)
                .filter(Unit.unit_code == 'TEST1000')
            )
        ).delete(synchronize_session=False)
        
        Module.query.filter(
            Module.unit_id.in_(
                db.session.query(Unit.id)
                .filter(Unit.unit_code == 'TEST1000')
            )
        ).delete(synchronize_session=False)
        
        Unit.query.filter_by(unit_code='TEST1000').delete()
        User.query.filter(User.email.like('%@test-no-interest.com')).delete()
        
        db.session.commit()
        print("  ✓ Cleanup complete\n")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("NO_INTEREST CONSTRAINT - INTEGRATION TEST WITH DATABASE")
    print("="*80)
    
    # Import Flask app
    from application import app
    
    try:
        # Run the integration test
        success = run_integration_test(app)
        
        # Clean up
        cleanup_test_data(app)
        
        if success:
            print("\n✅ INTEGRATION TEST PASSED\n")
            sys.exit(0)
        else:
            print("\n❌ INTEGRATION TEST FAILED\n")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        
        # Attempt cleanup
        try:
            cleanup_test_data(app)
        except:
            pass
        
        sys.exit(1)

