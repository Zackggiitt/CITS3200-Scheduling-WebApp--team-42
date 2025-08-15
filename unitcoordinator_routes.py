# unitcoordinator_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from auth import login_required, get_current_user
from models import UserRole
from utils import role_required

unitcoordinator_bp = Blueprint(
    "unitcoordinator", __name__, url_prefix="/unitcoordinator"
)

@unitcoordinator_bp.route("/dashboard")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def dashboard():
    try:
        return render_template("unitcoordinator_dashboard.html")
    except TemplateNotFound:
        flash("Dashboard template not found. Contact support.")
        return render_template("index.html")