from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from enum import Enum

db = SQLAlchemy()

class UserRole(Enum):
    ADMIN = "admin"
    UNIT_COORDINATOR = "Unit_Coordinator"
    FACILITATOR = "facilitator"
    

class SwapStatus(Enum):
    PENDING = "pending"
    FACILITATOR_PENDING = "facilitator_pending"
    COORDINATOR_PENDING = "coordinator_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FACILITATOR_DECLINED = "facilitator_declined"
    COORDINATOR_DECLINED = "coordinator_declined"

# Add new enum for skill levels
class SkillLevel(Enum):
    PROFICIENT = "proficient"
    LEADER = "leader"
    INTERESTED = "interested"
    UNINTERESTED = "uninterested"

# Add enum for recurring patterns
class RecurringPattern(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

# Add new models for units and modules
class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_code = db.Column(db.String(20), nullable=False)
    unit_name = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)   # ← add this
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_date  = db.Column(db.Date)   # first day unit runs
    end_date    = db.Column(db.Date)   # last day unit runs

    creator = db.relationship("User", backref="units")
    __table_args__ = (
        db.UniqueConstraint("unit_code", "year", "semester", "created_by", name="uq_unit_per_uc"),
    )
    
# models.py
class UnitVenue(db.Model):
    __tablename__ = "unit_venue"
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)

    unit = db.relationship('Unit', backref=db.backref('unit_venues', cascade='all, delete-orphan', lazy=True))
    venue = db.relationship('Venue', backref=db.backref('used_in_units', cascade='all, delete-orphan', lazy=True))

    __table_args__ = (db.UniqueConstraint('unit_id', 'venue_id', name='uq_venue_per_unit'),)



class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    module_name = db.Column(db.String(100), nullable=False)  # e.g., "Lab 1", "Workshop A"
    module_type = db.Column(db.String(50))  # lab, tutorial, lecture, workshop
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    unit = db.relationship('Unit', backref='modules')
    
    def __repr__(self):
        return f'<Module {self.unit.unit_code} - {self.module_name} ({self.module_type})>'

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
    
    # Hours constraints for optimization
    min_hours = db.Column(db.Integer, default=0)
    max_hours = db.Column(db.Integer, default=20)
    
    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.email
    
    def set_password(self, password):
        """Set password hash"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        from werkzeug.security import check_password_hash
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    # Relationships
    availability = db.relationship('Availability', backref='user', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='facilitator', lazy=True)
    swap_requests_made = db.relationship('SwapRequest', foreign_keys='SwapRequest.requester_id', backref='requester', lazy=True)
    swap_requests_received = db.relationship('SwapRequest', foreign_keys='SwapRequest.target_id', backref='target', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email} ({self.role.value}))>'

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    session_type = db.Column(db.String(100))  # lab, tutorial, etc.
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    day_of_week = db.Column(db.Integer)  # 0=Monday, 6=Sunday for recurring sessions
    location = db.Column(db.String(200))
    required_skills = db.Column(db.Text)  # JSON string of required skills
    max_facilitators = db.Column(db.Integer, default=1)
    lead_staff_required = db.Column(db.Integer, default=1)  # Number of lead staff required
    support_staff_required = db.Column(db.Integer, default=0)  # Number of support staff required
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    module = db.relationship('Module', backref='sessions')
    assignments = db.relationship('Assignment', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Session {self.module.module_name} - {self.start_time}>'
    
class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    capacity = db.Column(db.Integer, nullable=True)  # optional
    location = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<Venue {self.name}>"
    
class Facilitator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    staff_number = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Facilitator {self.first_name} {self.last_name}>'
    
class UnitFacilitator(db.Model):
    __tablename__ = "unit_facilitator"

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    unit = db.relationship('Unit', backref=db.backref('unit_facilitators', cascade='all, delete-orphan', lazy=True))
    user = db.relationship('User', backref=db.backref('facilitated_units', cascade='all, delete-orphan', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('unit_id', 'user_id', name='uq_facilitator_per_unit'),
    )

    def __repr__(self):
        return f'<UnitFacilitator unit={self.unit_id} user={self.user_id}>'



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

class Unavailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # Specific date instead of day_of_week
    start_time = db.Column(db.Time, nullable=True)  # Nullable for full day unavailability
    end_time = db.Column(db.Time, nullable=True)  # Nullable for full day unavailability
    is_full_day = db.Column(db.Boolean, default=False)  # Flag for full day unavailability
    recurring_pattern = db.Column(db.Enum(RecurringPattern), nullable=True)  # Enum for recurring pattern
    recurring_end_date = db.Column(db.Date, nullable=True)  # When recurring pattern ends
    recurring_interval = db.Column(db.Integer, default=1)  # For custom patterns (e.g., every 2 weeks)
    reason = db.Column(db.Text, nullable=True)  # Optional reason for unavailability
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='unavailabilities')
    unit = db.relationship('Unit', backref='unavailabilities')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('user_id', 'unit_id', 'date', 'start_time', 'end_time', name='unique_unavailability_slot'),
    )
    
    def __repr__(self):
        if self.is_full_day:
            return f'<Unavailability {self.user.email} - {self.unit.unit_code} - {self.date} (Full Day)>'
        else:
            return f'<Unavailability {self.user.email} - {self.unit.unit_code} - {self.date} ({self.start_time}-{self.end_time})>'
    
    @property
    def is_recurring(self):
        """Check if this unavailability is part of a recurring pattern"""
        return self.recurring_pattern is not None
    
    def get_recurring_dates(self):
        """Generate all dates for this recurring unavailability pattern"""
        if not self.is_recurring or not self.recurring_end_date:
            return [self.date]
        
        dates = [self.date]
        current_date = self.date
        
        while current_date < self.recurring_end_date:
            if self.recurring_pattern == RecurringPattern.DAILY:
                current_date = current_date + timedelta(days=self.recurring_interval)
            elif self.recurring_pattern == RecurringPattern.WEEKLY:
                current_date = current_date + timedelta(weeks=self.recurring_interval)
            elif self.recurring_pattern == RecurringPattern.MONTHLY:
                # Simple monthly increment (doesn't handle month-end edge cases)
                year = current_date.year
                month = current_date.month + self.recurring_interval
                if month > 12:
                    year += 1
                    month -= 12
                try:
                    current_date = current_date.replace(year=year, month=month)
                except ValueError:
                    # Handle month-end edge cases
                    current_date = current_date.replace(year=year, month=month, day=1) - timedelta(days=1)
            
            if current_date <= self.recurring_end_date:
                dates.append(current_date)
        
        return dates

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    facilitator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_confirmed = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Assignment {self.facilitator.email} -> {self.session.module.module_name}>'

class SwapRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requester_assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    target_assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.Enum(SwapStatus), default=SwapStatus.FACILITATOR_PENDING)
    
    # Two-step approval process fields
    facilitator_confirmed = db.Column(db.Boolean, default=False)
    facilitator_confirmed_at = db.Column(db.DateTime)
    facilitator_decline_reason = db.Column(db.Text)
    coordinator_decline_reason = db.Column(db.Text)
    
    # Legacy fields (keeping for backward compatibility)
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
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    skill_level = db.Column(db.Enum(SkillLevel), nullable=False, default=SkillLevel.INTERESTED)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    facilitator = db.relationship('User', backref=db.backref('facilitator_skills', lazy=True, cascade='all, delete-orphan'))
    module = db.relationship('Module', backref='facilitator_skills')
    
    __table_args__ = (
        db.UniqueConstraint('facilitator_id', 'module_id', name='unique_facilitator_module_skill'),
    )
    
    def __repr__(self):
        return f'<FacilitatorSkill {self.facilitator.email} - {self.module.module_name} ({self.skill_level.value})>'
    
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.user.email} - {self.message[:20]}>'

