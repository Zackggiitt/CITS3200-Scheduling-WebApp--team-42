#!/usr/bin/env python3
"""
Threshold Hybrid Algorithm Demo Script

This script demonstrates the threshold hybrid scheduling algorithm by:
1. Setting up sample data with proper model relationships
2. Running the threshold hybrid algorithm multiple times
3. Generating test reports and results
4. Providing performance analysis

Usage: python run_algorithm_demo_fixed.py
"""

import sys
import os
from datetime import datetime, timedelta
import random
from flask import Flask
from algorithm_tester import AlgorithmTester
from algorithm_comparison import AlgorithmType
from models import db, User, Session, Assignment, Unavailability, UserRole, SkillLevel, FacilitatorSkill, Unit, Module

def create_demo_app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demo_scheduling.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'demo-secret-key'
    
    db.init_app(app)
    return app

def setup_sample_data(app):
    """Create comprehensive sample data for algorithm testing"""
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        print("Creating sample units and modules...")
        
        # First create a demo admin user for created_by field
        admin_user = User(
            first_name='Demo',
            last_name='Admin',
            email='admin@demo.edu.au',
            role=UserRole.UNIT_COORDINATOR
        )
        admin_user.password_hash = 'demo_admin_hash'
        db.session.add(admin_user)
        db.session.flush()
        
        # Create sample units
        units_data = [
            {'unit_code': 'CITS3200', 'unit_name': 'Professional Computing'},
            {'unit_code': 'CITS1001', 'unit_name': 'Object-oriented Programming'},
            {'unit_code': 'CITS2002', 'unit_name': 'Systems Programming'},
            {'unit_code': 'CITS3002', 'unit_name': 'Computer Networks'}
        ]
        
        units = []
        for unit_data in units_data:
            unit = Unit(
                unit_code=unit_data['unit_code'],
                unit_name=unit_data['unit_name'],
                year=2025,
                semester='Semester 1',
                created_by=admin_user.id,
                description=f"Demo unit for {unit_data['unit_name']}"
            )
            db.session.add(unit)
            db.session.flush()
            units.append(unit)
        
        # Create modules for each unit
        modules = []
        module_types = ['Lab', 'Tutorial', 'Workshop', 'Lecture']
        
        for unit in units:
            for i, mod_type in enumerate(module_types):
                module = Module(
                    unit_id=unit.id,
                    module_name=f"{mod_type} {i+1}",
                    module_type=mod_type.lower()
                )
                db.session.add(module)
                db.session.flush()
                modules.append(module)
        
        print(f"Created {len(units)} units and {len(modules)} modules")
        
        print("Creating sample facilitators...")
        
        # Create sample facilitators with diverse skills
        facilitators_data = [
            {
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email': 'alice.johnson@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Python', SkillLevel.LEADER), ('Java', SkillLevel.PROFICIENT), ('Web Development', SkillLevel.INTERESTED)]
            },
            {
                'first_name': 'Bob',
                'last_name': 'Smith',
                'email': 'bob.smith@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Java', SkillLevel.LEADER), ('Python', SkillLevel.PROFICIENT), ('Database', SkillLevel.INTERESTED)]
            },
            {
                'first_name': 'Carol',
                'last_name': 'Davis',
                'email': 'carol.davis@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Web Development', SkillLevel.LEADER), ('JavaScript', SkillLevel.PROFICIENT), ('Python', SkillLevel.INTERESTED)]
            },
            {
                'first_name': 'David',
                'last_name': 'Wilson',
                'email': 'david.wilson@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Database', SkillLevel.LEADER), ('SQL', SkillLevel.PROFICIENT), ('Python', SkillLevel.INTERESTED)]
            },
            {
                'first_name': 'Emma',
                'last_name': 'Brown',
                'email': 'emma.brown@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Networks', SkillLevel.LEADER), ('Security', SkillLevel.PROFICIENT), ('Linux', SkillLevel.INTERESTED)]
            },
            {
                'first_name': 'Frank',
                'last_name': 'Taylor',
                'email': 'frank.taylor@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Machine Learning', SkillLevel.LEADER), ('Python', SkillLevel.PROFICIENT), ('Statistics', SkillLevel.INTERESTED)]
            }
        ]
        
        facilitators = []
        for fac_data in facilitators_data:
            facilitator = User(
                first_name=fac_data['first_name'],
                last_name=fac_data['last_name'],
                email=fac_data['email'],
                role=fac_data['role']
            )
            facilitator.password_hash = 'demo_password_hash'
            db.session.add(facilitator)
            db.session.flush()
            
            # Add skills by associating with random modules (simplified for demo)
            skill_modules = random.sample(modules, min(3, len(modules)))
            for i, (skill_name, skill_level) in enumerate(fac_data['skills']):
                if i < len(skill_modules):
                    skill = FacilitatorSkill(
                        facilitator_id=facilitator.id,
                        module_id=skill_modules[i].id,
                        skill_level=skill_level
                    )
                    db.session.add(skill)
            
            facilitators.append(facilitator)
        
        print(f"Created {len(facilitators)} facilitators")
        
        # Create sample sessions
        print("Creating sample sessions...")
        
        session_count = 0
        start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        for module in modules:
            # Create 2-3 sessions per module
            for session_num in range(random.randint(2, 3)):
                # Vary session times throughout the week
                session_date = start_date + timedelta(days=random.randint(0, 6))
                session_hour = random.choice([9, 11, 13, 15, 17])
                session_start = session_date.replace(hour=session_hour)
                session_end = session_start + timedelta(hours=random.choice([1, 2, 3]))
                
                session = Session(
                    module_id=module.id,
                    start_time=session_start,
                    end_time=session_end,
                    day_of_week=session_start.weekday(),
                    location=f"Room {random.randint(101, 999)}",
                    max_facilitators=random.randint(1, 2),
                    lead_staff_required=1,
                    support_staff_required=random.randint(0, 1)
                )
                db.session.add(session)
                session_count += 1
        
        print(f"Created {session_count} sessions")
        
        # Create sample availability data
        print("Creating sample availability data...")
        
        availability_count = 0
        for facilitator in facilitators:
            # Create availability for each day of the week
            for day in range(7):  # Monday to Sunday
                # Most facilitators are available during business hours
                if random.random() < 0.8:  # 80% chance of being available
                    start_hour = random.choice([8, 9, 10])
                    end_hour = random.choice([16, 17, 18, 19])
                    
                    availability = Availability(
                        user_id=facilitator.id,
                        day_of_week=day,
                        start_time=datetime.strptime(f"{start_hour}:00", "%H:%M").time(),
                        end_time=datetime.strptime(f"{end_hour}:00", "%H:%M").time()
                    )
                    db.session.add(availability)
                    availability_count += 1
        
        print(f"Created {availability_count} availability entries")
        
        # Commit all data
        db.session.commit()
        
        # Return statistics
        return {
            'facilitators': len(facilitators),
            'sessions': session_count,
            'availability_entries': availability_count,
            'units': len(units),
            'modules': len(modules)
        }

def run_demo():
    """Run the threshold hybrid algorithm demo"""
    print("=" * 60)
    print("THRESHOLD HYBRID SCHEDULING ALGORITHM DEMO")
    print("=" * 60)
    
    try:
        # Setup
        app = create_demo_app()
        
        print("\nSetting up sample data...")
        data_stats = setup_sample_data(app)
        
        print(f"\nSample data created:")
        print(f"  - {data_stats['units']} units")
        print(f"  - {data_stats['modules']} modules") 
        print(f"  - {data_stats['facilitators']} facilitators")
        print(f"  - {data_stats['sessions']} sessions")
        print(f"  - {data_stats['availability_entries']} availability entries")
        
        # Initialize tester
        with app.app_context():
            print("\nInitializing algorithm tester...")
            tester = AlgorithmTester()
            
            print("\nRunning threshold hybrid algorithm test (this may take a few minutes)...")
            
            # Run test with fewer iterations for demo
            results = tester.compare_all_algorithms(num_runs=3)
            
            print("\nGenerating comparison report...")
            report = tester.generate_comparison_report(results)
            
            print("\nSaving results...")
            # Save detailed results
            tester.save_results_to_json(report, 'algorithm_comparison_results.json')
            
            # Generate and save charts
            tester.create_visualization_plots(results, 'algorithm_comparison_charts.png')
            
            print("\n" + "=" * 60)
            print("THRESHOLD HYBRID ALGORITHM RESULTS")
            print("=" * 60)
            print(report)
            
            print("\nFiles generated:")
            print("  - algorithm_comparison_results.json (detailed results)")
            print("  - algorithm_comparison_charts.png (comparison charts)")
            
            print("\n" + "=" * 60)
            print("Demo completed successfully!")
            print("=" * 60)
            
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1)