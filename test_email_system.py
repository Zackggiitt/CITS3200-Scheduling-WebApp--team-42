#!/usr/bin/env python
"""
Test script for the email system
Run this to verify your email setup is working correctly
"""

import os
import sys
from application import app, db
from email_service import send_welcome_email, EmailToken

def test_database_setup():
    """Test if the email_token table exists"""
    print("=" * 60)
    print("TEST 1: Database Setup")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Try to query the EmailToken table
            count = EmailToken.query.count()
            print(f"✓ email_token table exists")
            print(f"  Current token count: {count}")
            return True
        except Exception as e:
            print(f"✗ email_token table does not exist")
            print(f"  Error: {e}")
            print("\n  FIX: Run the migration:")
            print("       flask db upgrade")
            print("  OR:")
            print("       python -c \"from application import app, db; app.app_context().push(); db.create_all()\"")
            return False

def test_environment_variables():
    """Test if required environment variables are set"""
    print("\n" + "=" * 60)
    print("TEST 2: Environment Variables")
    print("=" * 60)
    
    use_mock = os.environ.get('USE_MOCK_EMAIL', 'false').lower() == 'true'
    
    if use_mock:
        print("✓ USE_MOCK_EMAIL is set to 'true' (mock mode)")
        print("  Emails will be printed to console instead of sent")
        return True
    else:
        print("  USE_MOCK_EMAIL is not set (real email mode)")
        
        required_vars = [
            'SES_SENDER_EMAIL',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY'
        ]
        
        missing = []
        for var in required_vars:
            if os.environ.get(var):
                print(f"✓ {var} is set")
            else:
                print(f"✗ {var} is NOT set")
                missing.append(var)
        
        optional_vars = ['SES_REGION']
        for var in optional_vars:
            value = os.environ.get(var, 'ap-southeast-1')
            print(f"  {var}: {value}")
        
        if missing:
            print(f"\n  FIX: Set missing environment variables:")
            for var in missing:
                print(f"       export {var}=your-value")
            return False
        
        return True

def test_send_email():
    """Test sending a welcome email"""
    print("\n" + "=" * 60)
    print("TEST 3: Send Welcome Email")
    print("=" * 60)
    
    test_email = "test@example.com"
    test_name = "Test User"
    
    print(f"  Sending welcome email to: {test_email}")
    
    with app.app_context():
        try:
            success = send_welcome_email(test_email, test_name)
            
            if success:
                print(f"✓ Email sent successfully")
                
                # Check if token was created
                token = EmailToken.query.filter_by(email=test_email).order_by(EmailToken.created_at.desc()).first()
                if token:
                    print(f"✓ Token created in database")
                    print(f"  Token ID: {token.id}")
                    print(f"  Token Type: {token.token_type}")
                    print(f"  Expires: {token.expires_at}")
                else:
                    print(f"✗ Token was not created in database")
                    return False
                
                return True
            else:
                print(f"✗ Email failed to send")
                return False
                
        except Exception as e:
            print(f"✗ Error sending email: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("EMAIL SYSTEM TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Database setup
    results.append(("Database Setup", test_database_setup()))
    
    # Test 2: Environment variables
    results.append(("Environment Variables", test_environment_variables()))
    
    # Test 3: Send email (only if previous tests passed)
    if all(r[1] for r in results):
        results.append(("Send Email", test_send_email()))
    else:
        print("\n⚠ Skipping email send test due to previous failures")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Email system is ready to use.")
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
