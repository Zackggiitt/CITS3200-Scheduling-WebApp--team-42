"""
Script to add sample sessions to the database for testing the scheduling engine.
"""

import os
import sys
from datetime import datetime, time, timedelta

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Session, Module
from flask import Flask
from models import db

# Create a minimal app for database operations
def create_minimal_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def add_sample_sessions():
    app = create_minimal_app()
    
    with app.app_context():
        # Get modules
        lab1 = Module.query.get(1)
        lab2 = Module.query.get(2)
        workshop_a = Module.query.get(4)
        lecture1 = Module.query.get(6)
        
        if not lab1 or not lab2 or not workshop_a or not lecture1:
            print("Required modules not found!")
            return
        
        # Add sample sessions
        # Create datetime objects for next week
        base_date = datetime.utcnow() + timedelta(days=7)
        
        sessions = [
            Session(
                module_id=lab1.id,
                day_of_week=0,  # Monday
                start_time=datetime.combine(base_date.date(), time(9, 0)),
                end_time=datetime.combine(base_date.date(), time(11, 0)),
                max_facilitators=2
            ),
            Session(
                module_id=lab2.id,
                day_of_week=1,  # Tuesday
                start_time=datetime.combine(base_date.date() + timedelta(days=1), time(14, 0)),
                end_time=datetime.combine(base_date.date() + timedelta(days=1), time(16, 0)),
                max_facilitators=2
            ),
            Session(
                module_id=workshop_a.id,
                day_of_week=2,  # Wednesday
                start_time=datetime.combine(base_date.date() + timedelta(days=2), time(10, 0)),
                end_time=datetime.combine(base_date.date() + timedelta(days=2), time(12, 0)),
                max_facilitators=1
            ),
            Session(
                module_id=lecture1.id,
                day_of_week=3,  # Thursday
                start_time=datetime.combine(base_date.date() + timedelta(days=3), time(11, 0)),
                end_time=datetime.combine(base_date.date() + timedelta(days=3), time(12, 0)),
                max_facilitators=1
            )
        ]
        
        # Clear existing sessions
        Session.query.delete()
        
        for session in sessions:
            db.session.add(session)
        
        db.session.commit()
        print("Sample sessions added successfully!")

if __name__ == '__main__':
    add_sample_sessions()
