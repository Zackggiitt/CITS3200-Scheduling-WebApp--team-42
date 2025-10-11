#!/usr/bin/env python3
"""
Database migration script to add has_changed_initial_password field to User table.
"""

import sqlite3
import os

def migrate_database():
    """Add has_changed_initial_password column to User table."""
    # Database path
    db_path = 'instance/dev.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    # Connect directly to SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'has_changed_initial_password' not in columns:
            print("Adding has_changed_initial_password column to user table...")
            cursor.execute("""
                ALTER TABLE user 
                ADD COLUMN has_changed_initial_password BOOLEAN DEFAULT 0
            """)
            
            # Set existing users with passwords to True (they've already changed from initial)
            cursor.execute("""
                UPDATE user 
                SET has_changed_initial_password = 1 
                WHERE password_hash IS NOT NULL AND password_hash != ''
            """)
            
            conn.commit()
            print("Successfully added has_changed_initial_password column")
        else:
            print("Column has_changed_initial_password already exists")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()