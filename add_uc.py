# add_uc.py
from werkzeug.security import generate_password_hash
from application import db, app
from models import User, UserRole

with app.app_context():
    email = "uc_demo@example.com"
    first_name = "unitcoord"
    last_name = "Test"
    password = "password123"  # you can change this

    # Check if already exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        print(f"User {email} already exists.")
    else:
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=generate_password_hash(password),
            role=UserRole.UNIT_COORDINATOR,
        )
        db.session.add(user)
        db.session.commit()
        print(f"Created Unit Coordinator: {email} / {password}")
