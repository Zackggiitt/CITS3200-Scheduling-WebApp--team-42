import sys
import argparse
from getpass import getpass
from werkzeug.security import generate_password_hash

# --- Imports: adjust to your project structure if needed ---
# If your app exposes `app` and `db` from `application`, this works as-is.
from application import app, db
from models import User, UserRole


def main():
    parser = argparse.ArgumentParser(description="Create or update an Admin user.")
    parser.add_argument("--email", default="admin_demo@example.com", help="User email")
    parser.add_argument("--first", default="admin", help="First name")
    parser.add_argument("--last", default="Test", help="Last name")
    parser.add_argument(
        "--password",
        default=None,
        help="Password (omit to be prompted)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="If the user exists, update their name/role; also update password if provided.",
    )
    args = parser.parse_args()

    # Prompt for password if not provided via flag
    password = args.password or getpass("Password (leave blank to cancel): ").strip()
    if not password:
        print("No password provided. Aborting.")
        sys.exit(1)

    with app.app_context():
        # Make sure tables exist
        db.create_all()

        user = User.query.filter_by(email=args.email).first()
        if user:
            if not args.update:
                print(f"User {args.email} already exists. Use --update to modify.")
                return
            # Update existing
            user.first_name = args.first
            user.last_name = args.last
            user.role = UserRole.ADMIN
            if args.password:
                user.password_hash = generate_password_hash(password)
            db.session.commit()
            print(f"Updated Admin: {args.email}")
            if args.password:
                print("• Password was updated.")
            return

        # Create new
        user = User(
            email=args.email,
            first_name=args.first,
            last_name=args.last,
            role=UserRole.ADMIN,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        print(f"Created Admin:")
        print(f"• Email:    {args.email}")
        print(f"• Password: {password}")


if __name__ == "__main__":
    main()


