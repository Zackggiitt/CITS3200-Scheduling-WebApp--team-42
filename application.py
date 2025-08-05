import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, UserRole
from auth import login_required, is_safe_url, get_current_user
from authlib.integrations.flask_client import OAuth

# Import blueprints
from admin_routes import admin_bp
from facilitator_routes import facilitator_bp

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(facilitator_bp)

# OAuth configuration
oauth = OAuth(app)

# Google OAuth configuration
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///dev.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    
    # Create default admin user if it doesn't exist
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
        if user.role == UserRole.ADMIN:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('facilitator.dashboard'))
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user_role = request.form.get("user_role", "facilitator")
        
        user = User.query.filter_by(email=email).first()
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            # Check if selected role matches user's actual role
            if (user_role == "admin" and user.role != UserRole.ADMIN) or \
               (user_role == "facilitator" and user.role != UserRole.FACILITATOR):
                flash("Invalid role selected for this account.")
                return render_template("login.html")
            
            session["user_id"] = user.id
            
            # Redirect based on user role
            target = request.args.get("next")
            if target and is_safe_url(target):
                return redirect(target)
            
            if user.role == UserRole.ADMIN:
                return redirect(url_for("admin.dashboard"))
            else:
                return redirect(url_for("facilitator.dashboard"))
        
        flash("Invalid credentials")
    return render_template("login.html")

@app.get("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    if user.role == UserRole.ADMIN:
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('facilitator.dashboard'))

# Google OAuth routes
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
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                oauth_provider='google',
                oauth_id=oauth_id,
                avatar_url=avatar_url,
                role=UserRole.FACILITATOR  # Default role for OAuth users
            )
            db.session.add(user)
            db.session.commit()
        else:
            user.oauth_provider = 'google'
            user.oauth_id = oauth_id
            user.avatar_url = avatar_url
            db.session.commit()
        
        session['user_id'] = user.id
        flash('Successfully logged in with Google!')
        
        if user.role == UserRole.ADMIN:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('facilitator.dashboard'))
    
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
                role=UserRole.FACILITATOR  # Default role for new signups
            )
            db.session.add(user)
            db.session.commit()
            flash("Account created! Please log in.")
            return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out!")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)

