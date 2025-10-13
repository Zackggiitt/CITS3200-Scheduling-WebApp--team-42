"""
Script to inject skills for facilitators.

This script provides multiple methods to add skills to facilitators:
1. Random skill assignment
2. Assign all skills to all facilitators
3. Assign specific skills to specific facilitators
4. Clear existing skills

Usage:
    python inject_facilitator_skills.py --mode random
    python inject_facilitator_skills.py --mode all
    python inject_facilitator_skills.py --mode clear
"""

import os
import sys
import argparse
import random
from typing import List, Optional

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User, UserRole, Module, FacilitatorSkill, SkillLevel
from flask import Flask


def create_minimal_app():
    """Create a minimal Flask app for database operations."""
    app = Flask(__name__)
    
    # Use the database path from environment or default to dev.db
    # This matches the configuration in application.py
    database_url = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    db.init_app(app)
    return app


def get_all_facilitators() -> List[User]:
    """Get all facilitators from the database."""
    return User.query.filter_by(role=UserRole.FACILITATOR).all()


def get_all_modules() -> List[Module]:
    """Get all modules from the database."""
    return Module.query.all()


def clear_all_skills():
    """Clear all existing facilitator skills."""
    count = FacilitatorSkill.query.count()
    FacilitatorSkill.query.delete()
    db.session.commit()
    print(f"✓ Cleared {count} existing skill assignments")


def clear_facilitator_skills(facilitator_id: int):
    """Clear skills for a specific facilitator."""
    FacilitatorSkill.query.filter_by(facilitator_id=facilitator_id).delete()


def inject_random_skills(min_skills: int = 2, max_skills: int = 8):
    """
    Assign random skills to all facilitators.
    
    Args:
        min_skills: Minimum number of skills per facilitator
        max_skills: Maximum number of skills per facilitator
    """
    facilitators = get_all_facilitators()
    modules = get_all_modules()
    
    if not facilitators:
        print("⚠ No facilitators found in database")
        return
    
    if not modules:
        print("⚠ No modules found in database")
        return
    
    print(f"Found {len(facilitators)} facilitators and {len(modules)} modules")
    
    # Clear existing skills
    clear_all_skills()
    
    skill_levels = [SkillLevel.HAVE_SOME_SKILL, SkillLevel.PROFICIENT, SkillLevel.HAVE_RUN_BEFORE]
    added_count = 0
    
    for facilitator in facilitators:
        # Randomly select number of skills for this facilitator
        num_skills = random.randint(min_skills, min(max_skills, len(modules)))
        
        # Randomly select modules
        selected_modules = random.sample(modules, num_skills)
        
        for module in selected_modules:
            # Randomly select skill level with weighted distribution
            # More interested/proficient than leaders
            skill_level = random.choices(
                skill_levels,
                weights=[40, 50, 10],  # 40% interested, 50% proficient, 10% leader
                k=1
            )[0]
            
            facilitator_skill = FacilitatorSkill(
                facilitator_id=facilitator.id,
                module_id=module.id,
                skill_level=skill_level
            )
            db.session.add(facilitator_skill)
            added_count += 1
        
        print(f"  ✓ {facilitator.full_name}: {num_skills} skills assigned")
    
    db.session.commit()
    print(f"\n✓ Successfully added {added_count} skill assignments to {len(facilitators)} facilitators")


def inject_all_skills_to_all(default_level: SkillLevel = SkillLevel.HAVE_SOME_SKILL):
    """
    Assign all modules as skills to all facilitators.
    
    Args:
        default_level: Default skill level for all assignments
    """
    facilitators = get_all_facilitators()
    modules = get_all_modules()
    
    if not facilitators:
        print("⚠ No facilitators found in database")
        return
    
    if not modules:
        print("⚠ No modules found in database")
        return
    
    print(f"Found {len(facilitators)} facilitators and {len(modules)} modules")
    
    # Clear existing skills
    clear_all_skills()
    
    added_count = 0
    
    for facilitator in facilitators:
        for module in modules:
            facilitator_skill = FacilitatorSkill(
                facilitator_id=facilitator.id,
                module_id=module.id,
                skill_level=default_level
            )
            db.session.add(facilitator_skill)
            added_count += 1
        
        print(f"  ✓ {facilitator.full_name}: {len(modules)} skills assigned")
    
    db.session.commit()
    print(f"\n✓ Successfully added {added_count} skill assignments")


def inject_specific_skills(email: str, module_names: List[str], skill_level: SkillLevel):
    """
    Assign specific modules to a specific facilitator.
    
    Args:
        email: Facilitator email
        module_names: List of module names
        skill_level: Skill level to assign
    """
    facilitator = User.query.filter_by(email=email, role=UserRole.FACILITATOR).first()
    
    if not facilitator:
        print(f"⚠ Facilitator with email '{email}' not found")
        return
    
    # Clear existing skills for this facilitator
    clear_facilitator_skills(facilitator.id)
    
    added_count = 0
    
    for module_name in module_names:
        module = Module.query.filter_by(module_name=module_name).first()
        if not module:
            print(f"  ⚠ Module '{module_name}' not found")
            continue
        
        facilitator_skill = FacilitatorSkill(
            facilitator_id=facilitator.id,
            module_id=module.id,
            skill_level=skill_level
        )
        db.session.add(facilitator_skill)
        added_count += 1
        print(f"  ✓ Added skill: {module_name} ({skill_level.value})")
    
    db.session.commit()
    print(f"\n✓ Successfully added {added_count} skills to {facilitator.full_name}")


def inject_distributed_skills():
    """
    Assign skills in a realistic distribution pattern:
    - Each facilitator gets 3-6 skills
    - Each module is assigned to multiple facilitators
    - Skill levels are distributed realistically
    """
    facilitators = get_all_facilitators()
    modules = get_all_modules()
    
    if not facilitators:
        print("⚠ No facilitators found in database")
        return
    
    if not modules:
        print("⚠ No modules found in database")
        return
    
    print(f"Found {len(facilitators)} facilitators and {len(modules)} modules")
    
    # Clear existing skills
    clear_all_skills()
    
    added_count = 0
    
    for facilitator in facilitators:
        # Each facilitator gets 3-6 skills
        num_skills = random.randint(3, min(6, len(modules)))
        selected_modules = random.sample(modules, num_skills)
        
        for i, module in enumerate(selected_modules):
            # First skill is often their strongest (leader/proficient)
            if i == 0:
                skill_level = random.choice([SkillLevel.HAVE_RUN_BEFORE, SkillLevel.PROFICIENT])
            # Most skills are proficient or interested
            else:
                skill_level = random.choices(
                    [SkillLevel.HAVE_SOME_SKILL, SkillLevel.PROFICIENT, SkillLevel.HAVE_RUN_BEFORE],
                    weights=[30, 60, 10],
                    k=1
                )[0]
            
            facilitator_skill = FacilitatorSkill(
                facilitator_id=facilitator.id,
                module_id=module.id,
                skill_level=skill_level
            )
            db.session.add(facilitator_skill)
            added_count += 1
        
        print(f"  ✓ {facilitator.full_name}: {num_skills} skills assigned")
    
    db.session.commit()
    print(f"\n✓ Successfully added {added_count} skill assignments to {len(facilitators)} facilitators")


def list_facilitators_and_skills():
    """List all facilitators and their current skills."""
    facilitators = get_all_facilitators()
    
    if not facilitators:
        print("⚠ No facilitators found in database")
        return
    
    print(f"\n{'='*80}")
    print("FACILITATORS AND THEIR SKILLS")
    print(f"{'='*80}\n")
    
    for facilitator in facilitators:
        skills = FacilitatorSkill.query.filter_by(facilitator_id=facilitator.id).all()
        
        print(f"📧 {facilitator.full_name} ({facilitator.email})")
        
        if not skills:
            print("   No skills assigned\n")
            continue
        
        # Group by skill level
        by_level = {}
        for skill in skills:
            level = skill.skill_level.value
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(skill.module.module_name)
        
        for level in ['leader', 'proficient', 'interested', 'uninterested']:
            if level in by_level:
                modules = ', '.join(sorted(by_level[level]))
                print(f"   {level.upper()}: {modules}")
        
        print(f"   Total: {len(skills)} skills\n")


def main():
    parser = argparse.ArgumentParser(
        description="Inject skills for facilitators",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python inject_facilitator_skills.py --mode random
  python inject_facilitator_skills.py --mode random --min-skills 3 --max-skills 10
  python inject_facilitator_skills.py --mode all --skill-level proficient
  python inject_facilitator_skills.py --mode distributed
  python inject_facilitator_skills.py --mode list
  python inject_facilitator_skills.py --mode clear
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['random', 'all', 'distributed', 'clear', 'list'],
        default='distributed',
        help='Mode for skill injection (default: distributed)'
    )
    
    parser.add_argument(
        '--min-skills',
        type=int,
        default=2,
        help='Minimum number of skills per facilitator (for random mode)'
    )
    
    parser.add_argument(
        '--max-skills',
        type=int,
        default=8,
        help='Maximum number of skills per facilitator (for random mode)'
    )
    
    parser.add_argument(
        '--skill-level',
        choices=['interested', 'proficient', 'leader', 'uninterested'],
        default='interested',
        help='Default skill level (for all mode)'
    )
    
    args = parser.parse_args()
    
    app = create_minimal_app()
    
    with app.app_context():
        print(f"\n{'='*80}")
        print("FACILITATOR SKILLS INJECTION SCRIPT")
        print(f"{'='*80}\n")
        
        if args.mode == 'random':
            print(f"Mode: Random assignment ({args.min_skills}-{args.max_skills} skills per facilitator)\n")
            inject_random_skills(args.min_skills, args.max_skills)
        
        elif args.mode == 'all':
            skill_level = SkillLevel(args.skill_level)
            print(f"Mode: Assign all modules to all facilitators (level: {skill_level.value})\n")
            inject_all_skills_to_all(skill_level)
        
        elif args.mode == 'distributed':
            print("Mode: Realistic distributed assignment\n")
            inject_distributed_skills()
        
        elif args.mode == 'clear':
            print("Mode: Clear all skills\n")
            clear_all_skills()
        
        elif args.mode == 'list':
            list_facilitators_and_skills()
        
        # Always show summary
        if args.mode != 'list':
            print("\n" + "="*80)
            print("SUMMARY")
            print("="*80 + "\n")
            list_facilitators_and_skills()


if __name__ == '__main__':
    main()

