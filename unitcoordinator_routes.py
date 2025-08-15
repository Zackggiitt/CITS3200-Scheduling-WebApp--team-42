# unitcoordinator_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash  # Changed import
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
    try:
        if not user:
            flash("User not authenticated.")
            return redirect(url_for("login"))
        return render_template("unitcoordinator_dashboard.html")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        flash("An error occurred. Please try again later.")
        return redirect(url_for("index"))