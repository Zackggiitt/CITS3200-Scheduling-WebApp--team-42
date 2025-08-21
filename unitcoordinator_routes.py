# unitcoordinator_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
import logging
from auth import login_required, get_current_user
from models import UserRole, Unit, db   
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
    # Only fetch units created by this coordinator
    units = Unit.query.filter_by(created_by=user.id).all()
    return render_template("unitcoordinator_dashboard.html", user=user, units=units)

@unitcoordinator_bp.route("/create_unit", methods=["POST"])
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def create_unit():
    user = get_current_user()   # ✅ fix #1
    unit_code = request.form.get("unit_code")
    unit_name = request.form.get("unit_name")
    year = request.form.get("year")
    semester = request.form.get("semester")

    if not unit_code or not unit_name or not year or not semester:
        flash("All fields (unit code, name, year, semester) are required.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))

    try:
        year = int(year)  # ✅ fix #2 (safe cast)
    except ValueError:
        flash("Year must be a number.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))

    existing = Unit.query.filter_by(
        unit_code=unit_code,
        year=year,
        semester=semester,
        created_by=user.id
    ).first()

    if existing:
        flash("You already created this unit for that semester/year.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))

    new_unit = Unit(
        unit_code=unit_code,
        unit_name=unit_name,
        year=year,
        semester=semester,
        created_by=user.id
    )
    db.session.add(new_unit)
    db.session.commit()

    flash("Unit created successfully!", "success")
    return redirect(url_for("unitcoordinator.dashboard"))
