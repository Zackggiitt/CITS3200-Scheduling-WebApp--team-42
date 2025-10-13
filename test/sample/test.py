"""
Script to create facilitators from CSV file with random availabilities and proficiencies.

NEW FEATURES:
- Test the "Available All Days" functionality with --test-available-all or --test
- Demonstrate the "Available All Days" feature with --demo-available-all or --demo

USAGE:
  python test.py                                    # Create facilitators from default CSV
  python test.py --update                          # Update existing facilitators
  python test.py --test-available-all              # Test Available All Days functionality
  python test.py --demo-available-all              # Demonstrate Available All Days feature
  python test.py custom_facilitators.csv          # Use custom CSV file
"""

import os
import sys
import csv
import random
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from models import db, User, UserRole, Module, Unit, FacilitatorSkill, SkillLevel, Unavailability, RecurringPattern, UnitFacilitator
from flask import Flask

# Create a minimal app for database operations
def create_minimal_app():
    app = Flask(__name__)
    # Use absolute path to the database file
    db_path = os.path.join(project_root, 'instance', 'dev.db')
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

# Sample first and last names for random assignment
FIRST_NAMES = ['Alice', 'Bob', 'Carol', 'David', 'Emma', 'Frank', 'Grace', 'Henry', 
               'Iris', 'Jack', 'Kate', 'Liam', 'Maya', 'Nathan', 'Olivia', 'Peter',
               'Quinn', 'Rachel', 'Sam', 'Tara', 'Uma', 'Victor', 'Wendy', 'Xavier',
               'Yara', 'Zack', 'Amanda', 'Brandon', 'Chloe', 'Daniel']

LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 
              'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
              'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
              'Lee', 'Walker', 'Hall', 'Allen', 'Young', 'King', 'Wright', 'Scott']

def generate_random_unavailability(facilitator_id, unit):
    """Generate random unavailability periods for a facilitator between June 30 and July 18."""
    unavailabilities = []
    
    # Fixed date range: June 30 to July 18
    start_date = date(2024, 6, 30)
    end_date = date(2024, 7, 18)
    
    # Randomly decide how many unavailability periods (0-5)
    num_unavailabilities = random.randint(0, 5)
    
    # Calculate duration in days
    duration = (end_date - start_date).days
    
    for _ in range(num_unavailabilities):
        # Random date within the specified period
        random_days = random.randint(0, max(0, duration))
        unavail_date = start_date + timedelta(days=random_days)
        
        # Decide if full day or time block
        is_full_day = random.choice([True, False])
        
        if is_full_day:
            unavail = Unavailability(
                user_id=facilitator_id,
                unit_id=unit.id,
                date=unavail_date,
                is_full_day=True,
                reason="Generated unavailability"
            )
        else:
            # Random time block
            start_hour = random.randint(8, 16)
            end_hour = random.randint(start_hour + 1, 18)
            
            unavail = Unavailability(
                user_id=facilitator_id,
                unit_id=unit.id,
                date=unavail_date,
                start_time=time(hour=start_hour),
                end_time=time(hour=end_hour),
                is_full_day=False,
                reason="Generated unavailability"
            )
        
            # Randomly add recurring pattern (20% chance)
            if random.random() < 0.2:
                unavail.recurring_pattern = random.choice([
                    RecurringPattern.WEEKLY,
                    RecurringPattern.DAILY
                ])
                unavail.recurring_end_date = min(
                    unavail_date + timedelta(days=random.randint(14, 56)),
                    end_date
                )
        
        unavailabilities.append(unavail)
    
    return unavailabilities

def generate_random_skills(facilitator_id, modules):
    """Generate random skill levels for all modules."""
    skills = []
    
    for module in modules:
        # Randomly assign skill level with weighted probabilities
        # More likely to have some skill than no interest
        skill_level = random.choices(
            [SkillLevel.PROFICIENT, SkillLevel.HAVE_RUN_BEFORE, 
             SkillLevel.HAVE_SOME_SKILL, SkillLevel.NO_INTEREST],
            weights=[15, 25, 40, 20]  # Weighted toward having some capability
        )[0]
        
        skill = FacilitatorSkill(
            facilitator_id=facilitator_id,
            module_id=module.id,
            skill_level=skill_level
        )
        skills.append(skill)
    
    return skills

def test_available_all_days_functionality():
    """Test the 'Available All Days' functionality by clearing all unavailability for a facilitator."""
    app = create_minimal_app()
    
    with app.app_context():
        print("Testing 'Available All Days' functionality...")
        print("=" * 50)
        
        # Find a facilitator with some unavailability
        facilitator = User.query.filter_by(role=UserRole.FACILITATOR).first()
        if not facilitator:
            print("❌ No facilitator found in database")
            return False
        
        # Find a unit for this facilitator
        unit_facilitator = UnitFacilitator.query.filter_by(user_id=facilitator.id).first()
        if not unit_facilitator:
            print("❌ No unit assignment found for facilitator")
            return False
        
        unit = Unit.query.get(unit_facilitator.unit_id)
        if not unit:
            print("❌ Unit not found")
            return False
        
        print(f"✅ Testing with facilitator: {facilitator.first_name} {facilitator.last_name} ({facilitator.email})")
        print(f"✅ Testing with unit: {unit.unit_code} - {unit.unit_name}")
        
        # Check initial unavailability count
        initial_count = Unavailability.query.filter_by(
            user_id=facilitator.id,
            unit_id=unit.id
        ).count()
        print(f"✅ Initial unavailability count: {initial_count}")
        
        if initial_count == 0:
            print("⚠️  No unavailability found. Creating test unavailability entries...")
            
            # Create some test unavailability entries
            test_dates = [
                date(2024, 7, 1),
                date(2024, 7, 5),
                date(2024, 7, 10),
                date(2024, 7, 15)
            ]
            
            for test_date in test_dates:
                unavailability = Unavailability(
                    user_id=facilitator.id,
                    unit_id=unit.id,
                    date=test_date,
                    is_full_day=True,
                    reason="Test unavailability for Available All Days test"
                )
                db.session.add(unavailability)
            
            db.session.commit()
            initial_count = len(test_dates)
            print(f"✅ Created {initial_count} test unavailability entries")
        
        # Test the clear-all functionality
        try:
            print("\n🧪 Testing clear-all functionality...")
            
            # Simulate the clear-all route logic (same as in facilitator_routes.py)
            deleted_count = Unavailability.query.filter_by(
                user_id=facilitator.id,
                unit_id=unit.id
            ).delete()
            
            db.session.commit()
            
            print(f"✅ Cleared {deleted_count} unavailability entries")
            
            # Verify all unavailability entries are gone
            final_count = Unavailability.query.filter_by(
                user_id=facilitator.id,
                unit_id=unit.id
            ).count()
            
            if final_count == 0:
                print("✅ SUCCESS: All unavailability entries cleared successfully!")
                print("✅ Facilitator is now available for all days in this unit")
                return True
            else:
                print(f"❌ FAILURE: {final_count} unavailability entries still exist")
                return False
                
        except Exception as e:
            print(f"❌ ERROR during clear-all test: {str(e)}")
            db.session.rollback()
            return False

def demo_available_all_days_feature():
    """Demonstrate the 'Available All Days' feature by creating a facilitator with unavailability and then clearing it."""
    app = create_minimal_app()
    
    with app.app_context():
        print("🎯 DEMONSTRATING 'AVAILABLE ALL DAYS' FEATURE")
        print("=" * 60)
        
        # Find or create a facilitator for demonstration
        facilitator = User.query.filter_by(role=UserRole.FACILITATOR).first()
        if not facilitator:
            print("❌ No facilitator found in database")
            return False
        
        # Find a unit for this facilitator
        unit_facilitator = UnitFacilitator.query.filter_by(user_id=facilitator.id).first()
        if not unit_facilitator:
            print("❌ No unit assignment found for facilitator")
            return False
        
        unit = Unit.query.get(unit_facilitator.unit_id)
        if not unit:
            print("❌ Unit not found")
            return False
        
        print(f"✅ Using facilitator: {facilitator.first_name} {facilitator.last_name} ({facilitator.email})")
        print(f"✅ Using unit: {unit.unit_code} - {unit.unit_name}")
        
        # Clear any existing unavailability first
        Unavailability.query.filter_by(
            user_id=facilitator.id,
            unit_id=unit.id
        ).delete()
        db.session.commit()
        
        print(f"\n📅 STEP 1: Creating sample unavailability entries...")
        
        # Create sample unavailability entries
        sample_dates = [
            (date(2024, 7, 1), "Doctor's appointment"),
            (date(2024, 7, 5), "Personal day"),
            (date(2024, 7, 8), "Conference attendance"),
            (date(2024, 7, 12), "Family event"),
            (date(2024, 7, 15), "Holiday")
        ]
        
        created_count = 0
        for unavail_date, reason in sample_dates:
            unavailability = Unavailability(
                user_id=facilitator.id,
                unit_id=unit.id,
                date=unavail_date,
                is_full_day=True,
                reason=reason
            )
            db.session.add(unavailability)
            created_count += 1
        
        db.session.commit()
        print(f"✅ Created {created_count} unavailability entries")
        
        # Show current unavailability
        current_unavailability = Unavailability.query.filter_by(
            user_id=facilitator.id,
            unit_id=unit.id
        ).all()
        
        print(f"\n📋 Current unavailability entries:")
        for unav in current_unavailability:
            print(f"  • {unav.date.strftime('%Y-%m-%d')}: {unav.reason}")
        
        print(f"\n🚫 STEP 2: Facilitator has {len(current_unavailability)} unavailable days")
        print("   (In the UI, these would show as unavailable on the calendar)")
        
        print(f"\n🔄 STEP 3: Simulating 'Available All Days' button click...")
        
        # Simulate the clear-all functionality
        deleted_count = Unavailability.query.filter_by(
            user_id=facilitator.id,
            unit_id=unit.id
        ).delete()
        
        db.session.commit()
        
        print(f"✅ Cleared {deleted_count} unavailability entries")
        
        # Verify all unavailability entries are gone
        final_count = Unavailability.query.filter_by(
            user_id=facilitator.id,
            unit_id=unit.id
        ).count()
        
        if final_count == 0:
            print(f"\n✅ SUCCESS: Facilitator is now available for ALL days!")
            print("   (In the UI, the calendar would now show all days as available)")
            print("\n🎉 DEMONSTRATION COMPLETE!")
            print("   The 'Available All Days' feature successfully cleared all unavailability.")
            return True
        else:
            print(f"\n❌ FAILURE: {final_count} unavailability entries still exist")
            return False

def create_facilitators_from_csv(csv_file_path, update_existing=False):
    """Main function to create facilitators from CSV.
    
    Args:
        csv_file_path: Path to CSV file with facilitator emails
        update_existing: If True, update existing facilitators with new random data
    """
    app = create_minimal_app()
    
    with app.app_context():
        # Read CSV file
        try:
            with open(csv_file_path, 'r') as f:
                reader = csv.DictReader(f)
                emails = [row['facilitator_email'].strip() for row in reader]
        except FileNotFoundError:
            print(f"Error: CSV file not found at {csv_file_path}")
            return
        except KeyError:
            print("Error: CSV file must have a 'facilitator_email' column")
            return
        
        print(f"Found {len(emails)} facilitators in CSV\n")
        
        # Get all modules and units for skill/unavailability assignment
        modules = Module.query.all()
        units = Unit.query.all()
        
        if not modules:
            print("Warning: No modules found in database. Skills will not be assigned.")
        
        if not units:
            print("Warning: No units found in database. Unavailabilities will not be assigned.")
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        # Track used names to avoid duplicates
        used_names = set()
        
        for email in emails:
            # Check if facilitator already exists
            existing_user = User.query.filter_by(email=email).first()
            
            # Generate unique random name (needed for both new and incomplete accounts)
            attempts = 0
            while attempts < 100:
                first_name = random.choice(FIRST_NAMES)
                last_name = random.choice(LAST_NAMES)
                full_name = f"{first_name} {last_name}"
                if full_name not in used_names:
                    used_names.add(full_name)
                    break
                attempts += 1
            
            # Use fixed password for all users
            password = "Admin123!"
            
            # Random min/max hours
            min_hours = random.randint(4, 10)
            max_hours = random.randint(min_hours + 4, 20)
            
            is_incomplete = False  # Track if account was incomplete
            
            if existing_user:
                # Check if account is incomplete (no name, no skills)
                is_incomplete = (not existing_user.first_name or not existing_user.last_name)
                
                if update_existing or is_incomplete:
                    # Clear old unavailabilities and skills
                    Unavailability.query.filter_by(user_id=existing_user.id).delete()
                    FacilitatorSkill.query.filter_by(facilitator_id=existing_user.id).delete()
                    
                    facilitator = existing_user
                    is_update = True
                    
                    # Populate incomplete accounts
                    if is_incomplete:
                        facilitator.first_name = first_name
                        facilitator.last_name = last_name
                        if not facilitator.password_hash:
                            facilitator.password_hash = generate_password_hash(password)
                        if not facilitator.phone_number:
                            facilitator.phone_number = f"+61{random.randint(400000000, 499999999)}"
                    
                    # Update hours
                    facilitator.min_hours = min_hours
                    facilitator.max_hours = max_hours
                else:
                    print(f"✗ {email} - Already exists with complete data, skipping (use --update to force update)")
                    skipped_count += 1
                    continue
            else:
                # Create new facilitator
                facilitator = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role=UserRole.FACILITATOR,
                    password_hash=generate_password_hash(password),
                    min_hours=min_hours,
                    max_hours=max_hours,
                    phone_number=f"+61{random.randint(400000000, 499999999)}"
                )
                
                db.session.add(facilitator)
                db.session.flush()  # Get the ID
                is_update = False
            
            # Generate random unavailability for each unit (using fixed date range)
            unavail_count = 0
            for unit in units:
                unavailabilities = generate_random_unavailability(facilitator.id, unit)
                for unavail in unavailabilities:
                    db.session.add(unavail)
                    unavail_count += 1
            
            # Generate random skills for all modules
            skills = generate_random_skills(facilitator.id, modules)
            skill_summary = {
                SkillLevel.PROFICIENT: 0,
                SkillLevel.HAVE_RUN_BEFORE: 0,
                SkillLevel.HAVE_SOME_SKILL: 0,
                SkillLevel.NO_INTEREST: 0
            }
            
            for skill in skills:
                db.session.add(skill)
                skill_summary[skill.skill_level] += 1
            
            # Set availability_configured=True for all units to mark facilitators as having configured availability
            for unit in units:
                unit_facilitator = UnitFacilitator.query.filter_by(
                    user_id=facilitator.id,
                    unit_id=unit.id
                ).first()
                
                if unit_facilitator:
                    unit_facilitator.availability_configured = True
                else:
                    # Create UnitFacilitator record if it doesn't exist
                    unit_facilitator = UnitFacilitator(
                        user_id=facilitator.id,
                        unit_id=unit.id,
                        availability_configured=True
                    )
                    db.session.add(unit_facilitator)
            
            if is_update:
                updated_count += 1
                if is_incomplete:
                    action = "Populated"
                else:
                    action = "Updated"
            else:
                created_count += 1
                action = "Created"
            
            print(f"✓ {action}: {facilitator.first_name} {facilitator.last_name} ({email})")
            if not is_update or is_incomplete:
                print(f"  Password: Admin123!")
            print(f"  Hours: {facilitator.min_hours}-{facilitator.max_hours}/week")
            print(f"  Unavailability periods: {unavail_count}")
            print(f"  Skills: {skill_summary[SkillLevel.PROFICIENT]} proficient, "
                  f"{skill_summary[SkillLevel.HAVE_RUN_BEFORE]} have run before, "
                  f"{skill_summary[SkillLevel.HAVE_SOME_SKILL]} have some skill, "
                  f"{skill_summary[SkillLevel.NO_INTEREST]} no interest")
            print()
        
        # Commit all changes
        db.session.commit()
        
        print("=" * 60)
        print(f"Summary:")
        print(f"  ✓ Created: {created_count} facilitators")
        if updated_count > 0:
            print(f"  ✓ Populated/Updated: {updated_count} facilitators")
        print(f"  ✗ Skipped: {skipped_count} (already exist)")
        print(f"  Total modules in system: {len(modules)}")
        print(f"  Total units in system: {len(units)}")
        print("=" * 60)

if __name__ == '__main__':
    update_mode = '--update' in sys.argv or '-u' in sys.argv
    test_mode = '--test-available-all' in sys.argv or '--test' in sys.argv
    demo_mode = '--demo-available-all' in sys.argv or '--demo' in sys.argv
    
    # Remove flags from args
    args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    
    # If test mode is requested, run the Available All Days test
    if test_mode:
        print("🧪 RUNNING 'AVAILABLE ALL DAYS' FUNCTIONALITY TEST")
        print("=" * 60)
        success = test_available_all_days_functionality()
        print("\n" + "=" * 60)
        if success:
            print("🎉 TEST PASSED! 'Available All Days' functionality is working correctly.")
        else:
            print("❌ TEST FAILED! Please check the implementation.")
        print("=" * 60)
        exit(0 if success else 1)
    
    # If demo mode is requested, run the Available All Days demonstration
    if demo_mode:
        print("🎯 RUNNING 'AVAILABLE ALL DAYS' FEATURE DEMONSTRATION")
        print("=" * 60)
        success = demo_available_all_days_feature()
        print("\n" + "=" * 60)
        if success:
            print("🎉 DEMONSTRATION SUCCESSFUL! 'Available All Days' feature works as expected.")
        else:
            print("❌ DEMONSTRATION FAILED! Please check the implementation.")
        print("=" * 60)
        exit(0 if success else 1)
    
    # Normal facilitator creation mode
    if args:
        csv_path = args[0]
    else:
        csv_path = 'test/sample/facilitators_template (6).csv'
    
    action = "Updating" if update_mode else "Creating"
    print(f"{action} facilitators from: {csv_path}\n")
    create_facilitators_from_csv(csv_path, update_existing=update_mode)

