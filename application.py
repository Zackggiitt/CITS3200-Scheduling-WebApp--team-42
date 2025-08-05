import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from functools import wraps
from urllib.parse import urlparse, urljoin
from authlib.integrations.flask_client import OAuth

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

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

# Microsoft OAuth configuration
microsoft = oauth.register(
    name='microsoft',
    client_id=os.getenv('MICROSOFT_CLIENT_ID'),
    client_secret=os.getenv('MICROSOFT_CLIENT_SECRET'),
    authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            # Capture where the user wanted to go
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper

def is_safe_url(target):
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and ref.netloc == test.netloc

@app.get("/dashboard")
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    return render_template("dashboard.html", user=user)

# Database configuration: use SQLite locally; swap to RDS later via env
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///dev.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.route("/")
def index():
    # Redirect to login or dashboard if logged in
    if "user_id" in session:
        return render_template("dashboard.html") if os.path.exists("templates/dashboard.html") else render_template("login.html")
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            # Send them where they were intended, else to dashboard
            target = request.args.get("next")
            if target and is_safe_url(target):
                return redirect(target)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")

# Google OAuth routes
@app.route('/auth/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    print(f"=== Google OAuth Debug ===")
    print(f"Redirect URI: {redirect_uri}")
    print(f"Client ID: {os.getenv('GOOGLE_CLIENT_ID')}")
    print(f"=========================")
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
                avatar_url=avatar_url
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update OAuth information
            user.oauth_provider = 'google'
            user.oauth_id = oauth_id
            user.avatar_url = avatar_url
            db.session.commit()
        
        session['user_id'] = user.id
        flash('Successfully logged in with Google!')
        return redirect(url_for('dashboard'))
    
    flash('Google login failed')
    return redirect(url_for('login'))

# Microsoft OAuth routes
@app.route('/auth/microsoft')
def microsoft_login():
    redirect_uri = url_for('microsoft_callback', _external=True)
    return microsoft.authorize_redirect(redirect_uri)

@app.route('/auth/microsoft/callback')
def microsoft_callback():
    token = microsoft.authorize_access_token()
    
    # Get user information
    resp = requests.get(
        'https://graph.microsoft.com/v1.0/me',
        headers={'Authorization': f'Bearer {token["access_token"]}'}
    )
    
    if resp.status_code == 200:
        user_info = resp.json()
        email = user_info['mail'] or user_info['userPrincipalName']
        first_name = user_info.get('givenName', '')
        last_name = user_info.get('surname', '')
        oauth_id = user_info['id']
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                oauth_provider='microsoft',
                oauth_id=oauth_id
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update OAuth information
            user.oauth_provider = 'microsoft'
            user.oauth_id = oauth_id
            db.session.commit()
        
        session['user_id'] = user.id
        flash('Successfully logged in with Microsoft!')
        return redirect(url_for('dashboard'))
    
    flash('Microsoft login failed')
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
                password_hash=generate_password_hash(password)
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

