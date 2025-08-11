from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Session, Assignment, SwapRequest, Availability, SwapStatus, FacilitatorSkill, SkillLevel
from auth import facilitator_required, get_current_user
from datetime import datetime, time
import json

facilitator_bp = Blueprint('facilitator', __name__, url_prefix='/facilitator')

@facilitator_bp.route('/dashboard')
@facilitator_required
def dashboard():
    user = get_current_user()
    upcoming_assignments = Assignment.query.filter_by(facilitator_id=user.id).join(Session).filter(Session.start_time > datetime.utcnow()).order_by(Session.start_time).limit(5).all()
    pending_swaps = SwapRequest.query.filter_by(requester_id=user.id, status=SwapStatus.PENDING).count()
    
    return render_template('facilitator_dashboard.html', 
                         user=user,
                         upcoming_assignments=upcoming_assignments,
                         pending_swaps=pending_swaps)

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
    
    if request.method == 'POST':
        preferences = request.form.get('preferences', '')
        skill_names = request.form.getlist('skill_names[]')
        skill_levels = request.form.getlist('skill_levels[]')
        
        # Update preferences
        user.preferences = preferences
        
        # Clear existing skills
        FacilitatorSkill.query.filter_by(facilitator_id=user.id).delete()
        
        # Add new skills with levels
        for skill_name, skill_level in zip(skill_names, skill_levels):
            if skill_name.strip():  # Only add non-empty skills
                facilitator_skill = FacilitatorSkill(
                    facilitator_id=user.id,
                    skill_name=skill_name.strip(),
                    skill_level=SkillLevel(skill_level)
                )
                db.session.add(facilitator_skill)
        
        db.session.commit()
        flash('Skills and preferences updated successfully!')
        return redirect(url_for('facilitator.manage_skills'))
    
    return render_template('manage_skills.html', user=user)

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