import logging
import csv
import re
from io import StringIO, BytesIO
from datetime import datetime, date
from sqlalchemy import and_, func

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    jsonify, send_file
)

from auth import login_required, get_current_user
from utils import role_required
from models import db
from models import UserRole, Unit, User, Venue, UnitFacilitator, UnitVenue, Module, Session

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
    "facilitator_email",   # optional per row
    "venue_name",          # optional per row
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


def _iso(d: date) -> str:
    return d.isoformat()


def _parse_dt(s: str):
    """Parse 'YYYY-MM-DDTHH:MM' to datetime."""
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def _get_or_create_default_module(unit: Unit) -> Module:
    """Get or create a default 'General' module for the unit."""
    m = Module.query.filter_by(unit_id=unit.id, module_name="General").first()
    if not m:
        m = Module(unit_id=unit.id, module_name="General", module_type="general")
        db.session.add(m)
        db.session.commit()
    return m


def _serialize_session(s: Session):
    """Serialize a Session object to JSON."""
    return {
        "id": s.id,
        "title": s.module.module_name or "Session",
        "start": s.start_time.isoformat(timespec="minutes"),
        "end": s.end_time.isoformat(timespec="minutes"),
        "venue": s.location or "",
    }


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

    unit_id = (request.form.get("unit_id") or "").strip()
    unit_code = (request.form.get("unit_code") or "").strip()
    unit_name = (request.form.get("unit_name") or "").strip()
    year_raw = (request.form.get("year") or "").strip()
    semester = (request.form.get("semester") or "").strip()
    description = (request.form.get("description") or "").strip()
    start_raw = (request.form.get("start_date") or "").strip()
    end_raw = (request.form.get("end_date") or "").strip()

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
    end_date = _parse_date_multi(end_raw)
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
        unit.unit_code = unit_code
        unit.unit_name = unit_name
        unit.year = year
        unit.semester = semester
        unit.description = description or None
        unit.start_date = start_date
        unit.end_date = end_date
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

    # Create default module for new unit
    _get_or_create_default_module(new_unit)

    flash("Unit created successfully!", "success")
    return redirect(url_for("unitcoordinator.dashboard"))


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
    year_raw = (request.form.get("year") or "").strip()
    semester = (request.form.get("semester") or "").strip()
    start_date = (request.form.get("start_date") or "").strip()
    end_date = (request.form.get("end_date") or "").strip()

    if not (unit_code and unit_name and year_raw and semester):
        return jsonify({"ok": False, "error": "Missing required fields"}), 400

    try:
        year = int(year_raw)
    except ValueError:
        return jsonify({"ok": False, "error": "Year must be an integer"}), 400

    parsed_start = _parse_date_multi(start_date)
    parsed_end = _parse_date_multi(end_date)
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
        # Create default module for new unit
        _get_or_create_default_module(unit)

    return jsonify({"ok": True, "unit_id": unit.id})


@unitcoordinator_bp.get("/csv-template")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def download_setup_csv_template():
    """
    Returns a CSV with two columns:
      - facilitator_email
      - venue_name
    Rows may have either or both. Blank cells are ignored.
    """
    sio = StringIO()
    writer = csv.DictWriter(sio, fieldnames=CSV_HEADERS, extrasaction="ignore")
    writer.writeheader()

    # --- SAMPLE ROWS (for debugging only, uncomment if needed) ---
    # writer.writerow({"facilitator_email": "alex@example.edu", "venue_name": ""})
    # writer.writerow({"facilitator_email": "riley@example.edu", "venue_name": ""})
    # writer.writerow({"facilitator_email": "", "venue_name": "Engineering Hub 2.07"})
    # writer.writerow({"facilitator_email": "", "venue_name": "Engineering Hub 2.12"})
    # writer.writerow({"facilitator_email": "sam@example.edu", "venue_name": "Engineering Hub 3.01"})

    mem = BytesIO(sio.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name="facilitators_venues_template.csv",
    )


@unitcoordinator_bp.post("/upload-setup-csv")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def upload_setup_csv():
    """
    Accepts a 2-column CSV:
      - facilitator_email
      - venue_name

    For each row:
      - If facilitator_email is present: ensure a User(role=FACILITATOR) exists; link to the Unit
      - If venue_name is present: upsert a Venue by name (name only); link to the Unit
    Returns counts + errors.
    """
    user = get_current_user()

    unit_id = request.form.get("unit_id")
    if not unit_id:
        return jsonify({"ok": False, "error": "Missing unit_id"}), 400

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

    # Validate headers
    fns = [fn.strip().lower() for fn in (reader.fieldnames or [])]
    required = {"facilitator_email", "venue_name"}
    if not required.issubset(set(fns)):
        return jsonify({
            "ok": False,
            "error": f"CSV must include headers: {', '.join(sorted(required))}"
        }), 400

    # Counters
    created_users = 0
    linked_facilitators = 0
    created_venues = 0
    linked_venues = 0
    errors = []

    for idx, row in enumerate(reader, start=2):  # start=2 for human-friendly row numbers
        fac_email = (row.get("facilitator_email") or "").strip()
        venue_name = (row.get("venue_name") or "").strip()

        # Process facilitator email if present
        if fac_email:
            if not _valid_email(fac_email):
                errors.append(f"Row {idx}: invalid facilitator_email '{fac_email}'")
            else:
                user_rec = User.query.filter_by(email=fac_email).first()
                if not user_rec:
                    user_rec = User(email=fac_email, role=UserRole.FACILITATOR)
                    db.session.add(user_rec)
                    created_users += 1

                exists = UnitFacilitator.query.filter_by(unit_id=unit.id, user_id=user_rec.id).first()
                if not exists:
                    db.session.add(UnitFacilitator(unit_id=unit.id, user_id=user_rec.id))
                    linked_facilitators += 1

        # Process venue name if present
        if venue_name:
            # Normalize venue name
            venue_name = " ".join(venue_name.lstrip(",").strip().split())

            # Case-insensitive lookup to prevent duplicates
            venue = db.session.query(Venue).filter(func.lower(Venue.name) == venue_name.lower()).first()

            # Upsert global catalog
            if not venue:
                venue = Venue(name=venue_name)
                db.session.add(venue)
                created_venues += 1  # Newly cataloged venue

            # Ensure per-unit link
            link = UnitVenue.query.filter_by(unit_id=unit.id, venue_id=venue.id).first()
            if not link:
                db.session.add(UnitVenue(unit_id=unit.id, venue_id=venue.id))
                linked_venues += 1

        # If a row is entirely blank, silently ignore it (no error)

    # Commit all changes at once
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        errors.append(f"Database error: {str(e)}")
        return jsonify({
            "ok": False,
            "created_users": created_users,
            "linked_facilitators": linked_facilitators,
            "created_venues": created_venues,
            "linked_venues": linked_venues,
            "updated_venues": 0,  # Keep for UI compatibility
            "errors": errors[:20],
        }), 400

    if errors:
        return jsonify({
            "ok": False,
            "created_users": created_users,
            "linked_facilitators": linked_facilitators,
            "created_venues": created_venues,
            "linked_venues": linked_venues,
            "updated_venues": 0,  # Keep for UI compatibility
            "errors": errors[:20],
        }), 400

    return jsonify({
        "ok": True,
        "created_users": created_users,
        "linked_facilitators": linked_facilitators,
        "created_venues": created_venues,
        "linked_venues": linked_venues,
        "updated_venues": 0,  # Keep for UI compatibility
    }), 200


@unitcoordinator_bp.put("/sessions/<int:session_id>")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def update_session(session_id: int):
    """Move/resize or update venue for a session."""
    user = get_current_user()
    session = Session.query.get(session_id)
    if not session or session.module.unit.created_by != user.id:
        return jsonify({"ok": False, "error": "Session not found or unauthorized"}), 404

    unit = session.module.unit
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"ok": False, "error": "Invalid or missing JSON data"}), 400

    # Validate and update start/end times
    if "start" in data:
        start_time = _parse_dt(data["start"])
        if not start_time:
            return jsonify({"ok": False, "error": "Invalid start time format (use YYYY-MM-DDTHH:MM)"}), 400
        session.start_time = start_time
        session.day_of_week = start_time.weekday()

    if "end" in data:
        end_time = _parse_dt(data["end"])
        if not end_time:
            return jsonify({"ok": False, "error": "Invalid end time format (use YYYY-MM-DDTHH:MM)"}), 400
        session.end_time = end_time

    # Validate and update venue
    if "venue" in data:
        venue_name = (data["venue"] or "").strip()
        if venue_name:
            # Check if venue exists and is linked to the unit
            venue = db.session.query(Venue).filter(func.lower(Venue.name) == venue_name.lower()).first()
            if not venue:
                return jsonify({"ok": False, "error": f"Venue '{venue_name}' not found"}), 404
            unit_venue = UnitVenue.query.filter_by(unit_id=unit.id, venue_id=venue.id).first()
            if not unit_venue:
                return jsonify({"ok": False, "error": f"Venue '{venue_name}' not linked to this unit"}), 400
            session.location = venue_name
        else:
            session.location = None

    # Range guard
    if unit.start_date and session.start_time.date() < unit.start_date:
        return jsonify({"ok": False, "error": "Session start date is before unit start date"}), 400
    if unit.end_date and session.end_time.date() > unit.end_date:
        return jsonify({"ok": False, "error": "Session end date is after unit end date"}), 400
    if session.end_time <= session.start_time:
        return jsonify({"ok": False, "error": "End time must be after start time"}), 400

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": f"Database error: {str(e)}"}), 500

    return jsonify({"ok": True, "session": _serialize_session(session)})


@unitcoordinator_bp.delete("/sessions/<int:session_id>")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def delete_session(session_id: int):
    """Delete a session."""
    user = get_current_user()
    session = Session.query.get(session_id)
    if not session or session.module.unit.created_by != user.id:
        return jsonify({"ok": False, "error": "Session not found or unauthorized"}), 404

    try:
        db.session.delete(session)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": f"Database error: {str(e)}"}), 500

    return jsonify({"ok": True})