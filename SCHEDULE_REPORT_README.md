# Auto-Schedule CSV Report Feature

## Overview
After running the auto-scheduler, you can now download a comprehensive CSV report that provides detailed statistics about the scheduling results.

## How to Use

1. **Run Auto-Assignment**: Click the "Auto-Assign Facilitators" button in the Unit Coordinator dashboard
2. **View Results**: After successful assignment, you'll see a summary alert with assignment details
3. **Download Report**: A "Download Report (CSV)" button will appear next to the Auto-Assign button
4. **Click to Download**: Click the download button to get your detailed CSV report

## Report Contents

The CSV report includes **8 comprehensive sections**:

### 1. Overview Statistics
- Total number of assignments created
- Number of facilitators used
- **Total facilitators in pool** (all available facilitators)
- **Facilitator utilization rate (%)** - percentage of facilitators who got assigned at least one shift
- **Facilitators not assigned** - count of facilitators who didn't receive any assignments
- Total hours scheduled across all sessions
- Average assignment quality score

### 2. Fairness Metrics
- **Minimum hours assigned** to any facilitator
- **Maximum hours assigned** to any facilitator
- **Average hours** per facilitator
- **Standard deviation** of hour distribution
- **Hours range** (difference between max and min)

These metrics help you evaluate how fairly the workload is distributed.

### 3. Skill Level Distribution
- Breakdown of assignments by facilitator skill level:
  - Proficient
  - Have Run Before
  - Have Some Skill
  - No Interest
- Shows both count and percentage for each skill level

### 4. Per-Facilitator Hours Summary
For each facilitator, shows:
- **Name and email**
- **Number of sessions assigned**
- **Total hours assigned**
- **Target hours** (min and max)
- **Within target?** (Yes/No indicator)
- **% of max hours** used
- **Average assignment quality score**
- **Unavailability count** - How many unavailability periods they have

This helps identify:
- Which facilitators are overloaded or underutilized
- Whether assignments respect facilitator hour preferences
- Quality of matches for each facilitator
- How many constraints each facilitator has

### 5. Skill Levels Per Facilitator
Shows how many assignments each facilitator received at each proficiency level:
- **Proficient** - Number of sessions where they had full proficiency
- **Have Run Before** - Sessions where they had previous experience
- **Have Some Skill** - Sessions where they had basic capability
- **No Interest** - Sessions where they had no prior interest/skill

This helps you see if facilitators are being matched appropriately to their skill levels.

### 6. Unavailability Information
Shows the unavailability constraints for each facilitator:
- **Facilitator name and email**
- **Unavailability count** - Number of unavailable periods
- **Unavailability details** - Specific dates and times when unavailable
  - Full day blocks (e.g., "2025-10-15 (Full Day)")
  - Time-specific blocks (e.g., "2025-10-16 14:00-16:00")
  - Recurring patterns (e.g., "2025-10-17 09:00-11:00 (Recurring: weekly)")

This helps you understand:
- Why certain facilitators might not be assigned to specific sessions
- Which facilitators have the most/least constraints
- Whether the scheduler is working around unavailability correctly

### 7. Facilitator Skill Declarations ⭐ NEW!
Shows ALL skill level declarations for ALL facilitators in the pool:
- **Facilitator name and email**
- **Module name** - Each module in the unit
- **Skill level** - Their declared proficiency (Proficient, Have Run Before, Have Some Skill, No Interest, or Not Declared)

This comprehensive matrix helps you:
- **Identify who marked "No Interest"** in which modules
- See gaps in facilitator coverage across modules
- Identify modules that need more skilled facilitators
- Plan training needs based on skill declarations
- Understand why certain facilitators weren't assigned to specific sessions

**Key Features:**
- Shows ALL facilitators, not just those who got assignments
- Shows ALL modules in the unit
- Includes "Not Declared" for facilitators who haven't set skill levels
- **Highlights "No Interest" entries** so you can see who can't be assigned where

### 8. Detailed Assignment List
Complete list of all assignments with:
- Facilitator name and email
- Module/session name
- Day and time
- Duration in hours
- **Facilitator skill level** - Their proficiency for that specific module
- Assignment quality score

## Sample Report Structure

```csv
AUTO-SCHEDULING REPORT - GENG2000 - Engineering Design
Generated: 2025-10-11 19:30:45

OVERVIEW STATISTICS
Metric,Value
Total Assignments,45
Total Facilitators Used,10
Total Facilitators in Pool,15
Facilitators Assigned (%),66.7%
Facilitators Not Assigned,5
Total Hours Scheduled,90.0
Average Assignment Score,0.847

FAIRNESS METRICS
Metric,Value
Minimum Hours Assigned,7.5
Maximum Hours Assigned,11.0
Average Hours Per Facilitator,9.0
Hours Standard Deviation,1.23
Hours Range (Max - Min),3.5

SKILL LEVEL DISTRIBUTION
Skill Level,Count,Percentage
Have Run Before,18,40.0%
Have Some Skill,15,33.3%
Proficient,10,22.2%
No Interest,2,4.4%

FACILITATOR HOURS SUMMARY
Facilitator Name,Email,Sessions Assigned,Total Hours,Min Hours Target,Max Hours Target,Within Target?,% of Max Hours,Avg Assignment Score,Unavailability Count
Alice Johnson,alice@gmail.com,5,11.0,8,16,Yes,68.8%,0.912,3
Bob Smith,bob@gmail.com,4,9.5,6,20,Yes,47.5%,0.867,1
Carol Davis,carol@gmail.com,3,8.0,6,18,Yes,44.4%,0.845,0
...

SKILL LEVELS PER FACILITATOR
Facilitator Name,Proficient,Have Run Before,Have Some Skill,No Interest
Alice Johnson,2,2,1,0
Bob Smith,1,2,1,0
Carol Davis,0,3,2,1
...

UNAVAILABILITY INFORMATION
Facilitator Name,Email,Unavailability Count,Unavailability Details
Alice Johnson,alice@gmail.com,3,2025-10-15 (Full Day); 2025-10-16 14:00-16:00; 2025-10-17 09:00-11:00 (Recurring: weekly)
Bob Smith,bob@gmail.com,1,2025-10-18 10:00-12:00
Carol Davis,carol@gmail.com,0,No unavailabilities
...

FACILITATOR SKILL DECLARATIONS
Facilitator Name,Email,Module,Skill Level
Alice Johnson,alice@gmail.com,Workshop-01 (workshop),Proficient
Alice Johnson,alice@gmail.com,Workshop-02 (workshop),Have Run Before
Alice Johnson,alice@gmail.com,Lab-01 (lab),Have Some Skill
Bob Smith,bob@gmail.com,Workshop-01 (workshop),Have Some Skill
Bob Smith,bob@gmail.com,Workshop-02 (workshop),No Interest
Bob Smith,bob@gmail.com,Lab-01 (lab),Proficient
Carol Davis,carol@gmail.com,Workshop-01 (workshop),No Interest
Carol Davis,carol@gmail.com,Workshop-02 (workshop),Not Declared
Carol Davis,carol@gmail.com,Lab-01 (lab),Have Run Before
...

DETAILED ASSIGNMENTS
Facilitator Name,Email,Module/Session,Day & Time,Duration (Hours),Facilitator Skill Level,Assignment Score
Alice Johnson,alice@gmail.com,GENG2000 - Workshop-01,Monday 09:00-11:00,2.0,Proficient,0.950
Alice Johnson,alice@gmail.com,GENG2000 - Workshop-02,Wednesday 14:00-16:00,2.0,Have Run Before,0.875
Bob Smith,bob@gmail.com,GENG2000 - Lab-01,Tuesday 10:00-12:00,2.0,Have Some Skill,0.820
...

END OF REPORT
```

## Benefits

**Transparency**: Full visibility into scheduling decisions
**Fairness Analysis**: Quickly identify workload imbalances
**Quality Metrics**: Understand how well facilitators match sessions
**Utilization Tracking**: See what % of facilitators are being used
✅ **Skill Matching**: Verify facilitators are assigned to appropriate skill levels
✅ **Proficiency Insights**: See each facilitator's skill level for every assignment
✅ **Unavailability Transparency**: See exactly when and why facilitators are unavailable
✅ **"No Interest" Visibility**: See which facilitators marked which modules as "No Interest" ⭐ NEW!
✅ **Coverage Analysis**: Identify modules with insufficient skilled facilitators ⭐ NEW!
✅ **Training Planning**: Use skill declarations to plan facilitator training needs ⭐ NEW!
✅ **Audit Trail**: Keep records of scheduling runs for reference
✅ **Excel Compatible**: Easy to analyze further in spreadsheet software
✅ **Stakeholder Reports**: Share with management or facilitators

## Technical Details

- **Format**: CSV (Comma-Separated Values)
- **Filename**: `schedule_report_<UNIT_CODE>_<TIMESTAMP>.csv`
- **Character Encoding**: UTF-8
- **Storage**: Report is cached in session for 24 hours
- **Regeneration**: New report created each time auto-assignment runs

### Algorithm Constraints

The auto-scheduler enforces these **hard constraints**:

1. **Availability**: Facilitators must be available during session times
2. **Skill Interest**: Facilitators with "no interest" in a module **cannot** be assigned to it
3. **Hour Limits**: Assignments respect facilitator min/max hour preferences

**Soft constraints** (optimized for but not strictly enforced):
- Fair workload distribution among facilitators
- Skill-level matching (prefer higher proficiency when possible)

## Notes

- The download button only appears after a successful auto-assignment
- If you refresh the page, the button will disappear (run auto-assignment again)
- The report includes all facilitators who received assignments
- Hours are calculated based on session start/end times
- Assignment scores range from 0.0 to 1.0 (higher is better)

## Example Use Cases

1. **Weekly Review**: Download report after each scheduling run to track patterns
2. **Fairness Audit**: Check if certain facilitators consistently get more/less work
3. **Skill Gap Analysis**: Identify if you're over-relying on certain skill levels
4. **Performance Reports**: Share with administrators or department heads
5. **Facilitator Communication**: Share individual statistics with facilitators
6. **Utilization Analysis**: Track what % of facilitators are getting shifts each week
7. **Skill Matching Review**: Verify people aren't being assigned to sessions they're not qualified for
8. **Training Needs**: Identify facilitators who frequently get "No Interest" assignments (may need training)
9. **Workload Redistribution**: Use proficiency data to balance assignments better next time
10. **Constraint Analysis**: See which facilitators have the most unavailability constraints
11. **Scheduling Validation**: Verify the auto-scheduler is working around unavailability correctly
12. **"No Interest" Analysis**: ⭐ NEW! Review which facilitators marked modules as "No Interest" and understand why they weren't assigned
13. **Coverage Planning**: ⭐ NEW! Identify modules where too many facilitators have "No Interest" or haven't declared skills
14. **Recruitment Planning**: ⭐ NEW! Use skill declarations to identify what expertise is needed in future hiring
15. **Facilitator Onboarding**: ⭐ NEW! See which new facilitators haven't declared skills yet and need to complete their profiles

