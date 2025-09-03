"""
Script to check available modules in the database and parse CSV data.
"""

import os
import sys
import csv
import re
from datetime import datetime, time, date, timedelta
from collections import defaultdict

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Module, Unit, Session, Venue, db
from flask import Flask

# Create a minimal app for database operations
def create_minimal_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def parse_csv_headers_and_contents(csv_file_path="GENG2000.csv"):
    """
    Parse the CSV file headers and contents, returning structured data.
    """
    parsed_data = {
        'headers': [],
        'workshops': [],
        'unique_workshops': set(),
        'unique_locations': set(),
        'schedule_data': []
    }
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            # Store headers
            parsed_data['headers'] = csv_reader.fieldnames
            
            for row in csv_reader:
                # Extract workshop information
                activity_code = row['activity_group_code']
                workshop_name = extract_workshop_name(activity_code)
                workshop_number = extract_workshop_number(activity_code)
                
                # Parse time
                start_time = parse_time(row['start_time'])
                
                # Parse weeks
                weeks = parse_weeks(row['weeks'])
                
                # Parse location
                location = parse_location(row['location'])
                
                # Store unique workshops and locations
                parsed_data['unique_workshops'].add(workshop_name)
                parsed_data['unique_locations'].add(location)
                
                # Create structured data entry
                schedule_entry = {
                    'activity_code': activity_code,
                    'workshop_name': workshop_name,
                    'workshop_number': workshop_number,
                    'day_of_week': row['day_of_week'],
                    'start_time': start_time,
                    'weeks': weeks,
                    'duration': int(row['duration']),
                    'location': location,
                    'raw_location': row['location']
                }
                
                parsed_data['schedule_data'].append(schedule_entry)
                parsed_data['workshops'].append(schedule_entry)
    
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error parsing CSV file: {e}")
        return None
    
    return parsed_data

def extract_workshop_name(activity_code):
    """Extract workshop name from activity code."""
    # Example: "Workshop-01_Practical_Safety-01" -> "Practical Safety"
    parts = activity_code.split('_')
    if len(parts) >= 2:
        return parts[1].replace('_', ' ')
    return activity_code

def extract_workshop_number(activity_code):
    """Extract workshop number from activity code."""
    # Example: "Workshop-01_Practical_Safety-01" -> "01"
    match = re.search(r'Workshop-(\d+)', activity_code)
    return match.group(1) if match else ""

def parse_time(time_str):
    """Parse time string to time object."""
    try:
        return datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return None

def parse_weeks(weeks_str):
    """Parse weeks string to extract week information."""
    # Handle different formats like "30/6", "7/7", "1/7", "30-Jun"
    if '/' in weeks_str:
        parts = weeks_str.split('/')
        if len(parts) == 2:
            try:
                week_num = int(parts[0])
                month = int(parts[1])
                return {'week': week_num, 'month': month}
            except ValueError:
                pass
    return {'raw': weeks_str}

def parse_location(location_str):
    """Parse location string to extract venue information."""
    # Extract venue name from location string
    # Example: "EZONENTH: [ 109] Learning Studio (30/6)" -> "EZONENTH: [ 109] Learning Studio"
    
    # Remove week information in parentheses
    location_clean = re.sub(r'\s*\([^)]+\)', '', location_str)
    
    # Handle multiple locations separated by commas
    locations = [loc.strip() for loc in location_clean.split(',')]
    
    # Return the first location for simplicity
    return locations[0] if locations else location_str

def display_parsed_data(parsed_data):
    """Display the parsed CSV data in a formatted way."""
    if not parsed_data:
        print("No data to display.")
        return
    
    print("=" * 60)
    print("CSV PARSING RESULTS")
    print("=" * 60)
    
    print(f"\nHeaders: {', '.join(parsed_data['headers'])}")
    
    print(f"\nUnique Workshops ({len(parsed_data['unique_workshops'])}):")
    for i, workshop in enumerate(sorted(parsed_data['unique_workshops']), 1):
        print(f"  {i}. {workshop}")
    
    print(f"\nUnique Locations ({len(parsed_data['unique_locations'])}):")
    for i, location in enumerate(sorted(parsed_data['unique_locations']), 1):
        print(f"  {i}. {location}")
    
    print(f"\nTotal Schedule Entries: {len(parsed_data['schedule_data'])}")
    
    # Show sample entries
    print(f"\nSample Schedule Entries (first 5):")
    for i, entry in enumerate(parsed_data['schedule_data'][:5], 1):
        print(f"  {i}. {entry['workshop_name']} - {entry['day_of_week']} {entry['start_time']} - {entry['location']}")

def create_database_entries(parsed_data, unit_code="GENG2000"):
    """
    Create database entries from parsed CSV data.
    """
    app = create_minimal_app()
    
    with app.app_context():
        try:
            # Find or create the unit
            unit = Unit.query.filter_by(unit_code=unit_code).first()
            if not unit:
                print(f"Unit {unit_code} not found. Please create it first.")
                return False
            
            # Create modules for each unique workshop
            created_modules = {}
            for workshop_name in parsed_data['unique_workshops']:
                module = Module.query.filter_by(
                    unit_id=unit.id,
                    module_name=workshop_name,
                    module_type="workshop"
                ).first()
                
                if not module:
                    module = Module(
                        unit_id=unit.id,
                        module_name=workshop_name,
                        module_type="workshop"
                    )
                    db.session.add(module)
                    db.session.flush()  # Get the ID
                    print(f"Created module: {workshop_name}")
                
                created_modules[workshop_name] = module
            
            # Create venues for unique locations
            created_venues = {}
            for location in parsed_data['unique_locations']:
                venue = Venue.query.filter_by(name=location).first()
                if not venue:
                    venue = Venue(name=location)
                    db.session.add(venue)
                    db.session.flush()  # Get the ID
                    print(f"Created venue: {location}")
                
                created_venues[location] = venue
            
            # Create sessions
            sessions_created = 0
            for entry in parsed_data['schedule_data']:
                module = created_modules[entry['workshop_name']]
                
                # Create session (you might want to add more logic for recurring sessions)
                session = Session(
                    module_id=module.id,
                    session_type="workshop",
                    start_time=datetime.combine(date.today(), entry['start_time']),
                    end_time=datetime.combine(date.today(), 
                        (datetime.combine(date.today(), entry['start_time']) + 
                         timedelta(minutes=entry['duration'])).time()),
                    day_of_week=get_day_number(entry['day_of_week']),
                    location=entry['location']
                )
                db.session.add(session)
                sessions_created += 1
            
            db.session.commit()
            print(f"\nSuccessfully created {sessions_created} sessions.")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating database entries: {e}")
            return False

def get_day_number(day_name):
    """Convert day name to number (0=Monday, 6=Sunday)."""
    days = {
        'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 
        'Fri': 4, 'Sat': 5, 'Sun': 6
    }
    return days.get(day_name, 0)

def check_modules():
    """Original function to check available modules."""
    app = create_minimal_app()
    
    with app.app_context():
        modules = Module.query.all()
        print("Available modules:")
        for m in modules:
            print(f"  {m.id}: {m.unit.unit_code} - {m.module_name} ({m.module_type})")

def main():
    """Main function to demonstrate CSV parsing."""
    print("CSV Parser for GENG2000 Workshop Data")
    print("=" * 50)
    
    # Parse the CSV file
    parsed_data = parse_csv_headers_and_contents()
    
    if parsed_data:
        # Display parsed data
        display_parsed_data(parsed_data)
        
        # Ask user if they want to create database entries
        print("\n" + "=" * 60)
        response = input("Do you want to create database entries from this data? (y/n): ")
        
        if response.lower() == 'y':
            success = create_database_entries(parsed_data)
            if success:
                print("Database entries created successfully!")
            else:
                print("Failed to create database entries.")
        
        # Show current modules
        print("\n" + "=" * 60)
        print("Current modules in database:")
        check_modules()

if __name__ == '__main__':
    main()
