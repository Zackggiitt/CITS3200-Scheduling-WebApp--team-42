import unittest
from datetime import datetime, timedelta, date
from flask import json
from application import app, db
from models import User, UserRole, Unit, Module, Session, Assignment, UnitFacilitator
from werkzeug.security import generate_password_hash
import uuid

class TestFacilitatorUnitDashboardAPI(unittest.TestCase):
    def setUp(self):
        """Set up test database and sample data"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Clean up any existing data
        db.drop_all()
        db.create_all()

        # Create unique test users using UUID to avoid conflicts
        test_id = str(uuid.uuid4())[:8]
        self.admin_user = User(
            email=f'admin{test_id}@example.com', 
            first_name='Admin', 
            last_name='User', 
            role=UserRole.ADMIN, 
            password_hash=generate_password_hash('password')
        )
        self.facilitator_user = User(
            email=f'facilitator{test_id}@example.com', 
            first_name='Facilitator', 
            last_name='User', 
            role=UserRole.FACILITATOR, 
            password_hash=generate_password_hash('password')
        )
        self.other_facilitator_user = User(
            email=f'other{test_id}@example.com', 
            first_name='Other', 
            last_name='Facilitator', 
            role=UserRole.FACILITATOR, 
            password_hash=generate_password_hash('password')
        )
        db.session.add_all([self.admin_user, self.facilitator_user, self.other_facilitator_user])
        db.session.commit()

        # Create test units
        self.active_unit = Unit(
            unit_code='CITS1001', 
            unit_name='Introduction to Computing', 
            year=2025, 
            semester='S2', 
            created_by=self.admin_user.id, 
            start_date=date.today() - timedelta(days=10), 
            end_date=date.today() + timedelta(days=50)
        )
        self.past_unit = Unit(
            unit_code='CITS1401', 
            unit_name='Computer Science', 
            year=2025, 
            semester='S1', 
            created_by=self.admin_user.id, 
            start_date=date.today() - timedelta(days=100), 
            end_date=date.today() - timedelta(days=10)
        )
        db.session.add_all([self.active_unit, self.past_unit])
        db.session.commit()

        # Assign facilitator to units
        db.session.add(UnitFacilitator(unit_id=self.active_unit.id, user_id=self.facilitator_user.id))
        db.session.add(UnitFacilitator(unit_id=self.past_unit.id, user_id=self.facilitator_user.id))
        db.session.commit()

        # Create modules for the active unit
        self.module_active = Module(
            unit_id=self.active_unit.id, 
            module_name='Lab A', 
            module_type='lab'
        )
        self.module_active2 = Module(
            unit_id=self.active_unit.id, 
            module_name='Workshop B', 
            module_type='workshop'
        )
        db.session.add_all([self.module_active, self.module_active2])
        db.session.commit()

        # Create sessions for the active unit
        now = datetime.utcnow()
        
        # This week sessions (for KPI calculation)
        self.session_this_week = Session(
            module_id=self.module_active.id, 
            session_type='lab', 
            start_time=now + timedelta(days=1, hours=10), 
            end_time=now + timedelta(days=1, hours=12), 
            location='Room 101'
        )
        
        # Last week session (for total hours calculation)
        self.session_last_week = Session(
            module_id=self.module_active.id, 
            session_type='lab', 
            start_time=now - timedelta(days=7) - timedelta(hours=12), 
            end_time=now - timedelta(days=7) - timedelta(hours=10), 
            location='Room 102'
        )
        
        # Future session (for upcoming sessions)
        self.session_future = Session(
            module_id=self.module_active2.id, 
            session_type='workshop', 
            start_time=now + timedelta(days=14, hours=14), 
            end_time=now + timedelta(days=14, hours=16), 
            location='Room 201'
        )
        
        # Past session (for recent past sessions)
        self.session_past = Session(
            module_id=self.module_active2.id, 
            session_type='workshop', 
            start_time=now - timedelta(days=3) - timedelta(hours=16), 
            end_time=now - timedelta(days=3) - timedelta(hours=14), 
            location='Room 202'
        )
        
        db.session.add_all([
            self.session_this_week, 
            self.session_last_week, 
            self.session_future, 
            self.session_past
        ])
        db.session.commit()

        # Create assignments for the facilitator
        self.assignment_this_week = Assignment(
            session_id=self.session_this_week.id, 
            facilitator_id=self.facilitator_user.id, 
            is_confirmed=True
        )
        self.assignment_last_week = Assignment(
            session_id=self.session_last_week.id, 
            facilitator_id=self.facilitator_user.id, 
            is_confirmed=True
        )
        self.assignment_future = Assignment(
            session_id=self.session_future.id, 
            facilitator_id=self.facilitator_user.id, 
            is_confirmed=False
        )
        self.assignment_past = Assignment(
            session_id=self.session_past.id, 
            facilitator_id=self.facilitator_user.id, 
            is_confirmed=True
        )
        
        db.session.add_all([
            self.assignment_this_week, 
            self.assignment_last_week, 
            self.assignment_future, 
            self.assignment_past
        ])
        db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, user):
        """Helper method to simulate user login"""
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = user.id
                sess['role'] = user.role.value
                sess['authenticated'] = True

    def test_get_unit_dashboard_data_success(self):
        """Test successful retrieval of dashboard data for an authorized unit"""
        self.login(self.facilitator_user)
        response = self.client.get(f'/facilitator/dashboard?unit_id={self.active_unit.id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check unit information
        self.assertIn('unit', data)
        self.assertEqual(data['unit']['id'], self.active_unit.id)
        self.assertEqual(data['unit']['code'], 'CITS1001')
        self.assertEqual(data['unit']['name'], 'Introduction to Computing')
        
        # Check KPIs
        self.assertIn('kpis', data)
        self.assertIn('this_week_hours', data['kpis'])
        self.assertIn('total_hours', data['kpis'])
        self.assertIn('active_sessions', data['kpis'])
        
        # Verify KPI calculations
        # This week should have 2 sessions: session_this_week (tomorrow) and session_past (3 days ago)
        # Both fall within the current week boundaries
        self.assertEqual(data['kpis']['this_week_hours'], 4.0)  # 2 hours each
        self.assertEqual(data['kpis']['active_sessions'], 2)
        
        # Total hours should include all assigned sessions: 4 sessions × 2 hours each = 8 hours total
        self.assertEqual(data['kpis']['total_hours'], 8.0)
        
        # Check sessions
        self.assertIn('sessions', data)
        self.assertIn('upcoming', data['sessions'])
        self.assertIn('recent_past', data['sessions'])
        
        # Should have 2 upcoming sessions (future and this_week) and 2 recent past sessions (past and last_week)
        self.assertEqual(len(data['sessions']['upcoming']), 2)
        self.assertEqual(len(data['sessions']['recent_past']), 2)
        
        # Verify session details - check that we have the expected sessions
        upcoming_modules = [s['module'] for s in data['sessions']['upcoming']]
        past_modules = [s['module'] for s in data['sessions']['recent_past']]
        
        # Should have both Lab A and Workshop B in upcoming (this_week and future sessions)
        self.assertIn('Lab A', upcoming_modules)
        self.assertIn('Workshop B', upcoming_modules)
        
        # Should have both Lab A and Workshop B in recent past (last_week and past sessions)
        self.assertIn('Lab A', past_modules)
        self.assertIn('Workshop B', past_modules)

    def test_get_unit_dashboard_data_unauthorized_unit(self):
        """Test that a facilitator cannot access dashboard data for a unit they are not assigned to"""
        # Assign the other facilitator to a different unit
        other_unit = Unit(
            unit_code='CITS2000', 
            unit_name='Other Unit', 
            year=2025, 
            semester='S2', 
            created_by=self.admin_user.id
        )
        db.session.add(other_unit)
        db.session.commit()
        
        db.session.add(UnitFacilitator(unit_id=other_unit.id, user_id=self.other_facilitator_user.id))
        db.session.commit()
        
        # Try to access the other unit's data as the first facilitator
        self.login(self.facilitator_user)
        response = self.client.get(f'/facilitator/dashboard?unit_id={other_unit.id}')
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'forbidden')

    def test_get_unit_dashboard_data_invalid_unit_id(self):
        """Test handling of invalid unit_id parameter"""
        self.login(self.facilitator_user)
        
        # Test with non-numeric unit_id
        response = self.client.get('/facilitator/dashboard?unit_id=invalid')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'invalid unit_id')
        
        # Test with non-existent unit_id
        response = self.client.get('/facilitator/dashboard?unit_id=99999')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'forbidden')

    def test_get_unit_dashboard_data_unauthorized_user(self):
        """Test that non-facilitator users cannot access the dashboard API"""
        self.login(self.admin_user)
        response = self.client.get(f'/facilitator/dashboard?unit_id={self.active_unit.id}')
        
        # Should redirect to login or return 403
        self.assertIn(response.status_code, [302, 403])

    def test_get_unit_dashboard_data_no_unit_id(self):
        """Test that the endpoint returns HTML dashboard when no unit_id is provided"""
        self.login(self.facilitator_user)
        response = self.client.get('/facilitator/dashboard')
        
        self.assertEqual(response.status_code, 200)
        # Should return HTML content, not JSON
        self.assertIn(b'<!DOCTYPE html>', response.data)

    def test_kpi_calculation_edge_cases(self):
        """Test KPI calculation with edge cases"""
        self.login(self.facilitator_user)
        
        # Create a unit with no sessions to test zero values
        empty_unit = Unit(
            unit_code='CITS9999', 
            unit_name='Empty Unit', 
            year=2025, 
            semester='S2', 
            created_by=self.admin_user.id
        )
        db.session.add(empty_unit)
        db.session.commit()
        
        db.session.add(UnitFacilitator(unit_id=empty_unit.id, user_id=self.facilitator_user.id))
        db.session.commit()
        
        response = self.client.get(f'/facilitator/dashboard?unit_id={empty_unit.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # All KPIs should be zero
        self.assertEqual(data['kpis']['this_week_hours'], 0.0)
        self.assertEqual(data['kpis']['total_hours'], 0.0)
        self.assertEqual(data['kpis']['active_sessions'], 0)
        
        # Sessions should be empty
        self.assertEqual(len(data['sessions']['upcoming']), 0)
        self.assertEqual(len(data['sessions']['recent_past']), 0)

    def test_session_ordering(self):
        """Test that sessions are properly ordered"""
        self.login(self.facilitator_user)
        response = self.client.get(f'/facilitator/dashboard?unit_id={self.active_unit.id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Upcoming sessions should be ordered by start_time ascending
        upcoming = data['sessions']['upcoming']
        if len(upcoming) > 1:
            for i in range(len(upcoming) - 1):
                self.assertLessEqual(
                    upcoming[i]['start_time'], 
                    upcoming[i + 1]['start_time']
                )
        
        # Recent past sessions should be ordered by start_time descending
        recent_past = data['sessions']['recent_past']
        if len(recent_past) > 1:
            for i in range(len(recent_past) - 1):
                self.assertGreaterEqual(
                    recent_past[i]['start_time'], 
                    recent_past[i + 1]['start_time']
                )

    def test_week_boundary_calculation(self):
        """Test that this week calculation uses proper week boundaries"""
        self.login(self.facilitator_user)
        
        # Create a session that's exactly on the week boundary
        now = datetime.utcnow()
        start_of_week = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
        
        boundary_session = Session(
            module_id=self.module_active.id, 
            session_type='lab', 
            start_time=start_of_week, 
            end_time=start_of_week + timedelta(hours=1), 
            location='Room 999'
        )
        db.session.add(boundary_session)
        db.session.commit()
        
        boundary_assignment = Assignment(
            session_id=boundary_session.id, 
            facilitator_id=self.facilitator_user.id, 
            is_confirmed=True
        )
        db.session.add(boundary_assignment)
        db.session.commit()
        
        response = self.client.get(f'/facilitator/dashboard?unit_id={self.active_unit.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should include the boundary session in this week's hours
        # Original 2 sessions (4h) + boundary session (1h) = 5h total
        self.assertEqual(data['kpis']['this_week_hours'], 5.0)  # 4 + 1
        self.assertEqual(data['kpis']['active_sessions'], 3)  # 2 + 1

if __name__ == '__main__':
    unittest.main()
