import unittest
from flask import Flask, session
from application import app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash
from auth import set_user_session, clear_user_session

class TestSessionHandling(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-key'
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test user within a session
        self.test_user = User(
            email='test@test.com',
            first_name='Test',
            last_name='User',
            role=UserRole.FACILITATOR,
            password_hash=generate_password_hash('password123')
        )
        db.session.add(self.test_user)
        db.session.commit()

    def test_set_user_session(self):
        
        with self.app.test_request_context():
            user = User.query.filter_by(email='test@test.com').first()
            result = set_user_session(user)
            self.assertTrue(result)
            self.assertEqual(session['user_id'], user.id)
            self.assertEqual(session['role'], user.role.value)
            self.assertTrue(session['authenticated'])

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

if __name__ == '__main__':
    unittest.main()
    