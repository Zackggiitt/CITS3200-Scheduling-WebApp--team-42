# application.py
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, UserRole
from auth import login_required, is_safe_url, get_current_user
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils import role_required

# Import blueprints
from admin_routes import admin_bp
from facilitator_routes import facilitator_bp
from unitcoordinator_routes import unitcoordinator_bp

load_dotenv()
app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(facilitator_bp)
app.register_blueprint(unitcoordinator_bp)

# OAuth configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# DB
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///dev.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

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

        role = user.role  # Use database-stored role
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
        selected_role = request.form.get("user_role", "facilitator")  # Default to facilitator if not set

        user = User.query.filter_by(email=email).first()
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            # Validate selected role against user's actual role
            allowed = (
                (selected_role == "admin" and user.role == UserRole.ADMIN) or
                (selected_role == "unit_coordinator" and user.role == UserRole.UNIT_COORDINATOR) or
                (selected_role == "facilitator" and user.role == UserRole.FACILITATOR)
            )
            if not allowed:
                flash("You don't have permission for the selected role.")
                return render_template("login.html")

            session["user_id"] = user.id
            role = user.role  # Use database-stored role for redirection
            target = request.args.get("next")
            if target and is_safe_url(target):
                return redirect(target)

            if role == UserRole.ADMIN:
                return redirect(url_for("admin.dashboard"))
            elif role == UserRole.UNIT_COORDINATOR:
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
                role=UserRole.FACILITATOR  # Default role
            )
            db.session.add(user)
            db.session.commit()
        else:
            user.oauth_provider = 'google'
            user.oauth_id = oauth_id
            user.avatar_url = avatar_url
            db.session.commit()

        session['user_id'] = user.id
        role = user.role
        if role == UserRole.ADMIN:
            return redirect(url_for("admin.dashboard"))
        elif role == UserRole.UNIT_COORDINATOR:
            return redirect(url_for("unitcoordinator.dashboard"))
        else:
            return redirect(url_for("facilitator.dashboard"))

    flash('Google login failed')
    return redirect(url_for('login'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first = request.form["first_name"].strip()
        last = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email already exists!")
        else:
            user = User(
                first_name=first,
                last_name=last,
                email=email,
                password_hash=generate_password_hash(password),
                role=UserRole.FACILITATOR  # Default role, no selection
            )
            db.session.add(user)
            db.session.commit()
            flash("Account created! Please log in.")
            return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("role", None)  # Remove any residual role
    flash("Logged out!")
    return redirect(url_for("login"))

@app.errorhandler(429)
def ratelimit_handler(e):
    flash("Too many login attempts. Please try again in few minutes.")
    return render_template("login.html"), 429

if __name__ == "__main__":
    app.run(debug=True)