"""
Script to create proper modules in the database.
This ensures we have actual modules (Lab 1, Lab 2, Tutorial, etc.) not just units.
"""

from flask import Flask
from models import db, Unit, Module

def create_minimal_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def create_modules():
    app = create_minimal_app()
    
    with app.app_context():
        # Check existing data
        units = Unit.query.all()
        modules = Module.query.all()
        
        print(f"Current units: {len(units)}")
        print(f"Current modules: {len(modules)}")
        
        # Create GENG2000 unit if it doesn't exist
        geng2000 = Unit.query.filter_by(unit_code='GENG2000').first()
        if not geng2000:
            geng2000 = Unit(
                unit_code='GENG2000',
                unit_name='Engineering Computing'
            )
            db.session.add(geng2000)
            db.session.flush()
            print("Created GENG2000 unit")
        
        # Create CITS3200 unit if it doesn't exist
        cits3200 = Unit.query.filter_by(unit_code='CITS3200').first()
        if not cits3200:
            cits3200 = Unit(
                unit_code='CITS3200',
                unit_name='Professional Computing'
            )
            db.session.add(cits3200)
            db.session.flush()
            print("Created CITS3200 unit")
        
        # Define modules to create
        modules_to_create = [
            # GENG2000 modules
            {'unit': geng2000, 'name': 'Lab 1', 'type': 'lab'},
            {'unit': geng2000, 'name': 'Lab 2', 'type': 'lab'},
            {'unit': geng2000, 'name': 'Lab 3', 'type': 'lab'},
            {'unit': geng2000, 'name': 'Tutorial A', 'type': 'tutorial'},
            {'unit': geng2000, 'name': 'Tutorial B', 'type': 'tutorial'},
            {'unit': geng2000, 'name': 'Workshop 1', 'type': 'workshop'},
            {'unit': geng2000, 'name': 'Workshop 2', 'type': 'workshop'},
            
            # CITS3200 modules
            {'unit': cits3200, 'name': 'Lab Session 1', 'type': 'lab'},
            {'unit': cits3200, 'name': 'Lab Session 2', 'type': 'lab'},
            {'unit': cits3200, 'name': 'Tutorial Session', 'type': 'tutorial'},
            {'unit': cits3200, 'name': 'Project Workshop', 'type': 'workshop'},
        ]
        
        created_count = 0
        for module_data in modules_to_create:
            # Check if module already exists
            existing = Module.query.filter_by(
                unit_id=module_data['unit'].id,
                module_name=module_data['name']
            ).first()
            
            if not existing:
                module = Module(
                    unit_id=module_data['unit'].id,
                    module_name=module_data['name'],
                    module_type=module_data['type']
                )
                db.session.add(module)
                created_count += 1
                print(f"Created: {module_data['name']} ({module_data['unit'].unit_code})")
        
        db.session.commit()
        print(f"\n✅ Created {created_count} new modules")
        
        # Show final state
        all_modules = Module.query.all()
        print(f"\nTotal modules in database: {len(all_modules)}")
        for module in all_modules:
            unit_code = module.unit.unit_code if module.unit else 'No Unit'
            print(f"  - {module.module_name} ({unit_code})")

if __name__ == '__main__':
    create_modules()
