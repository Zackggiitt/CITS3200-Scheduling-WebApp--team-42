# Bulk Staffing Implementation - Multiple Facilitators Per Session

## Overview

This implementation adds support for bulk staffing configuration where unit coordinators can specify the number of lead and support staff required for each module/session. The optimization algorithm now respects these settings and assigns the appropriate number of facilitators to each session.

## Changes Made

### 1. Database Model Updates

#### Assignment Model (`models.py`)
Added a `role` field to track whether an assignment is for a lead or support position:

```python
class Assignment(db.Model):
    # ... existing fields ...
    role = db.Column(db.String(20), default='lead')  # 'lead' or 'support'
```

#### Migration Script
Created migration file: `migrations/versions/add_role_to_assignment.py`
- Adds the `role` column to the `assignment` table
- Sets default value to 'lead' for existing records
- Makes the column non-nullable with a default value

### 2. Optimization Engine Updates (`optimization_engine.py`)

#### Enhanced `get_real_sessions()` Function
Now extracts bulk staffing settings from each session:
```python
'lead_staff_required': session.lead_staff_required or 1,
'support_staff_required': session.support_staff_required or 0
```

#### Completely Rewritten `generate_optimal_assignments()` Function
The algorithm now:
1. **Reads staffing requirements** from each session (lead_staff_required, support_staff_required)
2. **Assigns lead staff first** - Uses a scoring bonus to prefer higher-skilled facilitators for lead roles
3. **Assigns support staff second** - Assigns remaining positions after leads are filled
4. **Prevents double-booking** - Ensures the same facilitator isn't assigned multiple roles in the same session
5. **Tracks role information** - Each assignment now includes a 'role' field ('lead' or 'support')

#### Key Algorithm Features:
- **Lead Role Priority**: Lead positions get a 10% skill score bonus to prefer more experienced facilitators
- **Fair Distribution**: Maintains fairness across both lead and support roles
- **Constraint Enforcement**: All hard constraints (availability, time conflicts, location conflicts, no-interest) still apply
- **Detailed Conflict Reporting**: Reports specific failures when lead or support positions can't be filled

#### Updated Reporting Functions
Enhanced CSV report generation to include:
- **Lead/Support counts** per facilitator in the summary section
- **Role column** in the detailed assignments section
- **Better metrics** showing distribution of lead vs support assignments

### 3. API Integration Updates (`unitcoordinator_routes.py`)

#### Auto-Assignment Endpoint
Updated the assignment creation code to include the role field:
```python
new_assignment = Assignment(
    session_id=assignment['session']['id'],
    facilitator_id=assignment['facilitator']['id'],
    is_confirmed=False,
    role=assignment.get('role', 'lead')  # Track lead vs support role
)
```

## How It Works

### Unit Coordinator Workflow

1. **Create Unit**: Set up a unit with modules and sessions
2. **Configure Bulk Staffing**: For each session, specify:
   - Number of lead staff required (default: 1)
   - Number of support staff required (default: 0)
3. **Assign Facilitators**: Add facilitators to the unit
4. **Run Auto-Assignment**: The algorithm automatically:
   - Assigns the specified number of lead staff per session
   - Assigns the specified number of support staff per session
   - Prioritizes higher-skilled facilitators for lead roles
   - Maintains fairness in hour distribution

### Example Scenarios

#### Scenario 1: Simple Lab Session
- Lead staff required: 1
- Support staff required: 0
- Result: 1 facilitator assigned as lead

#### Scenario 2: Large Workshop
- Lead staff required: 2
- Support staff required: 1
- Result: 3 facilitators assigned (2 as leads, 1 as support)

#### Scenario 3: Complex Tutorial
- Lead staff required: 1
- Support staff required: 2
- Result: 3 facilitators assigned (1 as lead, 2 as support)

## Algorithm Logic

### Assignment Priority Order

1. Sessions are sorted by:
   - Duration (longer sessions first)
   - Required skill level (higher first)

2. For each session:
   - **Lead positions filled first** with highest-skilled available facilitators
   - **Support positions filled second** with remaining available facilitators

3. Each facilitator position checks:
   - No time conflicts (hard constraint)
   - No location conflicts (hard constraint)
   - Not already assigned to this session (hard constraint)
   - Availability matches (hard constraint)
   - No "no interest" skill level (hard constraint)
   - Fairness score for hour distribution
   - Skill score for module competency

### Scoring Function

For lead roles:
```
score = (W_availability × availability_match) + 
        (W_fairness × fairness_factor) + 
        (W_skill × skill_score) + 
        (0.1 × skill_score)  // 10% lead bonus
```

For support roles:
```
score = (W_availability × availability_match) + 
        (W_fairness × fairness_factor) + 
        (W_skill × skill_score)
```

## CSV Report Enhancements

The generated schedule report now includes:

### Facilitator Hours Summary
- Sessions Assigned (total)
- **Lead Roles** (count)
- **Support Roles** (count)
- Total Hours
- Other metrics...

### Detailed Assignments
- Facilitator Name
- Email
- Module/Session
- Day & Time
- Duration
- **Role** (Lead/Support)
- Skill Level
- Assignment Score

## Database Schema

### Session Model (existing fields used)
```sql
lead_staff_required INTEGER DEFAULT 1
support_staff_required INTEGER DEFAULT 0
```

### Assignment Model (new field added)
```sql
role VARCHAR(20) DEFAULT 'lead'
```

## Migration Instructions

To apply these changes to an existing database:

1. **Backup your database** before running migrations
2. Run the migration:
   ```bash
   python -m flask db upgrade
   ```
   Or apply the migration manually:
   ```bash
   python migrations/versions/add_role_to_assignment.py
   ```

3. Existing assignments will default to 'lead' role
4. New assignments will respect the bulk staffing configuration

## Testing Recommendations

Test the following scenarios:

1. **Single facilitator per session** (lead_staff_required=1, support_staff_required=0)
2. **Multiple leads** (lead_staff_required=2, support_staff_required=0)
3. **Mixed roles** (lead_staff_required=1, support_staff_required=2)
4. **Large staffing** (lead_staff_required=3, support_staff_required=3)
5. **Insufficient facilitators** - Verify proper conflict reporting
6. **Skill distribution** - Verify leads get higher-skilled facilitators
7. **Fairness** - Verify hours are distributed fairly across leads and supports

## Known Limitations

1. **No explicit lead qualification** - The system uses skill levels as a proxy for lead capability but doesn't have a separate "can lead" flag
2. **Simple scoring bonus** - The 10% lead bonus is fixed and not configurable
3. **No role preferences** - Facilitators cannot express preference for lead vs support roles
4. **Equal hour counting** - Lead and support hours count equally toward min/max hour targets

## Future Enhancements

Potential improvements for future versions:

1. **Lead qualifications** - Add a "can_lead" flag to facilitator profiles
2. **Role preferences** - Allow facilitators to prefer lead or support roles
3. **Weighted hours** - Count lead hours differently from support hours
4. **Dynamic bonuses** - Make the lead skill bonus configurable
5. **Team composition** - Ensure good skill mix within multi-facilitator sessions
6. **Role swapping** - Support swap requests that preserve or change roles

## Support

For issues or questions about bulk staffing:
- Check that `lead_staff_required` and `support_staff_required` are set correctly in the Session model
- Verify facilitators have appropriate skill levels declared
- Review the CSV report for detailed role assignments
- Check conflict messages for specific reasons why positions couldn't be filled

## Summary

The bulk staffing feature is now fully integrated into the optimization algorithm. Unit coordinators can specify exactly how many lead and support staff they need for each session, and the algorithm will automatically assign facilitators to fill those positions while maintaining fairness, respecting constraints, and preferring higher-skilled facilitators for lead roles.

