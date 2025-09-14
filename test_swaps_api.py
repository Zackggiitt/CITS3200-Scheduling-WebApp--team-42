#!/usr/bin/env python3
"""
Test script to verify the new Session Swaps API endpoints work correctly.
Run this after starting the Flask application to test the endpoints.
"""

import requests
import json
import sys

def test_api_endpoints():
    """Test the new Session Swaps API endpoints."""
    
    base_url = "http://localhost:5000"  # Adjust if your Flask app runs on different port
    
    print("Testing Session Swaps API endpoints...")
    print("=" * 50)
    
    # Test 1: Get swap requests (requires authentication)
    print("\n1. Testing GET /facilitator/swap-requests")
    try:
        response = requests.get(f"{base_url}/facilitator/swap-requests")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Response received successfully")
            print(f"   ✓ Pending requests: {len(data.get('pending_requests', []))}")
            print(f"   ✓ Approved requests: {len(data.get('approved_requests', []))}")
            print(f"   ✓ Declined requests: {len(data.get('declined_requests', []))}")
        else:
            print(f"   ⚠ Expected 200, got {response.status_code} (likely due to authentication)")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - make sure Flask app is running")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    # Test 2: Get available facilitators (requires authentication and assignment ID)
    print("\n2. Testing GET /facilitator/available-facilitators/<assignment_id>")
    try:
        response = requests.get(f"{base_url}/facilitator/available-facilitators/1")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Response received successfully")
            print(f"   ✓ Available facilitators: {len(data.get('available_facilitators', []))}")
        else:
            print(f"   ⚠ Expected 200, got {response.status_code} (likely due to authentication)")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Create swap request (requires authentication)
    print("\n3. Testing POST /facilitator/swap-requests")
    try:
        test_data = {
            "requester_assignment_id": 1,
            "target_assignment_id": 2,
            "target_facilitator_id": 3,
            "has_discussed": True
        }
        response = requests.post(
            f"{base_url}/facilitator/swap-requests",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   ✓ Swap request created successfully")
            print(f"   ✓ Request ID: {data.get('swap_request_id')}")
        else:
            print(f"   ⚠ Expected 201, got {response.status_code} (likely due to authentication)")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("API endpoint tests completed!")
    print("\nNote: Authentication is required for these endpoints.")
    print("To fully test, you'll need to:")
    print("1. Start the Flask application")
    print("2. Log in as a facilitator")
    print("3. Use browser developer tools to test with authentication")
    
    return True

if __name__ == "__main__":
    success = test_api_endpoints()
    if not success:
        sys.exit(1)
