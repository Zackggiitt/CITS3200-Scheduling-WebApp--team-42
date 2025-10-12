"""
Script to check available modules in the database.
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Module
from flask import Flask
from models import db

# Create a minimal app for database operations
def create_minimal_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def check_modules():
    app = create_minimal_app()
    
    with app.app_context():
        modules = Module.query.all()
        print("Available modules:")
        for m in modules:
            print(f"  {m.id}: {m.unit.unit_code} - {m.module_name} ({m.module_type})")

if __name__ == '__main__':
    check_modules()
