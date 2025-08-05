from functools import wraps
from flask import session, redirect, url_for, request, flash
from urllib.parse import urlparse, urljoin
from models import User, UserRole

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        
        user = User.query.get(session['user_id'])
        if not user or user.role != UserRole.ADMIN:
            flash("Access denied. Admin privileges required.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

def facilitator_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        
        user = User.query.get(session['user_id'])
        if not user or user.role != UserRole.FACILITATOR:
            flash("Access denied. Facilitator privileges required.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

def is_safe_url(target):
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and ref.netloc == test.netloc

def get_current_user():
    if "user_id" in session:
        return User.query.get(session['user_id'])
    return None