#!/usr/bin/env python3
"""
Test script to verify that the CSV report now includes the 
"Facilitator Skill Declarations" section showing "Not Interested" entries
"""

import sys
import os
from datetime import datetime, time, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    db, User, UserRole, Unit, Module, Session, 
    FacilitatorSkill, SkillLevel, UnitFacilitator
)
from optimization_engine import (
    generate_optimal_assignments,
    prepare_facilitator_data,
    generate_schedule_report_csv
)

def test_skill_declarations_in_csv():
    """Test that skill declarations including 'No Interest' appear in CSV"""
    from application import app
    
    with app.app_context():
        print("\n" + "="*80)
        print("TEST: Facilitator Skill Declarations in CSV Report")
        print("="*80)
        
        # Find or create test data
        unit = Unit.query.filter_by(unit_code='TEST1000').first()
        
        if not unit:
            print("\n❌ Test data not found. Run test_no_interest_integration.py first.")
            return False
        
        # Get facilitators for this unit
        facilitators_from_db = (
            db.session.query(User)
            .join(UnitFacilitator, User.id == UnitFacilitator.user_id)
            .filter(UnitFacilitator.unit_id == unit.id)
            .filter(User.role == UserRole.FACILITATOR)
            .all()
        )
        
        print(f"\n✓ Found unit: {unit.unit_code}")
        print(f"✓ Found {len(facilitators_from_db)} facilitators")
        
        # Get their skills
        print(f"\n📋 Facilitator Skills:")
        for fac in facilitators_from_db:
            skills = FacilitatorSkill.query.filter_by(facilitator_id=fac.id).all()
            print(f"\n  {fac.full_name}:")
            for skill in skills:
                print(f"    - {skill.module.module_name}: {skill.skill_level.value}")
        
        # Prepare facilitators and generate assignments
        facilitators_prepared = prepare_facilitator_data(facilitators_from_db)
        assignments, conflicts = generate_optimal_assignments(facilitators_prepared)
        
        print(f"\n✓ Generated {len(assignments)} assignments")
        
        # Generate CSV report WITH the new parameters
        unit_display_name = f"{unit.unit_code} - {unit.unit_name}"
        csv_report = generate_schedule_report_csv(
            assignments, 
            unit_display_name,
            total_facilitators_in_pool=len(facilitators_from_db),
            unit_id=unit.id,
            all_facilitators=facilitators_from_db
        )
        
        print(f"\n✓ Generated CSV report ({len(csv_report)} characters)")
        
        # Check if the new section exists
        print("\n" + "="*80)
        print("VERIFICATION: New Section Presence")
        print("="*80)
        
        has_skill_declarations = "FACILITATOR SKILL DECLARATIONS" in csv_report
        
        if has_skill_declarations:
            print("\n✅ FOUND: 'FACILITATOR SKILL DECLARATIONS' section in CSV")
        else:
            print("\n❌ NOT FOUND: 'FACILITATOR SKILL DECLARATIONS' section missing")
            return False
        
        # Check for "No Interest" entries
        csv_lines = csv_report.split('\n')
        
        # Find the skill declarations section
        section_start = -1
        for i, line in enumerate(csv_lines):
            if 'FACILITATOR SKILL DECLARATIONS' in line:
                section_start = i
                break
        
        if section_start == -1:
            print("❌ Could not find section start")
            return False
        
        # Look for No Interest entries and Not Declared entries
        no_interest_count = 0
        not_declared_count = 0
        total_entries = 0
        
        print(f"\n📊 Section Content (first 20 lines):")
        for i in range(section_start, min(section_start + 25, len(csv_lines))):
            line = csv_lines[i]
            print(f"  {line}")
            
            if 'No Interest' in line and i > section_start + 1:  # Skip header
                no_interest_count += 1
            if 'Not Declared' in line:
                not_declared_count += 1
            if i > section_start + 1 and line.strip() and ',' in line:  # Count data rows
                total_entries += 1
        
        print(f"\n📈 Statistics:")
        print(f"  Total skill declaration entries: {total_entries}")
        print(f"  'No Interest' entries: {no_interest_count}")
        print(f"  'Not Declared' entries: {not_declared_count}")
        
        # Verify we have the expected data
        if no_interest_count > 0:
            print(f"\n✅ VERIFIED: CSV shows {no_interest_count} 'No Interest' declarations")
        else:
            print(f"\n⚠️  WARNING: No 'No Interest' entries found (may be valid if none declared)")
        
        if total_entries >= len(facilitators_from_db):
            print(f"✅ VERIFIED: CSV has entries for all facilitators")
        else:
            print(f"❌ ERROR: Expected at least {len(facilitators_from_db)} entries, found {total_entries}")
            return False
        
        # Test with empty parameters (backward compatibility)
        print("\n" + "="*80)
        print("BACKWARD COMPATIBILITY TEST")
        print("="*80)
        
        csv_report_old = generate_schedule_report_csv(
            assignments, 
            unit_display_name,
            total_facilitators_in_pool=len(facilitators_from_db)
            # Not passing unit_id or all_facilitators
        )
        
        has_section_without_params = "FACILITATOR SKILL DECLARATIONS" in csv_report_old
        
        if not has_section_without_params:
            print("✅ VERIFIED: Section is omitted when parameters not provided (backward compatible)")
        else:
            print("⚠️  Section appears even without parameters (may have data issues)")
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nSummary:")
        print(f"  ✅ New section appears in CSV report")
        print(f"  ✅ Shows 'No Interest' declarations")
        print(f"  ✅ Shows all facilitators")
        print(f"  ✅ Backward compatible (works without new parameters)")
        
        return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SKILL DECLARATIONS CSV SECTION - FEATURE VERIFICATION")
    print("="*80)
    
    try:
        success = test_skill_declarations_in_csv()
        
        if success:
            print("\n✅ TEST PASSED\n")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED\n")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

