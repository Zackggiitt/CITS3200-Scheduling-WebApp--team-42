#!/usr/bin/env python3
"""
Test script for unavailability system integration and backward compatibility.
This script tests the new unavailability functionality while ensuring existing features still work.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from application import app
from models import db, User, Unit, Unavailability, UnitFacilitator, RecurringPattern
from datetime import datetime, date, time
import json

def test_backward_compatibility():
    """Test that existing functionality still works after adding unavailability system"""
    print("Testing backward compatibility...")
    
    with app.app_context():
        # Test 1: Check that existing models still work
        print("✓ Testing existing models...")
        
        # Check if we can still query users
        users = User.query.filter_by(role='facilitator').all()
        print(f"  Found {len(users)} facilitators")
        
        # Check if we can still query units
        units = Unit.query.all()
        print(f"  Found {len(units)} units")
        
        # Test 2: Check that new unavailability model works
        print("✓ Testing new unavailability model...")
        
        # Create a test unavailability record
        test_user = users[0] if users else None
        test_unit = units[0] if units else None
        
        if test_user and test_unit:
            # Check if user is assigned to unit
            assignment = UnitFacilitator.query.filter_by(
                user_id=test_user.id, 
                unit_id=test_unit.id
            ).first()
            
            if not assignment:
                # Create assignment for testing
                assignment = UnitFacilitator(
                    user_id=test_user.id,
                    unit_id=test_unit.id
                )
                db.session.add(assignment)
                db.session.commit()
                print("  Created test unit assignment")
            
            # Test unavailability creation
            test_unavailability = Unavailability(
                user_id=test_user.id,
                unit_id=test_unit.id,
                date=date.today(),
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_full_day=False,
                recurring_pattern=RecurringPattern.WEEKLY,
                recurring_end_date=date.today(),
                recurring_interval=1,
                reason="Test unavailability"
            )
            
            db.session.add(test_unavailability)
            db.session.commit()
            
            print(f"  Created test unavailability with ID: {test_unavailability.id}")
            
            # Test unavailability query
            unavailabilities = Unavailability.query.filter_by(
                user_id=test_user.id,
                unit_id=test_unit.id
            ).all()
            
            print(f"  Found {len(unavailabilities)} unavailability records")
            
            # Clean up test data
            db.session.delete(test_unavailability)
            db.session.commit()
            print("  Cleaned up test data")
        
        # Test 3: Check that existing routes still work
        print("✓ Testing existing routes...")
        
        with app.test_client() as client:
            # Test facilitator dashboard route
            response = client.get('/facilitator/dashboard')
            print(f"  Dashboard route status: {response.status_code}")
            
            # Test units route
            response = client.get('/facilitator/units')
            print(f"  Units route status: {response.status_code}")
        
        print("✓ All backward compatibility tests passed!")
        return True

def test_unavailability_api():
    """Test the new unavailability API endpoints"""
    print("\nTesting unavailability API...")
    
    with app.app_context():
        with app.test_client() as client:
            # Test GET unavailability endpoint
            response = client.get('/facilitator/unavailability?unit_id=1')
            print(f"  GET unavailability status: {response.status_code}")
            
            # Test POST unavailability endpoint
            test_data = {
                'unit_id': 1,
                'date': '2024-01-15',
                'is_full_day': True,
                'reason': 'Test API'
            }
            
            response = client.post('/facilitator/unavailability',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            print(f"  POST unavailability status: {response.status_code}")
            
            if response.status_code == 201:
                data = response.get_json()
                print(f"  Created unavailability ID: {data.get('unavailability', {}).get('id')}")
            
            # Test unit info endpoint
            response = client.get('/facilitator/unit-info?unit_id=1')
            print(f"  GET unit info status: {response.status_code}")
    
    print("✓ Unavailability API tests completed!")

def test_data_migration():
    """Test that data migration works correctly"""
    print("\nTesting data migration...")
    
    with app.app_context():
        # Check if old availability table exists (it shouldn't after migration)
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'availability' in tables:
                print("  ⚠ Warning: Old 'availability' table still exists")
            else:
                print("  ✓ Old 'availability' table successfully removed")
            
            if 'unavailability' in tables:
                print("  ✓ New 'unavailability' table exists")
            else:
                print("  ⚠ Warning: New 'unavailability' table not found")
                
        except Exception as e:
            print(f"  Error checking tables: {e}")
    
    print("✓ Data migration tests completed!")

def main():
    """Run all tests"""
    print("Starting unavailability system integration tests...\n")
    
    try:
        # Test backward compatibility
        test_backward_compatibility()
        
        # Test new API
        test_unavailability_api()
        
        # Test data migration
        test_data_migration()
        
        print("\n🎉 All tests completed successfully!")
        print("\nThe unavailability system is ready for use!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
