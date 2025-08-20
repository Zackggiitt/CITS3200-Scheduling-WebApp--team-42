# unitcoordinator_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
import logging
from auth import login_required, get_current_user
from models import UserRole
from utils import role_required

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

unitcoordinator_bp = Blueprint(
    "unitcoordinator", __name__, url_prefix="/unitcoordinator"
)

@unitcoordinator_bp.route("/dashboard")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def dashboard():
    user = get_current_user()
    logger.debug(f"Accessing dashboard for user: {user.email if user else 'None'}")
    return render_template("unitcoordinator_dashboard.html", user=user)  # Pass user here