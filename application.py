# application.py

import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, UserRole, Facilitator
from auth import login_required, is_safe_url, get_current_user
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils import role_required
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import RequestEntityTooLarge


# Blueprints
from admin_routes import admin_bp
from facilitator_routes import facilitator_bp
from unitcoordinator_routes import unitcoordinator_bp
from auth import auth_bp  # contains POST /logout

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

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



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first = request.form["first_name"].strip()
        last = request.form["last_name"].strip()
        phone = request.form["phone"].strip()
        staff_number = request.form["staff_number"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # Validation
        if not all([first, last, phone, staff_number, email, password]):
            flash("All fields are required!")
            return render_template("signup.html")

        # Check if email already exists in User table
        if User.query.filter_by(email=email).first():
            flash("Email already exists!")
            return render_template("signup.html")
        
        # Check if email already exists in Facilitator table
        if Facilitator.query.filter_by(email=email).first():
            flash("Email already exists!")
            return render_template("signup.html")
        
        # Check if staff number already exists in Facilitator table
        if Facilitator.query.filter_by(staff_number=staff_number).first():
            flash("Staff number already exists!")
            return render_template("signup.html")
        
        # Optional: Add phone validation
        if len(phone) < 10:
            flash("Please enter a valid phone number!")
            return render_template("signup.html")
        
        # Password validation
        if len(password) < 6:
            flash("Password must be at least 6 characters!")
            return render_template("signup.html")

        try:
            # Create facilitator record
            facilitator = Facilitator(
                first_name=first,
                last_name=last,
                phone=phone,
                staff_number=staff_number,
                email=email,
                password_hash=generate_password_hash(password)
            )
            
            # Also create user record for authentication
            user = User(
                first_name=first,
                last_name=last,
                email=email,
                password_hash=generate_password_hash(password),
                role=UserRole.FACILITATOR
            )
            
            db.session.add(facilitator)
            db.session.add(user)
            db.session.commit()
            
            flash("Facilitator account created successfully! Please log in.")
            return redirect(url_for("login"))
            
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.")
            return render_template("signup.html")
    
    return render_template("signup.html")




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
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///dev.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(facilitator_bp)
app.register_blueprint(unitcoordinator_bp)
app.register_blueprint(auth_bp)

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

# Create DB tables and ensure default admin
with app.app_context():
    db.create_all()
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    if not User.query.filter_by(email=admin_email).first():
        admin_user = User(
            email=admin_email,
            first_name='Admin',
            last_name='User',
            role=UserRole.ADMIN,
            password_hash=generate_password_hash(os.getenv('ADMIN_PASSWORD', 'admin123'))
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f"Default admin user created: {admin_email}")

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
@limiter.limit("5 per minute")
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
                return render_template("login.html")

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
    return render_template("login.html")

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
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                oauth_provider='google',
                oauth_id=oauth_id,
                avatar_url=avatar_url,
                role=UserRole.FACILITATOR
            )
            db.session.add(user)
            db.session.commit()
        else:
            user.oauth_provider = 'google'
            user.oauth_id = oauth_id
            user.avatar_url = avatar_url
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

if __name__ == "__main__":
    app.run(debug=True, port=5001)

