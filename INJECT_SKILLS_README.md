# Facilitator Skills Injection Script

This script helps you populate the database with facilitator skills for testing and development purposes.

## Features

- **Random Assignment**: Randomly assign 2-8 skills to each facilitator
- **All Assignment**: Assign all modules to all facilitators
- **Distributed Assignment**: Realistic distribution (3-6 skills per facilitator)
- **Clear Skills**: Remove all existing skill assignments
- **List Skills**: View current skill assignments

## Prerequisites

Make sure you have:
1. Facilitators in the database (created via CSV upload or other methods)
2. Modules in the database
3. Flask environment set up
4. Virtual environment activated

**Important**: Always activate the virtual environment before running the script:

```bash
source venv/bin/activate
```

## Usage

**Note**: All commands below assume you're in the project root directory and have activated the virtual environment.

### 1. Distributed Skills (Recommended for Testing)

Assigns 3-6 skills per facilitator with realistic skill level distribution:

```bash
python inject_facilitator_skills.py --mode distributed
```

### 2. Random Skills

Assigns random number of skills (customizable range):

```bash
# Default: 2-8 skills per facilitator
python inject_facilitator_skills.py --mode random

# Custom range: 3-10 skills per facilitator
python inject_facilitator_skills.py --mode random --min-skills 3 --max-skills 10
```

### 3. All Skills to All Facilitators

Assigns every module to every facilitator:

```bash
# Default: all as "interested"
python inject_facilitator_skills.py --mode all

# All as "proficient"
python inject_facilitator_skills.py --mode all --skill-level proficient

# All as "leader"
python inject_facilitator_skills.py --mode all --skill-level leader
```

### 4. List Current Skills

View all facilitators and their assigned skills:

```bash
python inject_facilitator_skills.py --mode list
```

### 5. Clear All Skills

Remove all skill assignments:

```bash
python inject_facilitator_skills.py --mode clear
```

## Skill Levels

The system supports four skill levels:
- **LEADER**: Can lead and teach the module
- **PROFICIENT**: Competent in the module
- **INTERESTED**: Willing to learn/assist
- **UNINTERESTED**: Prefer not to be assigned

## Examples

### Example 1: Quick Setup for Demo

```bash
# Add realistic skills for all facilitators
python inject_facilitator_skills.py --mode distributed

# View the results
python inject_facilitator_skills.py --mode list
```

### Example 2: Testing with Maximum Coverage

```bash
# Give everyone all skills as proficient
python inject_facilitator_skills.py --mode all --skill-level proficient
```

### Example 3: Reset and Restart

```bash
# Clear all existing skills
python inject_facilitator_skills.py --mode clear

# Add new random distribution
python inject_facilitator_skills.py --mode random --min-skills 4 --max-skills 8
```

## Output

The script provides detailed output including:
- Number of facilitators found
- Number of modules found
- Skills assigned per facilitator
- Total skill assignments
- Summary of all facilitators and their skills

### Sample Output

```
================================================================================
FACILITATOR SKILLS INJECTION SCRIPT
================================================================================

Mode: Realistic distributed assignment

Found 10 facilitators and 15 modules
✓ Cleared 0 existing skill assignments
  ✓ John Doe: 5 skills assigned
  ✓ Jane Smith: 4 skills assigned
  ✓ Bob Johnson: 6 skills assigned
  ...

✓ Successfully added 48 skill assignments to 10 facilitators

================================================================================
SUMMARY
================================================================================

================================================================================
FACILITATORS AND THEIR SKILLS
================================================================================

📧 John Doe (john.doe@example.com)
   LEADER: Python Programming
   PROFICIENT: Data Structures, Web Development
   INTERESTED: Database Systems, Machine Learning
   Total: 5 skills

📧 Jane Smith (jane.smith@example.com)
   PROFICIENT: Algorithms, Computer Networks
   INTERESTED: Operating Systems, Software Engineering
   Total: 4 skills
...
```

## Notes

- The script automatically clears existing skills before adding new ones (except in `list` mode)
- All operations are committed to the database immediately
- Use `--mode list` to verify results without making changes
- Skills are linked to modules via `FacilitatorSkill` model
- Each facilitator-module combination is unique (enforced by database constraint)

## Troubleshooting

**"No facilitators found in database"**
- Make sure facilitators have been added via CSV upload or signup
- Check that users have `role=FACILITATOR`

**"No modules found in database"**
- Create modules first through the unit coordinator dashboard
- Modules must be associated with a unit

**Database errors**
- Ensure the database path is correct (default: `instance/dev.db`)
- Check that you have write permissions to the database file
- Try clearing skills first if you get constraint errors

## Integration with Workflow

This script is typically used:
1. After creating a unit and modules (via UC dashboard)
2. After uploading facilitators (via CSV)
3. Before running the scheduling algorithm
4. For testing and development purposes

The skills created by this script are used by the scheduling algorithm to match facilitators to appropriate sessions.

