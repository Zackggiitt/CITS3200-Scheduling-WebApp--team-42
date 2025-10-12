# add_facilitator.py
import sys
import argparse
from getpass import getpass
from werkzeug.security import generate_password_hash

# --- Imports: adjust to your project structure if needed ---
from application import app, db
from models import User, UserRole


def main():
    parser = argparse.ArgumentParser(description="Create a Facilitator user and send setup email.")
    parser.add_argument("--email", required=True, help="User email (required)")
    parser.add_argument(
        "--update",
        action="store_true",
        help="If the user exists, resend the setup email.",
    )
    args = parser.parse_args()

    with app.app_context():
        # Make sure tables exist
        db.create_all()

        user = User.query.filter_by(email=args.email).first()
        if user:
            if not args.update:
                print(f"User {args.email} already exists. Use --update to resend setup email.")
                return
            
            # Check if user has already completed setup
            if user.first_name and user.last_name and user.password_hash:
                print(f"User {args.email} has already completed account setup.")
                print("Cannot resend setup email for completed accounts.")
                return
            
            print(f"Resending setup email to: {args.email}")
        else:
            # Create new user with only email and role
            user = User(
                email=args.email,
                role=UserRole.FACILITATOR,
                # No name or password - user will set these via the setup link
            )
            db.session.add(user)
            db.session.commit()
            print("Created Facilitator account:")
            print(f"• Email: {args.email}")
            print(f"• Status: Pending setup")
        
        # Send account setup email
        try:
            from email_service import send_welcome_email
            send_welcome_email(args.email, user_role=UserRole.FACILITATOR)
            print("• Setup email sent successfully")
            print("• User will receive a link to complete their account setup")
        except Exception as e:
            print(f"• Failed to send setup email: {e}")


if __name__ == "__main__":
    main()