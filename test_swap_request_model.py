#!/usr/bin/env python3
"""
Test script to verify the SwapRequest model updates work correctly.
Run this after applying the migration to test the new fields.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from application import app
from models import db, SwapRequest, SwapStatus, User, Assignment
from datetime import datetime

def test_swap_request_model():
    """Test the updated SwapRequest model with new fields."""
    
    with app.app_context():
        print("Testing SwapRequest model updates...")
        
        # Test 1: Check that new SwapStatus values exist
        print("\n1. Testing SwapStatus enum values:")
        for status in SwapStatus:
            print(f"   - {status.name}: {status.value}")
        
        # Test 2: Create a test swap request with new fields
        print("\n2. Testing SwapRequest creation with new fields:")
        
        # Get first two users (assuming they exist)
        users = User.query.limit(2).all()
        if len(users) < 2:
            print("   ERROR: Need at least 2 users in database for testing")
            return False
            
        # Get first two assignments (assuming they exist)
        assignments = Assignment.query.limit(2).all()
        if len(assignments) < 2:
            print("   ERROR: Need at least 2 assignments in database for testing")
            return False
        
        # Create a test swap request
        test_request = SwapRequest(
            requester_id=users[0].id,
            target_id=users[1].id,
            requester_assignment_id=assignments[0].id,
            target_assignment_id=assignments[1].id,
            reason="Test swap request",
            status=SwapStatus.FACILITATOR_PENDING,
            facilitator_confirmed=False,
            facilitator_confirmed_at=None,
            facilitator_decline_reason=None,
            coordinator_decline_reason=None
        )
        
        try:
            db.session.add(test_request)
            db.session.commit()
            print(f"   ✓ Created swap request with ID: {test_request.id}")
            print(f"   ✓ Status: {test_request.status.value}")
            print(f"   ✓ Facilitator confirmed: {test_request.facilitator_confirmed}")
            
            # Test 3: Update the request to simulate facilitator approval
            print("\n3. Testing facilitator approval process:")
            test_request.facilitator_confirmed = True
            test_request.facilitator_confirmed_at = datetime.utcnow()
            test_request.status = SwapStatus.COORDINATOR_PENDING
            db.session.commit()
            
            print(f"   ✓ Updated status to: {test_request.status.value}")
            print(f"   ✓ Facilitator confirmed: {test_request.facilitator_confirmed}")
            print(f"   ✓ Confirmation timestamp: {test_request.facilitator_confirmed_at}")
            
            # Test 4: Test decline scenario
            print("\n4. Testing decline scenario:")
            test_request.status = SwapStatus.FACILITATOR_DECLINED
            test_request.facilitator_decline_reason = "Not available due to other commitments"
            db.session.commit()
            
            print(f"   ✓ Updated status to: {test_request.status.value}")
            print(f"   ✓ Decline reason: {test_request.facilitator_decline_reason}")
            
            # Clean up test data
            db.session.delete(test_request)
            db.session.commit()
            print("\n✓ Test data cleaned up successfully")
            
            return True
            
        except Exception as e:
            print(f"   ERROR: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = test_swap_request_model()
    if success:
        print("\n🎉 All tests passed! SwapRequest model updates are working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
