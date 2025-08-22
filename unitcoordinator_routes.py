# unitcoordinator_routes.py
import logging
import csv
import re
from io import StringIO, BytesIO
from datetime import datetime
from sqlalchemy import and_

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    jsonify, send_file
)

from auth import login_required, get_current_user
from utils import role_required
from models import db
from models import UserRole, Unit, User, Venue, UnitFacilitator

# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

unitcoordinator_bp = Blueprint(
    "unitcoordinator", __name__, url_prefix="/unitcoordinator"
)

# CSV columns for the combined facilitators/venues file
CSV_HEADERS = [
    "type",            # facilitator | venue
    "email",           # (facilitator)
    "first_name",      # (facilitator, optional)
    "last_name",       # (facilitator, optional)
    "venue_name",      # (venue)
    "venue_capacity",  # (venue, optional int)
    "venue_location",  # (venue, optional)
]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def _parse_date_multi(s: str):
    """Accept either 'YYYY-MM-DD' or 'DD/MM/YYYY'. Return date or None."""
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _valid_email(s: str) -> bool:
    return bool(EMAIL_RE.match(s or ""))


def _get_user_unit_or_404(user, unit_id: int):
    """Return Unit if it exists AND is owned by user; else None."""
    try:
        unit_id = int(unit_id)
    except (TypeError, ValueError):
        return None
    unit = Unit.query.get(unit_id)
    if not unit or unit.created_by != user.id:
        return None
    return unit


# ------------------------------------------------------------------------------
# Views
# ------------------------------------------------------------------------------
@unitcoordinator_bp.route("/dashboard")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def dashboard():
    user = get_current_user()
    units = Unit.query.filter_by(created_by=user.id).all()
    return render_template("unitcoordinator_dashboard.html", user=user, units=units)


@unitcoordinator_bp.route("/create_unit", methods=["POST"])
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def create_unit():
    """
    Create OR update a Unit.
    - If unit_id is present and belongs to the current UC -> update
    - Else -> create (guarding duplicates per UC: unit_code+year+semester)
    Accepts dates in either YYYY-MM-DD or DD/MM/YYYY.
    """
    user = get_current_user()

    unit_id    = (request.form.get("unit_id") or "").strip()
    unit_code  = (request.form.get("unit_code") or "").strip()
    unit_name  = (request.form.get("unit_name") or "").strip()
    year_raw   = (request.form.get("year") or "").strip()
    semester   = (request.form.get("semester") or "").strip()
    description = (request.form.get("description") or "").strip()
    start_raw  = (request.form.get("start_date") or "").strip()
    end_raw    = (request.form.get("end_date") or "").strip()

    # Basic validation (Step 1 core)
    if not (unit_code and unit_name and year_raw and semester):
        flash("Please complete Unit Information.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))

    try:
        year = int(year_raw)
    except ValueError:
        flash("Year must be a number.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))

    # Dates (Step 2) – optional but validated if present
    start_date = _parse_date_multi(start_raw)
    end_date   = _parse_date_multi(end_raw)
    if start_raw and not start_date:
        flash("Invalid Start Date format.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))
    if end_raw and not end_date:
        flash("Invalid End Date format.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))
    if start_date and end_date and start_date > end_date:
        flash("Start Date must be before End Date.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))

    # UPDATE path when unit_id exists
    if unit_id:
        unit = _get_user_unit_or_404(user, unit_id)
        if not unit:
            flash("Unit not found or you do not have access.", "error")
            return redirect(url_for("unitcoordinator.dashboard"))

        # If identity (code/year/semester) changes, guard duplicates
        if (unit.unit_code != unit_code or unit.year != year or unit.semester != semester):
            dup = Unit.query.filter_by(
                unit_code=unit_code, year=year, semester=semester, created_by=user.id
            ).first()
            if dup and dup.id != unit.id:
                flash("Another unit with that code/year/semester already exists.", "error")
                return redirect(url_for("unitcoordinator.dashboard"))

        # Apply updates
        unit.unit_code   = unit_code
        unit.unit_name   = unit_name
        unit.year        = year
        unit.semester    = semester
        unit.description = description or None
        unit.start_date  = start_date
        unit.end_date    = end_date
        db.session.commit()

        flash("Unit updated successfully!", "success")
        return redirect(url_for("unitcoordinator.dashboard"))

    # CREATE path (no unit_id)
    # Per-UC uniqueness
    existing = Unit.query.filter_by(
        unit_code=unit_code, year=year, semester=semester, created_by=user.id
    ).first()
    if existing:
        flash("You already created this unit for that semester/year.", "error")
        return redirect(url_for("unitcoordinator.dashboard"))

    new_unit = Unit(
        unit_code=unit_code,
        unit_name=unit_name,
        year=year,
        semester=semester,
        description=description or None,
        start_date=start_date,
        end_date=end_date,
        created_by=user.id,
    )
    db.session.add(new_unit)
    db.session.commit()

    flash("Unit created successfully!", "success")
    return redirect(url_for("unitcoordinator.dashboard"))


# ------------------------------------------------------------------------------
# (Optional) Draft helper so Step 3 upload has a unit_id
# Call this after Step 1–2 to get/create a unit id without leaving the modal.
# ------------------------------------------------------------------------------
@unitcoordinator_bp.post("/create_or_get_draft")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def create_or_get_draft():
    """
    Idempotently returns an existing Unit for this UC+code+year+semester,
    or creates it if absent. Useful for attaching CSV uploads in Step 3.
    """
    user = get_current_user()

    unit_code = (request.form.get("unit_code") or "").strip()
    unit_name = (request.form.get("unit_name") or "").strip()
    year_raw  = (request.form.get("year") or "").strip()
    semester  = (request.form.get("semester") or "").strip()
    start_date = (request.form.get("start_date") or "").strip()
    end_date   = (request.form.get("end_date") or "").strip()

    if not (unit_code and unit_name and year_raw and semester):
        return jsonify({"ok": False, "error": "Missing required fields"}), 400

    try:
        year = int(year_raw)
    except ValueError:
        return jsonify({"ok": False, "error": "Year must be an integer"}), 400

    parsed_start = _parse_date_multi(start_date)
    parsed_end   = _parse_date_multi(end_date)
    if parsed_start and parsed_end and parsed_start > parsed_end:
        return jsonify({"ok": False, "error": "Start date must be before end date"}), 400

    unit = Unit.query.filter_by(
        unit_code=unit_code, year=year, semester=semester, created_by=user.id
    ).first()
    if not unit:
        unit = Unit(
            unit_code=unit_code,
            unit_name=unit_name,
            year=year,
            semester=semester,
            start_date=parsed_start,
            end_date=parsed_end,
            created_by=user.id,
        )
        db.session.add(unit)
        db.session.commit()

    return jsonify({"ok": True, "unit_id": unit.id})


# ------------------------------------------------------------------------------
# Step 3: CSV template + upload handlers
# ------------------------------------------------------------------------------
@unitcoordinator_bp.get("/csv-template")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def download_setup_csv_template():
    """
    Returns a single CSV with a 'type' column (facilitator|venue).
    """
    sio = StringIO()
    writer = csv.DictWriter(sio, fieldnames=CSV_HEADERS, extrasaction="ignore")
    writer.writeheader()
    # sample rows
    writer.writerow({"type": "facilitator", "email": "alex@example.edu", "first_name": "Alex", "last_name": "Ng"})
    writer.writerow({"type": "facilitator", "email": "riley@example.edu", "first_name": "Riley", "last_name": "Lee"})
    writer.writerow({"type": "venue", "venue_name": "Ezone 2.07", "venue_capacity": "40", "venue_location": "Ezone North"})
    writer.writerow({"type": "venue", "venue_name": "Ezone 2.12", "venue_capacity": "24", "venue_location": "Ezone North"})

    mem = BytesIO(sio.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True,
                     download_name="facilitators_venues_template.csv")


@unitcoordinator_bp.post("/upload-setup-csv")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def upload_setup_csv():

    """
    Accepts a CSV (template above) and:
      - ensures every facilitator exists as a User(role=FACILITATOR)
      - links facilitators to the given Unit
      - upserts Venues
    Returns counts + errors for UI.
    """
    user = get_current_user()

    unit_id = request.form.get("unit_id")
    if not unit_id:
        return jsonify({"ok": False, "error": "Missing unit_id"}), 400

    # Strict ownership check
    unit = _get_user_unit_or_404(user, unit_id)
    if not unit:
        return jsonify({"ok": False, "error": "Unit not found"}), 404

    file = request.files.get("setup_csv")
    if not file:
        return jsonify({"ok": False, "error": "No file uploaded"}), 400

    try:
        text = file.read().decode("utf-8", errors="replace")
        reader = csv.DictReader(StringIO(text))
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to read CSV: {e}"}), 400

    if "type" not in (reader.fieldnames or []):
        return jsonify({"ok": False, "error": "CSV missing required column: type"}), 400

    created_users = 0
    linked_facilitators = 0
    created_venues = 0
    updated_venues = 0
    errors = []

    for idx, row in enumerate(reader, start=2):
        kind = (row.get("type") or "").strip().lower()
        if kind not in {"facilitator", "venue"}:
            errors.append(f"Row {idx}: invalid type '{kind}'"); continue

        if kind == "facilitator":
            email = (row.get("email") or "").strip()
            if not _valid_email(email):
                errors.append(f"Row {idx}: invalid facilitator email"); continue

            user_rec = User.query.filter_by(email=email).first()
            if not user_rec:
                user_rec = User(
                    email=email,
                    first_name=(row.get("first_name") or "").strip() or None,
                    last_name=(row.get("last_name") or "").strip() or None,
                    role=UserRole.FACILITATOR,
                )
                db.session.add(user_rec)
                created_users += 1

            exists = UnitFacilitator.query.filter_by(unit_id=unit.id, user_id=user_rec.id).first()
            if not exists:
                db.session.add(UnitFacilitator(unit_id=unit.id, user_id=user_rec.id))
                linked_facilitators += 1

        else:  # venue
            name = (row.get("venue_name") or "").strip()
            if not name:
                errors.append(f"Row {idx}: venue_name is required"); continue

            cap_val = row.get("venue_capacity")
            try:
                capacity = int(cap_val) if cap_val not in (None, "") else None
            except ValueError:
                errors.append(f"Row {idx}: venue_capacity must be an integer"); continue

            venue = Venue.query.filter_by(name=name).first()
            if not venue:
                venue = Venue(
                    name=name,
                    capacity=capacity,
                    location=(row.get("venue_location") or "").strip() or None
                )
                db.session.add(venue)
                created_venues += 1
            else:
                changed = False
                if capacity is not None and venue.capacity != capacity:
                    venue.capacity = capacity; changed = True
                loc = (row.get("venue_location") or "").strip() or None
                if loc is not None and venue.location != loc:
                    venue.location = loc; changed = True
                if changed:
                    updated_venues += 1

    db.session.commit()

    if errors:
        return jsonify({
            "ok": False,
            "created_users": created_users,
            "linked_facilitators": linked_facilitators,
            "created_venues": created_venues,
            "updated_venues": updated_venues,
            "errors": errors[:20],
        }), 400

    return jsonify({
        "ok": True,
        "created_users": created_users,
        "linked_facilitators": linked_facilitators,
        "created_venues": created_venues,
        "updated_venues": updated_venues,
    })
