#!/usr/bin/env python3
"""
Comprehensive test for the new "Facilitator Skill Declarations" section in CSV report.
This test creates temporary data, generates assignments, verifies the CSV includes 
skill declarations (including "No Interest"), then cleans up.
"""

import sys
import os
from datetime import datetime, time, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    db, User, UserRole, Unit, Module, Session, 
    FacilitatorSkill, SkillLevel, UnitFacilitator, Assignment
)
from optimization_engine import (
    generate_optimal_assignments,
    prepare_facilitator_data,
    generate_schedule_report_csv
)

def cleanup_test_data(app):
    """Clean up test data"""
    with app.app_context():
        # Delete in correct order
        Assignment.query.filter(
            Assignment.session_id.in_(
                db.session.query(Session.id)
                .join(Module)
                .join(Unit)
                .filter(Unit.unit_code == 'CSVTEST')
            )
        ).delete(synchronize_session=False)
        
        FacilitatorSkill.query.filter(
            FacilitatorSkill.facilitator_id.in_(
                db.session.query(User.id)
                .filter(User.email.like('%@csvtest.com'))
            )
        ).delete(synchronize_session=False)
        
        UnitFacilitator.query.filter(
            UnitFacilitator.unit_id.in_(
                db.session.query(Unit.id)
                .filter(Unit.unit_code == 'CSVTEST')
            )
        ).delete(synchronize_session=False)
        
        Session.query.filter(
            Session.module_id.in_(
                db.session.query(Module.id)
                .join(Unit)
                .filter(Unit.unit_code == 'CSVTEST')
            )
        ).delete(synchronize_session=False)
        
        Module.query.filter(
            Module.unit_id.in_(
                db.session.query(Unit.id)
                .filter(Unit.unit_code == 'CSVTEST')
            )
        ).delete(synchronize_session=False)
        
        Unit.query.filter_by(unit_code='CSVTEST').delete()
        User.query.filter(User.email.like('%@csvtest.com')).delete()
        
        db.session.commit()

def run_test(app):
    """Main test function"""
    with app.app_context():
        print("\n" + "="*80)
        print("TEST: CSV Report with Facilitator Skill Declarations")
        print("="*80)
        
        # Clean up any existing test data
        cleanup_test_data(app)
        
        # Create Unit Coordinator
        uc = User(
            email='uc@csvtest.com',
            first_name='Test',
            last_name='Coordinator',
            role=UserRole.UNIT_COORDINATOR
        )
        uc.set_password('test123')
        db.session.add(uc)
        db.session.commit()
        
        # Create unit
        unit = Unit(
            unit_code='CSVTEST',
            unit_name='CSV Test Unit',
            year=2025,
            semester='Semester 1',
            created_by=uc.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90)
        )
        db.session.add(unit)
        db.session.commit()
        print(f"✓ Created unit: {unit.unit_code}")
        
        # Create modules
        mod1 = Module(unit_id=unit.id, module_name='Workshop A', module_type='workshop')
        mod2 = Module(unit_id=unit.id, module_name='Lab B', module_type='lab')
        db.session.add_all([mod1, mod2])
        db.session.commit()
        print(f"✓ Created modules: {mod1.module_name}, {mod2.module_name}")
        
        # Create sessions
        today = date.today()
        sess1 = Session(
            module_id=mod1.id, session_type='workshop',
            start_time=datetime.combine(today + timedelta(days=1), time(9, 0)),
            end_time=datetime.combine(today + timedelta(days=1), time(11, 0)),
            day_of_week=0, location='Room 1'
        )
        sess2 = Session(
            module_id=mod2.id, session_type='lab',
            start_time=datetime.combine(today + timedelta(days=2), time(14, 0)),
            end_time=datetime.combine(today + timedelta(days=2), time(16, 0)),
            day_of_week=1, location='Lab 1'
        )
        db.session.add_all([sess1, sess2])
        db.session.commit()
        print(f"✓ Created 2 sessions")
        
        # Create 3 facilitators with different skill profiles
        fac1 = User(
            email='alice@csvtest.com', first_name='Alice', last_name='Expert',
            role=UserRole.FACILITATOR, min_hours=0, max_hours=20
        )
        fac1.set_password('test123')
        
        fac2 = User(
            email='bob@csvtest.com', first_name='Bob', last_name='NotInterested',
            role=UserRole.FACILITATOR, min_hours=0, max_hours=20
        )
        fac2.set_password('test123')
        
        fac3 = User(
            email='carol@csvtest.com', first_name='Carol', last_name='Undeclared',
            role=UserRole.FACILITATOR, min_hours=0, max_hours=20
        )
        fac3.set_password('test123')
        
        db.session.add_all([fac1, fac2, fac3])
        db.session.commit()
        print(f"✓ Created 3 facilitators")
        
        # Add to unit
        for fac in [fac1, fac2, fac3]:
            uf = UnitFacilitator(unit_id=unit.id, user_id=fac.id)
            db.session.add(uf)
        db.session.commit()
        
        # Set up skills
        # Alice: PROFICIENT in both
        skill1_1 = FacilitatorSkill(facilitator_id=fac1.id, module_id=mod1.id, skill_level=SkillLevel.PROFICIENT)
        skill1_2 = FacilitatorSkill(facilitator_id=fac1.id, module_id=mod2.id, skill_level=SkillLevel.PROFICIENT)
        
        # Bob: PROFICIENT in Workshop A, NO_INTEREST in Lab B
        skill2_1 = FacilitatorSkill(facilitator_id=fac2.id, module_id=mod1.id, skill_level=SkillLevel.PROFICIENT)
        skill2_2 = FacilitatorSkill(facilitator_id=fac2.id, module_id=mod2.id, skill_level=SkillLevel.NO_INTEREST)
        
        # Carol: Has NOT declared skills for either module
        
        db.session.add_all([skill1_1, skill1_2, skill2_1, skill2_2])
        db.session.commit()
        print(f"✓ Created facilitator skills")
        
        print("\n📋 Skill Profile:")
        print("  Alice: PROFICIENT in Workshop A, PROFICIENT in Lab B")
        print("  Bob: PROFICIENT in Workshop A, NO_INTEREST in Lab B")
        print("  Carol: Not Declared for both modules")
        
        # Get facilitators and generate assignments
        facilitators_from_db = (
            db.session.query(User)
            .join(UnitFacilitator, User.id == UnitFacilitator.user_id)
            .filter(UnitFacilitator.unit_id == unit.id)
            .filter(User.role == UserRole.FACILITATOR)
            .all()
        )
        
        facilitators_prepared = prepare_facilitator_data(facilitators_from_db)
        assignments, conflicts = generate_optimal_assignments(facilitators_prepared)
        
        print(f"\n✓ Generated {len(assignments)} assignments")
        
        # Generate CSV report WITH new parameters
        print("\n" + "="*80)
        print("GENERATING CSV WITH SKILL DECLARATIONS")
        print("="*80)
        
        unit_display_name = f"{unit.unit_code} - {unit.unit_name}"
        csv_report = generate_schedule_report_csv(
            assignments, 
            unit_display_name,
            total_facilitators_in_pool=len(facilitators_from_db),
            unit_id=unit.id,
            all_facilitators=facilitators_from_db
        )
        
        print(f"✓ Generated CSV report ({len(csv_report)} characters)")
        
        # Parse and verify CSV content
        print("\n" + "="*80)
        print("VERIFICATION: Skill Declarations Section")
        print("="*80)
        
        csv_lines = csv_report.split('\n')
        
        # Find section
        section_start = -1
        section_end = -1
        for i, line in enumerate(csv_lines):
            if 'FACILITATOR SKILL DECLARATIONS' in line:
                section_start = i
            if section_start > -1 and section_end == -1:
                if line.strip() == '' and i > section_start + 2:
                    section_end = i
                    break
        
        if section_start == -1:
            print("❌ FAILED: 'FACILITATOR SKILL DECLARATIONS' section not found")
            return False
        
        print(f"✅ Found section at line {section_start}")
        
        # Extract section content
        section_lines = csv_lines[section_start:section_end if section_end > 0 else len(csv_lines)]
        print(f"\n📄 Section Content:")
        for line in section_lines[:15]:  # Show first 15 lines
            print(f"  {line}")
        
        # Count entries
        no_interest_entries = []
        not_declared_entries = []
        proficient_entries = []
        
        for line in section_lines[2:]:  # Skip header and title
            if not line.strip():
                break
            if 'No Interest' in line:
                no_interest_entries.append(line)
            if 'Not Declared' in line:
                not_declared_entries.append(line)
            if 'Proficient' in line:
                proficient_entries.append(line)
        
        print(f"\n📊 Statistics:")
        print(f"  Proficient entries: {len(proficient_entries)}")
        print(f"  No Interest entries: {len(no_interest_entries)}")
        print(f"  Not Declared entries: {len(not_declared_entries)}")
        
        # Verify expected content
        tests_passed = 0
        tests_total = 4
        
        # Test 1: Section exists
        if section_start > 0:
            print(f"\n✅ Test 1: Section exists in CSV")
            tests_passed += 1
        else:
            print(f"\n❌ Test 1: Section missing")
        
        # Test 2: "No Interest" entries present
        if len(no_interest_entries) > 0:
            print(f"✅ Test 2: Found {len(no_interest_entries)} 'No Interest' entries")
            print(f"     Example: {no_interest_entries[0]}")
            tests_passed += 1
        else:
            print(f"❌ Test 2: No 'No Interest' entries found")
        
        # Test 3: "Not Declared" entries present
        if len(not_declared_entries) > 0:
            print(f"✅ Test 3: Found {len(not_declared_entries)} 'Not Declared' entries")
            print(f"     Example: {not_declared_entries[0]}")
            tests_passed += 1
        else:
            print(f"❌ Test 3: No 'Not Declared' entries found")
        
        # Test 4: All facilitators represented
        # Should have: 3 facilitators × 2 modules = 6 total entries
        total_skill_entries = len(proficient_entries) + len(no_interest_entries) + len(not_declared_entries)
        expected_entries = len(facilitators_from_db) * Module.query.filter_by(unit_id=unit.id).count()
        
        if total_skill_entries == expected_entries:
            print(f"✅ Test 4: All facilitator-module combinations present ({total_skill_entries}/{expected_entries})")
            tests_passed += 1
        else:
            print(f"❌ Test 4: Missing entries ({total_skill_entries}/{expected_entries} expected)")
        
        print(f"\n" + "="*80)
        print(f"RESULTS: {tests_passed}/{tests_total} tests passed")
        print("="*80)
        
        if tests_passed == tests_total:
            print("\n✅ ALL TESTS PASSED!")
            print("\nVerified:")
            print("  ✅ Skill Declarations section appears in CSV")
            print("  ✅ 'No Interest' declarations are shown")
            print("  ✅ 'Not Declared' entries are shown")
            print("  ✅ All facilitators and modules are included")
            return True
        else:
            print(f"\n❌ {tests_total - tests_passed} TEST(S) FAILED")
            return False

if __name__ == "__main__":
    from application import app
    
    print("\n" + "="*80)
    print("CSV REPORT - FACILITATOR SKILL DECLARATIONS FEATURE TEST")
    print("="*80)
    
    try:
        success = run_test(app)
        
        # Clean up
        print("\n🧹 Cleaning up test data...")
        cleanup_test_data(app)
        print("  ✓ Cleanup complete")
        
        if success:
            print("\n✅ TEST SUITE PASSED\n")
            sys.exit(0)
        else:
            print("\n❌ TEST SUITE FAILED\n")
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

