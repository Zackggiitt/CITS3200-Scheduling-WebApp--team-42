from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Session, Assignment, SwapRequest, Unavailability, SwapStatus, FacilitatorSkill, SkillLevel, Unit, Module, UnitFacilitator, RecurringPattern
from auth import facilitator_required, get_current_user, login_required
from datetime import datetime, time, date, timedelta
from utils import role_required
from models import UserRole
import json

facilitator_bp = Blueprint('facilitator', __name__, url_prefix='/facilitator')


def get_greeting():
    """Return time-based greeting"""
    hour = datetime.now().hour
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"


@facilitator_bp.route("/units", methods=["GET"])
@login_required
@role_required(UserRole.FACILITATOR)
def list_units_grouped():
    """Return current user's units grouped into active and past.

    Active definition:
    - today between start_date and end_date (inclusive), OR
    - start_date set and today >= start_date with no end_date, OR
    - no dates but user has future assigned sessions in this unit.
    Past definition:
    - otherwise (typically end_date < today or no future sessions)
    """
    user = get_current_user()
    today = date.today()

    # Fetch units this facilitator is assigned to
    units = (
        Unit.query
        .join(UnitFacilitator, Unit.id == UnitFacilitator.unit_id)
        .filter(UnitFacilitator.user_id == user.id)
        .all()
    )

    # Pre-compute whether a unit has any future sessions assigned to the user
    future_assignments_by_unit = {
        row[0]: row[1]
        for row in (
            db.session.query(Module.unit_id, db.func.count(Session.id))
            .join(Session, Session.module_id == Module.id)
            .join(Assignment, Assignment.session_id == Session.id)
            .filter(
                Assignment.facilitator_id == user.id,
                Session.start_time > datetime.utcnow()
            )
            .group_by(Module.unit_id)
            .all()
        )
    }

    def serialize_unit(u: Unit):
        return {
            "id": u.id,
            "code": u.unit_code,
            "name": u.unit_name,
            "year": u.year,
            "semester": u.semester,
            "start_date": u.start_date.isoformat() if u.start_date else None,
            "end_date": u.end_date.isoformat() if u.end_date else None,
        }

    active_units = []
    past_units = []

    for u in units:
        has_future = future_assignments_by_unit.get(u.id, 0) > 0
        is_active = False

        if u.start_date and u.end_date:
            is_active = (u.start_date <= today <= u.end_date)
        elif u.start_date and not u.end_date:
            is_active = (u.start_date <= today)
        elif not u.start_date and u.end_date:
            is_active = (today <= u.end_date) or has_future
        else:
            is_active = has_future

        (active_units if is_active else past_units).append(serialize_unit(u))

    # Sort: active by start_date desc, then code; past by end_date desc, then code
    def date_key(value):
        return value or "0000-00-00"

    active_units.sort(key=lambda x: (date_key(x["start_date"]), x["code"]), reverse=True)
    past_units.sort(key=lambda x: (date_key(x["end_date"]), x["code"]), reverse=True)

    return jsonify({
        "active_units": active_units,
        "past_units": past_units
    })


@facilitator_bp.route("/dashboard")
@login_required
@role_required(UserRole.FACILITATOR)
def dashboard():
    user = get_current_user()

    # JSON unit-scoped dashboard API: /facilitator/dashboard?unit_id=...
    unit_id = request.args.get("unit_id")
    if unit_id is not None:
        try:
            unit_id_int = int(unit_id)
        except ValueError:
            return jsonify({"error": "invalid unit_id"}), 400

        # Authorization: ensure the user is assigned to this unit
        access = (
            db.session.query(Unit)
            .join(UnitFacilitator, Unit.id == UnitFacilitator.unit_id)
            .filter(Unit.id == unit_id_int, UnitFacilitator.user_id == user.id)
            .first()
        )
        if not access:
            return jsonify({"error": "forbidden"}), 403

        # Time windows
        now = datetime.utcnow()
        start_of_week = (now.replace(hour=0, minute=0, second=0, microsecond=0)
                         - timedelta(days=now.weekday()))
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

        # Base query for user's assignments within this unit
        base_q = (
            db.session.query(Assignment, Session, Module)
            .join(Session, Assignment.session_id == Session.id)
            .join(Module, Session.module_id == Module.id)
            .filter(Assignment.facilitator_id == user.id, Module.unit_id == unit_id_int)
        )

        # Total hours for the unit
        all_rows = base_q.all()
        def duration_hours(row):
            return max(0.0, (row[1].end_time - row[1].start_time).total_seconds() / 3600.0)
        total_hours = sum(duration_hours(r) for r in all_rows)

        # This week hours and active sessions count
        week_rows = [r for r in all_rows if start_of_week <= r[1].start_time < end_of_week]
        this_week_hours = sum(duration_hours(r) for r in week_rows)
        active_sessions = len(week_rows)

        # Upcoming sessions (next 10)
        upcoming_rows = (
            base_q.filter(Session.start_time >= now)
            .order_by(Session.start_time.asc())
            .limit(10)
            .all()
        )

        # Recent past sessions (last 10)
        past_rows = (
            base_q.filter(Session.start_time < now)
            .order_by(Session.start_time.desc())
            .limit(10)
            .all()
        )

        def serialize_session(r):
            a, s, m = r
            return {
                "assignment_id": a.id,
                "session_id": s.id,
                "module": m.module_name,
                "session_type": s.session_type,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat(),
                "location": s.location,
                "is_confirmed": bool(a.is_confirmed),
            }

        payload = {
            "unit": {
                "id": access.id,
                "code": access.unit_code,
                "name": access.unit_name,
                "year": access.year,
                "semester": access.semester,
            },
            "kpis": {
                "this_week_hours": round(this_week_hours, 2),
                "total_hours": round(total_hours, 2),
                "active_sessions": active_sessions,
            },
            "sessions": {
                "upcoming": [serialize_session(r) for r in upcoming_rows],
                "recent_past": [serialize_session(r) for r in past_rows],
            }
        }
        return jsonify(payload)

    # Fallback to HTML dashboard when no unit_id is provided
    greeting = get_greeting()
    
    # Get user's units for the dashboard
    units = (
        Unit.query
        .join(UnitFacilitator, Unit.id == UnitFacilitator.unit_id)
        .filter(UnitFacilitator.user_id == user.id)
        .order_by(Unit.start_date.desc())
        .all()
    )
    
    # Get current active unit (most recent with future sessions or current date range)
    current_unit = None
    today = date.today()
    
    for unit in units:
        # Check if unit is currently active
        if (unit.start_date and unit.end_date and 
            unit.start_date <= today <= unit.end_date):
            current_unit = unit
            break
        elif (unit.start_date and not unit.end_date and 
              unit.start_date <= today):
            current_unit = unit
            break
    
    # If no active unit found, use the most recent unit
    if not current_unit and units:
        current_unit = units[0]
    
    # Convert current_unit to dictionary for JSON serialization
    current_unit_dict = None
    if current_unit:
        current_unit_dict = {
            'id': current_unit.id,
            'unit_code': current_unit.unit_code,
            'unit_name': current_unit.unit_name,
            'year': current_unit.year,
            'semester': current_unit.semester,
            'start_date': current_unit.start_date.isoformat() if current_unit.start_date else None,
            'end_date': current_unit.end_date.isoformat() if current_unit.end_date else None,
            'description': current_unit.description
        }
    
    # Get units data for JavaScript
    units_data = []
    for unit in units:
        # Get assignments for this unit
        assignments = (
            db.session.query(Assignment, Session, Module)
            .join(Session, Assignment.session_id == Session.id)
            .join(Module, Session.module_id == Module.id)
            .filter(Assignment.facilitator_id == user.id, Module.unit_id == unit.id)
            .all()
        )
        
        # Get session count for this unit (sessions assigned to this facilitator)
        session_count = len(assignments)
        
        # Calculate KPIs
        total_hours = sum((s.end_time - s.start_time).total_seconds() / 3600.0 for _, s, _ in assignments)
        
        # This week hours
        now = datetime.utcnow()
        start_of_week = (now.replace(hour=0, minute=0, second=0, microsecond=0)
                         - timedelta(days=now.weekday()))
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        this_week_hours = sum(
            (s.end_time - s.start_time).total_seconds() / 3600.0 
            for _, s, _ in assignments 
            if start_of_week <= s.start_time < end_of_week
        )
        
        # Active sessions this week
        active_sessions = len([
            s for _, s, _ in assignments 
            if start_of_week <= s.start_time < end_of_week
        ])
        
        # Upcoming sessions
        upcoming_sessions = [
            {
                'id': a.id,
                'session_id': s.id,
                'module': m.module_name or 'Unknown Module',  # Handle null module names
                'session_type': s.session_type or 'Unknown Type',  # Handle null session types
                'start_time': s.start_time.isoformat(),
                'end_time': s.end_time.isoformat(),
                'location': s.location or 'TBA',  # Handle null locations
                'is_confirmed': bool(a.is_confirmed),
                'date': s.start_time.strftime('%d/%m/%Y'),
                'time': f"{s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}",
                'topic': m.module_name or 'Unknown Module',
                'status': 'confirmed' if a.is_confirmed else 'pending'
            }
            for a, s, m in assignments
            if s.start_time >= now
        ]
        
        # Past sessions
        past_sessions = [
            {
                'id': a.id,
                'session_id': s.id,
                'module': m.module_name or 'Unknown Module',  # Handle null module names
                'session_type': s.session_type or 'Unknown Type',  # Handle null session types
                'start_time': s.start_time.isoformat(),
                'end_time': s.end_time.isoformat(),
                'location': s.location or 'TBA',  # Handle null locations
                'is_confirmed': bool(a.is_confirmed),
                'date': s.start_time.strftime('%d/%m/%Y'),
                'time': f"{s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}",
                'topic': m.module_name or 'Unknown Module',
                'status': 'completed'
            }
            for a, s, m in assignments
            if s.start_time < now
        ]
        
        # Determine if unit is active
        today = date.today()
        is_active = False
        if unit.start_date and unit.end_date:
            is_active = (today <= unit.end_date)
        elif unit.start_date and not unit.end_date:
            is_active = (unit.start_date <= today)
        elif not unit.start_date and unit.end_date:
            is_active = (today <= unit.end_date)
        else:
            is_active = len(upcoming_sessions) > 0
        
        unit_data = {
            'id': unit.id,
            'code': unit.unit_code,
            'name': unit.unit_name,
            'year': unit.year,
            'semester': unit.semester,
            'start_date': unit.start_date.isoformat() if unit.start_date else None,
            'end_date': unit.end_date.isoformat() if unit.end_date else None,
            'status': 'active' if is_active else 'completed',
            'sessions': session_count,
            'date_range': f"{unit.start_date.strftime('%d/%m/%Y')} - {unit.end_date.strftime('%d/%m/%Y')}" if unit.start_date and unit.end_date else 'No date range',
            'kpis': {
                'this_week_hours': round(this_week_hours, 1),
                'total_hours': round(total_hours, 1),
                'active_sessions': active_sessions,
                'remaining_hours': round(total_hours - this_week_hours, 1),
                'total_sessions': session_count
            },
            'upcoming_sessions': upcoming_sessions,  # Show all upcoming sessions
            'past_sessions': past_sessions  # Show all past sessions
        }
        units_data.append(unit_data)
    
    return render_template("facilitator_dashboard.html", 
                         user=user, 
                         greeting=greeting,
                         units=units,
                         current_unit=current_unit,
                         current_unit_dict=current_unit_dict,
                         units_data=units_data)


@facilitator_bp.route("/")
@login_required
@role_required(UserRole.FACILITATOR)
def root():
    return redirect(url_for(".dashboard"))

@facilitator_bp.route('/schedule')
@facilitator_required
def view_schedule():
    user = get_current_user()
    assignments = Assignment.query.filter_by(facilitator_id=user.id).join(Session).order_by(Session.start_time).all()
    return render_template('view_schedule.html', user=user, assignments=assignments)

@facilitator_bp.route('/unit-info', methods=['GET'])
@facilitator_required
def get_unit_info():
    """Get unit information for unavailability system"""
    user = get_current_user()
    unit_id = request.args.get('unit_id', type=int)
    
    if not unit_id:
        return jsonify({"error": "unit_id is required"}), 400
    
    # Verify user has access to this unit
    unit = (
        db.session.query(Unit)
        .join(UnitFacilitator, Unit.id == UnitFacilitator.unit_id)
        .filter(Unit.id == unit_id, UnitFacilitator.user_id == user.id)
        .first()
    )
    
    if not unit:
        return jsonify({"error": "forbidden"}), 403
    
    # Serialize unit data
    unit_data = {
        "id": unit.id,
        "code": unit.unit_code,
        "name": unit.unit_name,
        "start_date": unit.start_date.isoformat() if unit.start_date else None,
        "end_date": unit.end_date.isoformat() if unit.end_date else None,
        "year": unit.year,
        "semester": unit.semester
    }
    
    return jsonify({"unit": unit_data})

@facilitator_bp.route('/unavailability', methods=['GET'])
@facilitator_required
def get_unavailability():
    """Get unavailability for a specific unit"""
    user = get_current_user()
    unit_id = request.args.get('unit_id', type=int)
    
    if not unit_id:
        return jsonify({"error": "unit_id is required"}), 400
    
    # Verify user has access to this unit
    access = (
        db.session.query(Unit)
        .join(UnitFacilitator, Unit.id == UnitFacilitator.unit_id)
        .filter(Unit.id == unit_id, UnitFacilitator.user_id == user.id)
        .first()
    )
    if not access:
        return jsonify({"error": "forbidden"}), 403
    
    # Get unavailability records for this user and unit
    unavailabilities = Unavailability.query.filter_by(
        user_id=user.id, 
        unit_id=unit_id
    ).all()
    
    # Serialize unavailability data
    unavailability_data = []
    for unav in unavailabilities:
        unavailability_data.append({
            'id': unav.id,
            'date': unav.date.isoformat(),
            'start_time': unav.start_time.isoformat() if unav.start_time else None,
            'end_time': unav.end_time.isoformat() if unav.end_time else None,
            'is_full_day': unav.is_full_day,
            'recurring_pattern': unav.recurring_pattern.value if unav.recurring_pattern else None,
            'recurring_end_date': unav.recurring_end_date.isoformat() if unav.recurring_end_date else None,
            'recurring_interval': unav.recurring_interval,
            'reason': unav.reason
        })
    
    return jsonify({
        'unit': {
            'id': access.id,
            'code': access.unit_code,
            'name': access.unit_name,
            'start_date': access.start_date.isoformat() if access.start_date else None,
            'end_date': access.end_date.isoformat() if access.end_date else None
        },
        'unavailabilities': unavailability_data
    })

@facilitator_bp.route('/unavailability', methods=['POST'])
@facilitator_required
def create_unavailability():
    """Create or update unavailability for a specific unit"""
    user = get_current_user()
    data = request.get_json()
    
    unit_id = data.get('unit_id')
    if not unit_id:
        return jsonify({"error": "unit_id is required"}), 400
    
    # Verify user has access to this unit
    access = (
        db.session.query(Unit)
        .join(UnitFacilitator, Unit.id == UnitFacilitator.unit_id)
        .filter(Unit.id == unit_id, UnitFacilitator.user_id == user.id)
        .first()
    )
    if not access:
        return jsonify({"error": "forbidden"}), 403
    
    # Validate date format and range
    try:
        unavailability_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    if access.start_date and unavailability_date < access.start_date:
        return jsonify({"error": "Date is before unit start date"}), 400
    if access.end_date and unavailability_date > access.end_date:
        return jsonify({"error": "Date is after unit end date"}), 400
    
    # Parse time data
    start_time = None
    end_time = None
    is_full_day = data.get('is_full_day', False)
    
    if not is_full_day:
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        
        if not start_time_str or not end_time_str:
            return jsonify({"error": "Start time and end time are required for partial day unavailability"}), 400
        
        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            return jsonify({"error": "Invalid time format. Use HH:MM"}), 400
        
        if start_time >= end_time:
            return jsonify({"error": "End time must be after start time"}), 400
    
    # Parse recurring pattern
    recurring_pattern = None
    recurring_end_date = None
    recurring_interval = 1
    
    if data.get('recurring_pattern'):
        recurring_pattern_str = data.get('recurring_pattern')
        if recurring_pattern_str not in [pattern.value for pattern in RecurringPattern]:
            return jsonify({"error": "Invalid recurring pattern"}), 400
        
        recurring_pattern = RecurringPattern(recurring_pattern_str)
        
        if not data.get('recurring_end_date'):
            return jsonify({"error": "Recurring end date is required for recurring unavailability"}), 400
        
        try:
            recurring_end_date = datetime.strptime(data.get('recurring_end_date'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid recurring end date format. Use YYYY-MM-DD"}), 400
        
        if recurring_end_date <= unavailability_date:
            return jsonify({"error": "Recurring end date must be after the start date"}), 400
        
        recurring_interval = data.get('recurring_interval', 1)
        if not isinstance(recurring_interval, int) or recurring_interval < 1 or recurring_interval > 52:
            return jsonify({"error": "Recurring interval must be between 1 and 52"}), 400
    
    # Validate reason length
    reason = data.get('reason', '')
    if len(reason) > 500:
        return jsonify({"error": "Reason must be 500 characters or less"}), 400
    
    # Check for existing unavailability on the same date
    existing = Unavailability.query.filter_by(
        user_id=user.id,
        unit_id=unit_id,
        date=unavailability_date
    ).first()
    
    if existing:
        return jsonify({"error": "Unavailability already exists for this date"}), 409
    
    # Create unavailability record
    unavailability = Unavailability(
        user_id=user.id,
        unit_id=unit_id,
        date=unavailability_date,
        start_time=start_time,
        end_time=end_time,
        is_full_day=is_full_day,
        recurring_pattern=recurring_pattern,
        recurring_end_date=recurring_end_date,
        recurring_interval=recurring_interval,
        reason=reason if reason else None
    )
    
    try:
        db.session.add(unavailability)
        db.session.commit()
        
        return jsonify({
            "message": "Unavailability created successfully",
            "unavailability": {
                "id": unavailability.id,
                "date": unavailability.date.isoformat(),
                "is_full_day": unavailability.is_full_day,
                "start_time": unavailability.start_time.isoformat() if unavailability.start_time else None,
                "end_time": unavailability.end_time.isoformat() if unavailability.end_time else None,
                "recurring_pattern": unavailability.recurring_pattern.value if unavailability.recurring_pattern else None,
                "reason": unavailability.reason
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create unavailability"}), 500

@facilitator_bp.route('/unavailability/<int:unavailability_id>', methods=['PUT'])
@facilitator_required
def update_unavailability(unavailability_id):
    """Update an existing unavailability record"""
    user = get_current_user()
    data = request.get_json()
    
    # Get the unavailability record
    unavailability = Unavailability.query.filter_by(
        id=unavailability_id, 
        user_id=user.id
    ).first()
    
    if not unavailability:
        return jsonify({"error": "Unavailability not found"}), 404
    
    # Update fields
    if 'date' in data:
        unavailability.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    if 'start_time' in data:
        unavailability.start_time = datetime.strptime(data['start_time'], '%H:%M').time() if data['start_time'] else None
    
    if 'end_time' in data:
        unavailability.end_time = datetime.strptime(data['end_time'], '%H:%M').time() if data['end_time'] else None
    
    if 'is_full_day' in data:
        unavailability.is_full_day = data['is_full_day']
    
    if 'recurring_pattern' in data:
        unavailability.recurring_pattern = RecurringPattern(data['recurring_pattern']) if data['recurring_pattern'] else None
    
    if 'recurring_end_date' in data:
        unavailability.recurring_end_date = datetime.strptime(data['recurring_end_date'], '%Y-%m-%d').date() if data['recurring_end_date'] else None
    
    if 'recurring_interval' in data:
        unavailability.recurring_interval = data['recurring_interval']
    
    if 'reason' in data:
        unavailability.reason = data['reason']
        
        db.session.commit()
    
    return jsonify({"message": "Unavailability updated successfully"})

@facilitator_bp.route('/unavailability/<int:unavailability_id>', methods=['DELETE'])
@facilitator_required
def delete_unavailability(unavailability_id):
    """Delete an unavailability record"""
    user = get_current_user()
    
    # Get the unavailability record
    unavailability = Unavailability.query.filter_by(
        id=unavailability_id, 
        user_id=user.id
    ).first()
    
    if not unavailability:
        return jsonify({"error": "Unavailability not found"}), 404
    
    db.session.delete(unavailability)
    db.session.commit()
    
    return jsonify({"message": "Unavailability deleted successfully"})

@facilitator_bp.route('/unavailability/generate-recurring', methods=['POST'])
@facilitator_required
def generate_recurring_unavailability():
    """Generate recurring unavailability entries based on pattern"""
    user = get_current_user()
    data = request.get_json()
    
    unit_id = data.get('unit_id')
    if not unit_id:
        return jsonify({"error": "unit_id is required"}), 400
    
    # Verify user has access to this unit
    access = (
        db.session.query(Unit)
        .join(UnitFacilitator, Unit.id == UnitFacilitator.unit_id)
        .filter(Unit.id == unit_id, UnitFacilitator.user_id == user.id)
        .first()
    )
    if not access:
        return jsonify({"error": "forbidden"}), 403
    
    # Parse the base unavailability data
    base_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    recurring_pattern = RecurringPattern(data.get('recurring_pattern'))
    recurring_end_date = datetime.strptime(data.get('recurring_end_date'), '%Y-%m-%d').date()
    recurring_interval = data.get('recurring_interval', 1)
    
    # Generate all dates for the recurring pattern
    dates = []
    current_date = base_date
    
    while current_date <= recurring_end_date:
        dates.append(current_date)
        
        if recurring_pattern == RecurringPattern.DAILY:
            current_date += timedelta(days=recurring_interval)
        elif recurring_pattern == RecurringPattern.WEEKLY:
            current_date += timedelta(weeks=recurring_interval)
        elif recurring_pattern == RecurringPattern.MONTHLY:
            # Simple monthly increment
            year = current_date.year
            month = current_date.month + recurring_interval
            if month > 12:
                year += 1
                month -= 12
            try:
                current_date = current_date.replace(year=year, month=month)
            except ValueError:
                current_date = current_date.replace(year=year, month=month, day=1) - timedelta(days=1)
    
    # Create unavailability records for each date
    created_count = 0
    for date in dates:
        # Check if unavailability already exists for this date
        existing = Unavailability.query.filter_by(
            user_id=user.id,
            unit_id=unit_id,
            date=date
        ).first()
        
        if not existing:
            unavailability = Unavailability(
                user_id=user.id,
                unit_id=unit_id,
                date=date,
                start_time=datetime.strptime(data.get('start_time'), '%H:%M').time() if data.get('start_time') else None,
                end_time=datetime.strptime(data.get('end_time'), '%H:%M').time() if data.get('end_time') else None,
                is_full_day=data.get('is_full_day', False),
                recurring_pattern=recurring_pattern,
                recurring_end_date=recurring_end_date,
                recurring_interval=recurring_interval,
                reason=data.get('reason')
            )
            db.session.add(unavailability)
            created_count += 1
    
    db.session.commit()
    
    return jsonify({
        "message": f"Created {created_count} recurring unavailability entries",
        "total_dates": len(dates),
        "created_count": created_count
    })

@facilitator_bp.route('/skills', methods=['GET', 'POST'])
@facilitator_required
def manage_skills():
    user = get_current_user()
    
    # Get all modules
    modules = Module.query.all()
    
    if request.method == 'POST':
        preferences = request.form.get('preferences', '')
        
        # Update preferences
        user.preferences = preferences
        
        # Clear existing skills
        FacilitatorSkill.query.filter_by(facilitator_id=user.id).delete()
        
        # Add new skills with levels based on module IDs
        for module in modules:
            skill_level = request.form.get(f'skill_level_{module.id}')
            if skill_level and skill_level != 'uninterested':
                facilitator_skill = FacilitatorSkill(
                    facilitator_id=user.id,
                    module_id=module.id,
                    skill_level=SkillLevel(skill_level)
                )
                db.session.add(facilitator_skill)
        
        db.session.commit()
        flash('Skills and preferences updated successfully!')
        return redirect(url_for('facilitator.manage_skills'))
    
    # Get current skills for this facilitator
    current_skills = {}
    facilitator_skills = FacilitatorSkill.query.filter_by(facilitator_id=user.id).all()
    for skill in facilitator_skills:
        current_skills[skill.module_id] = skill.skill_level.value
    
    return render_template('manage_skills.html', 
                         user=user,
                         modules=modules,
                         current_skills=current_skills,
                         current_preferences=user.preferences)

@facilitator_bp.route('/swaps')
@facilitator_required
def view_swaps():
    user = get_current_user()
    my_requests = SwapRequest.query.filter_by(requester_id=user.id).all()
    
    # Fix: Specify the join condition explicitly
    # Get swap requests where the target assignment belongs to the current user
    requests_for_me = SwapRequest.query.join(
        Assignment, 
        SwapRequest.target_assignment_id == Assignment.id
    ).filter(Assignment.facilitator_id == user.id).all()
    
    return render_template('view_swaps.html', 
                         user=user,
                         my_requests=my_requests, 
                         requests_for_me=requests_for_me)

@facilitator_bp.route('/swaps/request', methods=['GET', 'POST'])
@facilitator_required
def request_swap():
    user = get_current_user()
    
    if request.method == 'POST':
        my_assignment_id = request.form.get('my_assignment_id')
        target_assignment_id = request.form.get('target_assignment_id')
        reason = request.form.get('reason', '')
        
        # Validate assignments
        my_assignment = Assignment.query.filter_by(id=my_assignment_id, facilitator_id=user.id).first()
        target_assignment = Assignment.query.get(target_assignment_id)
        
        if not my_assignment or not target_assignment:
            flash('Invalid assignment selection.')
            return redirect(url_for('facilitator.request_swap'))
        
        # Check if swap request already exists
        existing_request = SwapRequest.query.filter_by(
            requester_id=user.id,
            requester_assignment_id=my_assignment_id,
            target_assignment_id=target_assignment_id
        ).first()
        
        if existing_request:
            flash('Swap request already exists for these assignments.')
            return redirect(url_for('facilitator.request_swap'))
        
        # Create swap request
        swap_request = SwapRequest(
            requester_id=user.id,
            target_id=target_assignment.facilitator_id,
            requester_assignment_id=my_assignment_id,
            target_assignment_id=target_assignment_id,
            reason=reason,
            status=SwapStatus.FACILITATOR_PENDING
        )
        
        db.session.add(swap_request)
        db.session.commit()
        
        flash('Swap request submitted successfully!')
        return redirect(url_for('facilitator.view_swaps'))
    
    # Get user's assignments and other available assignments
    my_assignments = Assignment.query.filter_by(facilitator_id=user.id).join(Session).filter(Session.start_time > datetime.utcnow()).all()
    other_assignments = Assignment.query.filter(Assignment.facilitator_id != user.id).join(Session).filter(Session.start_time > datetime.utcnow()).all()
    
    return render_template('request_swap.html', 
                         user=user,
                         my_assignments=my_assignments, 
                         other_assignments=other_assignments)


# New API endpoints for Session Swaps tab

@facilitator_bp.route('/swap-requests', methods=['POST'])
@login_required
@role_required(UserRole.FACILITATOR)
def create_swap_request():
    """Create a new swap request via API."""
    user = get_current_user()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    requester_assignment_id = data.get('requester_assignment_id')
    target_assignment_id = data.get('target_assignment_id')
    target_facilitator_id = data.get('target_facilitator_id')
    has_discussed = data.get('has_discussed', False)
    unit_id = data.get('unit_id')  # Optional unit context
    
    # Validate required fields
    if not all([requester_assignment_id, target_assignment_id, target_facilitator_id]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if not has_discussed:
        return jsonify({'error': 'Must confirm discussion with target facilitator'}), 400
    
    # Validate assignments
    requester_assignment = Assignment.query.filter_by(
        id=requester_assignment_id, 
        facilitator_id=user.id
    ).first()
    
    target_assignment = Assignment.query.filter_by(
        id=target_assignment_id,
        facilitator_id=target_facilitator_id
    ).first()
    
    if not requester_assignment or not target_assignment:
        return jsonify({'error': 'Invalid assignment selection'}), 400
    
    # Check if swap request already exists
    existing_request = SwapRequest.query.filter_by(
        requester_id=user.id,
        requester_assignment_id=requester_assignment_id,
        target_assignment_id=target_assignment_id
    ).first()
    
    if existing_request:
        return jsonify({'error': 'Swap request already exists for these assignments'}), 400
    
    # Create swap request
    swap_request = SwapRequest(
        requester_id=user.id,
        target_id=target_facilitator_id,
        requester_assignment_id=requester_assignment_id,
        target_assignment_id=target_assignment_id,
        reason="Session swap request",
        status=SwapStatus.FACILITATOR_PENDING,
        facilitator_confirmed=False
    )
    
    try:
        db.session.add(swap_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Swap request created successfully',
            'swap_request_id': swap_request.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create swap request: {str(e)}'}), 500


@facilitator_bp.route('/swap-requests', methods=['GET'])
@login_required
@role_required(UserRole.FACILITATOR)
def get_swap_requests():
    """Get user's swap requests grouped by status, filtered by unit."""
    user = get_current_user()
    unit_id = request.args.get('unit_id', type=int)
    
    # Base query for requests made by this user
    my_requests_query = SwapRequest.query.filter_by(requester_id=user.id)
    
    # Base query for requests where this user is the target facilitator
    requests_for_me_query = SwapRequest.query.filter_by(target_id=user.id)
    
    # Filter by unit if provided
    if unit_id:
        # Join with Assignment, Session, and Module to filter by unit
        my_requests_query = my_requests_query.join(Assignment).join(Session).join(Module).filter(Module.unit_id == unit_id)
        requests_for_me_query = requests_for_me_query.join(Assignment).join(Session).join(Module).filter(Module.unit_id == unit_id)
    
    my_requests = my_requests_query.all()
    requests_for_me = requests_for_me_query.all()
    
    def serialize_swap_request(req):
        return {
            'id': req.id,
            'requester_name': req.requester.full_name,
            'target_name': req.target.full_name,
            'session_name': req.requester_assignment.session.module.module_name,
            'session_date': req.requester_assignment.session.start_time.strftime('%Y-%m-%d'),
            'session_time': req.requester_assignment.session.start_time.strftime('%H:%M'),
            'session_location': req.requester_assignment.session.location,
            'status': req.status.value,
            'facilitator_confirmed': req.facilitator_confirmed,
            'facilitator_confirmed_at': req.facilitator_confirmed_at.isoformat() if req.facilitator_confirmed_at else None,
            'facilitator_decline_reason': req.facilitator_decline_reason,
            'coordinator_decline_reason': req.coordinator_decline_reason,
            'created_at': req.created_at.isoformat(),
            'is_my_request': req.requester_id == user.id
        }
    
    # Group requests by status
    pending_requests = []
    approved_requests = []
    declined_requests = []
    
    all_requests = my_requests + requests_for_me
    
    for req in all_requests:
        serialized = serialize_swap_request(req)
        
        if req.status in [SwapStatus.FACILITATOR_PENDING, SwapStatus.COORDINATOR_PENDING]:
            pending_requests.append(serialized)
        elif req.status == SwapStatus.APPROVED:
            approved_requests.append(serialized)
        elif req.status in [SwapStatus.FACILITATOR_DECLINED, SwapStatus.COORDINATOR_DECLINED, SwapStatus.REJECTED]:
            declined_requests.append(serialized)
    
    return jsonify({
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'declined_requests': declined_requests
    })


def check_facilitator_availability(facilitator_id, session_date, session_start_time, session_end_time, unit_id):
    """Check if a facilitator is available for a specific session time."""
    
    # Check for unavailability conflicts
    unavailability_conflict = Unavailability.query.filter(
        Unavailability.user_id == facilitator_id,
        Unavailability.unit_id == unit_id,
        Unavailability.date == session_date,
        db.or_(
            Unavailability.is_full_day == True,
            db.and_(
                Unavailability.start_time <= session_start_time,
                Unavailability.end_time >= session_end_time
            )
        )
    ).first()
    
    if unavailability_conflict:
        return False, "Facilitator has marked unavailability for this time"
    
    # Check for existing session assignments at the same time
    conflicting_assignment = Assignment.query.join(Session).filter(
        Assignment.facilitator_id == facilitator_id,
        Session.start_time.date() == session_date,
        db.or_(
            db.and_(
                Session.start_time.time() <= session_start_time,
                Session.end_time.time() > session_start_time
            ),
            db.and_(
                Session.start_time.time() < session_end_time,
                Session.end_time.time() >= session_end_time
            )
        )
    ).first()
    
    if conflicting_assignment:
        return False, "Facilitator has conflicting session assignment"
    
    return True, "Available"


@facilitator_bp.route('/available-facilitators/<int:assignment_id>', methods=['GET'])
@login_required
@role_required(UserRole.FACILITATOR)
def get_available_facilitators(assignment_id):
    """Get facilitators available for a specific assignment swap."""
    user = get_current_user()
    unit_id = request.args.get('unit_id', type=int)
    
    # Get the assignment details
    assignment = Assignment.query.get(assignment_id)
    if not assignment or assignment.facilitator_id != user.id:
        return jsonify({'error': 'Invalid assignment'}), 400
    
    session = assignment.session
    session_date = session.start_time.date()
    session_start_time = session.start_time.time()
    session_end_time = session.end_time.time()
    
    # Use provided unit_id or fall back to session's unit
    target_unit_id = unit_id if unit_id else session.module.unit_id
    
    # Get all facilitators assigned to the specified unit
    unit_facilitators = (
        User.query
        .join(UnitFacilitator, User.id == UnitFacilitator.user_id)
        .filter(
            UnitFacilitator.unit_id == target_unit_id,
            User.id != user.id,  # Exclude current user
            User.role == UserRole.FACILITATOR
        )
        .all()
    )
    
    available_facilitators = []
    
    for facilitator in unit_facilitators:
        is_available, reason = check_facilitator_availability(
            facilitator.id, 
            session_date, 
            session_start_time, 
            session_end_time, 
            session.module.unit_id
        )
        
        if is_available:
            available_facilitators.append({
                'id': facilitator.id,
                'name': facilitator.full_name,
                'email': facilitator.email
            })
    
    return jsonify({
        'available_facilitators': available_facilitators,
        'session_info': {
            'date': session_date.isoformat(),
            'start_time': session_start_time.isoformat(),
            'end_time': session_end_time.isoformat(),
            'unit_id': session.module.unit_id
        }
    })


@facilitator_bp.route('/swap-requests/<int:request_id>/facilitator-response', methods=['POST'])
@login_required
@role_required(UserRole.FACILITATOR)
def facilitator_response_to_swap(request_id):
    """Handle facilitator response to swap request (approve/decline)."""
    user = get_current_user()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    action = data.get('action')  # 'approve' or 'decline'
    reason = data.get('reason', '')
    
    if action not in ['approve', 'decline']:
        return jsonify({'error': 'Invalid action. Must be approve or decline'}), 400
    
    # Get the swap request
    swap_request = SwapRequest.query.get(request_id)
    if not swap_request:
        return jsonify({'error': 'Swap request not found'}), 404
    
    # Check if user is the target facilitator
    if swap_request.target_id != user.id:
        return jsonify({'error': 'Unauthorized. You are not the target facilitator'}), 403
    
    # Check if request is in correct status
    if swap_request.status != SwapStatus.FACILITATOR_PENDING:
        return jsonify({'error': 'Request is not in facilitator pending status'}), 400
    
    try:
        if action == 'approve':
            # Check availability before approving
            session = swap_request.requester_assignment.session
            session_date = session.start_time.date()
            session_start_time = session.start_time.time()
            session_end_time = session.end_time.time()
            
            is_available, availability_reason = check_facilitator_availability(
                user.id, session_date, session_start_time, session_end_time, session.module.unit_id
            )
            
            if not is_available:
                return jsonify({'error': f'Cannot approve: {availability_reason}'}), 400
            
            # Approve the request
            swap_request.facilitator_confirmed = True
            swap_request.facilitator_confirmed_at = datetime.utcnow()
            swap_request.status = SwapStatus.COORDINATOR_PENDING
            
        else:  # decline
            swap_request.facilitator_confirmed = False
            swap_request.facilitator_confirmed_at = datetime.utcnow()
            swap_request.facilitator_decline_reason = reason
            swap_request.status = SwapStatus.FACILITATOR_DECLINED
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Swap request {action}d successfully',
            'status': swap_request.status.value
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to process response: {str(e)}'}), 500


@facilitator_bp.route('/swap-requests/<int:request_id>/coordinator-response', methods=['POST'])
@login_required
@role_required(UserRole.UNIT_COORDINATOR)
def coordinator_response_to_swap(request_id):
    """Handle coordinator response to swap request (approve/decline)."""
    user = get_current_user()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    action = data.get('action')  # 'approve' or 'decline'
    reason = data.get('reason', '')
    
    if action not in ['approve', 'decline']:
        return jsonify({'error': 'Invalid action. Must be approve or decline'}), 400
    
    # Get the swap request
    swap_request = SwapRequest.query.get(request_id)
    if not swap_request:
        return jsonify({'error': 'Swap request not found'}), 404
    
    # Check if request is in correct status
    if swap_request.status != SwapStatus.COORDINATOR_PENDING:
        return jsonify({'error': 'Request is not in coordinator pending status'}), 400
    
    try:
        if action == 'approve':
            # Perform the actual swap
            requester_assignment = swap_request.requester_assignment
            target_assignment = swap_request.target_assignment
            
            # Swap the facilitators
            temp_facilitator_id = requester_assignment.facilitator_id
            requester_assignment.facilitator_id = target_assignment.facilitator_id
            target_assignment.facilitator_id = temp_facilitator_id
            
            swap_request.status = SwapStatus.APPROVED
            swap_request.reviewed_at = datetime.utcnow()
            swap_request.reviewed_by = user.id
            
        else:  # decline
            swap_request.status = SwapStatus.COORDINATOR_DECLINED
            swap_request.coordinator_decline_reason = reason
            swap_request.reviewed_at = datetime.utcnow()
            swap_request.reviewed_by = user.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Swap request {action}d successfully',
            'status': swap_request.status.value
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to process response: {str(e)}'}), 500