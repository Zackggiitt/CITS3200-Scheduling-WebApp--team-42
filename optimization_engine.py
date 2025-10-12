"""
Optimization Engine for Facilitator-to-Module Assignment
Uses real facilitator proficiency data from the database

Scoring Function: (W_avail × availability_match) + (W_fair × fairness_factor) + (W_skill × skill_score)
Skill Levels: proficient=1.0, have_run_before=0.8, have_some_skill=0.5, no_interest=0.0

HARD CONSTRAINTS (must be satisfied):
1. Availability: Facilitator must be available during session time
2. Skill Interest: Facilitator cannot have "no_interest" in the module (score = 0.0)

SOFT CONSTRAINTS (optimized for):
- Fairness: Distribute hours evenly among facilitators
- Skill Matching: Prefer higher skill levels when possible
"""

import csv
import io
from datetime import datetime, time
from models import User, UserRole, FacilitatorSkill, SkillLevel, db

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

def get_real_sessions(unit_id=None):
    """
    Get real sessions from database instead of dummy data
    If unit_id is provided, only get sessions from that specific unit
    """
    from models import Session, Module, Unit
    
    sessions_data = []
    
    # Query sessions from database, optionally filtered by unit
    query = Session.query.join(Module).join(Unit)
    if unit_id is not None:
        query = query.filter(Unit.id == unit_id)
    
    db_sessions = query.all()
    
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
            'date': session.start_time.date(),  # Add full date for conflict checking
            'start_datetime': session.start_time,  # Full datetime for conflict checking
            'end_datetime': session.end_time,  # Full datetime for conflict checking
            'duration_hours': duration,
            'required_skill_level': SkillLevel.HAVE_SOME_SKILL,  # Default skill level
            'location': session.location or 'TBA',
            'lead_staff_required': session.lead_staff_required or 1,  # Bulk staffing: number of leads
            'support_staff_required': session.support_staff_required or 0  # Bulk staffing: number of supports
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
    Now properly checks database unavailability data
    """
    from models import Unavailability, Module
    from datetime import datetime
    
    # Get session date and time information
    session_date = session.get('date')
    session_start_time = session.get('start_time')
    session_end_time = session.get('end_time')
    
    if not session_date or not session_start_time or not session_end_time:
        # If we don't have proper date/time info, assume available
        return 1.0
    
    # Get the module ID from the session
    module_id = session.get('module_id')
    if not module_id:
        return 1.0
    
    # Get the unit ID from the module
    module = Module.query.get(module_id)
    if not module:
        return 1.0
    
    unit_id = module.unit_id
    
    # Check if facilitator has any unavailability for this specific date and time
    unavailability = Unavailability.query.filter_by(
        user_id=facilitator['id'],
        unit_id=unit_id,
        date=session_date
    ).first()
    
    if not unavailability:
        # No unavailability entry means facilitator is available
        return 1.0
    
    # Check if it's a full day unavailability
    if unavailability.is_full_day:
        return 0.0  # Not available for full day
    
    # Check if the session time conflicts with the unavailability time block
    if unavailability.start_time and unavailability.end_time:
        session_start = session_start_time
        session_end = session_end_time
        unavail_start = unavailability.start_time
        unavail_end = unavailability.end_time
        
        # Check if sessions overlap
        if (session_start < unavail_end and session_end > unavail_start):
            return 0.0  # Conflict detected
    
    # If we get here, no conflict was found
    return 1.0

def check_time_conflict(facilitator, session, current_assignments):
    """
    Check if facilitator is already assigned to another session at the same time
    Returns True if there's a conflict (facilitator is double-booked)
    Returns False if no conflict (facilitator can be assigned)
    """
    # Get the session's datetime information
    session_start_dt = session.get('start_datetime')
    session_end_dt = session.get('end_datetime')
    
    if not session_start_dt or not session_end_dt:
        return False  # Can't check conflicts without datetime info
    
    # Check against all current assignments for this facilitator
    for assignment in current_assignments:
        if assignment['facilitator']['id'] == facilitator['id']:
            assigned_session = assignment['session']
            
            # Get assigned session datetime
            assigned_start_dt = assigned_session.get('start_datetime')
            assigned_end_dt = assigned_session.get('end_datetime')
            
            if assigned_start_dt and assigned_end_dt:
                # Sessions overlap if one starts before the other ends
                if (session_start_dt < assigned_end_dt and session_end_dt > assigned_start_dt):
                    return True  # Conflict detected!
    
    return False  # No conflict

def check_location_conflict(facilitator, session, current_assignments):
    """
    Check if facilitator is already assigned to another session at the same time in a different location
    Returns True if there's a location conflict (facilitator can't be in two places at once)
    Returns False if no location conflict (same location or no time overlap)
    """
    # Get the session's datetime and location information
    session_start_dt = session.get('start_datetime')
    session_end_dt = session.get('end_datetime')
    session_location = session.get('location', 'TBA')
    
    if not session_start_dt or not session_end_dt:
        return False  # Can't check conflicts without datetime info
    
    # Check against all current assignments for this facilitator
    for assignment in current_assignments:
        if assignment['facilitator']['id'] == facilitator['id']:
            assigned_session = assignment['session']
            
            # Get assigned session datetime and location
            assigned_start_dt = assigned_session.get('start_datetime')
            assigned_end_dt = assigned_session.get('end_datetime')
            assigned_location = assigned_session.get('location', 'TBA')
            
            if assigned_start_dt and assigned_end_dt:
                # Check if sessions overlap in time
                time_overlap = (session_start_dt < assigned_end_dt and session_end_dt > assigned_start_dt)
                
                # Check if sessions are in different locations
                different_location = (session_location != assigned_location and 
                                    session_location != 'TBA' and 
                                    assigned_location != 'TBA')
                
                # Location conflict occurs when there's both time overlap AND different locations
                if time_overlap and different_location:
                    return True  # Location conflict detected!
    
    return False  # No location conflict

def get_skill_score(facilitator, session):
    """
    Get skill score for facilitator-session match based on real proficiency data
    Uses the SKILL_SCORES mapping
    
    Note: This function assumes skill constraints have already been checked.
    If a facilitator has "no interest", they should not reach this function.
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

def check_skill_constraint(facilitator, session):
    """
    Check if facilitator has "no interest" in this session (hard constraint)
    Returns False if facilitator should NOT be assigned (no interest)
    Returns True if facilitator CAN be assigned (any other skill level)
    """
    module_id = session.get('module_id')
    
    # Check if facilitator has skills data and has this specific module skill
    if 'skills' in facilitator and module_id in facilitator['skills']:
        skill_level = facilitator['skills'][module_id]
        # Hard constraint: NO_INTEREST means cannot be assigned
        return skill_level != SkillLevel.NO_INTEREST
    
    # If no skill data exists for this module, allow assignment (fallback)
    # This is safer than blocking assignments due to missing data
    return True

def calculate_facilitator_score(facilitator, session, current_assignments, total_hours_per_facilitator=None):
    """
    Calculate the score for assigning a facilitator to a session
    Uses the formula: (W_avail × availability_match) + (W_fair × fairness_factor) + (W_skill × skill_score)
    """
    # Skill constraint check (hard constraint - no interest = cannot be assigned)
    if not check_skill_constraint(facilitator, session):
        return 0.0  # Hard constraint violation - no interest in this session
    
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

def generate_optimal_assignments(facilitators, unit_id=None):
    """
    Main function to generate optimal facilitator-to-session assignments
    Uses enhanced fairness algorithm to ensure equal distribution of hours
    Now supports multiple facilitators per session (lead and support staff)
    
    Args:
        facilitators: List of facilitator data dictionaries
        unit_id: Optional unit ID to filter sessions (if None, gets sessions from all units)
    """
    sessions = get_real_sessions(unit_id)
    
    if not facilitators:
        return [], ["No facilitators found in database"]
    
    assignments = []
    conflicts = []
    
    # Sort sessions by priority (longer sessions first, then by required skill level)
    sorted_sessions = sorted(sessions, key=lambda s: (-s['duration_hours'], -SKILL_SCORES.get(s['required_skill_level'], 0)))
    
    for session in sorted_sessions:
        # Get staffing requirements from session
        lead_staff_needed = session.get('lead_staff_required', 1)
        support_staff_needed = session.get('support_staff_required', 0)
        total_staff_needed = lead_staff_needed + support_staff_needed
        
        # Calculate current hours per facilitator for fairness calculation
        total_hours_per_facilitator = {}
        for facilitator in facilitators:
            total_hours_per_facilitator[facilitator['id']] = get_assigned_hours(facilitator, assignments)
        
        # Track assigned facilitators for this session
        session_assignments = []
        
        # First, assign lead staff (prefer higher skill levels)
        for lead_slot in range(lead_staff_needed):
            best_facilitator = None
            best_score = 0.0
            
            # Find the best available facilitator for this lead role
            for facilitator in facilitators:
                # Skip if already assigned to this session
                if any(a['facilitator']['id'] == facilitator['id'] for a in session_assignments):
                    continue
                
                # Check for time conflicts (hard constraint)
                if check_time_conflict(facilitator, session, assignments):
                    continue
                
                # Check for location conflicts (hard constraint)
                if check_location_conflict(facilitator, session, assignments):
                    continue
                
                score = calculate_facilitator_score(
                    facilitator, 
                    session, 
                    assignments, 
                    total_hours_per_facilitator
                )
                
                # Bonus for lead roles: prefer higher skill levels
                skill_score = get_skill_score(facilitator, session)
                score = score + (skill_score * 0.1)  # Add 10% bonus based on skill
                
                if score > best_score:
                    best_score = score
                    best_facilitator = facilitator
            
            # Assign lead if found
            if best_facilitator and best_score > 0:
                assignment = {
                    'facilitator': best_facilitator,
                    'session': session,
                    'score': best_score,
                    'role': 'lead'
                }
                session_assignments.append(assignment)
                assignments.append(assignment)
            else:
                # Could not fill this lead position
                conflict_msg = f"Could not assign lead staff {lead_slot + 1}/{lead_staff_needed} for {session['module_name']} ({format_session_time(session)})"
                conflicts.append(conflict_msg)
        
        # Second, assign support staff
        for support_slot in range(support_staff_needed):
            best_facilitator = None
            best_score = 0.0
            
            # Find the best available facilitator for this support role
            for facilitator in facilitators:
                # Skip if already assigned to this session
                if any(a['facilitator']['id'] == facilitator['id'] for a in session_assignments):
                    continue
                
                # Check for time conflicts (hard constraint)
                if check_time_conflict(facilitator, session, assignments):
                    continue
                
                # Check for location conflicts (hard constraint)
                if check_location_conflict(facilitator, session, assignments):
                    continue
                
                score = calculate_facilitator_score(
                    facilitator, 
                    session, 
                    assignments, 
                    total_hours_per_facilitator
                )
                
                if score > best_score:
                    best_score = score
                    best_facilitator = facilitator
            
            # Assign support if found
            if best_facilitator and best_score > 0:
                assignment = {
                    'facilitator': best_facilitator,
                    'session': session,
                    'score': best_score,
                    'role': 'support'
                }
                session_assignments.append(assignment)
                assignments.append(assignment)
            else:
                # Could not fill this support position
                conflict_msg = f"Could not assign support staff {support_slot + 1}/{support_staff_needed} for {session['module_name']} ({format_session_time(session)})"
                conflicts.append(conflict_msg)
        
        # If no facilitators were assigned at all, provide detailed reasons
        if not session_assignments and total_staff_needed > 0:
            conflict_reasons = []
            
            # Check why no facilitator was suitable
            for facilitator in facilitators:
                # Check time conflicts
                if check_time_conflict(facilitator, session, assignments):
                    conflict_reasons.append(f"{facilitator['name']} is already assigned to another session at this time")
                
                # Check location conflicts
                elif check_location_conflict(facilitator, session, assignments):
                    conflict_reasons.append(f"{facilitator['name']} is already assigned to a different location at this time")
                
                # Check skill constraints
                elif not check_skill_constraint(facilitator, session):
                    module_id = session.get('module_id')
                    if 'skills' in facilitator and module_id in facilitator['skills']:
                        conflict_reasons.append(f"{facilitator['name']} has no interest in this module")
                
                # Check availability constraints
                elif check_availability(facilitator, session) == 0.0:
                    conflict_reasons.append(f"{facilitator['name']} is unavailable at this time")
            
            if conflict_reasons:
                conflict_msg = f"No facilitators found for {session['module_name']} ({format_session_time(session)}) - Reasons: {'; '.join(conflict_reasons[:3])}"
            else:
                conflict_msg = f"No facilitators found for {session['module_name']} ({format_session_time(session)})"
            
            conflicts.append(conflict_msg)
    
    return assignments, conflicts

def format_session_time(session):
    """
    Format session timing for display
    Includes full date to avoid confusion when multiple sessions occur on the same day of week
    """
    # If we have start_datetime, use it for accurate date display
    if 'start_datetime' in session and session['start_datetime']:
        start_dt = session['start_datetime']
        end_dt = session.get('end_datetime', start_dt)
        
        # Format: "Monday 2025-07-01 09:00-12:30"
        day_name = start_dt.strftime('%A')
        date_str = start_dt.strftime('%Y-%m-%d')
        start_time_str = start_dt.strftime('%H:%M')
        end_time_str = end_dt.strftime('%H:%M')
        
        return f"{day_name} {date_str} {start_time_str}-{end_time_str}"
    else:
        # Fallback to old format if datetime not available
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

def generate_schedule_report_csv(assignments, unit_name="Unit", total_facilitators_in_pool=None, unit_id=None, all_facilitators=None):
    """
    Generate a comprehensive CSV report of the auto-scheduling results
    
    Returns a CSV string with multiple sections:
    1. Overview Statistics
    2. Session Staffing Statistics (NEW)
    3. Fairness Metrics
    4. Skill Level Distribution
    5. Per-Facilitator Hours Summary
    6. Skill Levels Per Facilitator
    7. Unavailability Information
    8. Facilitator Skill Declarations
    9. Detailed Assignment List
    
    Args:
        assignments: List of assignment dictionaries
        unit_name: Name of the unit for the report header
        total_facilitators_in_pool: Total number of facilitators available (for utilization %)
        unit_id: Unit ID for querying skill declarations (optional)
        all_facilitators: List of all facilitator objects in the pool (optional)
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    if not assignments:
        writer.writerow(["No assignments to report"])
        return output.getvalue()
    
    # Calculate metrics
    metrics = calculate_metrics(assignments)
    fairness = metrics['fairness_metrics']
    
    # Get unavailability data from database
    from models import Unavailability, User, Module, FacilitatorSkill
    
    # Get all facilitators who have assignments
    facilitator_ids = set(a['facilitator']['id'] for a in assignments)
    facilitator_unavailabilities = {}
    
    for fac_id in facilitator_ids:
        # Get unavailabilities for this facilitator
        unavailabilities = Unavailability.query.filter_by(user_id=fac_id).all()
        facilitator_unavailabilities[fac_id] = unavailabilities
    
    # Build facilitator statistics
    facilitator_stats = {}
    for assignment in assignments:
        fac_id = assignment['facilitator']['id']
        fac_name = assignment['facilitator']['name']
        fac_email = assignment['facilitator']['email']
        
        if fac_id not in facilitator_stats:
            facilitator_stats[fac_id] = {
                'name': fac_name,
                'email': fac_email,
                'total_hours': 0,
                'session_count': 0,
                'lead_count': 0,
                'support_count': 0,
                'min_hours_target': assignment['facilitator'].get('min_hours', 0),
                'max_hours_target': assignment['facilitator'].get('max_hours', 20),
                'avg_score': 0,
                'sessions': [],
                'unavailabilities': facilitator_unavailabilities.get(fac_id, [])
            }
        
        # Get skill level for this assignment
        skill_score = get_skill_score(assignment['facilitator'], assignment['session'])
        skill_level_name = "Unknown"
        for skill_level, score in SKILL_SCORES.items():
            if abs(score - skill_score) < 0.01:
                skill_level_name = get_skill_level_name(skill_level)
                break
        
        # Track role counts
        role = assignment.get('role', 'lead')
        if role == 'lead':
            facilitator_stats[fac_id]['lead_count'] += 1
        else:
            facilitator_stats[fac_id]['support_count'] += 1
        
        facilitator_stats[fac_id]['total_hours'] += assignment['session']['duration_hours']
        facilitator_stats[fac_id]['session_count'] += 1
        facilitator_stats[fac_id]['avg_score'] += assignment['score']
        facilitator_stats[fac_id]['sessions'].append({
            'module': assignment['session']['module_name'],
            'time': format_session_time(assignment['session']),
            'hours': assignment['session']['duration_hours'],
            'score': assignment['score'],
            'skill_level': skill_level_name,
            'role': role
        })
    
    # Calculate average scores
    for fac_id in facilitator_stats:
        count = facilitator_stats[fac_id]['session_count']
        if count > 0:
            facilitator_stats[fac_id]['avg_score'] /= count
    
    # === SECTION 1: Overview Statistics ===
    writer.writerow([f"AUTO-SCHEDULING REPORT - {unit_name}"])
    writer.writerow([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    writer.writerow([])
    
    # Calculate utilization percentage
    facilitators_assigned = metrics['facilitator_count']
    if total_facilitators_in_pool and total_facilitators_in_pool > 0:
        utilization_pct = (facilitators_assigned / total_facilitators_in_pool) * 100
        facilitators_not_assigned = total_facilitators_in_pool - facilitators_assigned
    else:
        utilization_pct = None
        facilitators_not_assigned = None
    
    
    writer.writerow(["OVERVIEW STATISTICS"])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Assignments", len(assignments)])
    writer.writerow(["Total Facilitators Used", metrics['facilitator_count']])
    if total_facilitators_in_pool:
        writer.writerow(["Total Facilitators in Pool", total_facilitators_in_pool])
        writer.writerow(["Facilitators Assigned (%)", f"{utilization_pct:.1f}%"])
        writer.writerow(["Facilitators Not Assigned", facilitators_not_assigned])
    writer.writerow(["Total Hours Scheduled", f"{metrics['total_hours']:.1f}"])
    writer.writerow(["Average Assignment Score", f"{metrics['avg_score']:.3f}"])
    writer.writerow([])
    
    # === SECTION 2: Session Staffing Statistics ===
    if unit_id:
        # Calculate session staffing statistics using the same logic as the dashboard
        from models import Session, Module, Assignment
        from sqlalchemy import func
        
        session_rows = (
            db.session.query(
                Session.id.label("sid"),
                func.coalesce(Session.max_facilitators, 1).label("maxf"),
                func.count(Assignment.id).label("assigned"),
            )
            .join(Module, Module.id == Session.module_id)
            .outerjoin(Assignment, Assignment.session_id == Session.id)
            .filter(Module.unit_id == unit_id)
            .group_by(Session.id, Session.max_facilitators)
            .all()
        )

        # Get sessions that need a lead facilitator specifically
        sessions_with_lead = (
            db.session.query(Session.id)
            .join(Module, Module.id == Session.module_id)
            .join(Assignment, Assignment.session_id == Session.id)
            .filter(Module.unit_id == unit_id)
            .filter(Assignment.role == 'lead')
            .distinct()
            .all()
        )
        
        sessions_with_lead_ids = {s.id for s in sessions_with_lead}

        total_sessions = len(session_rows)
        fully_staffed = sum(1 for r in session_rows if r.assigned >= r.maxf and r.maxf > 0)
        unstaffed = sum(1 for r in session_rows if r.assigned == 0)
        needs_lead = sum(1 for r in session_rows if r.assigned > 0 and r.sid not in sessions_with_lead_ids)
        
        writer.writerow(["SESSION STAFFING STATISTICS"])
        writer.writerow(["Metric", "Count"])
        writer.writerow(["Total Sessions", total_sessions])
        writer.writerow(["Fully Staffed", fully_staffed])
        writer.writerow(["Needs Lead", needs_lead])
        writer.writerow(["Unstaffed", unstaffed])
        writer.writerow(["Partially Staffed", total_sessions - fully_staffed - unstaffed])
        writer.writerow([])
    
    # === SECTION 3: Fairness Metrics ===
    writer.writerow(["FAIRNESS METRICS"])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Minimum Hours Assigned", f"{fairness['min_hours']:.1f}"])
    writer.writerow(["Maximum Hours Assigned", f"{fairness['max_hours']:.1f}"])
    writer.writerow(["Average Hours Per Facilitator", f"{fairness['avg_hours']:.1f}"])
    writer.writerow(["Hours Standard Deviation", f"{fairness['hours_std_dev']:.2f}"])
    writer.writerow(["Hours Range (Max - Min)", f"{fairness['max_hours'] - fairness['min_hours']:.1f}"])
    writer.writerow([])
    
    # === SECTION 3: Skill Distribution ===
    writer.writerow(["SKILL LEVEL DISTRIBUTION"])
    writer.writerow(["Skill Level", "Count", "Percentage"])
    skill_dist = metrics['skill_distribution']
    total_assignments = len(assignments)
    for skill_name, count in sorted(skill_dist.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_assignments * 100) if total_assignments > 0 else 0
        writer.writerow([skill_name, count, f"{percentage:.1f}%"])
    writer.writerow([])
    
    # === SECTION 4: Per-Facilitator Summary ===
    writer.writerow(["FACILITATOR HOURS SUMMARY"])
    writer.writerow([
        "Facilitator Name", 
        "Email",
        "Sessions Assigned",
        "Lead Roles",
        "Support Roles",
        "Total Hours", 
        "Min Hours Target",
        "Max Hours Target",
        "Within Target?",
        "% of Max Hours",
        "Avg Assignment Score",
        "Unavailability Count"
    ])
    
    # Sort by total hours descending
    sorted_facilitators = sorted(
        facilitator_stats.items(), 
        key=lambda x: x[1]['total_hours'], 
        reverse=True
    )
    
    for fac_id, stats in sorted_facilitators:
        total_hours = stats['total_hours']
        min_target = stats['min_hours_target']
        max_target = stats['max_hours_target']
        unavail_count = len(stats.get('unavailabilities', []))
        
        within_target = "Yes" if min_target <= total_hours <= max_target else "No"
        pct_of_max = (total_hours / max_target * 100) if max_target > 0 else 0
        
        writer.writerow([
            stats['name'],
            stats['email'],
            stats['session_count'],
            stats['lead_count'],
            stats['support_count'],
            f"{total_hours:.1f}",
            min_target,
            max_target,
            within_target,
            f"{pct_of_max:.1f}%",
            f"{stats['avg_score']:.3f}",
            unavail_count
        ])
    
    writer.writerow([])
    
    # === SECTION 5: Facilitator Skill Level Breakdown ===
    writer.writerow(["SKILL LEVELS PER FACILITATOR"])
    writer.writerow([
        "Facilitator Name",
        "Proficient",
        "Have Run Before", 
        "Have Some Skill",
        "No Interest"
    ])
    
    # Build skill breakdown per facilitator
    for fac_id, stats in sorted_facilitators:
        skill_counts = {
            'Proficient': 0,
            'Have Run Before': 0,
            'Have Some Skill': 0,
            'No Interest': 0
        }
        
        for session in stats['sessions']:
            skill_level = session.get('skill_level', 'Unknown')
            if skill_level in skill_counts:
                skill_counts[skill_level] += 1
        
        writer.writerow([
            stats['name'],
            skill_counts['Proficient'],
            skill_counts['Have Run Before'],
            skill_counts['Have Some Skill'],
            skill_counts['No Interest']
        ])
    
    writer.writerow([])
    
    # === SECTION 6: Unavailability Information ===
    writer.writerow(["UNAVAILABILITY INFORMATION"])
    writer.writerow([
        "Facilitator Name",
        "Email",
        "Unavailability Count",
        "Unavailability Details"
    ])
    
    # Sort by name for consistency
    sorted_facilitators_for_unavail = sorted(
        facilitator_stats.items(), 
        key=lambda x: x[1]['name']
    )
    
    for fac_id, stats in sorted_facilitators_for_unavail:
        unavailabilities = stats.get('unavailabilities', [])
        
        if not unavailabilities:
            writer.writerow([
                stats['name'],
                stats['email'],
                0,
                "No unavailabilities"
            ])
        else:
            # Format unavailability details
            unavail_details = []
            for unavail in unavailabilities:
                if unavail.is_full_day:
                    detail = f"{unavail.date} (Full Day)"
                else:
                    detail = f"{unavail.date} {unavail.start_time.strftime('%H:%M')}-{unavail.end_time.strftime('%H:%M')}"
                
                # Add recurring info if applicable
                if unavail.recurring_pattern:
                    detail += f" (Recurring: {unavail.recurring_pattern.value})"
                
                unavail_details.append(detail)
            
            # Join all unavailability details with semicolon separator
            unavail_string = "; ".join(unavail_details)
            
            writer.writerow([
                stats['name'],
                stats['email'],
                len(unavailabilities),
                unavail_string
            ])
    
    writer.writerow([])
    
    # === SECTION 7: Facilitator Skill Declarations ===
    if unit_id and all_facilitators:
        writer.writerow(["FACILITATOR SKILL DECLARATIONS"])
        writer.writerow([
            "Facilitator Name",
            "Email",
            "Module",
            "Skill Level"
        ])
        
        # Get all modules for this unit
        modules = Module.query.filter_by(unit_id=unit_id).all()
        
        # Create a comprehensive list of skill declarations
        skill_declarations = []
        
        for facilitator in all_facilitators:
            # Get all skills for this facilitator in this unit
            facilitator_skills = FacilitatorSkill.query.filter(
                FacilitatorSkill.facilitator_id == facilitator.id,
                FacilitatorSkill.module_id.in_([m.id for m in modules])
            ).all()
            
            # Create a lookup dict for quick access
            skill_lookup = {skill.module_id: skill.skill_level for skill in facilitator_skills}
            
            # Add entries for all modules
            for module in modules:
                skill_level = skill_lookup.get(module.id)
                if skill_level:
                    skill_level_name = get_skill_level_name(skill_level)
                else:
                    skill_level_name = "Not Declared"
                
                skill_declarations.append({
                    'facilitator_name': facilitator.full_name,
                    'facilitator_email': facilitator.email,
                    'module_name': f"{module.module_name} ({module.module_type})",
                    'skill_level': skill_level_name
                })
        
        # Sort by facilitator name, then by module name
        skill_declarations.sort(key=lambda x: (x['facilitator_name'], x['module_name']))
        
        # Write to CSV
        for declaration in skill_declarations:
            writer.writerow([
                declaration['facilitator_name'],
                declaration['facilitator_email'],
                declaration['module_name'],
                declaration['skill_level']
            ])
        
        writer.writerow([])
    
    # === SECTION 8: Detailed Assignment List ===
    writer.writerow(["DETAILED ASSIGNMENTS"])
    writer.writerow([
        "Facilitator Name",
        "Email", 
        "Module/Session",
        "Day & Time",
        "Duration (Hours)",
        "Role",
        "Facilitator Skill Level",
        "Assignment Score"
    ])
    
    # Sort by facilitator name, then by session time
    all_assignments = []
    for fac_id, stats in facilitator_stats.items():
        for session in stats['sessions']:
            all_assignments.append({
                'name': stats['name'],
                'email': stats['email'],
                'module': session['module'],
                'time': session['time'],
                'hours': session['hours'],
                'role': session.get('role', 'lead'),
                'skill_level': session['skill_level'],
                'score': session['score']
            })
    
    # Sort by name, then by time
    all_assignments.sort(key=lambda x: (x['name'], x['time']))
    
    for assignment in all_assignments:
        writer.writerow([
            assignment['name'],
            assignment['email'],
            assignment['module'],
            assignment['time'],
            f"{assignment['hours']:.1f}",
            assignment['role'].capitalize(),
            assignment['skill_level'],
            f"{assignment['score']:.3f}"
        ])
    
    writer.writerow([])
    writer.writerow(["END OF REPORT"])
    
    return output.getvalue()
