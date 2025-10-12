from application import app
from models import db, Session, Module, Unit, User, UserRole, Assignment
from datetime import datetime, timedelta, time

with app.app_context():
    # Get the GENG2000 unit
    geng2000 = Unit.query.filter_by(unit_code='GENG2000').first()
    if not geng2000:
        print("GENG2000 unit not found!")
        exit()
    
    # Get some modules
    modules = Module.query.filter_by(unit_id=geng2000.id).limit(4).all()
    if not modules:
        print("No modules found!")
        exit()
    
    # Get some facilitators
    facilitators = User.query.filter_by(role=UserRole.FACILITATOR).limit(3).all()
    if not facilitators:
        print("No facilitators found!")
        exit()
    
    # Create sessions for today and this week
    today = datetime.now().date()
    
    # Clear existing sessions for today and this week
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get session IDs to delete
    session_ids = db.session.query(Session.id).join(Module).filter(
        Module.unit_id == geng2000.id,
        db.func.date(Session.start_time) >= start_of_week,
        db.func.date(Session.start_time) <= end_of_week
    ).all()
    
    if session_ids:
        Session.query.filter(Session.id.in_([s.id for s in session_ids])).delete(synchronize_session=False)
    
    # Create today's sessions
    today_sessions = []
    for i, module in enumerate(modules[:2]):
        start_hour = 9 + i * 3  # 9 AM and 12 PM
        session = Session(
            module_id=module.id,
            session_type='workshop',
            start_time=datetime.combine(today, time(start_hour, 0)),
            end_time=datetime.combine(today, time(start_hour + 2, 0)),
            location=f"EZONE {i+1}.{i+1}5" if i == 0 else "Private session - home",
            max_facilitators=1 if i == 0 else 2
        )
        today_sessions.append(session)
        db.session.add(session)
    
    # Create tomorrow's sessions
    tomorrow = today + timedelta(days=1)
    for i, module in enumerate(modules[2:4]):
        start_hour = 10 + i * 2  # 10 AM and 12 PM
        session = Session(
            module_id=module.id,
            session_type='tutorial',
            start_time=datetime.combine(tomorrow, time(start_hour, 0)),
            end_time=datetime.combine(tomorrow, time(start_hour + 1, 0)),
            location=f"Room {3}.{i+1}1" if i == 0 else "EZONE 2.15",
            max_facilitators=1
        )
        db.session.add(session)
    
    # Create Wednesday's sessions
    wednesday = today + timedelta(days=2)
    for i, module in enumerate(modules[:2]):
        start_hour = 11 + i * 2  # 11 AM and 1 PM
        session = Session(
            module_id=module.id,
            session_type='lab',
            start_time=datetime.combine(wednesday, time(start_hour, 0)),
            end_time=datetime.combine(wednesday, time(start_hour + 2, 0)),
            location=f"Zen Studio" if i == 0 else "Main Lab",
            max_facilitators=2
        )
        db.session.add(session)
    
    db.session.commit()
    
    # Create some assignments for today's sessions
    for i, session in enumerate(today_sessions):
        if i < len(facilitators):
            assignment = Assignment(
                session_id=session.id,
                facilitator_id=facilitators[i].id,
                is_confirmed=True
            )
            db.session.add(assignment)
    
    db.session.commit()
    
    print("✅ Created real sessions for today and this week!")
    print(f"Today's sessions: {len(today_sessions)}")
    print(f"Total facilitators: {len(facilitators)}")
    
    # Show what we created
    today_sessions_db = Session.query.join(Module).filter(
        Module.unit_id == geng2000.id,
        db.func.date(Session.start_time) == today
    ).all()
    
    print("\nToday's sessions:")
    for s in today_sessions_db:
        assignments = Assignment.query.filter_by(session_id=s.id).all()
        facilitator_names = [a.facilitator.first_name + ' ' + a.facilitator.last_name for a in assignments]
        print(f"  - {s.module.module_name}: {s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')} at {s.location}")
        print(f"    Facilitators: {', '.join(facilitator_names) if facilitator_names else 'Unassigned'}")
