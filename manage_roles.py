# manage_roles.py
import os
from application import app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def add_user_role(email, role, password=None):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.role = role
            if password:
                user.password_hash = generate_password_hash(password)
            db.session.commit()
            print(f"Updated role for {email} to {role.value}")
        else:
            new_user = User(
                email=email,
                first_name=email.split('@')[0],
                last_name="Test",
                role=role,
                password_hash=generate_password_hash(password) if password else None
            )
            db.session.add(new_user)
            db.session.commit()
            print(f"Created and updated role for {email} to {role.value}")

if __name__ == "__main__":
    add_user_role("admin@example.com", UserRole.ADMIN, "admin123")  # Default admin
    add_user_role("unitcoord@example.com", UserRole.UNIT_COORDINATOR, "password123")
    add_user_role("facilitator@example.com", UserRole.FACILITATOR, "password123")
    add_user_role("newuser@example.com", UserRole.FACILITATOR, "password123")
    print("Role updates complete. Run 'flask db upgrade' if using migrations, or restart app.")