# unitcoordinator_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
import logging
from auth import login_required, get_current_user
from models import UserRole, Unit, db   
from utils import role_required
from datetime import datetime


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
    user = get_current_user()

    unit_code   = request.form.get("unit_code", "").strip()
    unit_name   = request.form.get("unit_name", "").strip()
    year        = request.form.get("year", "").strip()
    semester    = request.form.get("semester", "").strip()
    description = request.form.get("description", "").strip()
    start_date  = request.form.get("start_date", "").strip()
    end_date    = request.form.get("end_date", "").strip()

    # Basic validation for step1
    if not (unit_code and unit_name and year and semester):
        flash("Please complete Unit Information.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))

    try:
        year = int(year)
    except ValueError:
        flash("Year must be a number.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))

    # Optional date validation for step2 (only if both provided)
    parsed_start = parsed_end = None
    if start_date and end_date:
        try:
            parsed_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            parsed_end   = datetime.strptime(end_date, "%Y-%m-%d").date()
            if parsed_start > parsed_end:
                flash("Start Date must be before End Date.", "error")
                return redirect(url_for("unitcoordinator.dashboard"))
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for("unitcoordinator.dashboard"))

    # Uniqueness guard
    existing = Unit.query.filter_by(
        unit_code=unit_code, year=year, semester=semester, created_by=user.id
    ).first()
    if existing:
        flash("You already created this unit for that semester/year.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))

    # Create
    new_unit = Unit(
        unit_code=unit_code,
        unit_name=unit_name,
        year=year,
        semester=semester,
        description=description or None,
        start_date=parsed_start,
        end_date=parsed_end,
        created_by=user.id,
    )
    db.session.add(new_unit)
    db.session.commit()

    flash("Unit created successfully!", "success")
    return redirect(url_for("unitcoordinator.dashboard"))