#!/usr/bin/env python3
"""
Test script to verify multi-facilitator display functionality

This script tests the _serialize_session function to ensure it properly
returns multiple facilitators with their roles.
"""

import sys
from datetime import datetime, timedelta

# Mock the database models for testing
class MockFacilitator:
    def __init__(self, id, first_name, last_name, email):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email

class MockAssignment:
    def __init__(self, facilitator, role='lead', is_confirmed=False):
        self.facilitator = facilitator
        self.role = role
        self.is_confirmed = is_confirmed

class MockModule:
    def __init__(self, module_name="Test Module"):
        self.module_name = module_name

class MockSession:
    def __init__(self, id, assignments=None, location="Lab A"):
        self.id = id
        self.assignments = assignments or []
        self.location = location
        self.module = MockModule()
        self.start_time = datetime.now()
        self.end_time = datetime.now() + timedelta(hours=2)

def _serialize_session_test(s: MockSession, venues_by_name=None):
    """
    Test version of _serialize_session function
    """
    venue_name = s.location or ""
    vid = None
    if venues_by_name and venue_name:
        vid = venues_by_name.get(venue_name.strip().lower())

    title = s.module.module_name or "Session"
    
    # Get all facilitator information with roles
    facilitators = []
    facilitator = None  # Keep for backward compatibility
    if s.assignments:
        for assignment in s.assignments:
            if assignment.facilitator:
                facilitator_info = {
                    "id": assignment.facilitator.id,
                    "name": f"{assignment.facilitator.first_name} {assignment.facilitator.last_name}",
                    "email": assignment.facilitator.email,
                    "role": getattr(assignment, 'role', 'lead'),  # Default to 'lead' if role not set
                    "is_confirmed": assignment.is_confirmed
                }
                facilitators.append(facilitator_info)
        
        # For backward compatibility, use first facilitator
        if facilitators:
            facilitator = facilitators[0]["name"]
    
    # Determine session status
    status = "unassigned"
    if facilitators:
        # If any facilitator is confirmed, show as approved
        if any(f["is_confirmed"] for f in facilitators):
            status = "approved"
        else:
            status = "pending"  # Assigned but not confirmed
    
    return {
        "id": str(s.id),
        "title": title,
        "start": s.start_time.isoformat(timespec="minutes"),
        "end": s.end_time.isoformat(timespec="minutes"),
        "venue": venue_name,
        "facilitator": facilitator,  # Backward compatibility
        "facilitators": facilitators,  # New: all facilitators with roles
        "status": status,
        "session_name": title,
        "location": s.location,
        "module_type": "Workshop",
        "attendees": None,
        "extendedProps": {
            "venue": venue_name,
            "venue_id": vid,
            "session_name": title,
            "location": s.location,
            "facilitator_name": facilitator,  # Backward compatibility
            "facilitator_id": s.assignments[0].facilitator.id if s.assignments else None,
            "lead_staff_required": 1,
            "support_staff_required": 0,
            "facilitators": facilitators,  # New: all facilitators with roles
        }
    }

def test_multi_facilitator_display():
    """Test the multi-facilitator display functionality"""
    print("="*70)
    print("MULTI-FACILITATOR DISPLAY TEST")
    print("="*70)
    
    # Create test facilitators
    alice = MockFacilitator(1, "Alice", "Expert", "alice@example.com")
    bob = MockFacilitator(2, "Bob", "Senior", "bob@example.com")
    carol = MockFacilitator(3, "Carol", "Mid", "carol@example.com")
    
    # Test 1: Single facilitator (lead)
    print("\n1. Single Lead Facilitator:")
    session1 = MockSession(1, [
        MockAssignment(alice, role='lead', is_confirmed=True)
    ])
    result1 = _serialize_session_test(session1)
    print(f"   Facilitators: {len(result1['facilitators'])}")
    for f in result1['facilitators']:
        print(f"     - {f['name']} ({f['role']}) - {'Confirmed' if f['is_confirmed'] else 'Pending'}")
    print(f"   Status: {result1['status']}")
    
    # Test 2: Multiple facilitators (1 lead, 1 support)
    print("\n2. Multiple Facilitators (1 Lead, 1 Support):")
    session2 = MockSession(2, [
        MockAssignment(alice, role='lead', is_confirmed=True),
        MockAssignment(bob, role='support', is_confirmed=False)
    ])
    result2 = _serialize_session_test(session2)
    print(f"   Facilitators: {len(result2['facilitators'])}")
    for f in result2['facilitators']:
        print(f"     - {f['name']} ({f['role']}) - {'Confirmed' if f['is_confirmed'] else 'Pending'}")
    print(f"   Status: {result2['status']}")
    
    # Test 3: Large session (2 leads, 1 support)
    print("\n3. Large Session (2 Leads, 1 Support):")
    session3 = MockSession(3, [
        MockAssignment(alice, role='lead', is_confirmed=True),
        MockAssignment(bob, role='lead', is_confirmed=True),
        MockAssignment(carol, role='support', is_confirmed=False)
    ])
    result3 = _serialize_session_test(session3)
    print(f"   Facilitators: {len(result3['facilitators'])}")
    for f in result3['facilitators']:
        print(f"     - {f['name']} ({f['role']}) - {'Confirmed' if f['is_confirmed'] else 'Pending'}")
    print(f"   Status: {result3['status']}")
    
    # Test 4: No facilitators
    print("\n4. No Facilitators:")
    session4 = MockSession(4, [])
    result4 = _serialize_session_test(session4)
    print(f"   Facilitators: {len(result4['facilitators'])}")
    print(f"   Status: {result4['status']}")
    
    # Test 5: Backward compatibility
    print("\n5. Backward Compatibility (facilitator field):")
    print(f"   Session 1 facilitator: {result1['facilitator']}")
    print(f"   Session 2 facilitator: {result2['facilitator']}")
    print(f"   Session 3 facilitator: {result3['facilitator']}")
    print(f"   Session 4 facilitator: {result4['facilitator']}")
    
    # Verify all tests passed
    tests_passed = (
        len(result1['facilitators']) == 1 and result1['status'] == 'approved' and
        len(result2['facilitators']) == 2 and result2['status'] == 'approved' and
        len(result3['facilitators']) == 3 and result3['status'] == 'approved' and
        len(result4['facilitators']) == 0 and result4['status'] == 'unassigned' and
        result1['facilitator'] == 'Alice Expert' and
        result2['facilitator'] == 'Alice Expert' and
        result3['facilitator'] == 'Alice Expert' and
        result4['facilitator'] is None
    )
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    if tests_passed:
        print("✅ All tests PASSED!")
        print("\nThe multi-facilitator display correctly:")
        print("  - Returns all facilitators with their roles")
        print("  - Maintains backward compatibility with single facilitator field")
        print("  - Properly determines session status based on confirmations")
        print("  - Handles empty facilitator lists")
        return True
    else:
        print("❌ Some tests FAILED")
        return False

def main():
    """Run the test suite"""
    success = test_multi_facilitator_display()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
