"""
Message Model - Represents a single message in a chat session
"""
from datetime import datetime
from app import db
# region agent log
from app.utils.debug_log import dbg
dbg("A", "backend/app/models/message.py:8", "import_message_module_enter", {"note": "about to declare Message model"})
# endregion


class Message(db.Model):
    """
    Message entity representing a single message in a conversation.
    Stores both user messages and AI responses.
    """
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Message content
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    
    # AI-specific metadata
    # SQLAlchemy reserves the attribute name `metadata` on Declarative models.
    # Keep the DB column name as `metadata`, but map it to a safe Python attribute.
    meta = db.Column('metadata', db.JSON)
    """
    Example metadata structure:
    For assistant messages:
    {
        'model': 'gpt-4o-mini',
        'tokens_used': 150,
        'processing_time_ms': 1200,
        'wines_suggested': [1, 5, 8],
        'confidence': 0.92,
        'intent_detected': 'wine_recommendation',
        'entities': {
            'wine_type': 'red',
            'food': 'beef',
            'budget': 'medium'
        }
    }
    
    For user messages:
    {
        'language_detected': 'it',
        'sentiment': 'positive',
        'intent': 'request_recommendation'
    }
    """
    
    # Products mentioned/recommended in this message
    products_mentioned = db.Column(db.JSON)  # List of product IDs
    
    # Response quality metrics
    was_helpful = db.Column(db.Boolean)  # User feedback
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Message {self.role}: {self.content[:50]}...>'
    
    def to_dict(self, include_metadata=False):
        """Convert message to dictionary for API responses"""
        data = {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'products_mentioned': self.products_mentioned,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_metadata and self.meta:
            data['metadata'] = self.meta
        
        return data
    
    @staticmethod
    def create_user_message(session_id, content, metadata=None):
        """Factory method for creating user messages"""
        return Message(
            session_id=session_id,
            role='user',
            content=content,
            meta=metadata
        )
    
    @staticmethod
    def create_assistant_message(session_id, content, metadata=None, products=None):
        """Factory method for creating assistant messages"""
        return Message(
            session_id=session_id,
            role='assistant',
            content=content,
            meta=metadata,
            products_mentioned=products
        )
    
    @staticmethod
    def create_system_message(session_id, content):
        """Factory method for creating system messages (not shown to user)"""
        return Message(
            session_id=session_id,
            role='system',
            content=content
        )


# Indexes for better query performance
db.Index('idx_messages_session_id', Message.session_id)
db.Index('idx_messages_role', Message.role)
db.Index('idx_messages_created_at', Message.created_at)
db.Index('idx_messages_session_created', Message.session_id, Message.created_at)

