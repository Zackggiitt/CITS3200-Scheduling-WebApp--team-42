# utils.py
from functools import wraps
from flask import redirect, url_for, flash
from auth import get_current_user

def role_required(required_role):
    @wraps(required_role)
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash("Please log in.")
                return redirect(url_for("login"))
            if user.role != required_role:
                flash("Unauthorized for this area.")
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator