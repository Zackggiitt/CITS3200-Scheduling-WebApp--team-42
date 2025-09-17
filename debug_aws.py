#!/usr/bin/env python3
"""
Simple debug script to test AWS deployment issues
Run this on AWS to see what's failing
"""

import os
import sys
import traceback

def test_imports():
    """Test all imports that might be failing"""
    print("=== Testing Imports ===")
    
    try:
        from flask import Flask
        print("✓ Flask imported successfully")
    except Exception as e:
        print(f"✗ Flask import failed: {e}")
        return False
    
    try:
        from models import db, User, UserRole, Facilitator
        print("✓ Models imported successfully")
    except Exception as e:
        print(f"✗ Models import failed: {e}")
        return False
    
    try:
        from auth import login_required, is_safe_url, get_current_user, auth_bp
        print("✓ Auth imported successfully")
    except Exception as e:
        print(f"✗ Auth import failed: {e}")
        return False
    
    try:
        from admin_routes import admin_bp
        print("✓ Admin routes imported successfully")
    except Exception as e:
        print(f"✗ Admin routes import failed: {e}")
        return False
    
    try:
        from facilitator_routes import facilitator_bp
        print("✓ Facilitator routes imported successfully")
    except Exception as e:
        print(f"✗ Facilitator routes import failed: {e}")
        return False
    
    try:
        from unitcoordinator_routes import unitcoordinator_bp
        print("✓ Unit coordinator routes imported successfully")
    except Exception as e:
        print(f"✗ Unit coordinator routes import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database connection"""
    print("\n=== Testing Database ===")
    
    try:
        from flask import Flask
        from models import db, User
        
        app = Flask(__name__)
        database_url = os.getenv("DATABASE_URL", "sqlite:///dev.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        
        print(f"Database URL: {database_url}")
        
        db.init_app(app)
        
        with app.app_context():
            # Test database connection
            user_count = User.query.count()
            print(f"✓ Database connected successfully, {user_count} users found")
            return True
            
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        traceback.print_exc()
        return False

def test_flask_app():
    """Test basic Flask app creation"""
    print("\n=== Testing Flask App Creation ===")
    
    try:
        from flask import Flask
        app = Flask(__name__)
        app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
        print("✓ Flask app created successfully")
        return True
    except Exception as e:
        print(f"✗ Flask app creation failed: {e}")
        traceback.print_exc()
        return False

def test_environment():
    """Test environment variables and file system"""
    print("\n=== Testing Environment ===")
    
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    # Check important environment variables
    env_vars = ["SECRET_KEY", "DATABASE_URL", "FLASK_ENV"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: Not set")
    
    # Check if important files exist
    files = ["models.py", "auth.py", "admin_routes.py", "facilitator_routes.py", "unitcoordinator_routes.py"]
    for file in files:
        if os.path.exists(file):
            print(f"✓ {file}: Exists")
        else:
            print(f"✗ {file}: Missing")

def main():
    print("AWS Deployment Debug Script")
    print("=" * 40)
    
    test_environment()
    
    if not test_imports():
        print("\n❌ Import test failed - this is likely the issue!")
        return False
    
    if not test_flask_app():
        print("\n❌ Flask app creation failed!")
        return False
    
    if not test_database():
        print("\n❌ Database test failed - this might be the issue!")
        return False
    
    print("\n✅ All tests passed! The issue might be with nginx/gunicorn configuration.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
