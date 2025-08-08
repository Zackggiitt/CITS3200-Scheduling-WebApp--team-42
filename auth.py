from functools import wraps
from flask import session, redirect, url_for, request, flash
from urllib.parse import urlparse, urljoin
from models import User, UserRole

def set_user_session(user):
    """Set user session data with authentication flag"""
    if user:
        session['user_id'] = user.id
        session['role'] = user.role.value
        session['authenticated'] = True  
        return True
    return False

def test_session_creation(self):
    """Test session creation"""
    with self.app.test_request_context():
        # Set session
        set_user_session(self.test_user)
        
        # Verify all session data
        expected_session = {
            'user_id': self.test_user.id,
            'role': self.test_user.role.value,
            'authenticated': True
        }
        
        for key, value in expected_session.items():
            self.assertIn(key, session)
            self.assertEqual(session[key], value)

def clear_user_session():
    """Clear user session data"""
    session.clear()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        # Verify user exists in database
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()  # Clear invalid session
            return redirect(url_for("login"))
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
        user = User.query.get(session['user_id'])
        if user is None:
            session.pop("user_id", None)
        return user
    return None