import unittest
import tempfile
import os
from io import StringIO
from flask import Flask, session
from application import app, db
from models import User, UserRole, Unit, Module, Session, FacilitatorSkill, SkillLevel
from werkzeug.security import generate_password_hash
from auth import set_user_session, clear_user_session

class TestUnitCreationFlow(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-key'
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test Unit Coordinator
        self.uc_user = User(
            email='uc@test.com',
            first_name='Unit',
            last_name='Coordinator',
            role=UserRole.UNIT_COORDINATOR,
            password_hash=generate_password_hash('password123')
        )
        db.session.add(self.uc_user)
        db.session.commit()

        # Create test facilitators
        self.facilitator1 = User(
            email='fac1@test.com',
            first_name='Facilitator',
            last_name='One',
            role=UserRole.FACILITATOR,
            password_hash=generate_password_hash('password123')
        )
        self.facilitator2 = User(
            email='fac2@test.com',
            first_name='Facilitator',
            last_name='Two',
            role=UserRole.FACILITATOR,
            password_hash=generate_password_hash('password123')
        )
        db.session.add(self.facilitator1)
        db.session.add(self.facilitator2)
        db.session.commit()

    def test_complete_unit_creation_flow(self):
        """Test the complete flow from unit creation to session population"""
        
        # Step 1: Login as Unit Coordinator
        with self.app.test_request_context():
            set_user_session(self.uc_user)
        
        # Step 2: Create a unit via the create_unit route
        response = self.client.post('/unitcoordinator/create_unit', data={
            'unit_code': 'TEST1000',
            'unit_name': 'Test Unit',
            'year': '2025',
            'semester': 'Semester 1',
            'description': 'Test unit for verification',
            'start_date': '2025-02-01',
            'end_date': '2025-05-30'
        })
        
        # Should redirect to dashboard on success
        self.assertEqual(response.status_code, 302)
        
        # Verify unit was created
        unit = Unit.query.filter_by(unit_code='TEST1000', created_by=self.uc_user.id).first()
        self.assertIsNotNone(unit)
        self.assertEqual(unit.unit_name, 'Test Unit')
        self.assertEqual(unit.year, 2025)
        self.assertEqual(unit.semester, 'Semester 1')
        
        # Verify default module was created
        default_module = Module.query.filter_by(unit_id=unit.id, module_name='General').first()
        self.assertIsNotNone(default_module)
        
        # Step 3: Upload facilitator CSV
        facilitator_csv = StringIO()
        facilitator_csv.write('facilitator_email\n')
        facilitator_csv.write('fac1@test.com\n')
        facilitator_csv.write('fac2@test.com\n')
        facilitator_csv.seek(0)
        
        response = self.client.post('/unitcoordinator/upload-setup-csv', data={
            'unit_id': str(unit.id),
            'setup_csv': (facilitator_csv, 'facilitators.csv')
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['linked_facilitators'], 2)
        
        # Step 4: Upload CAS CSV to create sessions
        cas_csv = StringIO()
        cas_csv.write('activity_group_code,day_of_week,start_time,duration,weeks,location\n')
        cas_csv.write('Tutorial A,Tuesday,09:00,120,1-12,EZONE 1.24\n')
        cas_csv.write('Lab B,Thursday,14:00,180,1-12,EZONE 2.15\n')
        cas_csv.seek(0)
        
        response = self.client.post(f'/unitcoordinator/units/{unit.id}/upload_cas_csv', data={
            'cas_csv': (cas_csv, 'cas_sessions.csv')
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['ok'])
        self.assertGreater(data['created'], 0)
        
        # Step 5: Verify sessions were created in database
        sessions = Session.query.join(Module).filter(Module.unit_id == unit.id).all()
        self.assertGreater(len(sessions), 0)
        
        # Verify session details
        for session in sessions:
            self.assertIsNotNone(session.start_time)
            self.assertIsNotNone(session.end_time)
            self.assertIsNotNone(session.module)
            self.assertIsNotNone(session.location)
            
        # Step 6: Verify modules were created for each activity
        modules = Module.query.filter_by(unit_id=unit.id).all()
        module_names = [m.module_name for m in modules]
        self.assertIn('Tutorial A', module_names)
        self.assertIn('Lab B', module_names)
        
        # Step 7: Test that facilitators can now input skills for these modules
        # This simulates what would happen when facilitators access their portal
        
        # Create facilitator skills for the modules
        tutorial_module = Module.query.filter_by(unit_id=unit.id, module_name='Tutorial A').first()
        lab_module = Module.query.filter_by(unit_id=unit.id, module_name='Lab B').first()
        
        # Facilitator 1 skills
        skill1 = FacilitatorSkill(
            facilitator_id=self.facilitator1.id,
            module_id=tutorial_module.id,
            skill_level=SkillLevel.PROFICIENT
        )
        skill2 = FacilitatorSkill(
            facilitator_id=self.facilitator1.id,
            module_id=lab_module.id,
            skill_level=SkillLevel.LEADER
        )
        
        # Facilitator 2 skills
        skill3 = FacilitatorSkill(
            facilitator_id=self.facilitator2.id,
            module_id=tutorial_module.id,
            skill_level=SkillLevel.INTERESTED
        )
        skill4 = FacilitatorSkill(
            facilitator_id=self.facilitator2.id,
            module_id=lab_module.id,
            skill_level=SkillLevel.PROFICIENT
        )
        
        db.session.add(skill1)
        db.session.add(skill2)
        db.session.add(skill3)
        db.session.add(skill4)
        db.session.commit()
        
        # Verify skills were created
        facilitator1_skills = FacilitatorSkill.query.filter_by(facilitator_id=self.facilitator1.id).all()
        facilitator2_skills = FacilitatorSkill.query.filter_by(facilitator_id=self.facilitator2.id).all()
        
        self.assertEqual(len(facilitator1_skills), 2)
        self.assertEqual(len(facilitator2_skills), 2)
        
        # Verify skill levels
        self.assertEqual(skill1.skill_level, SkillLevel.PROFICIENT)
        self.assertEqual(skill2.skill_level, SkillLevel.LEADER)
        self.assertEqual(skill3.skill_level, SkillLevel.INTERESTED)
        self.assertEqual(skill4.skill_level, SkillLevel.PROFICIENT)
        
        print(f"✅ Unit Creation Flow Test Passed!")
        print(f"   - Unit created: {unit.unit_code} - {unit.unit_name}")
        print(f"   - Modules created: {len(modules)}")
        print(f"   - Sessions created: {len(sessions)}")
        print(f"   - Facilitators linked: 2")
        print(f"   - Skills recorded: {len(facilitator1_skills + facilitator2_skills)}")

    def test_session_retrieval_for_facilitators(self):
        """Test that sessions are properly retrievable for facilitator skill input"""
        
        # Create a unit and sessions first
        with self.app.test_request_context():
            set_user_session(self.uc_user)
        
        # Create unit
        unit = Unit(
            unit_code='SKILL1000',
            unit_name='Skill Test Unit',
            year=2025,
            semester='Semester 1',
            created_by=self.uc_user.id
        )
        db.session.add(unit)
        db.session.commit()
        
        # Create modules
        tutorial_module = Module(
            unit_id=unit.id,
            module_name='Advanced Tutorial',
            module_type='tutorial'
        )
        lab_module = Module(
            unit_id=unit.id,
            module_name='Research Lab',
            module_type='lab'
        )
        db.session.add(tutorial_module)
        db.session.add(lab_module)
        db.session.commit()
        
        # Create sessions
        from datetime import datetime, timedelta
        start_date = datetime(2025, 2, 4, 9, 0)  # Tuesday 9 AM
        
        session1 = Session(
            module_id=tutorial_module.id,
            session_type='tutorial',
            start_time=start_date,
            end_time=start_date + timedelta(hours=2),
            day_of_week=1,  # Tuesday
            location='EZONE 1.24',
            max_facilitators=1
        )
        
        session2 = Session(
            module_id=lab_module.id,
            session_type='lab',
            start_time=start_date + timedelta(days=2, hours=5),  # Thursday 2 PM
            end_time=start_date + timedelta(days=2, hours=8),  # Thursday 5 PM
            day_of_week=3,  # Thursday
            location='EZONE 2.15',
            max_facilitators=1
        )
        
        db.session.add(session1)
        db.session.add(session2)
        db.session.commit()
        
        # Test that facilitators can retrieve sessions/modules for skill input
        # This would be the API endpoint that facilitators would call
        
        # Simulate facilitator login
        with self.app.test_request_context():
            set_user_session(self.facilitator1)
        
        # Get modules available for skill input (this would be a facilitator route)
        modules_for_skills = Module.query.filter_by(unit_id=unit.id).all()
        
        self.assertEqual(len(modules_for_skills), 2)
        
        # Verify module details
        module_names = [m.module_name for m in modules_for_skills]
        self.assertIn('Advanced Tutorial', module_names)
        self.assertIn('Research Lab', module_names)
        
        # Test skill input for each module
        for module in modules_for_skills:
            skill = FacilitatorSkill(
                facilitator_id=self.facilitator1.id,
                module_id=module.id,
                skill_level=SkillLevel.PROFICIENT
            )
            db.session.add(skill)
        
        db.session.commit()
        
        # Verify skills were recorded
        facilitator_skills = FacilitatorSkill.query.filter_by(facilitator_id=self.facilitator1.id).all()
        self.assertEqual(len(facilitator_skills), 2)
        
        print(f"✅ Session Retrieval Test Passed!")
        print(f"   - Modules available for skills: {len(modules_for_skills)}")
        print(f"   - Skills recorded: {len(facilitator_skills)}")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

if __name__ == '__main__':
    unittest.main()
