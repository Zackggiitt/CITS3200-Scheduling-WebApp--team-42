# application.py

import os
import re
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from models import db, User, UserRole, Facilitator
    print("models imported successfully")
    from auth import login_required, is_safe_url, get_current_user
    print("auth utils imported successfully")
    from email_service import EmailToken
    print("email_service imported successfully")
except Exception as e:
    print(f"Error importing models/auth: {e}")
    raise
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils import role_required
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import RequestEntityTooLarge


# Blueprints
try:
    from admin_routes import admin_bp
    print("admin_routes imported successfully")
    from facilitator_routes import facilitator_bp
    print("facilitator_routes imported successfully")
    from unitcoordinator_routes import unitcoordinator_bp
    print("unitcoordinator_routes imported successfully")
    from auth import auth_bp  # contains POST /logout
    print("auth imported successfully")
except Exception as e:
    print(f"Error importing blueprints: {e}")
    raise

load_dotenv()

try:
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
    print("Flask app created successfully")
except Exception as e:
    print(f"Error creating Flask app: {e}")
    raise

# Recommended cookie hardening
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",               # consider "Strict" if it fits your flows
    SESSION_COOKIE_SECURE=False,  # Always False for HTTP deployment
)

# Rate limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["2000 per day", "500 per hour"])

# CSRF protection (protects all POST forms, incl. logout form)
csrf = CSRFProtect(app)

# Additional CSRF settings for deployment
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['WTF_CSRF_SSL_STRICT'] = False



@app.route("/setup-account", methods=["GET"])
def setup_account():
    """Handle account setup link from email"""
    token = request.args.get('token')
    
    if not token:
        flash("Invalid or missing setup link. Please check your email.")
        return redirect(url_for("login"))
    
    # Verify token and get email
    from email_service import verify_email_token
    email = verify_email_token(token)
    
    if not email:
        flash("This setup link is invalid or has expired. Please contact your administrator.")
        return redirect(url_for("login"))
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User account not found. Please contact your administrator.")
        return redirect(url_for("login"))
    
    # Check if user has already completed setup
    if user.first_name and user.last_name and user.password_hash:
        flash("This account has already been set up. Please log in.")
        return redirect(url_for("login"))
    
    # Get role name for display and determine which signup page to use
    if user.role == UserRole.ADMIN:
        # Admins use simplified signup page (no phone/staff number)
        return render_template("admin_signup.html", email=email, token=token)
    else:
        role_name = "Unit Coordinator" if user.role == UserRole.UNIT_COORDINATOR else "Facilitator"
        # Facilitators and UCs use full signup page
        return render_template("signup.html", email=email, token=token, role_name=role_name)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first = request.form["first_name"].strip()
        last = request.form["last_name"].strip()
        phone = request.form["phone"].strip()
        staff_number = request.form.get("staff_number", "").strip() or None
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        token = request.form.get("token")  # Get token if provided

        # If token is provided, verify it
        if token:
            from email_service import verify_email_token
            token_email = verify_email_token(token)
            
            if not token_email:
                flash("This setup link is invalid or has expired. Please contact your administrator.")
                return redirect(url_for("login"))
            
            # Ensure the email from the form matches the token
            if token_email.lower() != email:
                flash("Invalid setup link. Please use the link from your email.")
                return redirect(url_for("login"))

        # Validation
        if not all([first, last, phone, email, password, confirm_password]):
            flash("All fields except staff number are required!")
            return render_template("signup.html", email=email, token=token, 
                                 first_name=first, last_name=last, phone=phone, staff_number=staff_number)
        
        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!")
            return render_template("signup.html", email=email, token=token,
                                 first_name=first, last_name=last, phone=phone, staff_number=staff_number)

        # Check if email was pre-registered by admin
        existing_user = User.query.filter_by(email=email).first()
        if not existing_user or existing_user.role not in [UserRole.FACILITATOR, UserRole.UNIT_COORDINATOR]:
            flash("This email is not authorized to sign up. Please contact your administrator.")
            return render_template("signup.html", email=email, token=token,
                                 first_name=first, last_name=last, phone=phone, staff_number=staff_number)
        
        # Check if user has already completed signup (has name set)
        if existing_user.first_name and existing_user.last_name:
            flash("This account has already been set up. Please log in instead.")
            return render_template("signup.html", email=email, token=token,
                                 first_name=first, last_name=last, phone=phone, staff_number=staff_number)
        
        # Check if staff number already exists (only if provided)
        if staff_number:
            existing_staff = User.query.filter_by(staff_number=staff_number).first()
            if existing_staff and existing_staff.id != existing_user.id:
                flash("Staff number already exists!")
                return render_template("signup.html", email=email, token=token,
                                     first_name=first, last_name=last, phone=phone, staff_number=staff_number)
        
        # Phone validation - Australian mobile format (04XX XXX XXX)
        # Remove spaces and check format
        phone_clean = phone.replace(" ", "").replace("-", "")
        if not re.match(r'^04\d{8}$', phone_clean):
            flash("Phone number must be in format 04XXXXXXXX (10 digits starting with 04)!")
            return render_template("signup.html", email=email, token=token,
                                 first_name=first, last_name=last, phone=phone, staff_number=staff_number)
        
        # Password validation
        if len(password) < 8:
            flash("Password must be at least 8 characters!")
            return render_template("signup.html", email=email, token=token,
                                 first_name=first, last_name=last, phone=phone, staff_number=staff_number)
        
        if not re.search(r'[A-Z]', password):
            flash("Password must contain at least one uppercase letter!")
            return render_template("signup.html", email=email, token=token,
                                 first_name=first, last_name=last, phone=phone, staff_number=staff_number)
        
        if not re.search(r'[a-z]', password):
            flash("Password must contain at least one lowercase letter!")
            return render_template("signup.html", email=email, token=token,
                                 first_name=first, last_name=last, phone=phone, staff_number=staff_number)
        
        if not re.search(r'[0-9]', password):
            flash("Password must contain at least one number!")
            return render_template("signup.html", email=email, token=token,
                                 first_name=first, last_name=last, phone=phone, staff_number=staff_number)
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)!")
            return render_template("signup.html", email=email, token=token,
                                 first_name=first, last_name=last, phone=phone, staff_number=staff_number)

        try:
            # Update the existing user record with complete profile information
            existing_user.first_name = first
            existing_user.last_name = last
            existing_user.phone_number = phone
            existing_user.staff_number = staff_number
            existing_user.password_hash = generate_password_hash(password)
            
            db.session.commit()
            
            # Mark token as used if it was provided
            if token:
                from email_service import mark_token_as_used
                mark_token_as_used(token)
            
            # Dynamic success message based on role
            role_name = "Unit Coordinator" if existing_user.role == UserRole.UNIT_COORDINATOR else "Facilitator"
            flash(f"{role_name} account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
            
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.")
            return render_template("signup.html", email=email, token=token)
    
    return render_template("signup.html")


@app.route("/admin-signup", methods=["POST"])
def admin_signup():
    """Handle admin account setup (simplified - no phone/staff number)"""
    first = request.form["first_name"].strip()
    last = request.form["last_name"].strip()
    email = request.form["email"].strip().lower()
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]
    token = request.form.get("token")

    # Verify token
    if not token:
        flash("Invalid setup link. Please use the link from your email.")
        return redirect(url_for("login"))
    
    from email_service import verify_email_token
    token_email = verify_email_token(token)
    
    if not token_email or token_email.lower() != email:
        flash("This setup link is invalid or has expired. Please contact your administrator.")
        return redirect(url_for("login"))

    # Validation
    if not all([first, last, email, password, confirm_password]):
        flash("All fields are required!")
        return render_template("admin_signup.html", email=email, token=token, 
                             first_name=first, last_name=last)
    
    # Check if passwords match
    if password != confirm_password:
        flash("Passwords do not match!")
        return render_template("admin_signup.html", email=email, token=token,
                             first_name=first, last_name=last)

    # Check if email was pre-registered as admin
    existing_user = User.query.filter_by(email=email).first()
    if not existing_user or existing_user.role != UserRole.ADMIN:
        flash("This email is not authorized for admin signup. Please contact your administrator.")
        return render_template("admin_signup.html", email=email, token=token,
                             first_name=first, last_name=last)
    
    # Check if user has already completed signup
    if existing_user.first_name and existing_user.last_name and existing_user.password_hash:
        flash("This account has already been set up. Please log in instead.")
        return redirect(url_for("login"))
    
    # Password validation
    if len(password) < 8:
        flash("Password must be at least 8 characters!")
        return render_template("admin_signup.html", email=email, token=token,
                             first_name=first, last_name=last)
    
    if not re.search(r'[A-Z]', password):
        flash("Password must contain at least one uppercase letter!")
        return render_template("admin_signup.html", email=email, token=token,
                             first_name=first, last_name=last)
    
    if not re.search(r'[a-z]', password):
        flash("Password must contain at least one lowercase letter!")
        return render_template("admin_signup.html", email=email, token=token,
                             first_name=first, last_name=last)
    
    if not re.search(r'\d', password):
        flash("Password must contain at least one number!")
        return render_template("admin_signup.html", email=email, token=token,
                             first_name=first, last_name=last)

    try:
        # Update the existing admin user record
        existing_user.first_name = first
        existing_user.last_name = last
        existing_user.password_hash = generate_password_hash(password)
        
        db.session.commit()
        
        # Mark token as used
        from email_service import mark_token_as_used
        mark_token_as_used(token)
        
        flash("Admin account created successfully! Please log in.", "success")
        return redirect(url_for("login"))
        
    except Exception as e:
        db.session.rollback()
        flash("Registration failed. Please try again.")
        return render_template("admin_signup.html", email=email, token=token,
                             first_name=first, last_name=last)



# Make csrf_token available in all templates
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

# File uploads (CSV)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB cap
# Ensure Flask‑WTF accepts header-style CSRF tokens sent by fetch()
app.config["WTF_CSRF_METHODS"] = ["POST", "PUT", "PATCH", "DELETE"]
# (Flask‑WTF already reads 'X-CSRFToken' / 'X-CSRF-Token' from headers)

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return "File too large (max 5MB). Please reduce the CSV size.", 413


# DB
try:
    database_url = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    print(f"Database URL: {database_url}")
    db.init_app(app)
    print("Database initialized successfully")
except Exception as e:
    print(f"Database initialization error: {e}")
    raise

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(facilitator_bp)
app.register_blueprint(unitcoordinator_bp)
app.register_blueprint(auth_bp)

# Register email blueprint
try:
    from email_routes import email_bp
    app.register_blueprint(email_bp)
    print("email routes registered successfully")
except Exception as e:
    print(f"Error registering email routes: {e}")

# OAuth configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Make current user available globally (optional, handy for headers)
@app.context_processor
def inject_user():
    return {"user": get_current_user()}

# Set g.user for all requests (kept from your version)
@app.before_request
def before_request():
    g.user = get_current_user()

# Add safe security headers (won't break Flask development server)
@app.after_request
def add_security_headers(response):
    """Add security headers that are safe for development"""
    # Prevent clickjacking - stops your app from being embedded in iframes
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME type sniffing attacks
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable browser XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Control referrer information for privacy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    csp = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:* 127.0.0.1:*; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:* 127.0.0.1:* https://accounts.google.com; "
        "style-src 'self' 'unsafe-inline' localhost:* 127.0.0.1:*; "
        "img-src 'self' data: https: localhost:* 127.0.0.1:*; "
        "font-src 'self' localhost:* 127.0.0.1:*; "
        "connect-src 'self' localhost:* 127.0.0.1:*; "
        "frame-ancestors 'none';"
    )
    response.headers['Content-Security-Policy'] = csp
    
    return response

# Create DB tables
with app.app_context():
    db.create_all()

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.route("/")
def index():
    if "user_id" in session:
        user = get_current_user()
        if user is None:
            session.pop("user_id", None)
            flash("Session expired. Please log in again.")
            return render_template("login.html")

        role = user.role
        if role == UserRole.ADMIN:
            return redirect(url_for('admin.dashboard'))
        elif role == UserRole.UNIT_COORDINATOR:
            return redirect(url_for('unitcoordinator.dashboard'))
        else:
            return redirect(url_for('facilitator.dashboard'))
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("100 per minute")
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        selected_role = request.form.get("user_role", "facilitator")

        user = User.query.filter_by(email=email).first()
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            allowed = (
                (selected_role == "admin" and user.role == UserRole.ADMIN) or
                (selected_role == "unit_coordinator" and user.role == UserRole.UNIT_COORDINATOR) or
                (selected_role == "facilitator" and user.role == UserRole.FACILITATOR)
            )
            if not allowed:
                flash("You don't have permission for the selected role.")
                return render_template("login.html", selected_role=selected_role)
            
            session["user_id"] = user.id
            target = request.args.get("next")
            if target and is_safe_url(target):
                return redirect(target)

            if user.role == UserRole.ADMIN:
                return redirect(url_for("admin.dashboard"))
            elif user.role == UserRole.UNIT_COORDINATOR:
                return redirect(url_for("unitcoordinator.dashboard"))
            else:
                return redirect(url_for("facilitator.dashboard"))

        flash("Invalid credentials")
        return render_template("login.html", selected_role=selected_role)
    
    # GET request - check for selected_role in query params or default to facilitator
    selected_role = request.args.get("role", "facilitator")
    return render_template("login.html", selected_role=selected_role)

@app.route('/auth/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')

    if user_info:
        email = user_info['email']
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        avatar_url = user_info.get('picture', '')
        oauth_id = user_info['sub']

        user = User.query.filter_by(email=email).first()
        if not user:
            # Only allow Google sign-in for pre-registered facilitators or admins/coordinators
            flash('This email is not authorized. Please contact your unit coordinator to be added as a facilitator, or sign up manually if you are an admin or unit coordinator.')
            return redirect(url_for('login'))
        
        # Update OAuth information for existing user
        user.oauth_provider = 'google'
        user.oauth_id = oauth_id
        user.avatar_url = avatar_url
        
        # Update name if not already set (for facilitators completing their profile via OAuth)
        if not user.first_name:
            user.first_name = first_name
        if not user.last_name:
            user.last_name = last_name
            
        db.session.commit()

        session['user_id'] = user.id
        if user.role == UserRole.ADMIN:
            return redirect(url_for("admin.dashboard"))
        elif user.role == UserRole.UNIT_COORDINATOR:
            return redirect(url_for("unitcoordinator.dashboard"))
        else:
            return redirect(url_for("facilitator.dashboard"))

    flash('Google login failed')
    return redirect(url_for('login'))


@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def forgot_password():
    """Handle forgot password requests"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        
        if not email:
            flash("Please enter your email address.", "error")
            return render_template("forgot_password.html")
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        # Always show success message (don't reveal if email exists)
        # This prevents email enumeration attacks
        flash("If an account exists with that email, you will receive a password reset link shortly.", "success")
        
        if user:
            # Generate password reset token
            from email_service import generate_token, send_password_reset_email, EmailToken
            from datetime import datetime, timedelta
            
            token = generate_token()
            expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
            
            # Store token in database
            email_token = EmailToken(
                email=email,
                token=token,
                expires_at=expires_at,
                token_type='password_reset'
            )
            
            try:
                db.session.add(email_token)
                db.session.commit()
                
                # Send password reset email
                base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
                reset_link = f"{base_url}/reset-password?token={token}"
                
                send_password_reset_email(email, reset_link)
                print(f"Password reset email sent to {email}")
                
            except Exception as e:
                db.session.rollback()
                print(f"Error sending password reset email: {e}")
        
        return redirect(url_for('login'))
    
    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def reset_password():
    """Handle password reset with token"""
    if request.method == "GET":
        token = request.args.get("token", "").strip()
        
        if not token:
            flash("Invalid or missing reset token.", "error")
            return redirect(url_for('login'))
        
        # Validate token
        from email_service import EmailToken
        from datetime import datetime
        
        email_token = EmailToken.query.filter_by(
            token=token,
            token_type='password_reset',
            used=False
        ).first()
        
        if not email_token:
            flash("Invalid or expired reset link.", "error")
            return redirect(url_for('login'))
        
        # Check if token is expired
        if email_token.expires_at < datetime.utcnow():
            flash("This reset link has expired. Please request a new one.", "error")
            return redirect(url_for('forgot_password'))
        
        # Show reset password form
        return render_template("reset_password.html", token=token)
    
    # POST request - update password
    token = request.form.get("token", "").strip()
    password = request.form.get("password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()
    
    if not token or not password or not confirm_password:
        flash("All fields are required.", "error")
        return redirect(url_for('reset_password') + f"?token={token}")
    
    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for('reset_password') + f"?token={token}")
    
    # Validate password strength
    if len(password) < 8:
        flash("Password must be at least 8 characters long.", "error")
        return redirect(url_for('reset_password') + f"?token={token}")
    
    if not any(c.isupper() for c in password):
        flash("Password must contain at least one uppercase letter.", "error")
        return redirect(url_for('reset_password') + f"?token={token}")
    
    if not any(c.isdigit() for c in password):
        flash("Password must contain at least one number.", "error")
        return redirect(url_for('reset_password') + f"?token={token}")
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        flash("Password must contain at least one special character.", "error")
        return redirect(url_for('reset_password') + f"?token={token}")
    
    # Validate token again
    from email_service import EmailToken
    from datetime import datetime
    
    email_token = EmailToken.query.filter_by(
        token=token,
        token_type='password_reset',
        used=False
    ).first()
    
    if not email_token or email_token.expires_at < datetime.utcnow():
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for('login'))
    
    # Find user and update password
    user = User.query.filter_by(email=email_token.email).first()
    
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('login'))
    
    # Update password
    user.set_password(password)
    
    # Mark token as used
    email_token.used = True
    
    try:
        db.session.commit()
        flash("Your password has been reset successfully! You can now log in.", "success")
        print(f"Password reset successful for {user.email}")
        return redirect(url_for('login'))
    except Exception as e:
        db.session.rollback()
        print(f"Error resetting password: {e}")
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for('reset_password') + f"?token={token}")


if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')
