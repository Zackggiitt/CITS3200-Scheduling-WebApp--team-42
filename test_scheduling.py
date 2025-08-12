"""
Script to test the scheduling engine with module-based skills.
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduling_engine import generate_optimal_schedule
from flask import Flask
from models import db

def create_minimal_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def test_scheduling():
    app = create_minimal_app()
    
    with app.app_context():
        result = generate_optimal_schedule()
        print("Scheduling result:")
        print(f"Success: {result['success']}")
        print(f"Assignments made: {result['assignments_made']}")
        print(f"Message: {result['message']}")
        if result['conflicts']:
            print("Conflicts:")
            for conflict in result['conflicts']:
                print(f"  - {conflict}")

if __name__ == '__main__':
    test_scheduling()
