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
            print(f"User {email} not found.")

if __name__ == "__main__":
    # Example usage
    add_user_role("unitcoord@example.com", UserRole.UNIT_COORDINATOR, "password123")
    add_user_role("admin2@example.com", UserRole.ADMIN, "adminpass")
    print("Role updates complete. Run 'flask db upgrade' if using migrations, or restart app.")