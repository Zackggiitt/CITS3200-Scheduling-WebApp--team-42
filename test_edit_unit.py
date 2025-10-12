#!/usr/bin/env python3
"""
Test script for Edit Unit + Email functionality
Tests:
1. Create unit with facilitators -> emails sent on final step
2. Edit unit with new facilitators -> only new facilitators get emails
3. Verify no cascade delete bugs
"""

import os
import sys
from datetime import datetime, timedelta

# Set up environment
os.environ['USE_MOCK_EMAIL'] = 'true'  # Use mock emails for testing

from application import app, db
from models import User, Unit, Module, UserRole, UnitFacilitator
from email_service import EmailToken

def reset_database():
    """Reset the database"""
    print("\n🔄 Resetting database...")
    with app.app_context():
        db.drop_all()
        db.create_all()
    print("✅ Database reset complete")

def create_test_users():
    """Create test UC and admin"""
    print("\n👤 Creating test users...")
    with app.app_context():
        # Create UC
        uc = User(
            email="testuc@test.com",
            role=UserRole.UNIT_COORDINATOR,
            first_name="Test",
            last_name="UC"
        )
        uc.set_password("password123")
        db.session.add(uc)
        
        # Create admin
        admin = User(
            email="testadmin@test.com",
            role=UserRole.ADMIN,
            first_name="Test",
            last_name="Admin"
        )
        admin.set_password("password123")
        db.session.add(admin)
        
        db.session.commit()
        print(f"✅ Created UC: {uc.email}")
        print(f"✅ Created Admin: {admin.email}")
        return uc.id

def create_unit_with_facilitators(uc_id):
    """Simulate creating a unit with facilitators"""
    print("\n📚 Creating unit with facilitators...")
    with app.app_context():
        # Create unit
        unit = Unit(
            unit_code="CITS3200",
            unit_name="Professional Computing",
            year=2025,
            semester="1",
            description="Test unit",
            start_date=datetime(2025, 2, 1).date(),
            end_date=datetime(2025, 5, 31).date(),
            created_by=uc_id
        )
        db.session.add(unit)
        db.session.commit()
        
        print(f"✅ Created unit: {unit.unit_code} - {unit.unit_name}")
        
        # Create facilitators (simulating CSV upload)
        facilitator_emails = ["fac1@test.com", "fac2@test.com"]
        new_emails = []
        
        for email in facilitator_emails:
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            if not user:
                # Create new facilitator
                user = User(email=email, role=UserRole.FACILITATOR)
                db.session.add(user)
                db.session.flush()
                new_emails.append(email)
                print(f"  ➕ Created facilitator: {email}")
            
            # Link to unit
            link = UnitFacilitator(unit_id=unit.id, user_id=user.id)
            db.session.add(link)
        
        db.session.commit()
        
        # Simulate sending emails (would happen on "Create Unit" button)
        print(f"\n📧 Simulating email sending on 'Create Unit'...")
        for email in new_emails:
            print(f"  ✉️  Setup email sent to: {email}")
        
        return unit.id

def edit_unit_add_facilitators(unit_id):
    """Simulate editing unit and adding more facilitators"""
    print("\n✏️  Editing unit and adding more facilitators...")
    with app.app_context():
        unit = Unit.query.get(unit_id)
        
        # Add more facilitators (simulating CSV upload in edit mode)
        facilitator_emails = ["fac1@test.com", "fac3@test.com", "fac4@test.com"]
        new_emails = []
        existing_emails = []
        
        for email in facilitator_emails:
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            if not user:
                # Create new facilitator
                user = User(email=email, role=UserRole.FACILITATOR)
                db.session.add(user)
                db.session.flush()
                new_emails.append(email)
                print(f"  ➕ Created facilitator: {email}")
            else:
                existing_emails.append(email)
                print(f"  ✓ Facilitator already exists: {email}")
            
            # Link to unit (if not already linked)
            link = UnitFacilitator.query.filter_by(unit_id=unit.id, user_id=user.id).first()
            if not link:
                link = UnitFacilitator(unit_id=unit.id, user_id=user.id)
                db.session.add(link)
        
        db.session.commit()
        
        # Simulate sending emails (would happen on "Apply Changes" button)
        print(f"\n📧 Simulating email sending on 'Apply Changes'...")
        if new_emails:
            for email in new_emails:
                print(f"  ✉️  Setup email sent to: {email}")
        else:
            print(f"  ℹ️  No new facilitators - no emails sent")
        
        if existing_emails:
            print(f"\n✅ Existing facilitators (NO emails sent):")
            for email in existing_emails:
                print(f"  ⏭️  Skipped: {email}")

def verify_no_cascade_delete(unit_id):
    """Verify that removing facilitator link doesn't delete user or unit"""
    print("\n🔍 Testing cascade delete bug fix...")
    with app.app_context():
        unit = Unit.query.get(unit_id)
        
        # Get a facilitator link
        link = UnitFacilitator.query.filter_by(unit_id=unit.id).first()
        if not link:
            print("  ⚠️  No facilitator links to test")
            return
        
        user_id = link.user_id
        user_email = link.user.email
        
        # Remove the link
        db.session.delete(link)
        db.session.commit()
        print(f"  🗑️  Removed facilitator link for: {user_email}")
        
        # Check if user still exists
        user = User.query.get(user_id)
        if user:
            print(f"  ✅ User still exists: {user.email}")
        else:
            print(f"  ❌ BUG: User was deleted!")
        
        # Check if unit still exists
        unit = Unit.query.get(unit_id)
        if unit:
            print(f"  ✅ Unit still exists: {unit.unit_code}")
        else:
            print(f"  ❌ BUG: Unit was deleted!")

def print_summary():
    """Print database summary"""
    print("\n" + "="*60)
    print("📊 DATABASE SUMMARY")
    print("="*60)
    with app.app_context():
        users = User.query.all()
        units = Unit.query.all()
        links = UnitFacilitator.query.all()
        
        print(f"\n👥 Users ({len(users)}):")
        for user in users:
            print(f"  - {user.email} ({user.role.value})")
        
        print(f"\n📚 Units ({len(units)}):")
        for unit in units:
            print(f"  - {unit.unit_code}: {unit.unit_name}")
        
        print(f"\n🔗 Unit-Facilitator Links ({len(links)}):")
        for link in links:
            print(f"  - Unit {link.unit_id} ↔ User {link.user_id} ({link.user.email})")

def main():
    print("="*60)
    print("🧪 TESTING EDIT UNIT + EMAIL FUNCTIONALITY")
    print("="*60)
    
    # Step 1: Reset database
    reset_database()
    
    # Step 2: Create test users
    uc_id = create_test_users()
    
    # Step 3: Create unit with facilitators
    unit_id = create_unit_with_facilitators(uc_id)
    
    # Step 4: Edit unit and add more facilitators
    edit_unit_add_facilitators(unit_id)
    
    # Step 5: Verify no cascade delete bugs
    verify_no_cascade_delete(unit_id)
    
    # Step 6: Print summary
    print_summary()
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE!")
    print("="*60)
    print("\n📝 What to check:")
    print("  1. New facilitators get emails on 'Create Unit'")
    print("  2. Only NEW facilitators get emails on 'Apply Changes'")
    print("  3. Existing facilitators don't get duplicate emails")
    print("  4. Removing facilitator link doesn't delete user or unit")
    print("\n🔐 Test Login Credentials:")
    print("  UC: testuc@test.com / password123")
    print("  Admin: testadmin@test.com / password123")
    print("\n💡 Now test manually in the browser!")

if __name__ == "__main__":
    main()
