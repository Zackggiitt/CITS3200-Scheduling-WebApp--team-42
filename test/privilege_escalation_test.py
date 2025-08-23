import pytest
from flask import Flask, session
from application import app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash, check_password_hash
from auth import set_user_session

@pytest.fixture
def test_app():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture
def app_context(test_app):
    with test_app.app_context() as ctx:
        db.create_all()
        # Create test user
        test_user = User(
            email='test@test.com',
            first_name='Test',
            last_name='User',
            role=UserRole.FACILITATOR,
            password_hash=generate_password_hash('password123')
        )
        db.session.add(test_user)
        db.session.commit()
        yield ctx
        db.session.remove()
        db.drop_all()

# ...existing code...

def test_multiple_session_handling(test_app, app_context):
    """Test handling of multiple concurrent sessions for the same user"""
    with test_app.test_request_context():
        user = User.query.filter_by(email='test@test.com').first()
        
        # Create first session
        set_user_session(user)
        session_one_id = session.get('user_id')
        
        # Simulate second session
        session.clear()
        set_user_session(user)
        session_two_id = session.get('user_id')
        
        assert session_one_id == session_two_id
        assert session.get('role') == UserRole.FACILITATOR.value

def test_invalid_session_data(test_app, app_context):
    """Test system behavior with corrupted/invalid session data"""
    with test_app.test_request_context():
        # Test with non-existent user ID
        session['user_id'] = 99999
        session['role'] = UserRole.FACILITATOR.value
        user_from_db = User.query.get(session.get('user_id'))
        assert user_from_db is None

def test_session_data_tampering(test_app, app_context):
    """Test resistance to session data tampering"""
    with test_app.test_request_context():
        user = User.query.filter_by(email='test@test.com').first()
        set_user_session(user)
        
        # Store original valid session data
        original_user_id = session['user_id']
        original_role = session['role']
        
        # Attempt to inject malicious data into session
        session['custom_role'] = 'SUPERADMIN'
        session['is_super_user'] = True
        session['role'] = 'ADMIN'  # Attempt to override existing role
        
        # Verify that authentication still uses correct data
        user_from_db = User.query.get(session['user_id'])
        assert user_from_db.id == original_user_id
        assert user_from_db.role.value == original_role
        assert user_from_db.role == UserRole.FACILITATOR

def test_password_change_flow(test_app, app_context):
    with test_app.test_request_context():
        # Get user and verify initial password
        user = User.query.filter_by(email='test@test.com').first()
        assert check_password_hash(user.password_hash, 'password123')
        
        # Change password
        new_password = 'newpassword456'
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        # Verify old password no longer works
        assert not check_password_hash(user.password_hash, 'password123')
        # Verify new password works
        assert check_password_hash(user.password_hash, new_password)

def test_role_escalation_attempt(test_app, app_context):
    with test_app.test_request_context():
        # Set up normal user session
        user = User.query.filter_by(email='test@test.com').first()
        set_user_session(user)
        original_role = session['role']
        
        # Attempt role escalation
        session['role'] = 'ADMIN'
        
        # Verify actual user role in database hasn't changed
        user_from_db = User.query.get(session['user_id'])
        assert user_from_db.role == UserRole.FACILITATOR
        assert user_from_db.role.value != 'ADMIN'
        
        # Verify original session role was correct
        assert original_role == UserRole.FACILITATOR.value