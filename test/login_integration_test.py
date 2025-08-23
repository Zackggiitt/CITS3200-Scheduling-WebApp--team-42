import pytest
from flask import Flask, session, url_for
from application import app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash

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

def test_login_to_dashboard_flow(test_app, client, app_context):
    """Test complete login flow through to dashboard access"""
    # Attempt login
    response = client.post('/login', data={
        'email': 'test@test.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verify session is set
    with client.session_transaction() as sess:
        assert sess['authenticated'] == True
        assert sess['role'] == UserRole.FACILITATOR.value
    
    # Try accessing dashboard
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_failed_login_redirect(test_app, client, app_context):
    """Test failed login attempt and proper redirection"""
    response = client.post('/login', data={
        'email': 'test@test.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invalid credentials' in response.data
    
    # Verify no session was created
    with client.session_transaction() as sess:
        assert 'authenticated' not in sess

def test_protected_route_access(test_app, client, app_context):
    """Test accessing protected routes with and without authentication"""
    # Try accessing protected route without login
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data
    
    # Login and try again
    client.post('/login', data={
        'email': 'test@test.com',
        'password': 'password123'
    })
    
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data