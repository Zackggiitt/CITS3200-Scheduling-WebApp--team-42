# seed_multiple_swaps.py
"""
Seeds multiple facilitators, sessions, assignments, and swap requests so you can
see multiple items in the Approval Queue and tiles update.

Run: python seed_multiple_swaps.py
"""

from datetime import datetime, timedelta

# --- import your app + db (edit this section if your module name differs) ---
app = None
db = None
models = None

tried = []
for mod in ("app", "application", "wsgi", "main"):
    try:
        m = __import__(mod)
        if hasattr(m, "app"):
            app = getattr(m, "app")
        if hasattr(m, "db"):
            db = getattr(m, "db")
        if app and db:
            break
    except Exception as e:
        tried.append((mod, str(e)))

if not app or not db:
    raise RuntimeError(
        f"Could not import your Flask app/db. Tried: {tried}. "
        "Edit this file to import your actual app + db."
    )

# --- import models from your project ---
from models import (
    db,
    User,
    UserRole,
    Unit,
    Module,
    Session,
    Assignment,
    SwapRequest,
    SwapStatus,
)

def get_or_create_uc():
    uc = User.query.filter(User.role == UserRole.UNIT_COORDINATOR).first()
    if not uc:
        uc = User(
            email="uc@example.com",
            first_name="Unit",
            last_name="Coordinator",
            role=UserRole.UNIT_COORDINATOR,
        )
        db.session.add(uc)
        db.session.flush()
    return uc

def get_or_create_unit(uc):
    unit = Unit.query.first()
    if unit:
        return unit
    unit = Unit(
        unit_code="GENG69",
        unit_name="Engineering Design",
        year=datetime.utcnow().year,
        semester="Semester 1",
        description="Seeded unit for swap testing",
        created_by=uc.id,
        start_date=datetime.utcnow().date(),
        end_date=(datetime.utcnow().date() + timedelta(days=120)),
    )
    db.session.add(unit)
    db.session.flush()
    return unit

def get_or_create_module(unit):
    mod = Module.query.filter_by(unit_id=unit.id, module_name="Swap Test Module").first()
    if not mod:
        mod = Module(unit_id=unit.id, module_name="Swap Test Module", module_type="workshop")
        db.session.add(mod)
        db.session.flush()
    return mod

def create_sessions(mod):
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    s1 = Session(
        module_id=mod.id, session_type="workshop",
        start_time=now + timedelta(days=3, hours=9), end_time=now + timedelta(days=3, hours=12),
        day_of_week=0, location="ENG-101", required_skills=None, max_facilitators=1
    )
    s2 = Session(
        module_id=mod.id, session_type="lab",
        start_time=now + timedelta(days=4, hours=14), end_time=now + timedelta(days=4, hours=17),
        day_of_week=2, location="ENG-202", required_skills=None, max_facilitators=1
    )
    s3 = Session(
        module_id=mod.id, session_type="studio",
        start_time=now + timedelta(days=6, hours=10), end_time=now + timedelta(days=6, hours=12),
        day_of_week=4, location="ENG-303", required_skills=None, max_facilitators=1
    )
    s4 = Session(
        module_id=mod.id, session_type="tutorial",
        start_time=now + timedelta(days=7, hours=15), end_time=now + timedelta(days=7, hours=17),
        day_of_week=5, location="ENG-404", required_skills=None, max_facilitators=1
    )
    db.session.add_all([s1, s2, s3, s4])
    db.session.flush()
    return s1, s2, s3, s4

def get_or_create_facilitator(email, first, last):
    u = User.query.filter_by(email=email).first()
    if not u:
        u = User(email=email, first_name=first, last_name=last, role=UserRole.FACILITATOR)
        db.session.add(u)
        db.session.flush()
    return u

def create_assignments(sessions, facilitators):
    assigns = []
    for sess, fac in zip(sessions, facilitators):
        a = Assignment(session_id=sess.id, facilitator_id=fac.id)
        assigns.append(a)
    db.session.add_all(assigns)
    db.session.flush()
    return assigns

def create_swaps(assigns, facs):
    """
    Create several swaps:
      - Pending #1: Sarah (a1) -> Mike (a2)
      - Pending #2: Priya (a3) -> Luca (a4)
      - Pending #3: Mike (a2)  -> Sarah (a1) (reverse, just to show multiple)
      - Approved this week: Luca (a4) -> Priya (a3)
    """
    now = datetime.utcnow()

    sw1 = SwapRequest(
        requester_id=facs[0].id, target_id=facs[1].id,
        requester_assignment_id=assigns[0].id, target_assignment_id=assigns[1].id,
        reason="Clashes with another class I’m assisting.",
        status=SwapStatus.PENDING, created_at=now - timedelta(hours=6)
    )
    sw2 = SwapRequest(
        requester_id=facs[2].id, target_id=facs[3].id,
        requester_assignment_id=assigns[2].id, target_assignment_id=assigns[3].id,
        reason="Family commitment on that day.",
        status=SwapStatus.PENDING, created_at=now - timedelta(days=1, hours=2)
    )
    sw3 = SwapRequest(
        requester_id=facs[1].id, target_id=facs[0].id,
        requester_assignment_id=assigns[1].id, target_assignment_id=assigns[0].id,
        reason="Prefer to keep my weekday free.",
        status=SwapStatus.PENDING, created_at=now - timedelta(days=2, hours=3)
    )
    sw4 = SwapRequest(
        requester_id=facs[3].id, target_id=facs[2].id,
        requester_assignment_id=assigns[3].id, target_assignment_id=assigns[2].id,
        reason="Traveling later that afternoon.",
        status=SwapStatus.APPROVED,
        created_at=now - timedelta(days=4),
        reviewed_at=now - timedelta(days=1)  # within last 7 days so it counts in “Approved This Week”
    )
    db.session.add_all([sw1, sw2, sw3, sw4])
    db.session.flush()
    return [sw1, sw2, sw3, sw4]

def main():
    with app.app_context():
        uc = get_or_create_uc()
        unit = get_or_create_unit(uc)
        mod = get_or_create_module(unit)
        s1, s2, s3, s4 = create_sessions(mod)

        # four facilitators
        f1 = get_or_create_facilitator("sarah.chen@example.com", "Sarah", "Chen")
        f2 = get_or_create_facilitator("mike.johnson@example.com", "Mike", "Johnson")
        f3 = get_or_create_facilitator("priya.patel@example.com", "Priya", "Patel")
        f4 = get_or_create_facilitator("luca.rossi@example.com", "Luca", "Rossi")

        assigns = create_assignments((s1, s2, s3, s4), (f1, f2, f3, f4))
        swaps = create_swaps(assigns, (f1, f2, f3, f4))

        db.session.commit()

        print("Seed complete ✅")
        print(f"Unit: {unit.unit_code} ({unit.id})")
        print(f"Module: {mod.module_name} ({mod.id})")
        print(f"Sessions: {[s1.id, s2.id, s3.id, s4.id]}")
        print(f"Facilitators: {[f1.email, f2.email, f3.email, f4.email]}")
        print(f"Assignments: {[a.id for a in assigns]}")
        print("Swaps:", [(sw.id, sw.status.name) for sw in swaps])

if __name__ == "__main__":
    main()
