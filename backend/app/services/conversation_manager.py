"""
Conversation Manager Service for LIBER
Handles session and message management
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from flask import current_app
from app import db
from app.models import Session, Message, User


class ConversationManager:
    """
    Manages chat sessions and messages for both B2B and B2C modes.
    Handles session creation, message storage, and context management.
    """
    
    def __init__(self):
        self.session_timeout = current_app.config.get('SESSION_TIMEOUT_MINUTES', 60)
        self.max_history = current_app.config.get('MAX_CONVERSATION_HISTORY', 20)
    
    def create_session(
        self,
        venue_id: int,
        mode: str,
        user_id: Optional[int] = None,
        device_type: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Session:
        """
        Create a new chat session.
        
        Args:
            venue_id: The venue ID
            mode: 'b2c' for customers, 'b2b' for owners
            user_id: Optional user ID (for B2B)
            device_type: Device type (mobile, tablet, desktop)
            user_agent: Browser user agent
            ip_address: Client IP address
            context: Initial context data
            
        Returns:
            Created Session object
        """
        session = Session(
            venue_id=venue_id,
            user_id=user_id,
            session_token=Session.generate_token(),
            mode=mode,
            device_type=device_type,
            user_agent=user_agent,
            ip_address=ip_address,
            context=context or {},
            status='active'
        )
        
        db.session.add(session)
        db.session.commit()
        
        return session
    
    def get_or_create_b2b_session(self, user: User) -> Session:
        """
        Get or create a B2B session for a user.
        Reuses existing active session if available.
        
        Args:
            user: User object
            
        Returns:
            Session object
        """
        # Look for existing active B2B session
        session = Session.query.filter_by(
            user_id=user.id,
            mode='b2b',
            status='active'
        ).first()
        
        if session:
            # Check if session is still valid (not timed out)
            timeout_threshold = datetime.utcnow() - timedelta(minutes=self.session_timeout * 24)  # B2B sessions last longer
            
            if session.last_activity > timeout_threshold:
                session.update_activity()
                db.session.commit()
                return session
            else:
                # Session expired, mark as completed
                session.end_session(status='timeout')
        
        # Create new session
        return self.create_session(
            venue_id=user.venue_id,
            mode='b2b',
            user_id=user.id
        )
    
    def get_session(self, session_token: str) -> Optional[Session]:
        """
        Get a session by token.
        
        Args:
            session_token: The session token
            
        Returns:
            Session object or None
        """
        return Session.query.filter_by(
            session_token=session_token
        ).first()
    
    def add_message(
        self,
        session: Session,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
        products: Optional[List[int]] = None
    ) -> Message:
        """
        Add a message to a session.
        
        Args:
            session: Session object
            role: 'user', 'assistant', or 'system'
            content: Message content
            metadata: Optional metadata dict
            products: Optional list of product IDs mentioned
            
        Returns:
            Created Message object
        """
        message = Message(
            session_id=session.id,
            role=role,
            content=content,
            meta=metadata,
            products_mentioned=products
        )
        
        db.session.add(message)
        session.increment_message_count()
        session.update_activity()
        db.session.commit()
        
        return message
    
    def get_messages(
        self, 
        session: Session, 
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages for a session.
        
        Args:
            session: Session object
            limit: Max messages to return
            
        Returns:
            List of Message objects
        """
        query = Message.query.filter_by(
            session_id=session.id
        ).order_by(Message.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_conversation_for_ai(
        self, 
        session: Session,
        include_system: bool = False
    ) -> List[Dict]:
        """
        Get conversation history formatted for AI.
        
        Args:
            session: Session object
            include_system: Whether to include system messages
            
        Returns:
            List of message dicts with 'role' and 'content'
        """
        query = Message.query.filter_by(session_id=session.id)
        
        if not include_system:
            query = query.filter(Message.role != 'system')
        
        query = query.order_by(Message.created_at.asc())
        
        # Get last N messages
        messages = query.all()[-self.max_history:]
        
        return [
            {'role': m.role, 'content': m.content}
            for m in messages
        ]
    
    def update_context(
        self, 
        session: Session, 
        context_update: Dict
    ) -> Session:
        """
        Update session context.
        
        Args:
            session: Session object
            context_update: Dict to merge with existing context
            
        Returns:
            Updated Session object
        """
        current_context = session.context or {}
        current_context.update(context_update)
        session.context = current_context
        
        db.session.commit()
        return session
    
    def end_session(
        self, 
        session: Session, 
        status: str = 'completed',
        rating: Optional[int] = None,
        feedback: Optional[str] = None
    ) -> Session:
        """
        End a chat session.
        
        Args:
            session: Session object
            status: End status ('completed', 'abandoned', 'timeout')
            rating: Optional 1-5 rating
            feedback: Optional text feedback
            
        Returns:
            Updated Session object
        """
        session.end_session(status)
        
        if rating is not None:
            session.rating = rating
        
        if feedback:
            session.feedback = feedback
        
        db.session.commit()
        return session
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Clean up old inactive sessions.
        
        Args:
            days: Delete sessions older than this
            
        Returns:
            Number of sessions deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # First, mark old active sessions as abandoned
        Session.query.filter(
            Session.status == 'active',
            Session.last_activity < cutoff_date
        ).update({
            'status': 'abandoned',
            'ended_at': datetime.utcnow()
        })
        
        # Delete very old sessions (e.g., > 90 days)
        very_old = datetime.utcnow() - timedelta(days=days * 3)
        deleted = Session.query.filter(
            Session.created_at < very_old
        ).delete()
        
        db.session.commit()
        return deleted
    
    def get_session_stats(self, venue_id: int, days: int = 30) -> Dict:
        """
        Get session statistics for a venue.
        
        Args:
            venue_id: Venue ID
            days: Number of days to look back
            
        Returns:
            Dict with statistics
        """
        from sqlalchemy import func
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        base_query = Session.query.filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= cutoff
        )
        
        total = base_query.count()
        completed = base_query.filter(Session.status == 'completed').count()
        
        avg_messages = db.session.query(
            func.avg(Session.message_count)
        ).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= cutoff
        ).scalar() or 0
        
        avg_rating = db.session.query(
            func.avg(Session.rating)
        ).filter(
            Session.venue_id == venue_id,
            Session.rating.isnot(None),
            Session.created_at >= cutoff
        ).scalar() or 0
        
        return {
            'total_sessions': total,
            'completed_sessions': completed,
            'completion_rate': (completed / total * 100) if total > 0 else 0,
            'avg_messages': round(avg_messages, 1),
            'avg_rating': round(avg_rating, 1)
        }

