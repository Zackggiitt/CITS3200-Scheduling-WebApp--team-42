# CSV Report Enhancement: Facilitator Skill Declarations Section

## ✅ Feature Implemented

The CSV report now includes a comprehensive **Facilitator Skill Declarations** section that shows ALL skill level declarations for ALL facilitators, including those marked as "Not Interested".

---

## What Was Added

### New Section in CSV Report (Section 7)

**"FACILITATOR SKILL DECLARATIONS"** - A complete matrix showing:
- Every facilitator in the unit's pool
- Every module in the unit
- The skill level each facilitator declared for each module
- **"No Interest"** entries (users who can't be assigned)
- **"Not Declared"** entries (users who haven't set their skill level)

### Sample Output

```csv
FACILITATOR SKILL DECLARATIONS
Facilitator Name,Email,Module,Skill Level
Alice Expert,alice@csvtest.com,Lab B (lab),Proficient
Alice Expert,alice@csvtest.com,Workshop A (workshop),Proficient
Bob NotInterested,bob@csvtest.com,Lab B (lab),No Interest
Bob NotInterested,bob@csvtest.com,Workshop A (workshop),Proficient
Carol Undeclared,carol@csvtest.com,Lab B (lab),Not Declared
Carol Undeclared,carol@csvtest.com,Workshop A (workshop),Not Declared
```

---

## How It Works

### 1. Data Collection
When generating the CSV report, the system now:
- Queries all facilitators assigned to the unit
- Queries all modules in the unit
- Retrieves all FacilitatorSkill records for this unit
- Creates a complete matrix of facilitator × module combinations

### 2. Skill Level Classification
For each facilitator-module pair, the system shows:
- **"Proficient"** - Fully skilled
- **"Have Run Before"** - Previous experience
- **"Have Some Skill"** - Basic capability
- **"No Interest"** - Cannot be assigned (hard constraint)
- **"Not Declared"** - Facilitator hasn't set their skill level

### 3. Report Generation
The section is automatically included when:
- `unit_id` parameter is provided
- `all_facilitators` parameter is provided
- If these parameters are omitted, the section is gracefully skipped (backward compatible)

---

## Benefits for Unit Coordinators

### 1. **Visibility into "No Interest" Declarations** ⭐
- See exactly which facilitators marked which modules as "No Interest"
- Understand why certain facilitators weren't assigned to specific sessions
- Identify if too many facilitators have "No Interest" in critical modules

### 2. **Coverage Gap Analysis** ⭐
- Identify modules with insufficient skilled facilitators
- See which modules have many "Not Declared" entries
- Plan recruitment based on skill gaps

### 3. **Training Needs Planning** ⭐
- Identify facilitators who need training in specific modules
- See which modules need more expertise
- Track skill development over time

### 4. **Complete Audit Trail** ⭐
- Record of all skill declarations at time of scheduling
- Can be compared across multiple scheduling runs
- Helps explain scheduling decisions

---

## Technical Implementation

### Files Modified

1. **`optimization_engine.py`** (lines 359-680)
   - Updated `generate_schedule_report_csv()` function signature
   - Added new parameters: `unit_id`, `all_facilitators`
   - Added Section 7: Facilitator Skill Declarations
   - Renumbered Section 7 → Section 8 (Detailed Assignments)

2. **`unitcoordinator_routes.py`** (lines 2222-2228)
   - Updated call to `generate_schedule_report_csv()`
   - Now passes `unit_id` and `all_facilitators` parameters

3. **`SCHEDULE_REPORT_README.md`**
   - Updated section count (7 → 8 sections)
   - Added detailed documentation for new Section 7
   - Added new use cases and benefits
   - Updated sample report structure

### Code Changes

#### optimization_engine.py
```python
def generate_schedule_report_csv(
    assignments, 
    unit_name="Unit", 
    total_facilitators_in_pool=None, 
    unit_id=None,              # NEW
    all_facilitators=None      # NEW
):
    # ... existing code ...
    
    # === SECTION 7: Facilitator Skill Declarations ===
    if unit_id and all_facilitators:
        writer.writerow(["FACILITATOR SKILL DECLARATIONS"])
        writer.writerow(["Facilitator Name", "Email", "Module", "Skill Level"])
        
        modules = Module.query.filter_by(unit_id=unit_id).all()
        
        for facilitator in all_facilitators:
            facilitator_skills = FacilitatorSkill.query.filter(
                FacilitatorSkill.facilitator_id == facilitator.id,
                FacilitatorSkill.module_id.in_([m.id for m in modules])
            ).all()
            
            skill_lookup = {skill.module_id: skill.skill_level for skill in facilitator_skills}
            
            for module in modules:
                skill_level = skill_lookup.get(module.id)
                if skill_level:
                    skill_level_name = get_skill_level_name(skill_level)
                else:
                    skill_level_name = "Not Declared"
                
                # Write row to CSV
                writer.writerow([
                    facilitator.full_name,
                    facilitator.email,
                    f"{module.module_name} ({module.module_type})",
                    skill_level_name
                ])
```

#### unitcoordinator_routes.py
```python
csv_report = generate_schedule_report_csv(
    assignments, 
    unit_display_name,
    total_facilitators_in_pool=len(facilitators_from_db),
    unit_id=unit_id,              # NEW
    all_facilitators=facilitators_from_db  # NEW
)
```

---

## Testing

### Test Suite: `test_csv_with_skill_declarations.py`

✅ **All 4 tests PASSED:**

1. ✅ **Section exists in CSV** - Verifies the new section appears
2. ✅ **'No Interest' entries shown** - Verifies "No Interest" declarations are visible
3. ✅ **'Not Declared' entries shown** - Verifies undeclared skills are marked
4. ✅ **All facilitator-module combinations present** - Verifies completeness

### Test Scenario

The test creates:
- 3 facilitators (Alice, Bob, Carol)
- 2 modules (Workshop A, Lab B)
- Skill declarations:
  - Alice: Proficient in both
  - Bob: Proficient in Workshop A, **No Interest** in Lab B
  - Carol: **Not Declared** for both

**Result**: CSV correctly shows all 6 combinations (3 facilitators × 2 modules) with proper skill levels including "No Interest" and "Not Declared".

---

## Backward Compatibility

✅ **Fully backward compatible**

- Old code that doesn't pass `unit_id` and `all_facilitators` will work normally
- The new section is only added when both new parameters are provided
- Existing reports continue to work without changes

---

## Example Use Cases

### 1. Investigating Why a Facilitator Wasn't Assigned

**Scenario**: Unit Coordinator wonders why Alice didn't get assigned to Lab B.

**Solution**: Check Section 7 - Facilitator Skill Declarations
- If it shows "No Interest", she can't be assigned (hard constraint)
- If it shows "Not Declared", she should complete her skill profile
- If it shows a skill level, check other sections for the reason (availability, fairness, etc.)

### 2. Planning Module Coverage

**Scenario**: Unit Coordinator needs to ensure adequate coverage for critical modules.

**Solution**: Review Section 7 and count:
- How many facilitators marked "No Interest" (can't be used)
- How many marked "Not Declared" (potential but need to declare)
- How many have actual skills (available pool)

### 3. Training Needs Analysis

**Scenario**: Lab C has many "No Interest" or "Not Declared" entries.

**Solution**: 
- Identify facilitators with "Not Declared" and encourage them to declare
- Consider training for facilitators with "Have Some Skill"
- Plan recruitment if too many have "No Interest"

---

## CSV Report Structure (Updated)

The full CSV report now contains **8 sections**:

1. Overview Statistics
2. Fairness Metrics
3. Skill Level Distribution
4. Per-Facilitator Hours Summary
5. Skill Levels Per Facilitator (for assignments made)
6. Unavailability Information
7. **Facilitator Skill Declarations** ⭐ NEW!
8. Detailed Assignment List

---

## Key Benefits Summary

✅ **Transparency**: See all skill declarations, not just assignments made
✅ **"No Interest" Visibility**: Clearly shows who can't be assigned where
✅ **Coverage Analysis**: Identify gaps in facilitator expertise
✅ **Training Planning**: Use data to plan professional development
✅ **Complete Audit**: Full record of skills at time of scheduling
✅ **Decision Support**: Understand why scheduling decisions were made

---

## Related Files

- `optimization_engine.py` - Report generation logic
- `unitcoordinator_routes.py` - Auto-assignment endpoint
- `SCHEDULE_REPORT_README.md` - User documentation
- `test_csv_with_skill_declarations.py` - Feature tests
- `models.py` - FacilitatorSkill and SkillLevel definitions

---

## Future Enhancements

Potential improvements for future versions:

1. **Aggregate Statistics**: Add summary showing % of facilitators with each skill level per module
2. **Highlight Critical Gaps**: Flag modules where >50% have "No Interest" or "Not Declared"
3. **Historical Comparison**: Compare skill declarations across multiple scheduling runs
4. **Visualization**: Generate charts showing skill coverage per module
5. **Recommendations**: Auto-suggest training needs based on gaps

---

## Summary

✅ **Feature Status**: IMPLEMENTED and TESTED
✅ **Test Results**: ALL TESTS PASSED
✅ **Backward Compatibility**: MAINTAINED
✅ **Documentation**: UPDATED
✅ **User Benefit**: HIGH - Provides critical visibility into facilitator skills and "No Interest" declarations

The CSV report now provides complete transparency into facilitator skill declarations, making it easy for Unit Coordinators to see who marked modules as "Not Interested" and plan accordingly.

