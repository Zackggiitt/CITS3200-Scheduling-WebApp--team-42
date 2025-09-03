import logging
import csv
import re
from io import StringIO, BytesIO
from datetime import datetime, date, timedelta
from sqlalchemy import and_, func
from sqlalchemy import func
# from models import Unit, Module, Session
from datetime import date

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    jsonify, send_file
)

from auth import login_required, get_current_user
from utils import role_required
from models import db

from models import db, UserRole, Unit, User, Venue, UnitFacilitator, UnitVenue, Module, Session, Assignment, Availability, Facilitator, SwapRequest, SwapStatus, FacilitatorSkill

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


ACTIVITY_ALLOWED = {"workshop", "tutorial", "lab"}

def _coerce_activity_type(s: str) -> str:
    v = (s or "").strip().lower()
    return v if v in ACTIVITY_ALLOWED else "other"

TIME_RANGE_RE = re.compile(
    r"^\s*(\d{1,2})[:\.](\d{2})\s*[-–—]\s*(\d{1,2})[:\.](\d{2})\s*$"
)

def _parse_time_range(s: str):
    """
    Accepts '09:00-11:30', '9.00 – 11.30', etc.
    Returns (start_h, start_m, end_h, end_m) or None.
    """
    if not s: return None
    m = TIME_RANGE_RE.match(s)
    if not m: return None
    h1, m1, h2, m2 = map(int, m.groups())
    if not (0 <= h1 <= 23 and 0 <= h2 <= 23 and 0 <= m1 <= 59 and 0 <= m2 <= 59):
        return None
    return h1, m1, h2, m2



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
    """Check datetime against unit.start_date/end_date (if set). Only start_date is required."""
    d = dt.date()
    if unit.start_date and d < unit.start_date:
        return False
    # Only check end_date if it's actually set
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
# in unitcoordinator_route.py


# unitcoordinator_routes.py
from datetime import date
from sqlalchemy import func
# ...other imports incl. request...

# unitcoordinator_route.py (dashboard)
@unitcoordinator_bp.route("/dashboard")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def dashboard():
    from sqlalchemy import func

    user = get_current_user()

    # Build list of units this UC owns + session counts (for the single-card header)
    rows = (
        db.session.query(Unit, func.count(Session.id))
        .outerjoin(Module, Module.unit_id == Unit.id)
        .outerjoin(Session, Session.module_id == Module.id)
        .filter(Unit.created_by == user.id)
        .group_by(Unit.id)
        .order_by(Unit.unit_code.asc())
        .all()
    )
    units = []
    for u, cnt in rows:
        setattr(u, "session_count", int(cnt or 0))
        units.append(u)

    # Which unit is selected (via ?unit=) — otherwise first
    selected_id = request.args.get("unit", type=int)
    current_unit = (
        next((u for u in units if u.id == selected_id), None)
        if selected_id
        else (units[0] if units else None)
    )

# ----- Staffing tiles (safe if no current_unit) -----
    stats = {"total": 0, "fully": 0, "needs_lead": 0, "unstaffed": 0}

    if current_unit:
        session_rows = (
            db.session.query(
                Session.id.label("sid"),
                func.coalesce(Session.max_facilitators, 1).label("maxf"),
                func.count(Assignment.id).label("assigned"),
            )
            .join(Module, Module.id == Session.module_id)
            .outerjoin(Assignment, Assignment.session_id == Session.id)
            .filter(Module.unit_id == current_unit.id)
            .group_by(Session.id, Session.max_facilitators)
            .all()
        )

        total_sessions = len(session_rows)
        fully_staffed  = sum(1 for r in session_rows if r.assigned >= r.maxf and r.maxf > 0)
        unstaffed      = sum(1 for r in session_rows if r.assigned == 0)
        # Inclusive: anything not fully staffed (includes unstaffed)
        needs_lead     = sum(1 for r in session_rows if r.assigned < r.maxf)

        stats = {
            "total": total_sessions,
            "fully": fully_staffed,
            "needs_lead": needs_lead,
            "unstaffed": unstaffed,
        }


    # ----- Facilitator Setup Progress + Details -----
    fac_progress = {"total": 0, "account": 0, "availability": 0, "ready": 0}
    facilitators = []

    if current_unit:
        # All facilitator links for this unit
        links = (
            db.session.query(UnitFacilitator, User)
            .join(User, UnitFacilitator.user_id == User.id)
            .filter(UnitFacilitator.unit_id == current_unit.id)
            .order_by(User.last_name.asc().nulls_last(), User.first_name.asc().nulls_last())
            .all()
        )

        fac_progress["total"] = len(links)

        for _, f in links:
            # "Account setup" heuristic: any profile fields present
            has_profile = bool(
                (getattr(f, "first_name", None) or getattr(f, "last_name", None))
                or getattr(f, "phone", None)
                or getattr(f, "staff_number", None)
                or getattr(f, "avatar_url", None)
            )

            # Availability: current model is *global*, not unit-scoped — will be
            # rerouted once unit-specific availability is in place (TODO noted below)
            has_avail = (
                db.session.query(Availability.id)
                .filter(Availability.user_id == f.id)
                .limit(1)
                .first()
                is not None
            )

            is_ready = has_profile and has_avail
            fac_progress["account"] += 1 if has_profile else 0
            fac_progress["availability"] += 1 if has_avail else 0
            fac_progress["ready"] += 1 if is_ready else 0

            facilitators.append(
                {
                    "id": f.id,
                    "name": getattr(f, "full_name", None) or f.email,
                    "email": f.email,
                    "phone": getattr(f, "phone", None),
                    "staff_number": getattr(f, "staff_number", None),
                    # Display-only placeholders — wire these to Assignments/Sessions when ready.
                    "experience_years": None,         # TODO: reroute when experience field exists
                    "upcoming_sessions": None,        # TODO: reroute using Session/Assignment join
                    "total_hours": None,              # TODO: reroute using Assignment durations
                    "last_login": getattr(f, "last_login", None),  # if your User has it
                    # Status flags
                    "has_profile": has_profile,
                    "has_availability": has_avail,
                    "is_ready": is_ready,
                }
            )

    return render_template(
        "unitcoordinator_dashboard.html",
        user=user,
        units=units,
        current_unit=current_unit,
        today=date.today(),
        stats=stats,
        fac_progress=fac_progress,
        facilitators=facilitators,
    )

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


@unitcoordinator_bp.route('/facilitators/<int:facilitator_id>/profile')
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def facilitator_profile(facilitator_id):
    """View a specific facilitator's profile"""
    user = get_current_user()
    
    # Get facilitator from Facilitator table
    facilitator = Facilitator.query.get_or_404(facilitator_id)
    
    # Get corresponding User record
    facilitator_user = User.query.filter_by(email=facilitator.email).first()
    
    # Calculate stats
    stats = {
        'units_assigned': 0,
        'pending_approvals': 0,
        'total_sessions': 0,
        'skills_count': 0,
        'availability_status': 'Not Set'
    }
    
    if facilitator_user:
        try:
            # Count units assigned to this facilitator
            stats['units_assigned'] = db.session.query(UnitFacilitator).filter_by(user_id=facilitator_user.id).count()
            
            # Count pending swap requests
            stats['pending_approvals'] = SwapRequest.query.filter_by(
                requested_by=facilitator_user.id, 
                status=SwapStatus.PENDING
            ).count()
            
            # Count total sessions assigned
            stats['total_sessions'] = Assignment.query.filter_by(facilitator_id=facilitator_user.id).count()
            
            # Count skills registered
            stats['skills_count'] = FacilitatorSkill.query.filter_by(user_id=facilitator_user.id).count()
            
            # Check availability status
            has_availability = Availability.query.filter_by(user_id=facilitator_user.id).first()
            stats['availability_status'] = 'Available' if has_availability else 'Not Set'
            
        except Exception as e:
            print(f"Error calculating stats: {e}")
    
    return render_template('unitcoordinator/facilitator_profile.html', 
                         facilitator=facilitator,
                         facilitator_user=facilitator_user,
                         stats=stats)

@unitcoordinator_bp.route('/facilitators/<int:facilitator_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def edit_facilitator_profile(facilitator_id):
    """Edit a facilitator's profile"""
    user = get_current_user()
    facilitator = Facilitator.query.get_or_404(facilitator_id)
    facilitator_user = User.query.filter_by(email=facilitator.email).first()
    
    if request.method == 'POST':
        try:
            # Update facilitator data
            facilitator.first_name = request.form.get('first_name', '').strip()
            facilitator.last_name = request.form.get('last_name', '').strip()
            facilitator.phone = request.form.get('phone', '').strip()
            facilitator.staff_number = request.form.get('staff_number', '').strip()
            
            # Update user data if exists
            if facilitator_user:
                facilitator_user.first_name = facilitator.first_name
                facilitator_user.last_name = facilitator.last_name
            
            db.session.commit()
            flash('Facilitator profile updated successfully!', 'success')
            return redirect(url_for('unitcoordinator.facilitator_profile', facilitator_id=facilitator_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('unitcoordinator/edit_facilitator_profile.html', 
                         facilitator=facilitator,
                         facilitator_user=facilitator_user)



@unitcoordinator_bp.post("/create_or_get_draft")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def create_or_get_draft():
    user = get_current_user()
    
    # CHECK FOR CANCEL ACTION FIRST
    action = request.form.get('action', '').strip()
    if action == 'cancel_draft':
        unit_id = request.form.get('unit_id', '').strip()
        if unit_id:
            try:
                unit_id = int(unit_id)
                unit = Unit.query.get(unit_id)
                if unit and unit.created_by == user.id:
                    # Delete all sessions for this unit
                    sessions = db.session.query(Session).join(Module).filter(Module.unit_id == unit.id).all()
                    for session in sessions:
                        db.session.delete(session)
                    
                    # Delete all modules for this unit
                    modules = Module.query.filter_by(unit_id=unit.id).all()
                    for module in modules:
                        db.session.delete(module)
                    
                    # Delete unit facilitator links
                    UnitFacilitator.query.filter_by(unit_id=unit.id).delete()
                    
                    # Delete unit venue links
                    UnitVenue.query.filter_by(unit_id=unit.id).delete()
                    
                    # Delete the unit itself
                    db.session.delete(unit)
                    db.session.commit()
                    
                    logger.info(f"Cancelled and deleted draft unit {unit_id} for user {user.id}")
                    return jsonify({"ok": True, "message": "Draft cancelled successfully"})
                else:
                    return jsonify({"ok": False, "error": "Unit not found or unauthorized"}), 404
            except ValueError:
                return jsonify({"ok": False, "error": "Invalid unit ID"}), 400
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error cancelling draft: {e}")
                return jsonify({"ok": False, "error": "Failed to cancel draft"}), 500
        
        return jsonify({"ok": True, "message": "No unit to cancel"})

    # EXISTING CREATE/GET LOGIC
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

@unitcoordinator_bp.route("/units/<int:unit_id>/upload_sessions_csv", methods=["POST"])
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def upload_sessions_csv(unit_id: int):
    """
    Accept CSV with headers: activity_group_code, day_of_week, start_time, weeks, duration, location
    Creates sessions for GENG2000 format.
    """
    user = get_current_user()
    unit = _get_user_unit_or_404(user, unit_id)
    if not unit:
        return jsonify({"ok": False, "error": "Unit not found or unauthorized"}), 404

    file = request.files.get("sessions_csv")
    if not file:
        return jsonify({"ok": False, "error": "No file uploaded"}), 400

    try:
        text = file.read().decode("utf-8", errors="replace")
        # Add debug logging
        logger.info(f"CSV content first 500 chars: {text[:500]}")
        reader = csv.DictReader(StringIO(text))
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to read CSV: {e}"}), 400

    # Header check for GENG format
    fns = [fn.strip().lower() for fn in (reader.fieldnames or [])]
    logger.info(f"CSV headers found: {fns}")
    needed = {"activity_group_code", "day_of_week", "start_time", "weeks", "duration", "location"}
    if not needed.issubset(set(fns)):
        return jsonify({"ok": False, "error": f"CSV must include headers: {needed}. Found: {set(fns)}"}), 400

    created = 0
    skipped = 0
    errors = []
    seen = set()
    created_ids = []

    # Helper to parse week date format "30/6" or "7/7"
    def parse_week_date(week_str, year=2025):
        try:
            if '/' in week_str:
                day, month = week_str.split('/')
                return datetime(year, int(month), int(day)).date()
        except Exception as e:
            logger.error(f"Failed to parse week date '{week_str}': {e}")
        return None

    # Helper to convert day name to date
    def get_date_from_day_and_week(day_name, week_date):
        days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
        day_short = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
        
        day_num = days.get(day_name.lower()) or day_short.get(day_name.lower()[:3])
        if day_num is None:
            return None
            
        # Find the date for that day in the week containing week_date
        days_diff = day_num - week_date.weekday()
        return week_date + timedelta(days=days_diff)

    # Helper to parse multiple venues from location field
    def parse_venues(location_str):
        """Extract venue names from location string like 'EZONENTH: [ 109] Learning Studio (30/6), EZONENTH: [ 110] Learning Studio (30/6)'"""
        venues = []
        # Split by comma and clean up each venue
        for venue_part in location_str.split(','):
            venue_part = venue_part.strip()
            if venue_part:
                # Remove date suffix like "(30/6)" if present
                if '(' in venue_part and ')' in venue_part:
                    venue_part = venue_part.split('(')[0].strip()
                # Clean up the venue name
                if ':' in venue_part:
                    # Extract building name before colon
                    building = venue_part.split(':')[0].strip()
                    venues.append(building)
                else:
                    venues.append(venue_part)
        return venues if venues else [location_str.strip()]

    # Preload/collect existing venues for fast lookup
    name_to_venue = {v.name.strip().lower(): v for v in Venue.query.all()}

    def ensure_unit_venue(venue_name: str) -> Venue:
        # Clean venue name
        clean_name = venue_name.strip()
        
        vkey = clean_name.lower()
        venue = name_to_venue.get(vkey)
        if not venue:
            venue = Venue(name=clean_name)
            db.session.add(venue)
            db.session.flush()
            name_to_venue[vkey] = venue
        
        # ensure UnitVenue link
        if not UnitVenue.query.filter_by(unit_id=unit.id, venue_id=venue.id).first():
            db.session.add(UnitVenue(unit_id=unit.id, venue_id=venue.id))
        return venue

    # Process rows
    MAX_ROWS = 2000
    row_count = 0
    for idx, row in enumerate(reader, start=2):
        row_count += 1
        logger.info(f"Processing row {idx}: {row}")
        
        if row_count > MAX_ROWS:
            errors.append(f"Row {idx}: skipped due to row limit ({MAX_ROWS}).")
            skipped += 1
            continue

        activity_code = (row.get("activity_group_code") or "").strip()
        day_of_week = (row.get("day_of_week") or "").strip()
        start_time_str = (row.get("start_time") or "").strip()
        weeks_str = (row.get("weeks") or "").strip()
        duration_str = (row.get("duration") or "").strip()
        location = (row.get("location") or "").strip()

        logger.info(f"Row {idx} parsed: activity={activity_code}, day={day_of_week}, time={start_time_str}, weeks={weeks_str}, duration={duration_str}, location={location}")

        if not all([activity_code, day_of_week, start_time_str, weeks_str, duration_str, location]):
            skipped += 1
            errors.append(f"Row {idx}: missing required fields. Got: activity={activity_code}, day={day_of_week}, time={start_time_str}, weeks={weeks_str}, duration={duration_str}, location={location}")
            continue

        # Parse week date
        week_date = parse_week_date(weeks_str)
        if not week_date:
            skipped += 1
            errors.append(f"Row {idx}: invalid week format '{weeks_str}'.")
            continue

        # Get actual date for this day of week
        session_date = get_date_from_day_and_week(day_of_week, week_date)
        if not session_date:
            skipped += 1
            errors.append(f"Row {idx}: invalid day of week '{day_of_week}'.")
            continue

        # Parse start time
        try:
            hour, minute = map(int, start_time_str.split(':'))
            start_dt = datetime.combine(session_date, datetime.min.time().replace(hour=hour, minute=minute))
        except Exception as e:
            skipped += 1
            errors.append(f"Row {idx}: invalid start time '{start_time_str}': {e}")
            continue

        # Calculate end time from duration (in minutes)
        try:
            duration_minutes = int(duration_str)
            end_dt = start_dt + timedelta(minutes=duration_minutes)
        except Exception as e:
            skipped += 1
            errors.append(f"Row {idx}: invalid duration '{duration_str}': {e}")
            continue

        # Range guard
        # if not _within_unit_range(unit, start_dt) or not _within_unit_range(unit, end_dt):
        #     skipped += 1
        #     errors.append(f"Row {idx}: outside unit date range. Unit range: {unit.start_date} to {unit.end_date}, Session: {start_dt.date()}")
        #     continue

        # Parse venues from location
        venue_names = parse_venues(location)
        
        # Create sessions for each venue
        for venue_name in venue_names:
            # File-level dedupe
            dedupe_key = (activity_code.lower(), session_date, start_dt.time(), end_dt.time(), venue_name.lower())
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            # Ensure venue + link to unit
            venue_obj = ensure_unit_venue(venue_name)

            # Extract session name from activity code
            session_name = activity_code.replace('_', ' ').replace('-', ' - ')
            
            # Determine activity type
            activity_type = "workshop"  # Default for GENG2000
            if "practical" in activity_code.lower():
                activity_type = "lab"
            elif "tutorial" in activity_code.lower():
                activity_type = "tutorial"

            # Module: name = session name, type = activity type
            mod = _get_or_create_module_by_name(unit, session_name)
            mod.module_type = activity_type

            # DB-level dedupe: same module + start + end + venue
            exists = (
                Session.query
                .filter(
                    Session.module_id == mod.id,
                    Session.start_time == start_dt,
                    Session.end_time == end_dt,
                    Session.location == venue_obj.name,
                )
                .first()
            )
            if exists:
                skipped += 1
                continue

            try:
                s = Session(
                    module_id=mod.id,
                    session_type="general",
                    start_time=start_dt,
                    end_time=end_dt,
                    day_of_week=start_dt.weekday(),
                    location=venue_obj.name,
                    required_skills=None,
                    max_facilitators=1,
                )
                db.session.add(s)
                db.session.flush()
                created_ids.append(s.id)
                created += 1
                logger.info(f"Created session: {session_name} at {venue_obj.name} on {start_dt}")
            except Exception as e:
                db.session.rollback()
                errors.append(f"Row {idx}, venue {venue_name}: database error: {e}")
                logger.error(f"Database error creating session: {e}")
                continue

    logger.info(f"Upload summary: {row_count} rows processed, {created} created, {skipped} skipped")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": f"Commit failed: {e}"}), 500

    return jsonify({
        "ok": True,
        "created": created,
        "skipped": skipped,
        "errors": errors[:30],
        "created_session_ids": created_ids,
        "processed_rows": row_count,
    })

# ---------- Step 3B: Calendar / Sessions ----------
@unitcoordinator_bp.get("/units/<int:unit_id>/calendar")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def calendar_week(unit_id: int):
    user = get_current_user()
    unit = _get_user_unit_or_404(user, unit_id)
    if not unit:
        return jsonify({"ok": False, "error": "Unit not found or unauthorized"}), 404

    week_start_raw = (request.args.get("week_start") or "").strip()
    logger.info(f"Calendar requesting week_start: {week_start_raw}")
    
    try:
        week_start = datetime.strptime(week_start_raw, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"ok": False, "error": "Invalid week_start format (use YYYY-MM-DD)"}), 400

    week_end = week_start + timedelta(days=7)
    logger.info(f"Calendar date range: {week_start} to {week_end}")
    
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

    logger.info(f"Found {len(sessions)} sessions for date range {week_start} to {week_end}")
    for s in sessions[:5]:  # Log first 5 sessions
        logger.info(f"Session: {s.start_time} - {s.end_time} at {s.location}")
    
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

    # Optional recurrence
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

    # Determine/validate venue; we store the venue NAME in `location`
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
                # Skip exact duplicates (same module + start_time)
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

    # Serialize the first + include all IDs
    first = Session.query.get(created_ids[0])
    return jsonify({
        "ok": True,
        "session_id": created_ids[0],
        "created_session_ids": created_ids,
        "session": _serialize_session(first, venues_by_name),
    }), 201

@unitcoordinator_bp.route("/sessions/<int:session_id>", methods=["PUT", "PATCH"])
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def update_session(session_id: int):
    """Update an existing session"""
    user = get_current_user()
    
    # Get session and verify ownership through unit
    session = Session.query.get_or_404(session_id)
    unit = Unit.query.join(Module).filter(
        Module.id == session.module_id,
        Unit.created_by == user.id
    ).first()
    
    if not unit:
        return jsonify({"ok": False, "error": "Session not found or unauthorized"}), 404

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"ok": False, "error": "Invalid or missing JSON data"}), 400

    try:
        # Update session fields
        if "start" in data:
            start_dt = _parse_dt(data["start"])
            if start_dt:
                session.start_time = start_dt
                session.day_of_week = start_dt.weekday()
        
        if "end" in data:
            end_dt = _parse_dt(data["end"])
            if end_dt:
                session.end_time = end_dt
        
        if "venue" in data:
            session.location = data["venue"]
        
        if "session_name" in data or "title" in data:
            new_name = data.get("session_name") or data.get("title")
            if new_name:
                mod = _get_or_create_module_by_name(unit, new_name.strip())
                session.module_id = mod.id

        db.session.commit()
        
        # Build venues mapping for serialization
        unit_venues = (
            db.session.query(Venue.id, Venue.name)
            .join(UnitVenue, UnitVenue.venue_id == Venue.id)
            .filter(UnitVenue.unit_id == unit.id)
            .all()
        )
        venues_by_name = { (name or "").strip().lower(): vid for vid, name in unit_venues }

        return jsonify({
            "ok": True,
            "session": _serialize_session(session, venues_by_name)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": f"Update failed: {str(e)}"}), 500

@unitcoordinator_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def delete_session(session_id: int):
    """Delete a session"""
    user = get_current_user()
    
    # Get session and verify ownership through unit
    session = Session.query.get_or_404(session_id)
    unit = Unit.query.join(Module).filter(
        Module.id == session.module_id,
        Unit.created_by == user.id
    ).first()
    
    if not unit:
        return jsonify({"ok": False, "error": "Session not found or unauthorized"}), 404

    try:
        # Delete any assignments first
        Assignment.query.filter_by(session_id=session.id).delete()
        
        # Delete the session
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({"ok": True, "message": "Session deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": f"Delete failed: {str(e)}"}), 500

@unitcoordinator_bp.route("/units/<int:unit_id>/facilitators")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def list_facilitators(unit_id: int):
    """List facilitators for a unit"""
    user = get_current_user()
    unit = _get_user_unit_or_404(user, unit_id)
    if not unit:
        return jsonify({"ok": False, "error": "Unit not found or unauthorized"}), 404

    # Get facilitators linked to this unit
    facilitators = (
        db.session.query(User)
        .join(UnitFacilitator, UnitFacilitator.user_id == User.id)
        .filter(UnitFacilitator.unit_id == unit.id)
        .order_by(User.last_name.asc().nulls_last(), User.first_name.asc().nulls_last())
        .all()
    )

    facilitator_list = []
    for f in facilitators:
        facilitator_list.append({
            "id": f.id,
            "name": getattr(f, "full_name", None) or f.email,
            "email": f.email,
            "first_name": getattr(f, "first_name", None),
            "last_name": getattr(f, "last_name", None),
        })

    return jsonify({
        "ok": True,
        "facilitators": facilitator_list
    })

@unitcoordinator_bp.route("/units/<int:unit_id>/venues")
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def list_venues(unit_id: int):
    """List venues for a unit"""
    user = get_current_user()
    unit = _get_user_unit_or_404(user, unit_id)
    if not unit:
        return jsonify({"ok": False, "error": "Unit not found or unauthorized"}), 404

    # Get venues linked to this unit
    venues = (
        db.session.query(Venue)
        .join(UnitVenue, UnitVenue.venue_id == Venue.id)
        .filter(UnitVenue.unit_id == unit.id)
        .order_by(Venue.name.asc())
        .all()
    )

    venue_list = []
    for v in venues:
        venue_list.append({
            "id": v.id,
            "name": v.name,
            "capacity": getattr(v, "capacity", None),
            "location": getattr(v, "location", None),
        })

    return jsonify({
        "ok": True,
        "venues": venue_list
    })


@unitcoordinator_bp.route('/facilitator/profile/<staff_id>')
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def view_facilitator_profile(staff_id):
    print(f"DEBUG: Accessing profile for staff_id: {staff_id}")
    
    try:
        # Get the facilitator by staff_number
        facilitator = Facilitator.query.filter_by(staff_number=staff_id).first()
        
        if not facilitator:
            flash('Facilitator not found', 'error')
            return redirect(url_for('unitcoordinator.dashboard'))
        
        # Get the corresponding user
        user = User.query.filter_by(email=facilitator.email, role=UserRole.FACILITATOR).first()
        
        if not user:
            flash('User record not found for this facilitator', 'error')
            return redirect(url_for('unitcoordinator.dashboard'))
        
        print(f"DEBUG: Found facilitator: {facilitator.first_name} {facilitator.last_name}")
        print(f"DEBUG: Found user: {user.email}")
        
        # Calculate stats for the facilitator
        stats = {
            'units_assigned': 0,
            'pending_approvals': 0,
            'total_sessions': 0,
            'skills_count': 0,
            'availability_status': 'Available',
        }
        
        return render_template('facilitator_profile.html', 
                             user=user, 
                             facilitator=facilitator, 
                             stats=stats)
                             
    except Exception as e:
        print(f"DEBUG: Error in view_facilitator_profile: {e}")
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('unitcoordinator.dashboard'))