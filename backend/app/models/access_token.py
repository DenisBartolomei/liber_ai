"""
Access Token Model - Temporary tokens for B2C access
Prevents URL sharing abuse by making tokens one-time use and time-limited
"""
from datetime import datetime, timedelta
from app import db
import uuid
import logging

logger = logging.getLogger(__name__)


class AccessToken(db.Model):
    """
    Temporary access token for B2C customer sessions.
    Each token can be used only once to create a session.
    Tokens expire after a set time (e.g., 10 minutes).
    """
    __tablename__ = 'access_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Token identification
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Usage tracking
    is_used = db.Column(db.Boolean, default=False, index=True)  # True after first session creation
    used_at = db.Column(db.DateTime, nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    
    # Relationships
    venue = db.relationship('Venue', backref='access_tokens')
    session = db.relationship('Session', backref='access_token_ref')
    
    def __repr__(self):
        return f'<AccessToken {self.token[:8]}... (used={self.is_used})>'
    
    @staticmethod
    def generate_token():
        """Generate a unique token"""
        return str(uuid.uuid4())
    
    def is_valid(self):
        """Check if token is still valid (not used and not expired)"""
        if self.is_used:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def mark_as_used(self, session_id):
        """Mark token as used and associate with session"""
        self.is_used = True
        self.used_at = datetime.utcnow()
        self.session_id = session_id
        db.session.commit()
    
    @staticmethod
    def create_for_venue(venue_id, expires_in_minutes=10):
        """
        Create a new access token for a venue.
        
        Args:
            venue_id: Venue ID
            expires_in_minutes: Token expiration time in minutes (default 10)
            
        Returns:
            AccessToken instance
        """
        token = AccessToken(
            venue_id=venue_id,
            token=AccessToken.generate_token(),
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        )
        db.session.add(token)
        db.session.commit()
        logger.info(f"Created access token {token.token[:8]}... for venue {venue_id}, expires at {token.expires_at}")
        return token

