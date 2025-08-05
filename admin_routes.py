from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Session, Assignment, SwapRequest, UserRole, SwapStatus, FacilitatorSkill, SkillLevel
from auth import admin_required, get_current_user
from datetime import datetime
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
    swap = SwapRequest.query.get_or_404(swap_id)
    
    if swap.status != SwapStatus.PENDING:
        flash('Swap request is no longer pending!')
        return redirect(url_for('admin.manage_swaps'))
    
    reason = request.form.get('reason', 'No reason provided')
    
    swap.status = SwapStatus.REJECTED
    swap.admin_response = f"Rejected: {reason}"
    
    db.session.commit()
    flash('Swap request rejected.')
    
    return redirect(url_for('admin.manage_swaps'))