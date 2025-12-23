"""
User Model - Represents a user account (restaurant owner/staff)
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    """
    User entity representing a restaurant owner or staff member.
    Handles authentication and venue access.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Authentication
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    # Role and Permissions
    role = db.Column(db.String(50), default='owner')  # owner, manager, staff
    permissions = db.Column(db.JSON)  # Granular permissions
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Email verification
    verification_token = db.Column(db.String(255))
    verification_sent_at = db.Column(db.DateTime)
    
    # Password reset
    reset_token = db.Column(db.String(255))
    reset_token_expires_at = db.Column(db.DateTime)
    
    # Login tracking
    last_login_at = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify a password against the hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_venue=False):
        """Convert user to dictionary for API responses"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_venue and self.venue:
            data['venue'] = self.venue.to_dict()
        
        return data
    
    @property
    def full_name(self):
        """Get the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    def has_permission(self, permission):
        """Check if user has a specific permission"""
        if self.role == 'owner':
            return True  # Owners have all permissions
        
        if self.permissions and permission in self.permissions:
            return self.permissions[permission]
        
        # Default permissions by role
        default_permissions = {
            'manager': ['view_products', 'edit_products', 'view_analytics', 'manage_chat'],
            'staff': ['view_products', 'view_analytics']
        }
        
        return permission in default_permissions.get(self.role, [])
    
    def record_login(self):
        """Record a successful login"""
        self.last_login_at = datetime.utcnow()
        self.login_count = (self.login_count or 0) + 1


# Indexes for better query performance
db.Index('idx_users_email', User.email)
db.Index('idx_users_venue_id', User.venue_id)
db.Index('idx_users_is_active', User.is_active)

