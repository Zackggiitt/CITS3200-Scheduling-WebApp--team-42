from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Session, Assignment, SwapRequest, UserRole, SwapStatus, FacilitatorSkill, SkillLevel, Unit, Module
from auth import admin_required, get_current_user
from datetime import datetime, time
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Get current user
    user = get_current_user()
    
    # Get statistics for admin dashboard
    total_facilitators = User.query.filter_by(role=UserRole.FACILITATOR).count()
    total_sessions = Session.query.count()
    pending_swaps = SwapRequest.query.filter_by(status=SwapStatus.PENDING).count()
    unassigned_sessions = Session.query.outerjoin(Assignment).filter(Assignment.id == None).count()
    
    return render_template('admin_dashboard.html',
                         user=user,
                         total_facilitators=total_facilitators,
                         total_sessions=total_sessions,
                         pending_swaps=pending_swaps,
                         unassigned_sessions=unassigned_sessions)

@admin_bp.route('/facilitators')
@admin_required
def manage_facilitators():
    user = get_current_user()
    facilitators = User.query.filter_by(role=UserRole.FACILITATOR).all()
    return render_template('manage_facilitators.html', user=user, facilitators=facilitators)

@admin_bp.route('/facilitators/create', methods=['GET', 'POST'])
@admin_required
def create_facilitator():
    user = get_current_user()
    
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        password = request.form['password']
        skill_names = request.form.getlist('skill_names[]')
        skill_levels = request.form.getlist('skill_levels[]')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!')
        else:
            # Create facilitator
            facilitator = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.FACILITATOR,
                password_hash=generate_password_hash(password)
            )
            db.session.add(facilitator)
            db.session.flush()  # Get the ID without committing
            
            # Add skills with levels
            for skill_name, skill_level in zip(skill_names, skill_levels):
                if skill_name.strip():  # Only add non-empty skills
                    facilitator_skill = FacilitatorSkill(
                        facilitator_id=facilitator.id,
                        skill_name=skill_name.strip(),
                        skill_level=SkillLevel(skill_level)
                    )
                    db.session.add(facilitator_skill)
            
            db.session.commit()
            flash('Facilitator created successfully!')
            return redirect(url_for('admin.manage_facilitators'))
    
    return render_template('create_facilitator.html', user=user)

@admin_bp.route('/sessions')
@admin_required
def manage_sessions():
    user = get_current_user()
    sessions = Session.query.all()
    return render_template('manage_sessions.html', user=user, sessions=sessions)

@admin_bp.route('/sessions/create', methods=['GET', 'POST'])
@admin_required
def create_session():
    user = get_current_user()
    
    if request.method == 'POST':
        module_code = request.form['module_code'].strip()
        session_type = request.form['session_type']
        start_time = datetime.fromisoformat(request.form['start_time'])
        end_time = datetime.fromisoformat(request.form['end_time'])
        location = request.form['location'].strip()
        required_skills = request.form.get('required_skills', '').split(',')
        max_facilitators = int(request.form['max_facilitators'])
        
        session = Session(
            module_code=module_code,
            session_type=session_type,
            start_time=start_time,
            end_time=end_time,
            location=location,
            required_skills=json.dumps([skill.strip() for skill in required_skills if skill.strip()]),
            max_facilitators=max_facilitators
        )
        
        db.session.add(session)
        db.session.commit()
        flash('Session created successfully!')
        return redirect(url_for('admin.manage_sessions'))
    
    return render_template('create_session.html', user=user)

@admin_bp.route('/schedule')
@admin_required
def view_schedule():
    user = get_current_user()
    assignments = Assignment.query.join(Session).join(User).all()
    return render_template('view_schedule.html', user=user, assignments=assignments)

@admin_bp.route('/schedule/generate', methods=['POST'])
@admin_required
def generate_schedule():
    from scheduling_engine import generate_optimal_schedule
    
    try:
        # Get all unassigned sessions
        unassigned_sessions = Session.query.outerjoin(Assignment).filter(Assignment.id == None).all()
        
        if not unassigned_sessions:
            flash('No unassigned sessions found!')
            return redirect(url_for('admin.view_schedule'))
        
        # Generate schedule
        assignments = generate_optimal_schedule(unassigned_sessions)
        
        # Save assignments to database
        for assignment in assignments:
            db.session.add(assignment)
        
        db.session.commit()
        flash(f'Schedule generated successfully! {len(assignments)} assignments created.')
        
    except Exception as e:
        flash(f'Error generating schedule: {str(e)}')
    
    return redirect(url_for('admin.view_schedule'))

@admin_bp.route('/swaps')
@admin_required
def manage_swaps():
    user = get_current_user()
    swaps = SwapRequest.query.all()
    return render_template('manage_swaps.html', user=user, swaps=swaps)

@admin_bp.route('/swaps/<int:swap_id>/approve', methods=['POST'])
@admin_required
def approve_swap(swap_id):
    swap = SwapRequest.query.get_or_404(swap_id)
    
    if swap.status != SwapStatus.PENDING:
        flash('Swap request is no longer pending!')
        return redirect(url_for('admin.manage_swaps'))
    
    try:
        # Get the assignments
        requester_assignment = Assignment.query.get(swap.requester_assignment_id)
        target_assignment = Assignment.query.get(swap.target_assignment_id)
        
        # Swap the facilitators
        requester_assignment.facilitator_id, target_assignment.facilitator_id = \
            target_assignment.facilitator_id, requester_assignment.facilitator_id
        
        # Update swap status
        swap.status = SwapStatus.APPROVED
        swap.admin_response = f"Approved by admin on {datetime.now()}"
        
        db.session.commit()
        flash('Swap request approved successfully!')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving swap: {str(e)}')
    
    return redirect(url_for('admin.manage_swaps'))

@admin_bp.route('/swaps/<int:swap_id>/reject', methods=['POST'])
@admin_required
def reject_swap(swap_id):
    user = get_current_user()
    swap_request = SwapRequest.query.get_or_404(swap_id)
    
    swap_request.status = SwapStatus.REJECTED
    swap_request.reviewed_at = datetime.utcnow()
    swap_request.reviewed_by = user.id
    
    db.session.commit()
    flash('Swap request rejected.')
    
    return redirect(url_for('admin.manage_swaps'))

@admin_bp.route('/modules')
@admin_required
def manage_modules():
    user = get_current_user()
    # Get all modules with their associated sessions
    modules = Module.query.all()
    return render_template('manage_modules.html', user=user, modules=modules)

@admin_bp.route('/modules/create', methods=['GET', 'POST'])
@admin_required
def create_module():
    user = get_current_user()
    units = Unit.query.all()
    
    if request.method == 'POST':
        unit_id = int(request.form['unit_id'])
        module_name = request.form['module_name'].strip()
        module_type = request.form['module_type']
        day_of_week = request.form.get('day_of_week', '')
        start_time = request.form.get('start_time', '')
        end_time = request.form.get('end_time', '')
        
        # Validate input
        if not module_name:
            flash('Module name is required!', 'error')
            return render_template('create_module.html', user=user, units=units)
        
        if not unit_id:
            flash('Unit must be selected!', 'error')
            return render_template('create_module.html', user=user, units=units)
        
        # Check if module already exists in this unit
        existing_module = Module.query.filter_by(unit_id=unit_id, module_name=module_name).first()
        if existing_module:
            flash('A module with this name already exists in the selected unit!', 'error')
            return render_template('create_module.html', user=user, units=units)
        
        module = Module(
            unit_id=unit_id,
            module_name=module_name,
            module_type=module_type
        )
        
        db.session.add(module)
        db.session.flush()  # Get the module ID without committing
        
        # Handle timing information if provided
        if day_of_week != '' and start_time and end_time:
            from datetime import datetime, time
            
            # Create datetime objects with today's date and specified times
            today = datetime.today()
            start_hour, start_minute = map(int, start_time.split(':'))
            end_hour, end_minute = map(int, end_time.split(':'))
            
            start_datetime = datetime.combine(today.date(), time(start_hour, start_minute))
            end_datetime = datetime.combine(today.date(), time(end_hour, end_minute))
            
            session = Session(
                module_id=module.id,
                day_of_week=int(day_of_week),
                start_time=start_datetime,
                end_time=end_datetime,
                session_type=module_type
            )
            db.session.add(session)
        
        db.session.commit()
        flash('Module created successfully!', 'success')
        return redirect(url_for('admin.manage_modules'))
    
    return render_template('create_module.html', user=user, units=units)

@admin_bp.route('/modules/<int:module_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_module(module_id):
    user = get_current_user()
    module = Module.query.get_or_404(module_id)
    units = Unit.query.all()
    
    if request.method == 'POST':
        unit_id = int(request.form['unit_id'])
        module_name = request.form['module_name'].strip()
        module_type = request.form['module_type']
        day_of_week = request.form.get('day_of_week', '')
        start_time = request.form.get('start_time', '')
        end_time = request.form.get('end_time', '')
        
        # Validate input
        if not module_name:
            flash('Module name is required!', 'error')
            return render_template('create_module.html', user=user, units=units, module=module)
        
        if not unit_id:
            flash('Unit must be selected!', 'error')
            return render_template('create_module.html', user=user, units=units, module=module)
        
        # Check if another module already exists with this name for this unit
        existing_module = Module.query.filter_by(unit_id=unit_id, module_name=module_name).first()
        if existing_module and existing_module.id != module_id:
            flash('A module with this name already exists in the selected unit!', 'error')
            return render_template('create_module.html', user=user, units=units, module=module)
        
        # Update module information
        module.unit_id = unit_id
        module.module_name = module_name
        module.module_type = module_type
        
        # Handle timing information
        # Get the first session for this module (assuming one-to-one relationship for simplicity)
        session = module.sessions[0] if module.sessions else None
        
        if day_of_week != '' and start_time and end_time:
            # If session exists, update it
            if session:
                # Update day of week
                session.day_of_week = int(day_of_week)
                
                # Update start and end times (keeping today's date but changing time)
                start_hour, start_minute = map(int, start_time.split(':'))
                end_hour, end_minute = map(int, end_time.split(':'))
                
                if session.start_time:
                    start_datetime = session.start_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                    session.start_time = start_datetime
                
                if session.end_time:
                    end_datetime = session.end_time.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
                    session.end_time = end_datetime
            else:
                # Create a new session if none exists
                from datetime import datetime, time
                
                # Create datetime objects with today's date and specified times
                today = datetime.today()
                start_hour, start_minute = map(int, start_time.split(':'))
                end_hour, end_minute = map(int, end_time.split(':'))
                
                start_datetime = datetime.combine(today.date(), time(start_hour, start_minute))
                end_datetime = datetime.combine(today.date(), time(end_hour, end_minute))
                
                session = Session(
                    module_id=module.id,
                    day_of_week=int(day_of_week),
                    start_time=start_datetime,
                    end_time=end_datetime,
                    session_type=module_type
                )
                db.session.add(session)
        elif session:
            # If timing information is removed, delete the session
            db.session.delete(session)
        
        db.session.commit()
        flash('Module updated successfully!', 'success')
        return redirect(url_for('admin.manage_modules'))
    
    return render_template('create_module.html', user=user, units=units, module=module)

@admin_bp.route('/modules/<int:module_id>/delete', methods=['POST'])
@admin_required
def delete_module(module_id):
    user = get_current_user()
    module = Module.query.get_or_404(module_id)
    
    # Delete associated sessions and facilitator skills
    Session.query.filter_by(module_id=module_id).delete()
    FacilitatorSkill.query.filter_by(module_id=module_id).delete()
    
    db.session.delete(module)
    db.session.commit()
    flash('Module deleted successfully!', 'success')
    
    return redirect(url_for('admin.manage_modules'))

@admin_bp.route('/modules/<int:module_id>/details')
@admin_required
def module_details(module_id):
    user = get_current_user()
    module = Module.query.get_or_404(module_id)
    
    # Get facilitators grouped by skill level
    facilitator_skills = FacilitatorSkill.query.filter_by(module_id=module_id).all()
    
    # Group facilitators by skill level
    skill_groups = {
        'proficient': [],
        'leader': [],
        'interested': [],
        'uninterested': []
    }
    
    for fs in facilitator_skills:
        skill_groups[fs.skill_level.value].append(fs.facilitator)
    
    return render_template('module_details.html', user=user, module=module, skill_groups=skill_groups)

@admin_bp.route('/module_details/create', methods=['GET', 'POST'])
@admin_required
def create_module_details():
    user = get_current_user()
    
    if request.method == 'POST':
        # Handle form submission for creating module details
        module_code = request.form['module_code']
        session_type = request.form['session_type']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        location = request.form['location']
        required_skills = request.form.get('required_skills', '')
        max_facilitators = int(request.form.get('max_facilitators', 1))
        
        # Create session (which represents module details)
        session = Session(
            module_code=module_code,
            session_type=session_type,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
            location=location,
            required_skills=required_skills,
            max_facilitators=max_facilitators
        )
        
        db.session.add(session)
        db.session.commit()
        flash('Module details created successfully!', 'success')
        return redirect(url_for('admin.manage_module_details'))
    
    return render_template('create_module_details.html', user=user)