from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, UserRole, Unit, Module, FacilitatorSkill, SkillLevel, Availability, SwapRequest, SwapStatus, Session, Assignment
from werkzeug.security import generate_password_hash
from datetime import datetime, time
from auth import admin_required, get_current_user
from flask_wtf.csrf import validate_csrf
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Add custom template filter for JSON parsing
@admin_bp.app_template_filter('from_json')
def from_json_filter(value):
    if value:
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}

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
    
    # Get facilitator data for the directory
    facilitators = User.query.filter_by(role=UserRole.FACILITATOR).all()
    
    # Calculate additional statistics
    active_facilitators = User.query.filter_by(role=UserRole.FACILITATOR).count()  # All facilitators are considered active
    
    # Calculate experience level distribution
    expert_facilitators = 0
    senior_facilitators = 0
    junior_facilitators = 0
    
    total_hours_worked = 0
    avg_rating = 4.5  # Default value
    
    for facilitator in facilitators:
        # Parse preferences to get additional data
        if facilitator.preferences:
            try:
                import json
                prefs = json.loads(facilitator.preferences)
                experience_level = prefs.get('experience_level', 'junior')
                hourly_rate = prefs.get('hourly_rate', 25)
                
                # Count by experience level
                if experience_level == 'expert':
                    expert_facilitators += 1
                elif experience_level == 'senior':
                    senior_facilitators += 1
                else:
                    junior_facilitators += 1
                    
                # Add to total hours (mock calculation)
                total_hours_worked += hourly_rate * 8  # Assume 8 hours per week
            except:
                junior_facilitators += 1
    
    return render_template('admin_dashboard.html',
                         user=user,
                         total_facilitators=total_facilitators,
                         total_sessions=total_sessions,
                         pending_swaps=pending_swaps,
                         unassigned_sessions=unassigned_sessions,
                         facilitators=facilitators,
                         total_facilitators_count=total_facilitators,
                         active_facilitators_count=active_facilitators,
                         total_hours_worked=total_hours_worked,
                         avg_rating=avg_rating,
                         expert_facilitators=expert_facilitators,
                         senior_facilitators=senior_facilitators,
                         junior_facilitators=junior_facilitators)

@admin_bp.route('/delete-facilitator/<int:facilitator_id>', methods=['DELETE'])
@admin_required
def delete_facilitator(facilitator_id):
    try:
        print(f"Delete request received for facilitator ID: {facilitator_id}")
        
        # Get the facilitator to delete
        facilitator = User.query.get(facilitator_id)
        print(f"Found facilitator: {facilitator}")
        
        if not facilitator:
            print("Facilitator not found")
            return jsonify({'success': False, 'message': 'Facilitator not found'}), 404
        
        if facilitator.role != UserRole.FACILITATOR:
            print(f"Invalid role: {facilitator.role}")
            return jsonify({'success': False, 'message': 'Only facilitators can be deleted via this endpoint'}), 403
        
        # Delete the facilitator from database
        print(f"Deleting facilitator: {facilitator.full_name}")
        db.session.delete(facilitator)
        db.session.commit()
        print("Facilitator deleted successfully")
        
        return jsonify({'success': True, 'message': 'Facilitator account deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting facilitator: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the facilitator'}), 500

@admin_bp.route('/create-facilitator-modal', methods=['POST'])
@admin_required
def create_facilitator_modal():
    """Create a new facilitator from the admin dashboard modal"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['fullName', 'email', 'phone', 'role', 'experienceLevel', 'hourlyRate']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Determine user role based on form data
        role_mapping = {
            'lab_facilitator': UserRole.FACILITATOR,
            'senior_facilitator': UserRole.FACILITATOR,
            'lead_facilitator': UserRole.FACILITATOR
        }
        
        user_role = role_mapping.get(data['role'], UserRole.FACILITATOR)
        
        # Parse full name into first and last name
        full_name = data['fullName'].strip()
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create new user (only using fields that exist in the model)
        new_user = User(
            email=data['email'],
            first_name=first_name,
            last_name=last_name,
            role=user_role,
            # Generate a temporary password (user will need to reset)
            password_hash=generate_password_hash('temp_password_123')
        )
        
        # Store additional data in preferences field as JSON
        additional_data = {
            'phone': data['phone'],
            'hourly_rate': float(data['hourlyRate']),
            'experience_level': data['experienceLevel'],
            'position': data.get('position', ''),
            'department': data.get('department', ''),
            'status': data.get('status', 'active')
        }
        new_user.preferences = json.dumps(additional_data)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Facilitator created successfully!',
            'user_id': new_user.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/units/create', methods=['GET', 'POST'])
@admin_required
def create_unit():
    user = get_current_user()
    
    if request.method == 'POST':
        unit_code = request.form['unit_code'].strip().upper()
        unit_name = request.form['unit_name'].strip()
        
        if Unit.query.filter_by(unit_code=unit_code).first():
            flash('Unit code already exists!')
        else:
            unit = Unit(unit_code=unit_code, unit_name=unit_name)
            db.session.add(unit)
            db.session.commit()
            flash('Unit created successfully!')
            return redirect(url_for('admin.manage_units'))
    
    return render_template('create_unit.html', user=user)

@admin_bp.route('/initialize-sample-modules')
@admin_required
def initialize_sample_modules():
    """Initialize sample modules and sessions by running add_sample_sessions.py"""
    user = get_current_user()
    
    try:
        # Import and run the add_sample_sessions script
        from add_sample_sessions import add_sample_sessions
        
        # Run the function to add sample sessions
        add_sample_sessions()
        
        flash('Successfully initialized sample modules and sessions from add_sample_sessions.py! ')
        
    except Exception as e:
        flash(f'Error running add_sample_sessions.py: {str(e)}')
    
    return redirect(url_for('admin.manage_modules'))

@admin_bp.route('/facilitators/create', methods=['GET', 'POST'])
@admin_required
def create_facilitator():
    user = get_current_user()
    
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        password = request.form['password']
        min_hours = int(request.form.get('min_hours', 0))
        max_hours = int(request.form.get('max_hours', 20))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!')
        else:
            # Create facilitator
            facilitator = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.FACILITATOR,
                password_hash=generate_password_hash(password),
                min_hours=min_hours,
                max_hours=max_hours
            )
            db.session.add(facilitator)
            db.session.flush()  # Get the ID without committing
            
            # Add module skills
            modules = Module.query.all()
            for module in modules:
                skill_level_value = request.form.get(f'skill_{module.id}')
                if skill_level_value:
                    facilitator_skill = FacilitatorSkill(
                        facilitator_id=facilitator.id,
                        module_id=module.id,
                        skill_level=SkillLevel(skill_level_value)
                    )
                    db.session.add(facilitator_skill)
            
            # Add availability slots
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
            
            for day_idx in range(5):
                for hour in hours:
                    field_name = f'available_{day_idx}_{hour.replace(":", "")}'
                    if request.form.get(field_name):
                        availability = Availability(
                            user_id=facilitator.id,
                            day_of_week=day_idx,
                            start_time=datetime.strptime(hour, '%H:%M').time(),
                            end_time=datetime.strptime(hour, '%H:%M').time(),
                            is_available=True
                        )
                        db.session.add(availability)
            
            db.session.commit()
            flash('Facilitator created successfully with skills and availability!')
            return redirect(url_for('admin.manage_facilitators'))
    
    # Get modules for the form
    modules = Module.query.all()
    return render_template('create_facilitator.html', user=user, modules=modules)

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

@admin_bp.route('/schedule/generate', methods=['GET', 'POST'])
@admin_required
def generate_schedule():
    """
    New optimization engine - Phase 2: Real facilitator data integration
    Uses real facilitators from database with dummy session data
    """
    user = get_current_user()
    
    if request.method == 'POST':
        try:
            # Import the optimization engine
            from optimization_engine import generate_optimal_assignments, calculate_metrics, format_session_time, prepare_facilitator_data
            from models import User, UserRole
            
            # Get facilitators from database
            facilitators_from_db = User.query.filter_by(role=UserRole.FACILITATOR).all()
            facilitators = prepare_facilitator_data(facilitators_from_db)
            
            # Generate assignments using real facilitator data
            assignments, conflicts = generate_optimal_assignments(facilitators)
            
            # Format results for template
            formatted_assignments = []
            for assignment in assignments:
                formatted_assignments.append({
                    'facilitator': assignment['facilitator']['name'],
                    'module': assignment['session']['module_name'],
                    'time': format_session_time(assignment['session']),
                    'score': round(assignment['score'], 2),
                    'location': assignment['session']['location']
                })
            
            # Calculate metrics
            metrics = calculate_metrics(assignments)
            
            # Create results structure
            results = {
                'success': len(assignments) > 0,
                'assignments_made': len(assignments),
                'conflicts': conflicts if conflicts else ['No conflicts found'],
                'message': f'Phase 2: Generated {len(assignments)} assignments using real facilitator data! 🚀',
                'assignments': formatted_assignments,
                'metrics': metrics
            }
            
            # Flash appropriate message
            if results['success']:
                flash(results['message'], 'success')
            else:
                flash('No assignments could be generated. Check facilitator availability and skills.', 'warning')
            
            return render_template('schedule_results.html', user=user, results=results)
            
        except Exception as e:
            # Handle any errors gracefully
            error_message = f"Error generating schedule: {str(e)}"
            flash(error_message, 'error')
            
            # Return dummy results as fallback
            fallback_results = {
                'success': False,
                'assignments_made': 0,
                'conflicts': [error_message],
                'message': 'Schedule generation failed - check logs',
                'assignments': []
            }
            return render_template('schedule_results.html', user=user, results=fallback_results)
    
    # GET request - show the generation form/page
    return render_template('generate_schedule.html', user=user)

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
        try:
            validate_csrf(request.form.get('csrf_token'))
        except:
            flash('CSRF token validation failed. Please try again.', 'error')
            return render_template('edit_module.html', user=user, units=units, module=module)
        unit_id = int(request.form['unit_id'])
        module_name = request.form['module_name'].strip()
        module_type = request.form['module_type']
        day_of_week = request.form.get('day_of_week', '')
        start_time = request.form.get('start_time', '')
        end_time = request.form.get('end_time', '')
        
        # Validate input
        if not module_name:
            flash('Module name is required!', 'error')
            return render_template('edit_module.html', user=user, units=units, module=module)
        
        if not unit_id:
            flash('Unit must be selected!', 'error')
            return render_template('edit_module.html', user=user, units=units, module=module)
        
        # Check if another module already exists with this name for this unit
        existing_module = Module.query.filter_by(unit_id=unit_id, module_name=module_name).first()
        if existing_module and existing_module.id != module_id:
            flash('A module with this name already exists in the selected unit!', 'error')
            return render_template('edit_module.html', user=user, units=units, module=module)
        
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
    
    return render_template('edit_module.html', user=user, units=units, module=module)

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

@admin_bp.route('/facilitators')
@admin_required
def manage_facilitators():
    """
    Phase 2.5: Manage facilitators - list all facilitators with edit capabilities
    """
    user = get_current_user()
    
    # Get all facilitators with their skills and availability
    facilitators = User.query.filter_by(role=UserRole.FACILITATOR).all()
    
    # Get all modules for skill management
    modules = Module.query.all()
    
    # Prepare facilitator data with skills and availability summary
    facilitator_data = []
    for facilitator in facilitators:
        # Count skills
        skills_count = FacilitatorSkill.query.filter_by(facilitator_id=facilitator.id).count()
        
        # Count availability slots
        availability_count = Availability.query.filter_by(user_id=facilitator.id, is_available=True).count()
        
        facilitator_data.append({
            'facilitator': facilitator,
            'skills_count': skills_count,
            'availability_count': availability_count,
            'total_modules': len(modules)
        })
    
    return render_template('manage_facilitators.html', 
                         user=user, 
                         facilitator_data=facilitator_data,
                         modules=modules)

@admin_bp.route('/facilitators/<int:facilitator_id>/edit')
@admin_required
def edit_facilitator(facilitator_id):
    """
    Edit individual facilitator - availability and module skills
    """
    user = get_current_user()
    facilitator = User.query.get_or_404(facilitator_id)
    
    if facilitator.role != UserRole.FACILITATOR:
        flash('User is not a facilitator!', 'error')
        return redirect(url_for('admin.manage_facilitators'))
    
    # Get all modules
    modules = Module.query.all()
    
    # Get facilitator's current skills
    current_skills = {}
    for skill in facilitator.facilitator_skills:
        current_skills[skill.module_id] = skill.skill_level
    
    # Get facilitator's availability
    availability_slots = Availability.query.filter_by(user_id=facilitator_id).all()
    
    return render_template('edit_facilitator.html',
                         user=user,
                         facilitator=facilitator,
                         modules=modules,
                         current_skills=current_skills,
                         availability_slots=availability_slots,
                         skill_levels=SkillLevel)

@admin_bp.route('/facilitators/<int:facilitator_id>/update-basic', methods=['POST'])
@admin_required
def update_facilitator_basic(facilitator_id):
    """Update facilitator basic info (min/max hours)"""
    facilitator = User.query.get_or_404(facilitator_id)
    
    min_hours = request.form.get('min_hours', type=int)
    max_hours = request.form.get('max_hours', type=int)
    
    facilitator.min_hours = min_hours
    facilitator.max_hours = max_hours
    
    db.session.commit()
    flash('Basic information updated successfully!', 'success')
    return redirect(url_for('admin.edit_facilitator', facilitator_id=facilitator_id))

@admin_bp.route('/facilitators/<int:facilitator_id>/update-skills', methods=['POST'])
@admin_required
def update_facilitator_skills(facilitator_id):
    """Update facilitator module skills"""
    facilitator = User.query.get_or_404(facilitator_id)
    modules = Module.query.all()
    
    # Clear existing skills
    FacilitatorSkill.query.filter_by(facilitator_id=facilitator_id).delete()
    
    # Add new skills
    for module in modules:
        skill_value = request.form.get(f'skill_{module.id}')
        if skill_value:
            skill_level = SkillLevel(skill_value)
            facilitator_skill = FacilitatorSkill(
                facilitator_id=facilitator_id,
                module_id=module.id,
                skill_level=skill_level
            )
            db.session.add(facilitator_skill)
    
    db.session.commit()
    flash('Module skills updated successfully!', 'success')
    return redirect(url_for('admin.edit_facilitator', facilitator_id=facilitator_id))

@admin_bp.route('/facilitators/<int:facilitator_id>/update-availability', methods=['POST'])
@admin_required
def update_facilitator_availability(facilitator_id):
    """Update facilitator availability schedule"""
    facilitator = User.query.get_or_404(facilitator_id)
    
    # Clear existing availability
    Availability.query.filter_by(user_id=facilitator_id).delete()
    
    # Add new availability slots
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
    
    for day_idx in range(5):
        for hour in hours:
            checkbox_name = f'available_{day_idx}_{hour.replace(":", "")}'
            if request.form.get(checkbox_name):
                # Create availability slot
                start_time = datetime.strptime(hour, '%H:%M').time()
                end_time = datetime.strptime(f'{int(hour[:2])+1:02d}:00', '%H:%M').time()
                
                availability = Availability(
                    user_id=facilitator_id,
                    day_of_week=day_idx,
                    start_time=start_time,
                    end_time=end_time,
                    is_available=True
                )
                db.session.add(availability)
    
    db.session.commit()
    flash('Availability updated successfully!', 'success')
    return redirect(url_for('admin.edit_facilitator', facilitator_id=facilitator_id))