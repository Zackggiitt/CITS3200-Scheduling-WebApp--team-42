#!/usr/bin/env python3
"""
Algorithm Comparison Demo Script

This script demonstrates the algorithm comparison framework by:
1. Setting up sample data
2. Running all four algorithms multiple times
3. Generating comparison charts and reports
4. Providing recommendations for the best algorithm

Usage: python run_algorithm_demo.py
"""

import sys
import os
from datetime import datetime, timedelta
import random
from flask import Flask
from algorithm_tester import AlgorithmTester
from algorithm_comparison import AlgorithmType
from models import db, User, Session, Assignment, Availability, UserRole, SkillLevel, FacilitatorSkill

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
                'skills': [('Java', SkillLevel.LEADER), ('Database', SkillLevel.PROFICIENT), ('Python', SkillLevel.INTERESTED)]
            },
            {
                'first_name': 'Carol',
                'last_name': 'Davis',
                'email': 'carol.davis@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Web Development', SkillLevel.LEADER), ('JavaScript', SkillLevel.PROFICIENT), ('Database', SkillLevel.INTERESTED)]
            },
            {
                'first_name': 'David',
                'last_name': 'Wilson',
                'email': 'david.wilson@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Database', SkillLevel.LEADER), ('Python', SkillLevel.PROFICIENT), ('Machine Learning', SkillLevel.INTERESTED)]
            },
            {
                'first_name': 'Emma',
                'last_name': 'Brown',
                'email': 'emma.brown@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Machine Learning', SkillLevel.LEADER), ('Python', SkillLevel.PROFICIENT), ('Statistics', SkillLevel.PROFICIENT)]
            },
            {
                'first_name': 'Frank',
                'last_name': 'Miller',
                'email': 'frank.miller@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('JavaScript', SkillLevel.LEADER), ('Web Development', SkillLevel.PROFICIENT), ('Mobile Development', SkillLevel.INTERESTED)]
            },
            {
                'first_name': 'Grace',
                'last_name': 'Taylor',
                'email': 'grace.taylor@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Statistics', SkillLevel.LEADER), ('Machine Learning', SkillLevel.PROFICIENT), ('Python', SkillLevel.PROFICIENT)]
            },
            {
                'first_name': 'Henry',
                'last_name': 'Anderson',
                'email': 'henry.anderson@uwa.edu.au',
                'role': UserRole.FACILITATOR,
                'skills': [('Mobile Development', SkillLevel.LEADER), ('Java', SkillLevel.PROFICIENT), ('JavaScript', SkillLevel.INTERESTED)]
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
            facilitator.password_hash = 'demo_password_hash'  # Demo password hash
            db.session.add(facilitator)
            db.session.flush()  # Get the ID
            
            # Add skills
            for skill_name, skill_level in fac_data['skills']:
                skill = FacilitatorSkill(
                    facilitator_id=facilitator.id,
                    skill_name=skill_name,
                    skill_level=skill_level
                )
                db.session.add(skill)
            
            facilitators.append(facilitator)
        
        print(f"Created {len(facilitators)} facilitators")
        
        # Create sample sessions
        print("Creating sample sessions...")
        
        session_types = ['lecture', 'tutorial', 'lab', 'workshop']
        modules = ['CITS3200', 'CITS2200', 'CITS1001', 'CITS3403', 'CITS5501']
        required_skills = {
            'CITS3200': ['Python', 'Web Development'],
            'CITS2200': ['Java', 'Database'],
            'CITS1001': ['Python'],
            'CITS3403': ['Web Development', 'JavaScript'],
            'CITS5501': ['Machine Learning', 'Statistics']
        }
        
        sessions = []
        base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        for week in range(4):  # 4 weeks of sessions
            for day in range(5):  # Monday to Friday
                for hour in [9, 11, 13, 15]:  # 4 time slots per day
                    if random.random() < 0.7:  # 70% chance of having a session
                        module = random.choice(modules)
                        session_type = random.choice(session_types)
                        
                        start_time = base_date + timedelta(weeks=week, days=day, hours=hour-9)
                        end_time = start_time + timedelta(hours=2)
                        
                        session = Session(
                            course_name=module,
                            session_type=session_type,
                            start_time=start_time,
                            end_time=end_time,
                            location=f"Room {random.randint(101, 999)}",
                            required_skills=','.join(required_skills.get(module, ['General']))
                        )
                        db.session.add(session)
                        sessions.append(session)
        
        print(f"Created {len(sessions)} sessions")
        
        # Create availability for facilitators with different patterns
        print("Creating facilitator availability...")
        
        availability_patterns = [
            {'rate': 0.9, 'preference': 'morning'},    # High availability, prefers morning
            {'rate': 0.8, 'preference': 'afternoon'},  # High availability, prefers afternoon
            {'rate': 0.7, 'preference': 'all_day'},    # Medium availability, no preference
            {'rate': 0.6, 'preference': 'morning'},    # Lower availability, prefers morning
            {'rate': 0.5, 'preference': 'afternoon'},  # Lower availability, prefers afternoon
            {'rate': 0.4, 'preference': 'limited'},    # Very limited availability
            {'rate': 0.8, 'preference': 'weekdays'},   # Good availability on specific days
            {'rate': 0.6, 'preference': 'random'}      # Random availability pattern
        ]
        
        for i, facilitator in enumerate(facilitators):
            pattern = availability_patterns[i % len(availability_patterns)]
            base_rate = pattern['rate']
            preference = pattern['preference']
            
            for week in range(4):
                for day in range(5):
                    # Create longer availability blocks to cover 2-hour sessions
                    for hour in range(9, 17, 2):  # 9-11, 11-13, 13-15, 15-17
                        # Adjust availability rate based on preference
                        current_rate = base_rate
                        
                        if preference == 'morning' and hour >= 13:
                            current_rate *= 0.5  # Reduce afternoon availability
                        elif preference == 'afternoon' and hour < 13:
                            current_rate *= 0.5  # Reduce morning availability
                        elif preference == 'limited':
                            current_rate *= 0.6  # Generally lower availability
                        elif preference == 'weekdays' and day >= 3:  # Thu-Fri
                            current_rate *= 0.3  # Much lower availability on Thu-Fri
                        elif preference == 'random':
                            current_rate = random.uniform(0.2, 0.9)  # Completely random
                        
                        if random.random() < current_rate:
                            from datetime import time
                            
                            availability = Availability(
                                user_id=facilitator.id,
                                day_of_week=day,  # 0=Monday, 4=Friday
                                start_time=time(hour, 0),
                                end_time=time(min(hour + 2, 17), 0),  # 2-hour blocks
                                is_available=True
                            )
                            db.session.add(availability)
        
        print("Created facilitator availability")
        
        # Create admin user
        admin = User(
            first_name='Admin',
            last_name='User',
            email='admin@uwa.edu.au',
            role=UserRole.ADMIN
        )
        admin.password_hash = 'admin_password_hash'  # Demo password hash
        db.session.add(admin)
        
        db.session.commit()
        print("Sample data setup completed!")
        
        return {
            'facilitators': len(facilitators),
            'sessions': len(sessions),
            'admin': 1
        }

def run_demo():
    """Run the complete algorithm comparison demo"""
    print("="*60)
    print("SCHEDULING ALGORITHM COMPARISON DEMO")
    print("="*60)
    print()
    
    # Create Flask app and setup data
    app = create_demo_app()
    
    print("Setting up sample data...")
    data_stats = setup_sample_data(app)
    print(f"Data setup complete: {data_stats}")
    print()
    
    # Run algorithm comparison within app context
    with app.app_context():
        print("Initializing algorithm tester...")
        tester = AlgorithmTester()
        
        print("Starting comprehensive algorithm comparison...")
        print("This may take a few minutes...")
        print()
        
        # Run the comprehensive test
        report = tester.run_comprehensive_test(
            num_runs=8,  # Run each algorithm 8 times
            save_plots=True,
            save_report=True
        )
        
        print()
        print("="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print()
        print("Generated files:")
        print("- Algorithm comparison plots (PNG)")
        print("- Detailed comparison report (JSON)")
        print("- Console output with recommendations")
        print()
        print("Next steps:")
        print("1. Review the generated plots to visualize algorithm performance")
        print("2. Check the JSON report for detailed statistics")
        print("3. Use the recommendations to select the best algorithm")
        print("4. Integrate the chosen algorithm into your scheduling system")
        
        return report

def quick_test():
    """Run a quick test with fewer iterations for faster results"""
    print("Running quick algorithm test...")
    
    app = create_demo_app()
    setup_sample_data(app)
    
    with app.app_context():
        tester = AlgorithmTester()
        
        # Test each algorithm once
        results = {}
        for algorithm in AlgorithmType:
            print(f"Testing {algorithm.value}...")
            result = tester.run_single_test(algorithm, randomize=True)
            results[algorithm.value] = result
            
            if result['success']:
                print(f"  ✓ Success: {result['assignment_rate']:.1%} assignment rate, avg score: {result['avg_score']:.2f}")
            else:
                print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
        
        print("\nQuick test completed!")
        return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Algorithm Comparison Demo')
    parser.add_argument('--quick', action='store_true', help='Run quick test instead of full demo')
    parser.add_argument('--no-plots', action='store_true', help='Skip generating plots')
    
    args = parser.parse_args()
    
    try:
        if args.quick:
            quick_test()
        else:
            run_demo()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()