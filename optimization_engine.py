"""
Optimization Engine for Facilitator-to-Module Assignment
Uses real facilitator proficiency data from the database

Scoring Function: (W_avail × availability_match) + (W_fair × fairness_factor) + (W_skill × skill_score)
Skill Levels: proficient=1.0, have_run_before=0.8, have_some_skill=0.5, no_interest=0.0
"""

from datetime import datetime, time
from models import User, UserRole, FacilitatorSkill, SkillLevel

# Tunable weights for scoring function
W_AVAILABILITY = 0.4
W_FAIRNESS = 0.4  # Increased fairness weight
W_SKILL = 0.2     # Reduced skill weight to balance with fairness

# Skill level to score mapping (matches models.py SkillLevel enum)
SKILL_SCORES = {
    SkillLevel.PROFICIENT: 1.0,
    SkillLevel.HAVE_RUN_BEFORE: 0.8,  # "done it before"
    SkillLevel.HAVE_SOME_SKILL: 0.5,  # "interested/has some skill"
    SkillLevel.NO_INTEREST: 0.0
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
            'module_id': session.module_id,  # Add module_id for skill matching
            'module_name': f"{session.module.unit.unit_code} - {session.module.module_name}",
            'day_of_week': session.day_of_week if session.day_of_week is not None else 0,
            'start_time': session.start_time.time(),
            'end_time': session.end_time.time(),
            'duration_hours': duration,
            'required_skill_level': SkillLevel.HAVE_SOME_SKILL,  # Default skill level
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
        
        # Deprecated: slot-based weekly availability removed. Using unavailability model instead.
        availability = {}
        
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
    
    # If no availability data provided, treat as available by default
    if 'availability' not in facilitator or not facilitator['availability']:
        return 1.0
    if day not in facilitator['availability']:
        return 1.0
    
    for avail_slot in facilitator['availability'][day]:
        if (avail_slot['is_available'] and 
            avail_slot['start_time'] <= session_start and 
            avail_slot['end_time'] >= session_end):
            return 1.0
    
    return 0.0

def get_skill_score(facilitator, session):
    """
    Get skill score for facilitator-session match based on real proficiency data
    Uses the SKILL_SCORES mapping
    """
    module_id = session.get('module_id')
    
    # Check if facilitator has skills data and has this specific module skill
    if 'skills' in facilitator and module_id in facilitator['skills']:
        skill_level = facilitator['skills'][module_id]
        return SKILL_SCORES.get(skill_level, 0.0)
    
    # If no skill data exists for this module, return lowest score
    # This encourages assigning facilitators who have declared their skills
    return SKILL_SCORES[SkillLevel.NO_INTEREST]

def get_assigned_hours(facilitator, current_assignments):
    """
    Calculate total hours already assigned to this facilitator
    """
    total_hours = 0
    for assignment in current_assignments:
        if assignment['facilitator']['id'] == facilitator['id']:
            total_hours += assignment['session']['duration_hours']
    return total_hours

def calculate_facilitator_score(facilitator, session, current_assignments, total_hours_per_facilitator=None):
    """
    Calculate the score for assigning a facilitator to a session
    Uses the formula: (W_avail × availability_match) + (W_fair × fairness_factor) + (W_skill × skill_score)
    """
    # Availability check (hard constraint)
    availability_match = check_availability(facilitator, session)
    if availability_match == 0.0:
        return 0.0  # Hard constraint violation
    
    # Enhanced fairness calculation
    assigned_hours = get_assigned_hours(facilitator, current_assignments)
    
    # Calculate fairness based on relative distribution
    if total_hours_per_facilitator and len(total_hours_per_facilitator) > 1:
        # Find the minimum assigned hours among all facilitators
        min_assigned = min(total_hours_per_facilitator.values())
        max_assigned = max(total_hours_per_facilitator.values())
        
        if max_assigned > min_assigned:
            # Normalize fairness: facilitators with fewer hours get higher scores
            fairness_factor = 1.0 - ((assigned_hours - min_assigned) / (max_assigned - min_assigned))
        else:
            fairness_factor = 1.0  # All facilitators have equal hours
    else:
        # Fallback to original fairness calculation
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
    Uses enhanced fairness algorithm to ensure equal distribution of hours
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
        
        # Calculate current hours per facilitator for fairness calculation
        total_hours_per_facilitator = {}
        for facilitator in facilitators:
            total_hours_per_facilitator[facilitator['id']] = get_assigned_hours(facilitator, assignments)
        
        # Find the best facilitator for this session
        for facilitator in facilitators:
            score = calculate_facilitator_score(
                facilitator, 
                session, 
                assignments, 
                total_hours_per_facilitator
            )
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
        SkillLevel.HAVE_RUN_BEFORE: 'Have Run Before',
        SkillLevel.HAVE_SOME_SKILL: 'Have Some Skill',
        SkillLevel.NO_INTEREST: 'No Interest'
    }
    return skill_names.get(skill_level, 'Unknown')

def calculate_metrics(assignments):
    """
    Calculate performance metrics for the assignments including fairness distribution
    """
    if not assignments:
        return {
            'avg_score': 0,
            'total_hours': 0,
            'facilitator_count': 0,
            'skill_distribution': {},
            'fairness_metrics': {}
        }
    
    total_score = sum(a['score'] for a in assignments)
    avg_score = total_score / len(assignments)
    
    total_hours = sum(a['session']['duration_hours'] for a in assignments)
    
    facilitator_ids = set(a['facilitator']['id'] for a in assignments)
    facilitator_count = len(facilitator_ids)
    
    # Calculate hours per facilitator for fairness analysis
    facilitator_hours = {}
    for assignment in assignments:
        fac_id = assignment['facilitator']['id']
        fac_name = assignment['facilitator']['name']
        if fac_id not in facilitator_hours:
            facilitator_hours[fac_id] = {'name': fac_name, 'hours': 0}
        facilitator_hours[fac_id]['hours'] += assignment['session']['duration_hours']
    
    # Fairness metrics
    hours_list = [data['hours'] for data in facilitator_hours.values()]
    fairness_metrics = {
        'hours_per_facilitator': {data['name']: data['hours'] for data in facilitator_hours.values()},
        'min_hours': min(hours_list) if hours_list else 0,
        'max_hours': max(hours_list) if hours_list else 0,
        'avg_hours': sum(hours_list) / len(hours_list) if hours_list else 0,
        'hours_std_dev': (sum((h - sum(hours_list)/len(hours_list))**2 for h in hours_list) / len(hours_list))**0.5 if hours_list else 0
    }
    
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
        'total_hours': round(total_hours, 1),
        'facilitator_count': facilitator_count,
        'skill_distribution': skill_dist,
        'fairness_metrics': fairness_metrics
    }
