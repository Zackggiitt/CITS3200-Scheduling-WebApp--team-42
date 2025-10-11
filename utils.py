# utils.py
from functools import wraps
from flask import redirect, url_for, flash
from auth import get_current_user

def role_required(required_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash("Please log in.")
                return redirect(url_for("login"))
            
            # Handle both single role and list of roles
            if isinstance(required_roles, list):
                if user.role not in required_roles:
                    flash("Unauthorized for this area.")
                    return redirect(url_for("login"))
            else:
                if user.role != required_roles:
                    flash("Unauthorized for this area.")
                    return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator