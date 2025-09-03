from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Session, Assignment, SwapRequest, Availability, SwapStatus, FacilitatorSkill, SkillLevel, Unit, Module, UnitFacilitator
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
        end_of_week = start_of_week + timedelta(days=7)

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
    return render_template("facilitator_dashboard.html", user=user, greeting=greeting)


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

@facilitator_bp.route('/availability', methods=['GET', 'POST'])
@facilitator_required
def manage_availability():
    user = get_current_user()
    
    if request.method == 'POST':
        # Clear existing availability
        Availability.query.filter_by(user_id=user.id).delete()
        
        # Process individual time slots
        # Get all availability values from the form
        availability_values = request.form.getlist('availability')
        
        # Convert to a more structured format
        availability_slots = {}
        for value in availability_values:
            day_time = value.split('_')
            if len(day_time) == 2:
                day = day_time[0]
                time_str = day_time[1]
                if day not in availability_slots:
                    availability_slots[day] = []
                availability_slots[day].append(time_str)
        
        # Create availability records for each selected slot
        days_map = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6
        }
        
        for day, times in availability_slots.items():
            day_index = days_map.get(day)
            if day_index is not None:
                for time_str in times:
                    # Convert time string to time object
                    hour = int(time_str[:2])
                    minute = int(time_str[2:])
                    slot_time = time(hour, minute)
                    
                    # Create availability record for this specific time slot
                    availability = Availability(
                        user_id=user.id,
                        day_of_week=day_index,
                        start_time=slot_time,
                        end_time=slot_time
                    )
                    db.session.add(availability)
        
        db.session.commit()
        flash('Availability updated successfully!')
        return redirect(url_for('facilitator.manage_availability'))
    
    # Get current availability
    current_availability = Availability.query.filter_by(user_id=user.id).all()
    
    # Convert to a format that the frontend can use
    availability_dict = {}
    for avail in current_availability:
        day_key = avail.day_of_week
        time_key = f"{avail.start_time.hour:02d}{avail.start_time.minute:02d}"
        if day_key not in availability_dict:
            availability_dict[day_key] = []
        availability_dict[day_key].append(time_key)
    
    return render_template('manage_availability.html', 
                         user=user,
                         availability=availability_dict)

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
            my_assignment_id=my_assignment_id,
            target_assignment_id=target_assignment_id
        ).first()
        
        if existing_request:
            flash('Swap request already exists for these assignments.')
            return redirect(url_for('facilitator.request_swap'))
        
        # Create swap request
        swap_request = SwapRequest(
            requester_id=user.id,
            my_assignment_id=my_assignment_id,
            target_assignment_id=target_assignment_id,
            reason=reason,
            status=SwapStatus.PENDING
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