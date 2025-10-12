from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, UserRole, Unit, Module, FacilitatorSkill, SkillLevel, SwapRequest, SwapStatus, Session, Assignment, UnitFacilitator, Unavailability, RecurringPattern
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
    
    # Get the tab parameter from URL
    tab = request.args.get('tab', 'dashboard')
    
    # Get statistics for admin dashboard
    total_facilitators = User.query.filter_by(role=UserRole.FACILITATOR).count()
    total_sessions = Session.query.count()
    pending_swaps = SwapRequest.query.filter_by(status=SwapStatus.PENDING).count()
    unassigned_sessions = Session.query.outerjoin(Assignment).filter(Assignment.id == None).count()
    
    # Get all employees data for the directory
    facilitators = User.query.filter(User.role.in_([UserRole.FACILITATOR, UserRole.UNIT_COORDINATOR, UserRole.ADMIN])).all()
    
    # Count admins to check if we can delete the last one
    admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
    
    
    # Calculate additional statistics
    active_facilitators = User.query.filter_by(role=UserRole.FACILITATOR).count()  # Keep facilitator count for compatibility
    
    # Calculate unit status distribution based on session dates
    from datetime import datetime, date
    from sqlalchemy import func
    
    today = date.today()
    
    # Get all units with their session date ranges
    units_with_dates = (
        db.session.query(
            Unit.id,
            func.min(Session.start_time).label('first_session'),
            func.max(Session.start_time).label('last_session'),
            func.count(Session.id).label('session_count')
        )
        .outerjoin(Module, Module.unit_id == Unit.id)
        .outerjoin(Session, Session.module_id == Module.id)
        .group_by(Unit.id)
        .all()
    )
    
    # Initialize counters
    active_units_count = 0
    upcoming_units_count = 0
    completed_units_count = 0
    
    for unit_data in units_with_dates:
        if unit_data.session_count == 0:
            # Units with no sessions are considered upcoming
            upcoming_units_count += 1
        else:
            first_session_date = unit_data.first_session.date() if unit_data.first_session else None
            last_session_date = unit_data.last_session.date() if unit_data.last_session else None
            
            if first_session_date and last_session_date:
                if last_session_date < today:
                    # All sessions are in the past - completed
                    completed_units_count += 1
                elif first_session_date > today:
                    # All sessions are in the future - upcoming
                    upcoming_units_count += 1
                else:
                    # Some sessions in past, some in future - active
                    active_units_count += 1
            else:
                # Units with incomplete date information are considered upcoming
                upcoming_units_count += 1
    
    # Calculate average sessions per unit and total sessions completed
    avg_sessions_per_unit = db.session.query(func.avg(
        db.session.query(func.count(Session.id))
        .join(Module, Module.id == Session.module_id)
        .join(Unit, Unit.id == Module.unit_id)
        .group_by(Unit.id)
        .subquery().c.count
    )).scalar() or 0
    
    total_sessions_completed = (
        db.session.query(func.count(Session.id))
        .join(Module, Module.id == Session.module_id)
        .join(Unit, Unit.id == Module.unit_id)
        .filter(func.date(Session.start_time) < today)
        .scalar() or 0
    )
    
    # Calculate experience level distribution
    expert_facilitators = 0
    senior_facilitators = 0
    junior_facilitators = 0
    
    total_hours_worked = 0
    avg_rating = 4.5  # Default value
    
    for employee in facilitators:
        # Parse preferences to get additional data
        if employee.preferences:
            try:
                import json
                prefs = json.loads(employee.preferences)
                
                # Only count experience level for facilitators
                if employee.role == UserRole.FACILITATOR:
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
                else:
                    # For unit coordinators and admins, default to junior for now
                    junior_facilitators += 1
            except:
                # Count as junior for error cases (maintains compatibility)
                junior_facilitators += 1
    
    return render_template('admin_dashboard.html',
                         user=user,
                         tab=tab,  # Pass the tab parameter to template
                         total_facilitators=total_facilitators,
                         total_sessions=total_sessions,
                         pending_swaps=pending_swaps,
                         unassigned_sessions=unassigned_sessions,
                         facilitators=facilitators,  # This variable now contains all employees
                         all_employees=facilitators,  # Explicit alias for clarity
                         total_facilitators_count=total_facilitators,
                         active_facilitators_count=active_facilitators,
                         total_hours_worked=total_hours_worked,
                         avg_rating=avg_rating,
                         expert_facilitators=expert_facilitators,
                         senior_facilitators=senior_facilitators,
                         junior_facilitators=junior_facilitators,
                         admin_count=admin_count,
                         # Unit status metrics based on session dates
                         active_units_count=active_units_count,
                         upcoming_units_count=upcoming_units_count,
                         completed_units_count=completed_units_count,
                         avg_sessions_per_unit=round(avg_sessions_per_unit, 1) if avg_sessions_per_unit else 0,
                         total_sessions_completed=total_sessions_completed)

@admin_bp.route('/delete-employee/<int:employee_id>', methods=['DELETE'])
@admin_required
def delete_employee(employee_id):
    """Delete a user (facilitator, unit coordinator, or admin) account"""
    try:
        print(f"Delete request received for employee ID: {employee_id}")
        
        # Get the employee to delete
        employee = User.query.get(employee_id)
        print(f"Found employee: {employee}")
        
        if not employee:
            print("User not found")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        
        # Delete the user from database
        employee_name = employee.full_name if employee else 'Unknown'
        print(f"Deleting user: {employee_name} (Role: {employee.role})")
        
        db.session.delete(employee)
        db.session.commit()
        print("User deleted successfully")
        
        # Get position name for success message
        position_mapping = {
            UserRole.FACILITATOR: 'Facilitator',
            UserRole.UNIT_COORDINATOR: 'Unit Coordinator', 
            UserRole.ADMIN: 'Admin'
        }
        position_name = position_mapping.get(employee.role, 'User')
        
        return jsonify({'success': True, 'message': f'{position_name} account deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the user'}), 500

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

@admin_bp.route('/update-employee', methods=['PUT'])
@admin_required
def update_employee():
    """Update a user (facilitator, unit coordinator, or admin) information"""
    try:
        data = request.get_json()
        print(f"Update user request received: {data}")
        print(f"User ID from request: {data.get('employeeId')}")
        
        # Get the user to update
        employee_id = data.get('employeeId')
        if not employee_id:
            return jsonify({'success': False, 'error': 'User ID is required'}), 400
            
        employee = User.query.get(employee_id)
        print(f"Found user: {employee}")
        if not employee:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Validate required fields
        if not data.get('fullName'):
            return jsonify({'success': False, 'error': 'Full name is required'}), 400
        if not data.get('email'):
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        if not data.get('phone'):
            return jsonify({'success': False, 'error': 'Phone is required'}), 400
        if not data.get('position'):
            return jsonify({'success': False, 'error': 'Position is required'}), 400
        
        # If position is facilitator, validate role
        print(f"Position: {data.get('position')}")
        if data.get('position') == 'facilitator':
            print(f"Position is facilitator, checking role: {data.get('role')}")
            if not data.get('role'):
                return jsonify({'success': False, 'error': 'Role is required when position is facilitator'}), 400
        
        # Update basic fields
        if data.get('fullName'):
            # Parse full name into first and last name
            name_parts = data['fullName'].strip().split(' ', 1)
            employee.first_name = name_parts[0]
            employee.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if data.get('email'):
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != employee.id:
                return jsonify({'success': False, 'error': 'Email already exists'}), 400
            employee.email = data['email']
        
        # Update user role if position changed
        role_mapping = {
            'facilitator': UserRole.FACILITATOR,
            'unit_coordinator': UserRole.UNIT_COORDINATOR,
            'admin': UserRole.ADMIN
        }
        
        new_role = role_mapping.get(data['position'], employee.role)
        employee.role = new_role
        
        # Update preferences (JSON field)
        import json
        
        preferences = {}
        if employee.preferences:
            try:
                preferences = json.loads(employee.preferences)
            except (json.JSONDecodeError, TypeError):
                preferences = {}
        
        # Update preference fields that all employees have
        preferences['phone'] = data['phone']
        preferences['position'] = data['position']
        preferences['status'] = data.get('status', 'active')
        
        # Add role-specific data based on position
        if data['position'] == 'facilitator':
            if data.get('role'):
                preferences['role'] = data['role']
        elif data['position'] == 'unit_coordinator':
            preferences['admin_level'] = 'coordinator'
        elif data['position'] == 'admin':
            preferences['admin_level'] = 'system_admin'
        
        employee.preferences = json.dumps(preferences)
        
        # Save changes
        db.session.commit()
        
        print(f"Updated user: {employee.email} with role: {employee.role}")
        
        return jsonify({
            'success': True, 
            'message': 'User updated successfully',
            'employee_id': employee.id,
            'email': employee.email,
            'position': data['position']
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating user: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'An error occurred while updating the user: {str(e)}'}), 500

@admin_bp.route('/update-facilitator', methods=['PUT'])
@admin_required
def update_facilitator():
    try:
        data = request.get_json()
        print(f"Update request received: {data}")
        
        # Get the facilitator to update
        facilitator = User.query.get(data.get('employeeId'))
        if not facilitator:
            return jsonify({'success': False, 'error': 'Facilitator not found'}), 404
        
        if facilitator.role != UserRole.FACILITATOR:
            return jsonify({'success': False, 'error': 'Only facilitators can be updated via this endpoint'}), 403
        
        # Update basic fields
        if data.get('fullName'):
            # Parse full name into first and last name
            name_parts = data['fullName'].strip().split(' ', 1)
            facilitator.first_name = name_parts[0]
            facilitator.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if data.get('email'):
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != facilitator.id:
                return jsonify({'success': False, 'error': 'Email already exists'}), 400
            facilitator.email = data['email']
        
        # Update preferences (JSON field)
        import json
        
        preferences = {}
        if facilitator.preferences:
            try:
                preferences = json.loads(facilitator.preferences)
            except (json.JSONDecodeError, TypeError):
                preferences = {}
        
        # Update preference fields
        if data.get('phone'):
            preferences['phone'] = data['phone']
        if data.get('hourlyRate'):
            preferences['hourly_rate'] = float(data['hourlyRate'])
        if data.get('experienceLevel'):
            preferences['experience_level'] = data['experienceLevel']
        if data.get('position'):
            preferences['position'] = data['position']
        if data.get('department'):
            preferences['department'] = data['department']
        if data.get('status'):
            preferences['status'] = data['status']
        
        # Save updated preferences
        facilitator.preferences = json.dumps(preferences)
        
        # Commit changes
        db.session.commit()
        print(f"Facilitator {facilitator.full_name} updated successfully")
        
        return jsonify({'success': True, 'message': 'Facilitator updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating facilitator: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while updating the facilitator'}), 500

@admin_bp.route('/send-reset-link', methods=['POST'])
@admin_required
def send_reset_link():
    try:
        data = request.get_json()
        print(f"Send reset link request received: {data}")
        
        # Get the facilitator
        facilitator = User.query.get(data.get('employeeId'))
        if not facilitator:
            return jsonify({'success': False, 'message': 'Facilitator not found'}), 404
        
        if facilitator.role != UserRole.FACILITATOR:
            return jsonify({'success': False, 'message': 'Only facilitators can use this endpoint'}), 403
        
        # TODO: Implement actual email sending logic here
        # For now, just return success
        print(f"Reset link would be sent to {facilitator.email}")
        
        return jsonify({'success': True, 'message': f'Password reset link sent to {facilitator.email}'})
        
    except Exception as e:
        print(f"Error sending reset link: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while sending the reset link'}), 500

@admin_bp.route('/admin-reset-password', methods=['POST'])
@admin_required
def admin_reset_password():
    try:
        data = request.get_json()
        print(f"Admin reset password request received: {data}")
        
        # Get the facilitator
        facilitator = User.query.get(data.get('employeeId'))
        if not facilitator:
            return jsonify({'success': False, 'message': 'Facilitator not found'}), 404
        
        if facilitator.role != UserRole.FACILITATOR:
            return jsonify({'success': False, 'message': 'Only facilitators can use this endpoint'}), 403
        
        # Hash the new password
        from werkzeug.security import generate_password_hash
        new_password = data.get('newPassword')
        if not new_password or len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'}), 400
        
        facilitator.password_hash = generate_password_hash(new_password)
        
        # Commit changes
        db.session.commit()
        print(f"Password reset successfully for {facilitator.full_name}")
        
        return jsonify({'success': True, 'message': f'Password reset successfully for {facilitator.full_name}'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error resetting password: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while resetting the password'}), 500

@admin_bp.route('/create-employee', methods=['POST'])
@admin_required
def create_employee():
    """Create a new user (facilitator, unit coordinator, or admin) from the admin dashboard modal"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['fullName', 'email', 'phone', 'position']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # If position is facilitator, validate role
        if data.get('position') == 'facilitator':
            if not data.get('role'):
                return jsonify({'success': False, 'error': 'Role is required when position is facilitator'}), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Determine user role based on position
        role_mapping = {
            'facilitator': UserRole.FACILITATOR,
            'unit_coordinator': UserRole.UNIT_COORDINATOR,
            'admin': UserRole.ADMIN
        }
        
        user_role = role_mapping.get(data['position'], UserRole.FACILITATOR)
        
        # Parse full name into first and last name
        full_name = data['fullName'].strip()
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create new user
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
            'position': data['position'],
            'status': data.get('status', 'active')
        }
        
        # Add role-specific data based on position
        if data['position'] == 'facilitator':
            if data.get('role'):
                additional_data['role'] = data['role']
            additional_data['experience_level'] = data.get('experienceLevel', 'junior')
            additional_data['hourly_rate'] = data.get('hourlyRate', 25)
            additional_data['department'] = data.get('department', 'general')
        elif data['position'] == 'unit_coordinator':
            additional_data['department'] = data.get('department', 'academic')
            additional_data['admin_level'] = 'coordinator'
        elif data['position'] == 'admin':
            additional_data['admin_level'] = 'system_admin'
        
        new_user.preferences = json.dumps(additional_data)
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        # TODO: Send welcome email with temporary password
        position_name = data['position'].replace('_', ' ').title()
        print(f"Created new {position_name}: {new_user.email} with role: {user_role}")
        
        return jsonify({
            'success': True, 
            'message': f'{position_name} created successfully! They will receive login credentials via email.',
            'employee_id': new_user.id,
            'email': new_user.email,
            'position': position_name
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating user: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while creating the user'}), 500

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
            
            # Add availability slots (deprecated)
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
            
            for day_idx in range(5):
                for hour in hours:
                    field_name = f'available_{day_idx}_{hour.replace(":", "")}'
                    if request.form.get(field_name):
                        # Deprecated: Availability model removed. Use date-based Unavailability instead.
                        pass
            
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
        
        # Count unavailability entries
        availability_count = Unavailability.query.filter_by(user_id=facilitator.id).count()
        
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

@admin_bp.route('/facilitators/<int:facilitator_id>/profile')
@admin_required
def facilitator_profile(facilitator_id):
    """View a specific facilitator's profile"""
    user = get_current_user()
    
    # Get facilitator from User table
    facilitator = User.query.get_or_404(facilitator_id)
    
    if facilitator.role != UserRole.FACILITATOR:
        flash('User is not a facilitator!', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Calculate stats
    stats = {
        'units_assigned': 0,
        'pending_approvals': 0,
        'total_sessions': 0,
        'skills_count': 0,
        'availability_status': 'Not Set'
    }
    
    try:
        # Count units assigned to this facilitator
        stats['units_assigned'] = db.session.query(UnitFacilitator).filter_by(user_id=facilitator.id).count()
        
        # Count pending swap requests
        stats['pending_approvals'] = SwapRequest.query.filter_by(
            requested_by=facilitator.id, 
            status=SwapStatus.PENDING
        ).count()
        
        # Count total sessions assigned
        stats['total_sessions'] = Assignment.query.filter_by(facilitator_id=facilitator.id).count()
        
        # Count skills registered
        stats['skills_count'] = FacilitatorSkill.query.filter_by(facilitator_id=facilitator.id).count()
        
        # Check unavailability status (treat as configured if any entries exist)
        has_unavailability = Unavailability.query.filter_by(user_id=facilitator.id).first()
        stats['availability_status'] = 'Configured' if has_unavailability else 'Not Set'
        
    except Exception as e:
        print(f"Error calculating stats: {e}")
    
    return render_template('admin/facilitator_profile.html', 
                         facilitator=facilitator,
                         stats=stats)

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
    
    # Get facilitator's unavailability list (returned under same var name for template compatibility)
    availability_slots = Unavailability.query.filter_by(user_id=facilitator_id).all()
    
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
    
    # Clear existing unavailability for this facilitator
    Unavailability.query.filter_by(user_id=facilitator_id).delete()
    
    # Add new unavailability slots
    for key in request.form:
        if key.startswith('unavailable_'):
            date_str = key.split('_')[1]
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            unavailability = Unavailability(
                user_id=facilitator_id,
                date=date            )
            db.session.add(unavailability)

    db.session.commit()
    flash('Unavailability slots updated successfully!', 'success')
    return redirect(url_for('admin.edit_facilitator', facilitator_id=facilitator_id))


# -------------------------- Unavailability (Admin) --------------------------
@admin_bp.get('/unavailability')
@admin_required
def admin_list_unavailability():
    """List unavailability across users. Filters: user_id, unit_id, start, end (YYYY-MM-DD)."""
    user_id = request.args.get('user_id', type=int)
    unit_id = request.args.get('unit_id', type=int)
    start = request.args.get('start')
    end = request.args.get('end')

    q = Unavailability.query
    if user_id:
        q = q.filter(Unavailability.user_id == user_id)
    if unit_id:
        q = q.filter(Unavailability.unit_id == unit_id)
    try:
        if start:
            start_d = datetime.strptime(start, '%Y-%m-%d').date()
            q = q.filter(Unavailability.date >= start_d)
        if end:
            end_d = datetime.strptime(end, '%Y-%m-%d').date()
            q = q.filter(Unavailability.date <= end_d)
    except ValueError:
        return jsonify({'ok': False, 'error': 'Invalid date format; use YYYY-MM-DD'}), 400

    rows = q.order_by(Unavailability.date.asc(), Unavailability.start_time.asc().nulls_first()).all()

    def serialize(u: Unavailability):
        owner = User.query.get(u.user_id)
        unit = Unit.query.get(u.unit_id) if u.unit_id else None
        return {
            'id': u.id,
            'user_id': u.user_id,
            'user': f"{owner.first_name} {owner.last_name}".strip() if owner else None,
            'unit_id': u.unit_id,
            'unit': f"{unit.unit_code} {unit.unit_name}" if unit else None,
            'date': u.date.isoformat(),
            'is_full_day': bool(u.is_full_day),
            'start_time': u.start_time.isoformat() if u.start_time else None,
            'end_time': u.end_time.isoformat() if u.end_time else None,
            'recurring_pattern': u.recurring_pattern.value if u.recurring_pattern else None,
            'recurring_interval': u.recurring_interval,
            'recurring_end_date': u.recurring_end_date.isoformat() if u.recurring_end_date else None,
            'reason': u.reason or ''
        }

    return jsonify({'ok': True, 'items': [serialize(r) for r in rows]})


def _parse_hhmm(val: str):
    if not val:
        return None
    try:
        hh, mm = map(int, val.split(':', 1))
        return time(hh, mm)
    except Exception:
        return None


@admin_bp.post('/unavailability')
@admin_required
def admin_create_unavailability():
    """Create an unavailability record for any user."""
    data = request.get_json(silent=True) or {}

    user_id = data.get('user_id')
    unit_id = data.get('unit_id')
    date_str = data.get('date')
    is_full_day = bool(data.get('is_full_day'))
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    recurring = (data.get('recurring_pattern') or None)
    recurring_interval = int(data.get('recurring_interval') or 1)
    recurring_end_str = data.get('recurring_end_date')
    reason = (data.get('reason') or '').strip()

    if not user_id:
        return jsonify({'ok': False, 'error': 'user_id is required'}), 400
    owner = User.query.get(int(user_id))
    if not owner:
        return jsonify({'ok': False, 'error': 'User not found'}), 404

    unit = None
    if unit_id:
        unit = Unit.query.get(int(unit_id))
        if not unit:
            return jsonify({'ok': False, 'error': 'Unit not found'}), 404

    try:
        the_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid date; use YYYY-MM-DD'}), 400

    st = _parse_hhmm(start_time_str)
    et = _parse_hhmm(end_time_str)
    if not is_full_day:
        if not (st and et):
            return jsonify({'ok': False, 'error': 'start_time and end_time required unless is_full_day true'}), 400
        if st >= et:
            return jsonify({'ok': False, 'error': 'start_time must be before end_time'}), 400
    else:
        st = None
        et = None

    rp = None
    red = None
    if recurring:
        try:
            rp = RecurringPattern(recurring)
        except Exception:
            return jsonify({'ok': False, 'error': 'Invalid recurring_pattern; use daily|weekly|monthly|custom'}), 400
        if recurring_end_str:
            try:
                red = datetime.strptime(recurring_end_str, '%Y-%m-%d').date()
            except Exception:
                return jsonify({'ok': False, 'error': 'Invalid recurring_end_date; use YYYY-MM-DD'}), 400

    try:
        u = Unavailability(
            user_id=owner.id,
            unit_id=unit.id if unit else None,
            date=the_date,
            is_full_day=is_full_day,
            start_time=st,
            end_time=et,
            recurring_pattern=rp,
            recurring_interval=recurring_interval,
            recurring_end_date=red,
            reason=reason or None,
        )
        db.session.add(u)
        db.session.commit()
        return jsonify({'ok': True, 'id': u.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': f'Failed to create: {e}'}), 500


@admin_bp.put('/unavailability/<int:item_id>')
@admin_required
def admin_update_unavailability(item_id):
    u = Unavailability.query.get(item_id)
    if not u:
        return jsonify({'ok': False, 'error': 'Not found'}), 404

    data = request.get_json(silent=True) or {}

    if 'user_id' in data:
        new_user = User.query.get(int(data['user_id']))
        if not new_user:
            return jsonify({'ok': False, 'error': 'User not found'}), 404
        u.user_id = new_user.id
    if 'unit_id' in data:
        new_unit = Unit.query.get(int(data['unit_id']))
        if not new_unit:
            return jsonify({'ok': False, 'error': 'Unit not found'}), 404
        u.unit_id = new_unit.id
    if 'date' in data:
        try:
            u.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except Exception:
            return jsonify({'ok': False, 'error': 'Invalid date'}), 400
    if 'is_full_day' in data:
        u.is_full_day = bool(data['is_full_day'])
        if u.is_full_day:
            u.start_time = None
            u.end_time = None
    if 'start_time' in data:
        u.start_time = _parse_hhmm(data['start_time']) if data['start_time'] else None
    if 'end_time' in data:
        u.end_time = _parse_hhmm(data['end_time']) if data['end_time'] else None
    if 'recurring_pattern' in data:
        v = data['recurring_pattern']
        u.recurring_pattern = RecurringPattern(v) if v else None
    if 'recurring_interval' in data:
        u.recurring_interval = int(data['recurring_interval'] or 1)
    if 'recurring_end_date' in data:
        v = data['recurring_end_date']
        u.recurring_end_date = datetime.strptime(v, '%Y-%m-%d').date() if v else None
    if 'reason' in data:
        u.reason = (data['reason'] or '').strip() or None

    if not u.is_full_day and (u.start_time is None or u.end_time is None or u.start_time >= u.end_time):
        return jsonify({'ok': False, 'error': 'Invalid time range'}), 400

    try:
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': f'Failed to update: {e}'}), 500


@admin_bp.delete('/unavailability/<int:item_id>')
@admin_required
def admin_delete_unavailability(item_id):
    u = Unavailability.query.get(item_id)
    if not u:
        return jsonify({'ok': False, 'error': 'Not found'}), 404
    try:
        db.session.delete(u)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': f'Failed to delete: {e}'}), 500

