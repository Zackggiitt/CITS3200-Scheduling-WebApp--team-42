from application import app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Check if admin already exists
        if User.query.filter_by(email="admin@gmail.com").first():
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            email="admin@gmail.com",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            password_hash=generate_password_hash("admin")
        )
        
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")

if __name__ == "__main__":
    create_admin()
