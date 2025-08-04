import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from functools import wraps
from urllib.parse import urlparse, urljoin


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            # capture where the user wanted to go
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
    return render_template("dashboard.html")



# DB config: use SQLite locally; swap to RDS later via env
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
    # e.g., redirect to login or a dashboard if logged in
    if "user_id" in session:
        return render_template("dashboard.html") if os.path.exists("templates/dashboard.html") else render_template("login.html")
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            # send them where they were intended, else to dashboard
            target = request.args.get("next")
            if target and is_safe_url(target):
                return redirect(target)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")

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

