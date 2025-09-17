"""
Optimization Engine for Facilitator-to-Module Assignment
Phase 2: Real facilitator data integration with dummy session support

Scoring Function: (W_avail × availability_match) + (W_fair × fairness_factor) + (W_skill × skill_score)
Skill Levels: proficient=1.0, done_it_before=0.8, interested=0.5, not_interested=0.0
"""

from datetime import datetime, time
from models import User, UserRole, FacilitatorSkill, Unavailability, SkillLevel

# Tunable weights for scoring function
W_AVAILABILITY = 0.4
W_FAIRNESS = 0.3  
W_SKILL = 0.3

# Skill level to score mapping
SKILL_SCORES = {
    SkillLevel.PROFICIENT: 1.0,
    SkillLevel.LEADER: 0.8,  # "done it before"
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
            'module_name': f"{session.module.unit.unit_code} - {session.module.module_name}",
            'day_of_week': session.day_of_week if session.day_of_week is not None else 0,
            'start_time': session.start_time.time(),
            'end_time': session.end_time.time(),
            'duration_hours': duration,
            'required_skill_level': SkillLevel.INTERESTED,  # Default skill level
            'location': session.location or 'TBA'
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
        
        # Get unavailability (we'll store it as unavailability data)
        unavailability = {}
        if hasattr(facilitator, 'unavailabilities'):
            for unav in facilitator.unavailabilities:
                date_str = unav.date.isoformat()
                if date_str not in unavailability:
                    unavailability[date_str] = []
                unavailability[date_str].append({
                    'start_time': unav.start_time,
                    'end_time': unav.end_time,
                    'is_full_day': unav.is_full_day
                })
        
        facilitator_data.append({
            'id': facilitator.id,
            'name': f"{facilitator.first_name or 'Unknown'} {facilitator.last_name or 'User'}",
            'email': facilitator.email,
            'min_hours': facilitator.min_hours or 0,
            'max_hours': facilitator.max_hours or 20,
            'skills': skills,
            'unavailability': unavailability
        })
    
    return facilitator_data

def check_availability(facilitator, session):
    """
    Check if facilitator is available for the session time (not unavailable)
    Returns 1.0 if available, 0.0 if not (hard constraint)
    """
    # Convert session date to string format for comparison
    session_date = session.get('date')
    if isinstance(session_date, str):
        date_str = session_date
    else:
        # If session has datetime, extract date
        date_str = session_date.date().isoformat() if hasattr(session_date, 'date') else str(session_date)
    
    session_start = session['start_time']
    session_end = session['end_time']
    
    # If no unavailability records for this date, facilitator is available
    if date_str not in facilitator['unavailability']:
        return 1.0
    
    # Check if any unavailability conflicts with the session time
    for unav_slot in facilitator['unavailability'][date_str]:
        # If it's a full day unavailability, facilitator is not available
        if unav_slot['is_full_day']:
            return 0.0
        
        # Check for time overlap
        if (unav_slot['start_time'] and unav_slot['end_time'] and
            not (session_end <= unav_slot['start_time'] or 
                 session_start >= unav_slot['end_time'])):
            return 0.0
    
    return 1.0

def get_skill_score(facilitator, session):
    """
    Get skill score for facilitator-session match
    Uses the SKILL_SCORES mapping
    """
    # For dummy sessions, we'll use a generic skill check
    # In real implementation, this would check facilitator['skills'][session['module_id']]
    
    # For now, simulate some skill levels for testing
    facilitator_id = facilitator['id']
    session_id = session['id']
    
    # Simple simulation: alternate skill levels based on IDs
    if (facilitator_id + session_id) % 4 == 0:
        return SKILL_SCORES[SkillLevel.PROFICIENT]
    elif (facilitator_id + session_id) % 4 == 1:
        return SKILL_SCORES[SkillLevel.LEADER]
    elif (facilitator_id + session_id) % 4 == 2:
        return SKILL_SCORES[SkillLevel.INTERESTED]
    else:
        return SKILL_SCORES[SkillLevel.UNINTERESTED]

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

def generate_optimal_assignments(facilitators):
    """
    Main function to generate optimal facilitator-to-session assignments
    Takes facilitator data as parameter (from Flask route)
    Returns assignments and conflicts
    """
    sessions = get_real_sessions()
    
    if not facilitators:
        return [], ["No facilitators found in database"]
    
    assignments = []
    conflicts = []
    
    # Sort sessions by priority (longer sessions first, then by required skill level)
    sorted_sessions = sorted(sessions, key=lambda s: (-s['duration_hours'], -SKILL_SCORES.get(s['required_skill_level'], 0)))
    
    for session in sorted_sessions:
        best_facilitator = None
        best_score = 0.0
        
        # Find the best facilitator for this session
        for facilitator in facilitators:
            score = calculate_facilitator_score(facilitator, session, assignments)
            if score > best_score:
                best_score = score
                best_facilitator = facilitator
        
        # Assign if we found a suitable facilitator
        if best_facilitator and best_score > 0:
            assignments.append({
                'facilitator': best_facilitator,
                'session': session,
                'score': best_score
            })
        else:
            conflicts.append(f"No suitable facilitator found for {session['module_name']} ({format_session_time(session)})")
    
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
        SkillLevel.PROFICIENT: 'Proficient',
        SkillLevel.LEADER: 'Leader',
        SkillLevel.INTERESTED: 'Interested',
        SkillLevel.UNINTERESTED: 'Uninterested'
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
