"""
Session Model - Represents a chat session
"""
from datetime import datetime
import uuid
from app import db


class Session(db.Model):
    """
    Session entity representing a conversation session.
    Can be B2C (customer via QR) or B2B (restaurant owner).
    """
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Session identification
    session_token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Session type
    mode = db.Column(db.String(20), nullable=False)  # 'b2c' (customer) or 'b2b' (owner)
    
    # Context for AI
    context = db.Column(db.JSON)  # Stores conversation context, preferences, selected dishes
    """
    Example context structure:
    {
        'selected_dishes': ['Tagliata di manzo', 'Risotto ai funghi'],
        'preferences': {
            'budget': 'medium',
            'wine_types': ['red'],
            'avoid': ['sweet']
        },
        'previous_recommendations': [1, 5, 8],  # product IDs
        'customer_notes': 'Celebrating anniversary'
    }
    """
    
    # Session metadata
    device_type = db.Column(db.String(50))  # mobile, tablet, desktop
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    
    # Analytics
    message_count = db.Column(db.Integer, default=0)
    products_recommended = db.Column(db.JSON)  # List of product IDs recommended
    products_selected = db.Column(db.JSON)  # Products the customer showed interest in
    products_sold = db.Column(db.JSON)  # Products sold with timestamp: [{"product_id": 1, "sold_at": "2024-01-01T12:00:00"}, ...]
    
    # Budget and target tracking
    budget_initial = db.Column(db.Numeric(10, 2))  # Initial budget declared by customer (per bottle)
    num_bottiglie_target = db.Column(db.Integer)  # Target number of bottles for the journey
    
    # Satisfaction/Feedback
    rating = db.Column(db.Integer)  # 1-5 stars
    feedback = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, completed, abandoned
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    # Relationships
    messages = db.relationship('Message', backref='session', lazy='dynamic', 
                              cascade='all, delete-orphan', order_by='Message.created_at')
    
    def __repr__(self):
        return f'<Session {self.session_token[:8]}... ({self.mode})>'
    
    @staticmethod
    def generate_token():
        """Generate a unique session token"""
        return str(uuid.uuid4())
    
    def to_dict(self, include_messages=False):
        """Convert session to dictionary for API responses"""
        data = {
            'id': self.id,
            'session_token': self.session_token,
            'venue_id': self.venue_id,
            'mode': self.mode,
            'context': self.context,
            'message_count': self.message_count,
            'status': self.status,
            'rating': self.rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }
        
        if include_messages:
            data['messages'] = [msg.to_dict() for msg in self.messages.all()]
        
        return data
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def increment_message_count(self):
        """Increment the message counter"""
        self.message_count = (self.message_count or 0) + 1
    
    def add_recommendation(self, product_id):
        """Track a product recommendation"""
        if self.products_recommended is None:
            self.products_recommended = []
        if product_id not in self.products_recommended:
            self.products_recommended = self.products_recommended + [product_id]
    
    def add_selection(self, product_id):
        """Track a product the customer showed interest in"""
        if self.products_selected is None:
            self.products_selected = []
        if product_id not in self.products_selected:
            self.products_selected = self.products_selected + [product_id]
    
    def add_sale(self, product_id):
        """Track a product as sold with current timestamp"""
        if self.products_sold is None:
            self.products_sold = []
        
        # Check if this product was already sold in this session (avoid duplicates)
        existing_sale = next(
            (sale for sale in self.products_sold if sale.get('product_id') == product_id),
            None
        )
        
        if not existing_sale:
            # Add new sale with timestamp
            self.products_sold = self.products_sold + [{
                'product_id': product_id,
                'sold_at': datetime.utcnow().isoformat()
            }]
    
    def end_session(self, status='completed'):
        """Mark the session as ended"""
        self.status = status
        self.ended_at = datetime.utcnow()
    
    def get_conversation_history(self, limit=None):
        """Get conversation messages for AI context"""
        query = self.messages.order_by(db.asc(db.text('created_at')))
        if limit:
            query = query.limit(limit)
        
        return [
            {'role': msg.role, 'content': msg.content}
            for msg in query.all()
        ]
    
    def extract_budget_from_context(self):
        """Extract budget_initial from context and save it"""
        if not self.context:
            return
        
        preferences = self.context.get('preferences', {})
        budget = preferences.get('budget')
        
        if budget:
            # Convert budget to numeric if possible
            # Budget can be: 'base' (≤20), 'spinto'/'medium' (20-40), 'high'/'any' (no limit), or numeric value
            budget_labels_to_value = {
                'base': 20.0,
                'low': 20.0,
                'spinto': 30.0,
                'medium': 30.0,
                'high': None,  # No limit
                'any': None,
                'nolimit': None
            }
            
            if isinstance(budget, (int, float)):
                self.budget_initial = float(budget)
            elif isinstance(budget, str) and budget.lower() in budget_labels_to_value:
                value = budget_labels_to_value[budget.lower()]
                if value is not None:
                    self.budget_initial = value
    
    def extract_bottiglie_from_context(self):
        """Extract num_bottiglie_target from context and save it"""
        if not self.context:
            return
        
        preferences = self.context.get('preferences', {})
        bottles_count = preferences.get('bottles_count')
        
        if bottles_count:
            try:
                self.num_bottiglie_target = int(bottles_count)
            except (ValueError, TypeError):
                pass
        
        # Also check wine_count if bottles_count not available
        if not self.num_bottiglie_target:
            wine_count = self.context.get('wine_count')
            if wine_count:
                try:
                    self.num_bottiglie_target = int(wine_count)
                except (ValueError, TypeError):
                    pass
    
    def save_preferences_from_context(self):
        """
        Extract and save all deterministic preferences from context to session.
        This ensures preferences are persisted and can be retrieved later.
        
        Saves:
        - guest_count (in context)
        - wine_type, journey_preference, budget, bottles_count (in context.preferences)
        - All preferences are also kept in context for AI processing
        """
        if not self.context:
            return
        
        # Ensure context has a structured format
        if not isinstance(self.context, dict):
            self.context = {}
        
        # Extract and save budget
        self.extract_budget_from_context()
        
        # Extract and save bottles count
        self.extract_bottiglie_from_context()
        
        # Ensure preferences structure exists in context
        if 'preferences' not in self.context:
            self.context['preferences'] = {}
        
        # Normalize and validate preferences structure
        preferences = self.context.get('preferences', {})
        
        # Ensure all preference fields are properly set
        # wine_type: 'red', 'white', 'sparkling', 'rose', 'any'
        if 'wine_type' not in preferences or preferences.get('wine_type') is None:
            preferences['wine_type'] = 'any'
        
        # journey_preference: 'single' or 'journey'
        if 'journey_preference' not in preferences or preferences.get('journey_preference') is None:
            preferences['journey_preference'] = 'single'
        
        # budget: numeric value, 'nolimit', or None
        if 'budget' not in preferences:
            preferences['budget'] = None
        
        # bottles_count: integer or None (only for journey mode)
        if 'bottles_count' not in preferences:
            if preferences.get('journey_preference') == 'journey':
                # Use num_bottiglie_target if available, otherwise None
                preferences['bottles_count'] = self.num_bottiglie_target
            else:
                preferences['bottles_count'] = None
        
        # Update context with normalized preferences
        self.context['preferences'] = preferences
        
        # Ensure guest_count is in context (not in preferences)
        if 'guest_count' not in self.context:
            # Default to 2 if not provided
            self.context['guest_count'] = 2
    
    @property
    def duration_minutes(self):
        """Calculate session duration in minutes"""
        if self.ended_at:
            delta = self.ended_at - self.created_at
        else:
            delta = datetime.utcnow() - self.created_at
        return int(delta.total_seconds() / 60)


# Indexes for better query performance
db.Index('idx_sessions_session_token', Session.session_token)
db.Index('idx_sessions_venue_id', Session.venue_id)
db.Index('idx_sessions_mode', Session.mode)
db.Index('idx_sessions_status', Session.status)
db.Index('idx_sessions_created_at', Session.created_at)
db.Index('idx_sessions_venue_mode', Session.venue_id, Session.mode)

