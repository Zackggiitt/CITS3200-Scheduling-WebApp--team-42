"""
Optimization Engine for Facilitator-to-Module Assignment
Phase 2: Real facilitator data integration with dummy session support

Scoring Function: (W_avail × availability_match) + (W_fair × fairness_factor) + (W_skill × skill_score)
Skill Levels: proficient=1.0, done_it_before=0.8, interested=0.5, not_interested=0.0
"""

from datetime import datetime, time, timedelta
from models import User, UserRole, FacilitatorSkill, Unavailability, SkillLevel

# Tunable weights for scoring function
W_AVAILABILITY = 0.4
W_FAIRNESS = 0.3  
W_SKILL = 0.3

# Skill level to score mapping
SKILL_SCORES = {
    SkillLevel.PROFICIENT: 1.0,
    SkillLevel.LEADER: 0.8,
    SkillLevel.INTERESTED: 0.5,
    SkillLevel.UNINTERESTED: 0.0
}

def get_real_sessions():
    """
    Get real sessions from database instead of dummy data
    """
    from models import Session, Module, Unit
    
    sessions_data = []
    
    # Query all sessions from database
    db_sessions = Session.query.join(Module).join(Unit).all()
    
    for session in db_sessions:
        # Calculate duration directly from datetime objects
        duration = (session.end_time - session.start_time).total_seconds() / 3600
        
        sessions_data.append({
            'id': session.id,
            'module_id': session.module_id,
            'module_name': f"{session.module.unit.unit_code} - {session.module.module_name}",
            'day_of_week': session.day_of_week if session.day_of_week is not None else 0,
            'start_time': session.start_time.time(),
            'end_time': session.end_time.time(),
            'duration_hours': duration,
            'required_skill_level': SkillLevel.INTERESTED,  # Default skill level
            'location': session.location or 'TBA',
            'lead_staff_required': session.lead_staff_required or 1,
            'support_staff_required': session.support_staff_required or 0
        })
    
    # If no real sessions exist, return empty list instead of dummy data
    if not sessions_data:
        return []
    
    return sessions_data

def prepare_facilitator_data(facilitators_from_db):
    """
    Convert database facilitator objects to optimization-friendly format
    This function is called from the Flask route with database objects
    """
    facilitator_data = []
    for facilitator in facilitators_from_db:
        # Get facilitator skills
        skills = {}
        if hasattr(facilitator, 'facilitator_skills'):
            for skill in facilitator.facilitator_skills:
                skills[skill.module_id] = skill.skill_level
        
        # Get availability (inverse of unavailability)
        # For simplicity, assume facilitator is available all week except during unavailability periods
        availability = {}
        # Initialize all days as available (8:00-18:00 by default)
        for day in range(7):  # 0=Monday, 6=Sunday
            availability[day] = [{
                'start_time': time(8, 0),
                'end_time': time(18, 0),
                'is_available': True
            }]
        
        # Remove unavailable periods
        if hasattr(facilitator, 'unavailability'):
            for unavail in facilitator.unavailability:
                # For now, mark entire days as unavailable if there's any unavailability
                # This is a simplified approach - could be enhanced to handle partial day unavailability
                if unavail.start_date and unavail.end_date:
                    current_date = unavail.start_date
                    while current_date <= unavail.end_date:
                        day_of_week = current_date.weekday()
                        availability[day_of_week] = [{
                            'start_time': time(0, 0),
                            'end_time': time(0, 0),
                            'is_available': False
                        }]
                        current_date += timedelta(days=1)
        
        facilitator_data.append({
            'id': facilitator.id,
            'name': f"{facilitator.first_name or 'Unknown'} {facilitator.last_name or 'User'}",
            'email': facilitator.email,
            'min_hours': facilitator.min_hours or 0,
            'max_hours': facilitator.max_hours or 20,
            'skills': skills,
            'availability': availability
        })
    
    return facilitator_data

def check_availability(facilitator, session):
    """
    Check if facilitator is available for the session time
    Returns 1.0 if available, 0.0 if not (hard constraint)
    """
    day = session['day_of_week']
    session_start = session['start_time']
    session_end = session['end_time']
    
    if day not in facilitator['availability']:
        return 0.0
    
    for avail_slot in facilitator['availability'][day]:
        if (avail_slot['is_available'] and 
            avail_slot['start_time'] <= session_start and 
            avail_slot['end_time'] >= session_end):
            return 1.0
    
    return 0.0

def is_facilitator_available(facilitator_data, session_day, session_start_time, session_end_time):
    """Check if facilitator is available for a specific session time"""
    availability = facilitator_data.get('availability', {})
    
    if session_day not in availability:
        return False
    
    for time_slot in availability[session_day]:
        if (time_slot['is_available'] and 
            time_slot['start_time'] <= session_start_time and 
            time_slot['end_time'] >= session_end_time):
            return True
    
    return False

def get_skill_score(facilitator, session):
    """
    Get skill score for facilitator-session match
    Uses the SKILL_SCORES mapping
    """
    facilitator_skills = facilitator.get('skills', {})
    session_module_id = session.get('module_id')
    
    if session_module_id in facilitator_skills:
        skill_level = facilitator_skills[session_module_id]
        return SKILL_SCORES.get(skill_level, 0.0)
    
    # If no skill data available, return default interested level
    return SKILL_SCORES[SkillLevel.INTERESTED]

def get_assigned_hours(facilitator, current_assignments):
    """
    Calculate total hours already assigned to this facilitator
    """
    total_hours = 0
    for assignment in current_assignments:
        if assignment['facilitator']['id'] == facilitator['id']:
            total_hours += assignment['session']['duration_hours']
    return total_hours

def calculate_facilitator_score(facilitator, session, current_assignments):
    """
    Calculate the score for assigning a facilitator to a session
    Uses the formula: (W_avail × availability_match) + (W_fair × fairness_factor) + (W_skill × skill_score)
    """
    # Availability check (hard constraint)
    availability_match = check_availability(facilitator, session)
    if availability_match == 0.0:
        return 0.0  # Hard constraint violation
    
    # Fairness factor (1 - assigned_hours/target_hours)
    assigned_hours = get_assigned_hours(facilitator, current_assignments)
    target_hours = (facilitator['min_hours'] + facilitator['max_hours']) / 2
    if target_hours == 0:
        target_hours = 10  # Default target
    
    fairness_factor = max(0, 1 - (assigned_hours / target_hours))
    
    # Skill score
    skill_score = get_skill_score(facilitator, session)
    
    # Final weighted score
    score = (W_AVAILABILITY * availability_match) + (W_FAIRNESS * fairness_factor) + (W_SKILL * skill_score)
    
    return score

def generate_optimal_assignments(facilitators, sessions=None):
    """
    Main function to generate optimal facilitator-to-session assignments
    Takes facilitator data as parameter (from Flask route)
    Optionally takes custom sessions data, otherwise uses get_real_sessions()
    Returns assignments and conflicts
    """
    if sessions is None:
        sessions = get_real_sessions()
    
    if not facilitators:
        return [], ["No facilitators found in database"]
    
    assignments = []
    conflicts = []
    
    # Sort sessions by priority (longer sessions first, then by required skill level)
    sorted_sessions = sorted(sessions, key=lambda s: (-s['duration_hours'], -SKILL_SCORES.get(s['required_skill_level'], 0)))
    
    for session in sorted_sessions:
        # Get required staff counts from session
        lead_staff_required = session.get('lead_staff_required', 1)
        support_staff_required = session.get('support_staff_required', 0)
        total_staff_required = lead_staff_required + support_staff_required
        
        # Calculate current hours per facilitator for fairness calculation
        total_hours_per_facilitator = {}
        for facilitator in facilitators:
            total_hours_per_facilitator[facilitator['id']] = get_assigned_hours(facilitator, assignments)
        
        # Find multiple facilitators for this session
        session_assignments = []
        assigned_facilitator_ids = set()
        
        # Assign facilitators for this session (up to total_staff_required)
        for staff_position in range(total_staff_required):
            best_facilitator = None
            best_score = 0.0
            
            # Find the best available facilitator for this position
            for facilitator in facilitators:
                # Skip if already assigned to this session
                if facilitator['id'] in assigned_facilitator_ids:
                    continue
                
                score = calculate_facilitator_score(
                    facilitator, 
                    session, 
                    assignments + session_assignments,  # Include current session assignments
                    total_hours_per_facilitator
                )
                if score > best_score:
                    best_score = score
                    best_facilitator = facilitator
            
            # Assign if we found a suitable facilitator
            if best_facilitator and best_score > 0:
                # Determine role based on position
                role = 'leader' if staff_position < lead_staff_required else 'support'
                
                session_assignments.append({
                    'facilitator': best_facilitator,
                    'session': session,
                    'score': best_score,
                    'role': role
                })
                assigned_facilitator_ids.add(best_facilitator['id'])
            else:
                # Generate detailed conflict message for missing staff
                conflict_reasons = []
                
                # Check why no facilitator was suitable
                for facilitator in facilitators:
                    if facilitator['id'] in assigned_facilitator_ids:
                        continue
                        
                    # Check skill constraints
                    if not check_skill_constraint(facilitator, session):
                        module_id = session.get('module_id')
                        if 'skills' in facilitator and module_id in facilitator['skills']:
                            conflict_reasons.append(f"{facilitator['name']} has no interest in this module")
                    
                    # Check availability constraints
                    if check_availability(facilitator, session) == 0.0:
                        conflict_reasons.append(f"{facilitator['name']} is unavailable at this time")
                
                position_type = 'leader' if staff_position < lead_staff_required else 'support'
                if conflict_reasons:
                    conflict_msg = f"No suitable {position_type} facilitator found for {session['module_name']} ({format_session_time(session)}) - Reasons: {'; '.join(conflict_reasons[:3])}"
                else:
                    conflict_msg = f"No suitable {position_type} facilitator found for {session['module_name']} ({format_session_time(session)})"
                
                conflicts.append(conflict_msg)
                break  # Stop trying to assign more facilitators for this session
        
        # Add all successful assignments for this session
        assignments.extend(session_assignments)
    
    return assignments, conflicts

def format_session_time(session):
    """
    Format session timing for display
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_name = days[session['day_of_week']]
    start_str = session['start_time'].strftime('%H:%M')
    end_str = session['end_time'].strftime('%H:%M')
    return f"{day_name} {start_str}-{end_str}"

def get_skill_level_name(skill_level):
    """
    Convert skill level enum to readable name
    """
    skill_names = {
        SkillLevel.ADVANCED: 'Advanced',
        SkillLevel.INTERMEDIATE: 'Intermediate',
        SkillLevel.BEGINNER: 'Beginner'
    }
    return skill_names.get(skill_level, 'Unknown')

def calculate_metrics(assignments):
    """
    Calculate performance metrics for the assignments
    """
    if not assignments:
        return {
            'avg_score': 0,
            'total_hours': 0,
            'facilitator_count': 0,
            'skill_distribution': {}
        }
    
    total_score = sum(a['score'] for a in assignments)
    avg_score = total_score / len(assignments)
    
    total_hours = sum(a['session']['duration_hours'] for a in assignments)
    
    facilitator_ids = set(a['facilitator']['id'] for a in assignments)
    facilitator_count = len(facilitator_ids)
    
    # Skill distribution
    skill_dist = {}
    for assignment in assignments:
        skill_score = get_skill_score(assignment['facilitator'], assignment['session'])
        # Reverse lookup skill level from score
        for skill_level, score in SKILL_SCORES.items():
            if abs(score - skill_score) < 0.01:  # Float comparison
                skill_name = get_skill_level_name(skill_level)
                skill_dist[skill_name] = skill_dist.get(skill_name, 0) + 1
                break
    
    return {
        'avg_score': round(avg_score, 3),
        'total_hours': total_hours,
        'facilitator_count': facilitator_count,
        'skill_distribution': skill_dist
    }
