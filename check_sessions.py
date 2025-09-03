from models import Unit, Module, Session, db
from datetime import datetime

def check_sessions(unit_id=5):
    """Check sessions for a unit"""
    print(f"Checking sessions for unit {unit_id}...")
    
    unit = Unit.query.get(unit_id)
    if not unit:
        print(f"Unit {unit_id} not found!")
        return
    
    print(f"Unit: {unit.unit_code} - {unit.unit_name}")
    print(f"Unit date range: {unit.start_date} to {unit.end_date}")
    print()
    
    # Get all sessions for this unit
    sessions = (
        Session.query
        .join(Module)
        .filter(Module.unit_id == unit.id)
        .order_by(Session.start_time.asc())
        .all()
    )
    
    print(f"Total sessions found: {len(sessions)}")
    print()
    
    if sessions:
        print("First 10 sessions:")
        for i, s in enumerate(sessions[:10], 1):
            print(f"{i}. {s.module.module_name}")
            print(f"   Date: {s.start_time.date()}")
            print(f"   Time: {s.start_time.time()} - {s.end_time.time()}")
            print(f"   Location: {s.location}")
            print(f"   Day: {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][s.day_of_week]}")
            print()
        
        # Check date range
        earliest = min(s.start_time.date() for s in sessions)
        latest = max(s.start_time.date() for s in sessions)
        print(f"Session date range: {earliest} to {latest}")
        
        # Count by month
        from collections import Counter
        months = Counter(s.start_time.strftime('%Y-%m') for s in sessions)
        print(f"Sessions by month: {dict(months)}")
        
    else:
        print("No sessions found!")

if __name__ == "__main__":
    check_sessions()