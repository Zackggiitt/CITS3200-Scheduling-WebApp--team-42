import sys
from werkzeug.security import generate_password_hash
from datetime import datetime

# Import your Flask app and models
from application import app, db
from models import Facilitator, User, UserRole


def create_sample_facilitators():
    """Create 5 sample facilitators in the database"""
    
    # Sample facilitator data
    sample_facilitators = [
        {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'phone': '0412345678',
            'staff_number': 'STF001',
            'email': 'alice.johnson@university.edu',
            'password': 'password123'
        },
        {
            'first_name': 'Bob',
            'last_name': 'Smith',
            'phone': '0423456789',
            'staff_number': 'STF002',
            'email': 'bob.smith@university.edu',
            'password': 'password123'
        },
        {
            'first_name': 'Carol',
            'last_name': 'Williams',
            'phone': '0434567890',
            'staff_number': 'STF003',
            'email': 'carol.williams@university.edu',
            'password': 'password123'
        },
        {
            'first_name': 'David',
            'last_name': 'Brown',
            'phone': '0445678901',
            'staff_number': 'STF004',
            'email': 'david.brown@university.edu',
            'password': 'password123'
        },
        {
            'first_name': 'Emma',
            'last_name': 'Davis',
            'phone': '0456789012',
            'staff_number': 'STF005',
            'email': 'emma.davis@university.edu',
            'password': 'password123'
        }
    ]

    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        created_count = 0
        skipped_count = 0
        
        for fac_data in sample_facilitators:
            # Check if facilitator already exists (by email or staff number)
            existing_fac = Facilitator.query.filter(
                (Facilitator.email == fac_data['email']) | 
                (Facilitator.staff_number == fac_data['staff_number'])
            ).first()
            
            if existing_fac:
                print(f"Skipping {fac_data['first_name']} {fac_data['last_name']} - already exists")
                skipped_count += 1
                continue
            
            # Create new facilitator
            facilitator = Facilitator(
                first_name=fac_data['first_name'],
                last_name=fac_data['last_name'],
                phone=fac_data['phone'],
                staff_number=fac_data['staff_number'],
                email=fac_data['email'],
                password_hash=generate_password_hash(fac_data['password']),
                created_at=datetime.utcnow()
            )
            
            # Also create corresponding User record for authentication
            user = User(
                first_name=fac_data['first_name'],
                last_name=fac_data['last_name'],
                email=fac_data['email'],
                password_hash=generate_password_hash(fac_data['password']),
                role=UserRole.FACILITATOR
            )
            
            try:
                db.session.add(facilitator)
                db.session.add(user)
                db.session.commit()
                
                print(f"✓ Created: {fac_data['first_name']} {fac_data['last_name']} ({fac_data['email']})")
                created_count += 1
                
            except Exception as e:
                db.session.rollback()
                print(f"✗ Error creating {fac_data['first_name']} {fac_data['last_name']}: {str(e)}")
        
        print(f"\n--- Summary ---")
        print(f"Created: {created_count} facilitators")
        print(f"Skipped: {skipped_count} facilitators")
        print(f"Total facilitators in database: {Facilitator.query.count()}")


def clear_all_facilitators():
    """Clear all facilitators from the database (use with caution!)"""
    with app.app_context():
        try:
            # Delete all facilitators
            facilitator_count = Facilitator.query.count()
            Facilitator.query.delete()
            
            # Delete all users with FACILITATOR role
            user_count = User.query.filter_by(role=UserRole.FACILITATOR).count()
            User.query.filter_by(role=UserRole.FACILITATOR).delete()
            
            db.session.commit()
            
            print(f"✓ Cleared {facilitator_count} facilitators and {user_count} facilitator users")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error clearing facilitators: {str(e)}")


def list_all_facilitators():
    """List all facilitators in the database"""
    with app.app_context():
        facilitators = Facilitator.query.all()
        
        if not facilitators:
            print("No facilitators found in the database.")
            return
        
        print(f"\n--- All Facilitators ({len(facilitators)}) ---")
        for fac in facilitators:
            print(f"• {fac.first_name} {fac.last_name}")
            print(f"  Email: {fac.email}")
            print(f"  Phone: {fac.phone}")
            print(f"  Staff#: {fac.staff_number}")
            print(f"  Created: {fac.created_at.strftime('%Y-%m-%d %H:%M')}")
            print()


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "create":
            create_sample_facilitators()
        elif command == "list":
            list_all_facilitators()
        elif command == "clear":
            confirm = input("Are you sure you want to clear ALL facilitators? (yes/no): ")
            if confirm.lower() == "yes":
                clear_all_facilitators()
            else:
                print("Operation cancelled.")
        else:
            print("Unknown command. Use: create, list, or clear")
    else:
        print("Available commands:")
        print("  python create_sample_facilitators.py create  - Create 5 sample facilitators")
        print("  python create_sample_facilitators.py list    - List all facilitators")
        print("  python create_sample_facilitators.py clear   - Clear all facilitators")


if __name__ == "__main__":
    main()