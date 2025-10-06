"""
Migration helper script for Availability to Unavailability transition.
This script helps run the database migration and provides options for data migration.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, User, UserRole, Unit, Module, FacilitatorSkill, Session, Availability, Unavailability, Assignment, SwapRequest, RecurringPattern

app = Flask(__name__)
app.secret_key = "dev-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def backup_availability_data():
    """Backup existing availability data before migration"""
    with app.app_context():
        availability_records = Availability.query.all()
        backup_data = []
        
        for record in availability_records:
            backup_data.append({
                'user_id': record.user_id,
                'day_of_week': record.day_of_week,
                'start_time': record.start_time,
                'end_time': record.end_time,
                'is_available': record.is_available,
                'created_at': record.created_at
            })
        
        print(f"Backed up {len(backup_data)} availability records")
        return backup_data

def migrate_availability_to_unavailability(backup_data, unit_id=None):
    """
    Migrate availability data to unavailability format.
    This is a basic migration - you may need to customize based on your needs.
    """
    with app.app_context():
        if not unit_id:
            # Get the first available unit, or create a default one
            unit = Unit.query.first()
            if not unit:
                print("No units found. Please create a unit first.")
                return
            unit_id = unit.id
        
        migrated_count = 0
        
        for record in backup_data:
            if not record['is_available']:  # Only migrate unavailable times
                # Convert day_of_week to actual dates (this is simplified)
                # In a real migration, you'd need to specify the actual dates
                today = datetime.now().date()
                
                # Find the next occurrence of this day of week
                days_ahead = record['day_of_week'] - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                
                target_date = today + timedelta(days=days_ahead)
                
                # Create unavailability record
                unavailability = Unavailability(
                    user_id=record['user_id'],
                    unit_id=unit_id,
                    date=target_date,
                    start_time=record['start_time'],
                    end_time=record['end_time'],
                    is_full_day=False,
                    reason="Migrated from availability system"
                )
                
                db.session.add(unavailability)
                migrated_count += 1
        
        db.session.commit()
        print(f"Migrated {migrated_count} availability records to unavailability")

def run_migration():
    """Run the complete migration process"""
    print("Starting Availability to Unavailability migration...")
    
    # Step 1: Backup existing data
    print("Step 1: Backing up existing availability data...")
    backup_data = backup_availability_data()
    
    # Step 2: Drop and recreate tables (this will be handled by the migration)
    print("Step 2: Database schema will be updated by Alembic migration")
    print("Please run: flask db upgrade")
    
    # Step 3: Migrate data (optional)
    migrate_choice = input("Do you want to migrate existing availability data to unavailability? (y/n): ")
    if migrate_choice.lower() == 'y':
        print("Step 3: Migrating availability data...")
        migrate_availability_to_unavailability(backup_data)
    
    print("Migration process completed!")

if __name__ == '__main__':
    run_migration()
