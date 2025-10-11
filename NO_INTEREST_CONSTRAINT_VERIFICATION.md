# NO_INTEREST Constraint Verification Report

## Executive Summary

✅ **VERIFIED**: Users marked as "Not Interested" (NO_INTEREST skill level) in a given session **ARE NOT** allocated to that session.

✅ **VERIFIED**: This behavior is correctly represented in the generated CSV report.

## Test Results

### Unit Tests (test_no_interest_constraint.py)

All unit tests **PASSED** ✅

1. **Skill Constraint Check**: `check_skill_constraint()` correctly returns `False` for NO_INTEREST
2. **Score Calculation**: `calculate_facilitator_score()` returns `0.0` (blocking assignment) for NO_INTEREST
3. **Skill Score Mapping**: NO_INTEREST correctly mapped to score of `0.0`
4. **Score Ordering**: Skill scores correctly ordered: NO_INTEREST (0.0) < HAVE_SOME_SKILL (0.5) < HAVE_RUN_BEFORE (0.8) < PROFICIENT (1.0)

### Integration Tests (test_no_interest_integration.py)

Integration test **PASSED** with important findings ✅

**Test Setup:**
- Facilitator 1 (Alice): NO_INTEREST in Python, PROFICIENT in Java
- Facilitator 2 (Bob): PROFICIENT in Python, NO_INTEREST in Java  
- Facilitator 3 (Carol): HAVE_SOME_SKILL in both modules
- Sessions: 2x Python Workshop, 1x Java Lab

**Results:**
- ✅ Alice was NOT assigned to Python sessions (has NO_INTEREST)
- ✅ Bob was NOT assigned to Java sessions (has NO_INTEREST)
- ✅ NO constraint violations detected in any assignments
- ✅ CSV report correctly shows skill levels for all assignments

## How the Constraint Works

### Hard Constraint Enforcement

The NO_INTEREST constraint is enforced as a **hard constraint** in the optimization engine:

#### 1. Constraint Check (`optimization_engine.py:148-164`)

```python
def check_skill_constraint(facilitator, session):
    """
    Check if facilitator has "no interest" in this session (hard constraint)
    Returns False if facilitator should NOT be assigned (no interest)
    Returns True if facilitator CAN be assigned (any other skill level)
    """
    module_id = session.get('module_id')
    
    if 'skills' in facilitator and module_id in facilitator['skills']:
        skill_level = facilitator['skills'][module_id]
        # Hard constraint: NO_INTEREST means cannot be assigned
        return skill_level != SkillLevel.NO_INTEREST
    
    # If no skill data exists for this module, allow assignment (fallback)
    return True
```

**Key Point**: If a facilitator has explicitly marked a module as NO_INTEREST, they **cannot** be assigned to it.

#### 2. Score Calculation (`optimization_engine.py:166-207`)

```python
def calculate_facilitator_score(facilitator, session, current_assignments, ...):
    """Calculate the score for assigning a facilitator to a session"""
    
    # Skill constraint check (hard constraint - no interest = cannot be assigned)
    if not check_skill_constraint(facilitator, session):
        return 0.0  # Hard constraint violation - no interest in this session
    
    # ... rest of scoring logic
```

**Key Point**: If `check_skill_constraint()` returns False, the score is immediately set to `0.0`, preventing assignment.

#### 3. Assignment Generation (`optimization_engine.py:209-276`)

```python
def generate_optimal_assignments(facilitators):
    """Generate optimal facilitator-to-session assignments"""
    # ...
    for facilitator in facilitators:
        score = calculate_facilitator_score(...)
        if score > best_score:
            best_score = score
            best_facilitator = facilitator
    
    # Assign if we found a suitable facilitator
    if best_facilitator and best_score > 0:
        assignments.append(...)
```

**Key Point**: Only facilitators with score > 0 can be assigned. NO_INTEREST returns 0.0, so they are never selected.

### CSV Report Representation

The CSV report accurately represents skill levels in **three sections**:

#### Section 3: Skill Level Distribution

```csv
SKILL LEVEL DISTRIBUTION
Skill Level,Count,Percentage
Have Run Before,18,40.0%
Have Some Skill,15,33.3%
Proficient,10,22.2%
No Interest,0,0.0%
```

Shows aggregate counts of assignments at each skill level. **0** "No Interest" assignments indicates the constraint is working.

#### Section 5: Skill Levels Per Facilitator

```csv
SKILL LEVELS PER FACILITATOR
Facilitator Name,Proficient,Have Run Before,Have Some Skill,No Interest
Alice Johnson,2,2,1,0
Bob Smith,1,2,1,0
```

Shows breakdown of skill levels for each facilitator's assignments. **0** in "No Interest" column confirms no such assignments.

#### Section 7: Detailed Assignments

```csv
DETAILED ASSIGNMENTS
Facilitator Name,Email,Module/Session,Day & Time,Duration (Hours),Facilitator Skill Level,Assignment Score
Alice Johnson,alice@gmail.com,GENG2000 - Workshop-01,Monday 09:00-11:00,2.0,Proficient,0.950
```

Shows specific skill level for each individual assignment. "Facilitator Skill Level" will **never** be "No Interest" for actual assignments.

## Important Behavioral Notes

### Fallback Behavior for Missing Skill Data

There is an important distinction in how the system handles facilitators who:
1. **Explicitly marked NO_INTEREST**: Cannot be assigned (hard constraint)
2. **Haven't declared any skill level**: Can be assigned (fallback behavior)

This is intentional design:
- If every facilitator had to declare skills for every module, the system would be too rigid
- Allowing assignments when skill data is missing provides flexibility
- Unit coordinators should encourage facilitators to declare skill levels

### Skill Score Calculation

When determining assignment quality, the system uses these scores:

```python
SKILL_SCORES = {
    SkillLevel.PROFICIENT: 1.0,        # Best match
    SkillLevel.HAVE_RUN_BEFORE: 0.8,   # Good match
    SkillLevel.HAVE_SOME_SKILL: 0.5,   # Acceptable match
    SkillLevel.NO_INTEREST: 0.0        # Not allowed
}
```

The system prefers higher-skilled facilitators but will assign lower-skilled ones if needed.

## Documentation References

### Code Locations

1. **Constraint Check**: `optimization_engine.py:148-164`
2. **Score Calculation**: `optimization_engine.py:166-207`
3. **Assignment Generation**: `optimization_engine.py:209-276`
4. **CSV Report Generation**: `optimization_engine.py:359-665`
5. **Skill Scores Mapping**: `optimization_engine.py:28-33`

### Documentation

1. **Algorithm Documentation**: `SCHEDULE_REPORT_README.md:177-182`
   > "Skill Interest: Facilitators with 'no interest' in a module **cannot** be assigned to it"

2. **CSV Report Documentation**: `SCHEDULE_REPORT_README.md:36-41, 60-68, 84-91`
   - Section 3: Skill Level Distribution
   - Section 5: Skill Levels Per Facilitator  
   - Section 7: Detailed Assignments with skill levels

### Route Implementation

Auto-assignment endpoint: `unitcoordinator_routes.py:2141-2248`

This endpoint:
1. Gets facilitators assigned to the unit (line 2165-2171)
2. Prepares facilitator data including skills (line 2180)
3. Generates optimal assignments (line 2183)
4. Creates Assignment records in database (line 2193-2214)
5. Generates CSV report (line 2222-2226)

## Testing

### Running the Tests

```bash
# Unit tests (no database required)
source venv/bin/activate
python test_no_interest_constraint.py

# Integration tests (requires database)
source venv/bin/activate
python test_no_interest_integration.py
```

### Expected Output

Both tests should **PASS** with the following confirmations:

1. ✅ NO_INTEREST constraint blocks assignments
2. ✅ Score calculation returns 0.0 for NO_INTEREST
3. ✅ No facilitators assigned to sessions they're not interested in
4. ✅ CSV report shows accurate skill levels

## Conclusion

The NO_INTEREST constraint is **correctly implemented** and **properly enforced** as a hard constraint in the scheduling system. 

**Key Findings:**

1. ✅ Facilitators explicitly marked as NO_INTEREST cannot be assigned to those sessions
2. ✅ The constraint is enforced before any assignment is made
3. ✅ The CSV report accurately reflects skill levels for all assignments
4. ✅ The system differentiates between "explicit no interest" and "no skill data"
5. ✅ All tests pass successfully

**Recommendation**: The system is working as designed. Unit coordinators should:
- Encourage facilitators to declare their skill levels
- Review CSV reports to verify assignment quality
- Use the "Skill Level Distribution" section to ensure good matches

## Related Files

- `test_no_interest_constraint.py` - Unit tests
- `test_no_interest_integration.py` - Integration tests
- `optimization_engine.py` - Constraint enforcement
- `SCHEDULE_REPORT_README.md` - CSV report documentation
- `models.py` - SkillLevel enum definition
- `unitcoordinator_routes.py` - Auto-assignment endpoint

