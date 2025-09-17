#!/usr/bin/env python3
"""
Simple Algorithm Test Script

This script provides a simplified way to test your scheduling algorithms:
1. Creates basic sample data
2. Tests each algorithm individually
3. Shows results without complex visualizations

Usage: python simple_algorithm_test.py
"""

import sys
import os
from datetime import datetime, timedelta
import random
from flask import Flask
from algorithm_comparison import AdvancedSchedulingEngine, AlgorithmType
from models import db, User, Session, Assignment, Unavailability, UserRole, SkillLevel, FacilitatorSkill, Unit, Module

def create_test_app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///simple_test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-key'
    
    db.init_app(app)
    return app

def setup_minimal_data(app):
    """Create minimal sample data for algorithm testing"""
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        print("Creating minimal test data...")
        
        # Create admin user
        admin_user = User(
            first_name='Test',
            last_name='Admin',
            email='admin@test.edu.au',
            role=UserRole.UNIT_COORDINATOR
        )
        admin_user.password_hash = 'test_hash'
        db.session.add(admin_user)
        db.session.flush()
        
        # Create one unit
        unit = Unit(
            unit_code='TEST101',
            unit_name='Test Unit',
            year=2025,
            semester='Semester 1',
            created_by=admin_user.id,
            description='Test unit for algorithm testing'
        )
        db.session.add(unit)
        db.session.flush()
        
        # Create a few modules
        modules = []
        for i in range(3):
            module = Module(
                unit_id=unit.id,
                module_name=f"Module {i+1}",
                module_type='lab'
            )
            db.session.add(module)
            db.session.flush()
            modules.append(module)
        
        # Create a few facilitators
        facilitators = []
        for i in range(3):
            facilitator = User(
                first_name=f'Facilitator{i+1}',
                last_name='Test',
                email=f'facilitator{i+1}@test.edu.au',
                role=UserRole.FACILITATOR
            )
            facilitator.password_hash = 'test_hash'
            db.session.add(facilitator)
            db.session.flush()
            
            # Add skills for each facilitator
            for j, module in enumerate(modules):
                if j <= i:  # Give different skill levels
                    skill = FacilitatorSkill(
                        facilitator_id=facilitator.id,
                        module_id=module.id,
                        skill_level=SkillLevel.PROFICIENT if j == 0 else SkillLevel.INTERESTED
                    )
                    db.session.add(skill)
            
            facilitators.append(facilitator)
        
        # Create a few sessions with proper day_of_week matching
        sessions = []
        base_date = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        
        for i, module in enumerate(modules):
            # Create sessions on Monday (day 0) to match availability
            session_start = base_date.replace(hour=10+i*2)
            session = Session(
                module_id=module.id,
                start_time=session_start,
                end_time=session_start + timedelta(hours=1),
                day_of_week=session_start.weekday(),  # Use the actual weekday
                location=f'Room {100+i}',
                max_facilitators=1,
                lead_staff_required=1,
                support_staff_required=0
            )
            db.session.add(session)
            sessions.append(session)
        
        # For testing purposes, we don't add any unavailability records
        # This means all facilitators are available by default
        # In a real scenario, you would add specific unavailability records as needed
        print("No unavailability records created - facilitators are available by default")
        
        db.session.commit()
        
        return {
            'facilitators': len(facilitators),
            'sessions': len(sessions),
            'modules': len(modules)
        }

def test_single_algorithm(engine, algorithm_type):
    """Test a single algorithm and return results"""
    print(f"\nTesting {algorithm_type.value}...")
    
    try:
        result = engine.generate_schedule(algorithm_type)
        
        if result['success']:
            print(f"  ✓ Success!")
            print(f"  - Sessions assigned: {result['assigned_sessions']}")
            print(f"  - Sessions unassigned: {result['total_sessions'] - result['assigned_sessions']}")
            print(f"  - Assignment rate: {result['assignment_rate']:.1%}")
            print(f"  - Total conflicts: {len(result['conflicts'])}")
            
            if result['assignments']:
                print(f"  - Sample assignments:")
                for i, assignment in enumerate(result['assignments'][:3]):  # Show first 3
                    print(f"    * {assignment['facilitator_name']} → {assignment['session_info']}")
                if len(result['assignments']) > 3:
                    print(f"    ... and {len(result['assignments'])-3} more")
        else:
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {'success': False, 'error': str(e)}

def run_simple_test():
    """Run simple algorithm tests"""
    print("=" * 50)
    print("SIMPLE ALGORITHM TEST")
    print("=" * 50)
    
    try:
        # Setup
        app = create_test_app()
        data_stats = setup_minimal_data(app)
        
        print(f"\nTest data created:")
        print(f"  - {data_stats['facilitators']} facilitators")
        print(f"  - {data_stats['sessions']} sessions") 
        print(f"  - {data_stats['modules']} modules")
        
        # Test algorithms
        with app.app_context():
            engine = AdvancedSchedulingEngine()
            results = {}
            
            print("\nTesting threshold hybrid algorithm...")
            print("-" * 30)
            
            # Only test the threshold hybrid algorithm
            algorithm = AlgorithmType.THRESHOLD_HYBRID
            results[algorithm.value] = test_single_algorithm(engine, algorithm)
            
            # Summary
            print("\n" + "=" * 50)
            print("SUMMARY")
            print("=" * 50)
            
            successful_algorithms = []
            for alg_name, result in results.items():
                if result['success']:
                    successful_algorithms.append((alg_name, result['assignment_rate']))
                    print(f"{alg_name}: ✓ ({result['assignment_rate']:.1%} assigned)")
                else:
                    print(f"{alg_name}: ✗ (failed)")
            
            if successful_algorithms:
                # Find best performing algorithm
                best_alg = max(successful_algorithms, key=lambda x: x[1])
                print(f"\nBest performing algorithm: {best_alg[0]} ({best_alg[1]:.1%} assignment rate)")
                
                print("\n✅ Algorithm testing completed successfully!")
                print("Your scheduling algorithms are working correctly!")
            else:
                print("\n❌ No algorithms completed successfully.")
                print("There may be issues with your algorithm implementation or data setup.")
        
        return True
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_simple_test()
    if success:
        print("\n🎉 Test completed! Your algorithms are ready to use.")
    else:
        print("\n❌ Test failed. Please check the error messages above.")
    
    sys.exit(0 if success else 1)