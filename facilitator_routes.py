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
        
        # Add new availability
        for day in range(7):  # 0=Monday, 6=Sunday
            start_time_str = request.form.get(f'day_{day}_start')
            end_time_str = request.form.get(f'day_{day}_end')
            is_available = request.form.get(f'day_{day}_available') == 'on'
            
            if is_available and start_time_str and end_time_str:
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                
                availability = Availability(
                    user_id=user.id,
                    day_of_week=day,
                    start_time=start_time,
                    end_time=end_time
                )
                db.session.add(availability)
        
        db.session.commit()
        flash('Availability updated successfully!')
        return redirect(url_for('facilitator.manage_availability'))
    
    # Get current availability
    current_availability = Availability.query.filter_by(user_id=user.id).all()
    availability_dict = {}
    for avail in current_availability:
        availability_dict[avail.day_of_week] = {
            'start_time': avail.start_time.strftime('%H:%M'),
            'end_time': avail.end_time.strftime('%H:%M')
        }
    
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