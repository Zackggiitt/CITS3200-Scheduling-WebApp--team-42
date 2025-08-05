from models import db, User, Session, Assignment, Availability, UserRole
from datetime import datetime, timedelta
import json

def generate_optimal_schedule():
    """
    Generate optimal schedule based on facilitator availability, skills, and preferences.
    This is a simplified version - in production, you'd use more sophisticated algorithms.
    """
    try:
        # Clear existing assignments
        Assignment.query.delete()
        
        # Get all unassigned sessions
        sessions = Session.query.all()
        facilitators = User.query.filter_by(role=UserRole.FACILITATOR).all()
        
        assignments_made = 0
        conflicts = []
        
        for session in sessions:
            best_facilitator = find_best_facilitator(session, facilitators)
            
            if best_facilitator:
                assignment = Assignment(
                    session_id=session.id,
                    facilitator_id=best_facilitator.id
                )
                db.session.add(assignment)
                assignments_made += 1
            else:
                conflicts.append(f"No suitable facilitator found for {session.course_name} at {session.start_time}")
        
        db.session.commit()
        
        return {
            'success': True,
            'assignments_made': assignments_made,
            'conflicts': conflicts,
            'message': f"{assignments_made} assignments made, {len(conflicts)} conflicts"
        }
    
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': str(e)
        }

def find_best_facilitator(session, facilitators):
    """
    Find the best facilitator for a given session based on:
    - Availability
    - Skills match
    - Preferences
    - Experience (simplified)
    """
    suitable_facilitators = []
    
    for facilitator in facilitators:
        score = calculate_facilitator_score(facilitator, session)
        if score > 0:
            suitable_facilitators.append((facilitator, score))
    
    if suitable_facilitators:
        # Sort by score (highest first)
        suitable_facilitators.sort(key=lambda x: x[1], reverse=True)
        return suitable_facilitators[0][0]
    
    return None

def calculate_facilitator_score(facilitator, session):
    """
    Calculate a score for how well a facilitator matches a session.
    Returns 0 if not suitable, higher scores for better matches.
    """
    score = 0
    
    # Check availability
    if not is_facilitator_available(facilitator, session):
        return 0
    
    # Check skills match
    required_skills = json.loads(session.required_skills) if session.required_skills else []
    facilitator_skills = json.loads(facilitator.skills) if facilitator.skills else []
    
    skills_match = len(set(required_skills) & set(facilitator_skills))
    if required_skills and skills_match == 0:
        return 0  # Must have at least one required skill
    
    score += skills_match * 10  # 10 points per matching skill
    
    # Check preferences
    preferences = json.loads(facilitator.preferences) if facilitator.preferences else {}
    
    # Add preference-based scoring here
    # For example, if facilitator prefers morning sessions and this is a morning session
    
    # Check for conflicts with existing assignments
    existing_assignments = Assignment.query.filter_by(facilitator_id=facilitator.id).join(Session).filter(
        Session.start_time <= session.end_time,
        Session.end_time >= session.start_time
    ).count()
    
    if existing_assignments > 0:
        return 0  # Time conflict
    
    # Base score for being available and suitable
    score += 50
    
    return score

def is_facilitator_available(facilitator, session):
    """
    Check if facilitator is available for the given session time.
    """
    session_day = session.start_time.weekday()  # 0=Monday, 6=Sunday
    session_start_time = session.start_time.time()
    session_end_time = session.end_time.time()
    
    # Check if facilitator has availability for this day
    availability = Availability.query.filter_by(
        user_id=facilitator.id,
        day_of_week=session_day,
        is_available=True
    ).first()
    
    if not availability:
        return False
    
    # Check if session time falls within available hours
    return (availability.start_time <= session_start_time and 
            availability.end_time >= session_end_time)