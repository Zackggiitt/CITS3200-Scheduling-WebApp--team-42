from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

class UserRole(Enum):
    ADMIN = "admin"
    FACILITATOR = "facilitator"

class SwapStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# Add new enum for skill levels
class SkillLevel(Enum):
    PROFICIENT = "proficient"
    LEADER = "leader"
    INTERESTED = "interested"
    UNINTERESTED = "uninterested"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.FACILITATOR)
    
    # OAuth related fields
    oauth_provider = db.Column(db.String(50), nullable=True)
    oauth_id = db.Column(db.String(255), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    
    # Facilitator specific fields - Updated to store skill levels
    skills_with_levels = db.Column(db.Text)  # JSON string of {skill: level} pairs
    preferences = db.Column(db.Text)  # JSON string of preferences
    
    # Keep old skills field for backward compatibility
    skills = db.Column(db.Text)  # JSON string of skills
    
    # Relationships
    availability = db.relationship('Availability', backref='user', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='facilitator', lazy=True)
    swap_requests_made = db.relationship('SwapRequest', foreign_keys='SwapRequest.requester_id', backref='requester', lazy=True)
    swap_requests_received = db.relationship('SwapRequest', foreign_keys='SwapRequest.target_id', backref='target', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email} ({self.role.value}))>'

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(200), nullable=False)
    session_type = db.Column(db.String(100))  # lab, tutorial, etc.
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    required_skills = db.Column(db.Text)  # JSON string of required skills
    max_facilitators = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('Assignment', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Session {self.course_name} - {self.start_time}>'

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Availability {self.user.email} - Day {self.day_of_week}>'

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    facilitator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_confirmed = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Assignment {self.facilitator.email} -> {self.session.course_name}>'

class SwapRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requester_assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    target_assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.Enum(SwapStatus), default=SwapStatus.PENDING)
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    requester_assignment = db.relationship('Assignment', foreign_keys=[requester_assignment_id])
    target_assignment = db.relationship('Assignment', foreign_keys=[target_assignment_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f'<SwapRequest {self.requester.email} <-> {self.target.email} ({self.status.value})>'

# Add after existing models
class FacilitatorSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    facilitator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    skill_level = db.Column(db.Enum(SkillLevel), nullable=False, default=SkillLevel.INTERESTED)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    facilitator = db.relationship('User', backref=db.backref('facilitator_skills', lazy=True, cascade='all, delete-orphan'))
    
    # Unique constraint to prevent duplicate skill entries for same user
    __table_args__ = (db.UniqueConstraint('facilitator_id', 'skill_name', name='unique_facilitator_skill'),)
    
    def __repr__(self):
        return f'<FacilitatorSkill {self.facilitator.email} - {self.skill_name}: {self.skill_level.value}>'
