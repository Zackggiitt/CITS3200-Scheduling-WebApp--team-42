import logging
import csv
import re
from io import StringIO, BytesIO
from datetime import datetime, date, timedelta
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
    """Parse 'YYYY-MM-DDTHH:MM' or 'YYYY-MM-DD HH:MM' to datetime."""
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None



def _get_or_create_default_module(unit: Unit) -> Module:
    """Get or create a default 'General' module for the unit."""
    m = Module.query.filter_by(unit_id=unit.id, module_name="General").first()
    if not m:
        m = Module(unit_id=unit.id, module_name="General", module_type="general")
        db.session.add(m)
        db.session.commit()
    return m

def _serialize_session(s: Session, venues_by_name=None):
    venue_name = s.location or ""
    vid = None
    if venues_by_name and venue_name:
        vid = venues_by_name.get(venue_name.strip().lower())

    title = s.module.module_name or "Session"
    return {
        "id": str(s.id),  # turn this into a string
        "title": title,
        "start": s.start_time.isoformat(timespec="minutes"),
        "end": s.end_time.isoformat(timespec="minutes"),
        "venue": venue_name,
        "extendedProps": {
            "venue": venue_name,
            "venue_id": vid,
            "session_name": title,
        }
    }



def _get_or_create_module_by_name(unit: Unit, name: str) -> Module:
    name = (name or "").strip()
    if not name:
        return _get_or_create_default_module(unit)
    m = Module.query.filter_by(unit_id=unit.id, module_name=name).first()
    if not m:
        m = Module(unit_id=unit.id, module_name=name, module_type="general")
        db.session.add(m)
        db.session.flush()  # no commit yet; caller may commit
    return m


# --- Recurrence helpers -------------------------------------------------------

def _parse_recurrence(d: dict):
    """
    Expect shape like:
      {"occurs":"weekly", "interval":1, "byweekday":[0-6], "count":N, "until":"YYYY-MM-DD" | None}
    Return a normalized dict or {"occurs":"none"}.
    """
    if not isinstance(d, dict):
        return {"occurs": "none"}
    occurs = (d.get("occurs") or "none").lower()
    if occurs != "weekly":
        return {"occurs": "none"}
    interval = int(d.get("interval") or 1)
    if interval < 1:
        interval = 1
    # UI sends weekday of the first start date; we just step weekly from start, so this is informational.
    byweekday = d.get("byweekday") if isinstance(d.get("byweekday"), list) else None

    count = d.get("count")
    try:
        count = int(count) if count is not None else None
    except (TypeError, ValueError):
        count = None
    if count is not None and count < 1:
        count = 1

    until_raw = (d.get("until") or "").strip()
    until_date = _parse_date_multi(until_raw) if until_raw else None

    return {
        "occurs": "weekly",
        "interval": interval,
        "byweekday": byweekday,
        "count": count,
        "until": until_date,  # Python date or None
    }


def _within_unit_range(unit: Unit, dt: datetime) -> bool:
    """Check datetime against unit.start_date/end_date (if set)."""
    d = dt.date()
    if unit.start_date and d < unit.start_date:
        return False
    if unit.end_date and d > unit.end_date:
        return False
    return True


def _iter_weekly_occurrences(unit: Unit, start_dt: datetime, end_dt: datetime, rec: dict):
    """
    Yield (s,e) pairs for a weekly rule starting at (start_dt,end_dt), inclusive.
    Bounds:
      - stop when 'count' reached, OR
      - stop after 'until' (date), OR
      - stop when we step beyond unit.end_date.
    Always includes the first occurrence.
    """
    interval = rec.get("interval", 1) or 1
    count    = rec.get("count")
    until_d  = rec.get("until")  # date | None

    made = 0
    cur_s = start_dt
    cur_e = end_dt
    while True:
        # Stop conditions before yielding if outside range
        if not _within_unit_range(unit, cur_s) or not _within_unit_range(unit, cur_e):
            # If the first one is out of range we still don't yield it.
            pass
        else:
            yield (cur_s, cur_e)
            made += 1
            if count is not None and made >= count:
                break

        # compute next
        cur_s = cur_s + timedelta(weeks=interval)
        cur_e = cur_e + timedelta(weeks=interval)

        # if until is set, next start after 'until' should stop
        if until_d and cur_s.date() > until_d:
            break

        # unit end bound
        if unit.end_date and cur_s.date() > unit.end_date:
            break



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
    Returns a CSV with one column:
      - facilitator_email
    """
    sio = StringIO()
    writer = csv.DictWriter(sio, fieldnames=CSV_HEADERS, extrasaction="ignore")
    writer.writeheader()

    mem = BytesIO(sio.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name="facilitators_template.csv",
    )


# --------------------------------------------------------------------------
# Upload Facilitators CSV
# --------------------------------------------------------------------------
@unitcoordinator_bp.post("/upload-setup-csv")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def upload_setup_csv():
    """
    Accepts a 1-column CSV:
      - facilitator_email

    For each row:
      - If facilitator_email is present: ensure a User(role=FACILITATOR) exists; link to the Unit
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
    required = {"facilitator_email"}
    if not required.issubset(set(fns)):
        return jsonify({
            "ok": False,
            "error": "CSV must include header: facilitator_email"
        }), 400

    # Counters
    created_users = 0
    linked_facilitators = 0
    errors = []

    for idx, row in enumerate(reader, start=2):  # start=2 because header is row 1
        email = (row.get("facilitator_email") or "").strip().lower()
        if not email:
            continue
        if not _valid_email(email):
            errors.append(f"Row {idx}: invalid facilitator_email '{email}'")
            continue

        # Ensure facilitator user exists
        user_obj = User.query.filter_by(email=email).first()
        if not user_obj:
            user_obj = User(email=email, role=UserRole.FACILITATOR)
            db.session.add(user_obj)
            db.session.flush()  # <-- ensure user_obj.id is available
            created_users += 1

        # Ensure link to unit exists
        link = UnitFacilitator.query.filter_by(unit_id=unit.id, user_id=user_obj.id).first()
        if not link:
            link = UnitFacilitator(unit_id=unit.id, user_id=user_obj.id)
            db.session.add(link)
            linked_facilitators += 1



    db.session.commit()

    return jsonify({
        "ok": True,
        "created_users": created_users,
        "linked_facilitators": linked_facilitators,
        "errors": errors[:20],  # show up to 20 issues
    }), 200

# ---------- Step 3B: Calendar / Sessions ----------
@unitcoordinator_bp.get("/units/<int:unit_id>/calendar")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def calendar_week(unit_id: int):
    """Return sessions that intersect the visible week."""
    user = get_current_user()
    unit = _get_user_unit_or_404(user, unit_id)
    if not unit:
        return jsonify({"ok": False, "error": "Unit not found or unauthorized"}), 404

    week_start_raw = (request.args.get("week_start") or "").strip()  # YYYY-MM-DD
    try:
        week_start = datetime.strptime(week_start_raw, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"ok": False, "error": "Invalid week_start format (use YYYY-MM-DD)"}), 400

    week_end = week_start + timedelta(days=7)  # exclusive
    sessions = (
        Session.query.join(Module)
        .filter(
            Module.unit_id == unit.id,
            Session.start_time < datetime.combine(week_end, datetime.min.time()),
            Session.end_time >= datetime.combine(week_start, datetime.min.time()),
        )
        .order_by(Session.start_time.asc())
        .all()
    )

    # Build name->id map for this unit's venues
    unit_venues = (
        db.session.query(Venue.id, Venue.name)
        .join(UnitVenue, UnitVenue.venue_id == Venue.id)
        .filter(UnitVenue.unit_id == unit.id)
        .all()
    )
    venues_by_name = { (name or "").strip().lower(): vid for vid, name in unit_venues }

    return jsonify({
        "ok": True,
        "unit_range": {
            "start": unit.start_date.isoformat() if unit.start_date else None,
            "end": unit.end_date.isoformat() if unit.end_date else None,
        },
        "sessions": [_serialize_session(s, venues_by_name) for s in sessions],
    })


@unitcoordinator_bp.post("/units/<int:unit_id>/sessions")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def create_session(unit_id: int):
    """Create a session or a weekly series (based on 'recurrence')."""
    user = get_current_user()
    unit = _get_user_unit_or_404(user, unit_id)
    if not unit:
        return jsonify({"ok": False, "error": "Unit not found or unauthorized"}), 404

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"ok": False, "error": "Invalid or missing JSON data"}), 400

    # name coming from inspector / calendar
    name_in = (data.get("session_name") or data.get("module_name") or data.get("title") or "").strip()

    start_raw = (data.get("start") or "").strip()
    end_raw = (data.get("end") or "").strip()
    venue_name_in = (data.get("venue") or "").strip()
    venue_id_in = data.get("venue_id")

    # NEW: recurrence (optional)
    rec = _parse_recurrence(data.get("recurrence"))

    # Validate datetime inputs
    start_dt = _parse_dt(start_raw)
    end_dt = _parse_dt(end_raw)
    if not start_dt or not end_dt:
        return jsonify({"ok": False, "error": "Invalid datetime format (use YYYY-MM-DDTHH:MM)"}), 400
    if end_dt <= start_dt:
        return jsonify({"ok": False, "error": "End time must be after start time"}), 400

    # Range guard for the first
    if not _within_unit_range(unit, start_dt) or not _within_unit_range(unit, end_dt):
        return jsonify({"ok": False, "error": "Session outside unit date range"}), 400

    # Determine and validate venue; we store the venue NAME in `location`
    chosen_name = None
    if venue_id_in:
        link = (
            db.session.query(UnitVenue)
            .join(Venue, Venue.id == UnitVenue.venue_id)
            .filter(UnitVenue.unit_id == unit.id, UnitVenue.venue_id == venue_id_in)
            .first()
        )
        if not link:
            return jsonify({"ok": False, "error": "Invalid venue_id for this unit"}), 400
        chosen_name = Venue.query.get(venue_id_in).name
    elif venue_name_in:
        venue_rec = db.session.query(Venue).filter(func.lower(Venue.name) == venue_name_in.lower()).first()
        if not venue_rec:
            return jsonify({"ok": False, "error": f"Venue '{venue_name_in}' not found"}), 404
        unit_venue = UnitVenue.query.filter_by(unit_id=unit.id, venue_id=venue_rec.id).first()
        if not unit_venue:
            return jsonify({"ok": False, "error": f"Venue '{venue_name_in}' not linked to this unit"}), 400
        chosen_name = venue_rec.name  # normalize

    # Pick/create module by name (falls back to 'General' if empty)
    mod = _get_or_create_module_by_name(unit, name_in)

    created_ids = []
    try:
        if rec.get("occurs") == "weekly":
            # Fan out occurrences
            for s_dt, e_dt in _iter_weekly_occurrences(unit, start_dt, end_dt, rec):
                # Skip exact duplicates (same module + start_time) to be defensive
                exists = (
                    Session.query
                    .join(Module)
                    .filter(
                        Module.unit_id == unit.id,
                        Session.start_time == s_dt,
                        Session.end_time == e_dt,
                        Session.module_id == mod.id,
                    )
                    .first()
                )
                if exists:
                    continue

                sess = Session(
                    module_id=mod.id,
                    session_type="general",
                    start_time=s_dt,
                    end_time=e_dt,
                    day_of_week=s_dt.weekday(),
                    location=chosen_name,
                    required_skills=None,
                    max_facilitators=1,
                )
                db.session.add(sess)
                db.session.flush()
                created_ids.append(sess.id)
        else:
            # Single
            session = Session(
                module_id=mod.id,
                session_type="general",
                start_time=start_dt,
                end_time=end_dt,
                day_of_week=start_dt.weekday(),
                location=chosen_name,
                required_skills=None,
                max_facilitators=1,
            )
            db.session.add(session)
            db.session.flush()
            created_ids.append(session.id)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": f"Database error: {str(e)}"}), 500

    # Build mapping for serializer (venue_id resolution)
    venues_by_name = {}
    if chosen_name:
        v_id = db.session.query(Venue.id).filter(func.lower(Venue.name) == chosen_name.lower()).scalar()
        if v_id:
            venues_by_name[chosen_name.lower()] = v_id

    # Serialize the *first* (for FE to select) + include all IDs
    first = Session.query.get(created_ids[0])
    return jsonify({
        "ok": True,
        "session_id": created_ids[0],
        "created_session_ids": created_ids,
        "session": _serialize_session(first, venues_by_name),
    }), 201




@unitcoordinator_bp.put("/sessions/<int:session_id>")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def update_session(session_id: int):
    """Move/resize, update venue, or rename session; optional weekly fan-out when apply_to='series'."""
    user = get_current_user()
    session = Session.query.get(session_id)
    if not session or session.module.unit.created_by != user.id:
        return jsonify({"ok": False, "error": "Session not found or unauthorized"}), 404

    unit = session.module.unit
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"ok": False, "error": "Invalid or missing JSON data"}), 400

    # --- Rename session by switching its module ---
    name_in = (data.get("session_name") or data.get("module_name") or data.get("title") or "").strip()
    if name_in:
        new_mod = _get_or_create_module_by_name(unit, name_in)
        session.module_id = new_mod.id
    else:
        new_mod = session.module  # use current for fan-out below

    # --- Validate and update start/end times ---
    if "start" in data:
        start_time = _parse_dt(str(data["start"]))
        if not start_time:
            return jsonify({"ok": False, "error": "Invalid start time format (use YYYY-MM-DDTHH:MM)"}), 400
        session.start_time = start_time
        session.day_of_week = start_time.weekday()

    if "end" in data:
        end_time = _parse_dt(str(data["end"]))
        if not end_time:
            return jsonify({"ok": False, "error": "Invalid end time format (use YYYY-MM-DDTHH:MM)"}), 400
        session.end_time = end_time

    # --- Validate and update venue ---
    venue_set = False
    if "venue_id" in data:
        venue_id = data["venue_id"]
        if venue_id:
            link = (
                db.session.query(UnitVenue)
                .join(Venue, Venue.id == UnitVenue.venue_id)
                .filter(UnitVenue.unit_id == unit.id, UnitVenue.venue_id == venue_id)
                .first()
            )
            if not link:
                return jsonify({"ok": False, "error": "Invalid venue_id for this unit"}), 400
            session.location = Venue.query.get(venue_id).name
        else:
            session.location = None
        venue_set = True

    if not venue_set and "venue" in data:
        venue_name = (data["venue"] or "").strip()
        if venue_name:
            venue = db.session.query(Venue).filter(func.lower(Venue.name) == venue_name.lower()).first()
            if not venue:
                return jsonify({"ok": False, "error": f"Venue '{venue_name}' not found"}), 404
            unit_venue = UnitVenue.query.filter_by(unit_id=unit.id, venue_id=venue.id).first()
            if not unit_venue:
                return jsonify({"ok": False, "error": f"Venue '{venue_name}' not linked to this unit"}), 400
            session.location = venue.name
        else:
            session.location = None

    # --- Range and sanity checks ---
    if unit.start_date and session.start_time.date() < unit.start_date:
        return jsonify({"ok": False, "error": "Session start date is before unit start date"}), 400
    if unit.end_date and session.end_time.date() > unit.end_date:
        return jsonify({"ok": False, "error": "Session end date is after unit end date"}), 400
    if session.end_time <= session.start_time:
        return jsonify({"ok": False, "error": "End time must be after start time"}), 400

    created_ids = []

    # --- NEW: recurrence fan-out when saving with apply_to='series' ---
    rec = _parse_recurrence(data.get("recurrence"))
    apply_to = (data.get("apply_to") or "").lower()
    if rec.get("occurs") == "weekly" and apply_to == "series":
        # Use the *current* (possibly edited) times as the pattern seed
        seed_s = session.start_time
        seed_e = session.end_time
        chosen_name = session.location  # normalized earlier if set
        mod_for_series = new_mod

        try:
            for s_dt, e_dt in _iter_weekly_occurrences(unit, seed_s, seed_e, rec):
                # Skip the seed itself (already updated above)
                if s_dt == seed_s and e_dt == seed_e:
                    continue
                # Avoid exact duplicates for this module
                exists = (
                    Session.query
                    .join(Module)
                    .filter(
                        Module.unit_id == unit.id,
                        Session.start_time == s_dt,
                        Session.end_time == e_dt,
                        Session.module_id == mod_for_series.id,
                    )
                    .first()
                )
                if exists:
                    continue
                new_sess = Session(
                    module_id=mod_for_series.id,
                    session_type="general",
                    start_time=s_dt,
                    end_time=e_dt,
                    day_of_week=s_dt.weekday(),
                    location=chosen_name,
                    required_skills=None,
                    max_facilitators=1,
                )
                db.session.add(new_sess)
                db.session.flush()
                created_ids.append(new_sess.id)
        except Exception as e:
            db.session.rollback()
            return jsonify({"ok": False, "error": f"Database error while expanding series: {str(e)}"}), 500

    # --- Commit changes ---
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": f"Database error: {str(e)}"}), 500

    # --- Include venue_id in response (when resolvable) ---
    venues_by_name = {}
    if session.location:
        v_id = db.session.query(Venue.id).filter(func.lower(Venue.name) == session.location.lower()).scalar()
        if v_id:
            venues_by_name[session.location.lower()] = v_id

    resp = {
        "ok": True,
        "session": _serialize_session(session, venues_by_name)
    }
    if created_ids:
        resp["created_session_ids"] = created_ids
    return jsonify(resp)


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


@unitcoordinator_bp.get("/units/<int:unit_id>/venues")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def list_venues(unit_id: int):
    """Return venues linked to this unit (id + name)."""
    user = get_current_user()
    unit = _get_user_unit_or_404(user, unit_id)
    if not unit:
        return jsonify({"ok": False, "error": "Unit not found or unauthorized"}), 404

    venues = (
        db.session.query(Venue.id, Venue.name)
        .join(UnitVenue, UnitVenue.venue_id == Venue.id)
        .filter(UnitVenue.unit_id == unit.id)
        .order_by(Venue.name.asc())
        .all()
    )
    return jsonify({
        "ok": True,
        "venues": [{"id": v.id, "name": v.name} for v in venues]
    })


@unitcoordinator_bp.get("/units/<int:unit_id>/facilitators")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def list_facilitators(unit_id: int):
    user = get_current_user()
    unit = _get_user_unit_or_404(user, unit_id)
    if not unit:
        return jsonify({"ok": False, "error": "Unit not found or unauthorized"}), 404

    facs = (
        db.session.query(User.email)
        .join(UnitFacilitator, UnitFacilitator.user_id == User.id)
        .filter(UnitFacilitator.unit_id == unit.id)
        .order_by(User.email.asc())
        .all()
    )
    emails = [e for (e,) in facs]
    return jsonify({"ok": True, "facilitators": emails})
