"""
Script to initialize sample units and modules for testing purposes.
This script creates sample data in the database for GENG2000 with 8 modules.
"""

from models import db, Unit, Module
from flask import Flask

# Create a minimal app for database operations
def create_minimal_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def init_sample_data():
    app = create_minimal_app()
    
    with app.app_context():
        # Check if sample data already exists
        existing_unit = Unit.query.filter_by(unit_code='GENG2000').first()
        if existing_unit:
            print("Sample data already exists. Skipping initialization.")
            return
        
        # Create GENG2000 unit
        geng2000 = Unit(
            unit_code='GENG2000',
            unit_name='Engineering Computing'
        )
        db.session.add(geng2000)
        db.session.flush()  # Get the ID without committing
        
        # Create 8 modules for GENG2000
        modules = [
            Module(unit_id=geng2000.id, module_name='Lab 1', module_type='lab'),
            Module(unit_id=geng2000.id, module_name='Lab 2', module_type='lab'),
            Module(unit_id=geng2000.id, module_name='Lab 3', module_type='lab'),
            Module(unit_id=geng2000.id, module_name='Workshop A', module_type='workshop'),
            Module(unit_id=geng2000.id, module_name='Workshop B', module_type='workshop'),
            Module(unit_id=geng2000.id, module_name='Lecture 1', module_type='lecture'),
            Module(unit_id=geng2000.id, module_name='Lecture 2', module_type='lecture'),
            Module(unit_id=geng2000.id, module_name='Tutorial', module_type='tutorial')
        ]
        
        for module in modules:
            db.session.add(module)
        
        db.session.commit()
        print("Sample data initialized successfully!")
        print(f"Created unit: {geng2000.unit_code} - {geng2000.unit_name}")
        print("Created modules:")
        for module in modules:
            print(f"  - {module.module_name} ({module.module_type})")

if __name__ == '__main__':
    init_sample_data()
