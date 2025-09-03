# session_check.py
from application import app, db
from models import Session

def list_sessions():
    with app.app_context():
        sessions = Session.query.all()
        if not sessions:
            print("No sessions found.")
            return

        for s in sessions:
            print(f"ID: {s.id}")
            # Print all column values dynamically
            for column in Session.__table__.columns:
                name = column.name
                value = getattr(s, name)
                print(f"  {name}: {value}")
            print("-" * 40)

if __name__ == "__main__":
    list_sessions()
