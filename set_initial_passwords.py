#!/usr/bin/env python3
"""
Script to set initial passwords for existing facilitators who don't have passwords.
This script should be run once to migrate existing data.
"""

from models import db, User, UserRole
from application import app

def set_initial_passwords():
    """Set initial passwords for facilitators who don't have passwords."""
    with app.app_context():
        # Find all facilitators without passwords
        facilitators_without_passwords = User.query.filter(
            User.role == UserRole.FACILITATOR,
            User.password_hash.is_(None)
        ).all()
        
        print(f"Found {len(facilitators_without_passwords)} facilitators without passwords")
        
        for user in facilitators_without_passwords:
            # Generate initial password based on email prefix
            email_prefix = user.email.split('@')[0]
            initial_password = f"{email_prefix}123"
            
            # Set password and mark as initial password
            user.set_password(initial_password)
            user.has_changed_initial_password = False
            
            print(f"Set initial password for {user.email}: {initial_password}")
        
        # Commit changes
        db.session.commit()
        print(f"Successfully set initial passwords for {len(facilitators_without_passwords)} facilitators")

if __name__ == "__main__":
    set_initial_passwords()