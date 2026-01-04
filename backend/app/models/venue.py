"""
Venue Model - Represents a restaurant/venue in the system
"""
from datetime import datetime
from app import db
from app.models.session import Session


class Venue(db.Model):
    """
    Venue entity representing a restaurant or establishment.
    Each venue has its own wine catalog and AI sommelier configuration.
    """
    __tablename__ = 'venues'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    
    # Restaurant characteristics
    cuisine_type = db.Column(db.String(100))
    menu_style = db.Column(db.JSON)  # {'style': 'classic', 'focus': ['italian', 'natural']}
    preferences = db.Column(db.JSON)  # AI customization preferences
    target_audience = db.Column(db.JSON)  # ['business', 'couples', 'families']
    
    # QR Code and branding
    qr_code_url = db.Column(db.String(500))
    logo_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7), default='#722F37')
    
    # AI Customization
    welcome_message = db.Column(db.Text)
    sommelier_style = db.Column(db.String(50), default='professional')  # professional, friendly, expert
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_onboarded = db.Column(db.Boolean, default=False)
    
    # Subscription/Plan
    plan = db.Column(db.String(50), default='trial')
    trial_ends_at = db.Column(db.DateTime)
    
    # Conversation limit
    annual_conversation_limit = db.Column(db.Integer, default=None)  # None = unlimited
    annual_conversation_limit_start_date = db.Column(db.DateTime, default=None)  # Date when the annual limit period started
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='venue', lazy='dynamic', cascade='all, delete-orphan')
    users = db.relationship('User', backref='venue', lazy='dynamic', cascade='all, delete-orphan')
    sessions = db.relationship('Session', backref='venue', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Venue {self.name}>'
    
    def to_dict(self, include_stats=False):
        """Convert venue to dictionary for API responses"""
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'cuisine_type': self.cuisine_type,
            'menu_style': self.menu_style,
            'preferences': self.preferences,
            'target_audience': self.target_audience,
            'qr_code_url': self.qr_code_url,
            'logo_url': self.logo_url,
            'primary_color': self.primary_color,
            'welcome_message': self.welcome_message,
            'sommelier_style': self.sommelier_style,
            'is_active': self.is_active,
            'is_onboarded': self.is_onboarded,
            'plan': self.plan,
            'annual_conversation_limit': self.annual_conversation_limit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'featured_wines': self.get_featured_wines()  # Include featured wines for easy access
        }
        
        if include_stats:
            data['stats'] = {
                'total_products': self.products.count(),
                'total_sessions': self.sessions.count(),
                'total_users': self.users.count()
            }
            data['annual_conversation_count'] = self.get_annual_conversation_count()
            data['annual_conversation_limit'] = self.annual_conversation_limit
            renewal_date = self.get_conversation_limit_renewal_date()
            data['conversation_limit_renewal_date'] = renewal_date.isoformat() if renewal_date else None
        
        return data
    
    def get_featured_wines(self):
        """
        Get list of featured wine product IDs from preferences.
        
        Returns:
            List of product IDs (max 2), empty list if none set
        """
        if not self.preferences or not isinstance(self.preferences, dict):
            return []
        
        featured = self.preferences.get('featured_wines', [])
        if not isinstance(featured, list):
            return []
        
        # Ensure all are integers and filter out invalid values
        return [int(wid) for wid in featured if isinstance(wid, (int, str)) and str(wid).isdigit()][:2]
    
    def set_featured_wines(self, product_ids):
        """
        Set featured wines in preferences.
        Validates that products exist, belong to venue, and are available.
        
        Args:
            product_ids: List of product IDs (max 2)
            
        Returns:
            Tuple (success: bool, message: str)
        """
        if not isinstance(product_ids, list):
            return False, "featured_wines deve essere una lista"
        
        if len(product_ids) > 2:
            return False, "Massimo 2 vini possono essere selezionati come vini in evidenza"
        
        # Validate product IDs
        from app.models import Product
        for product_id in product_ids:
            if not isinstance(product_id, int):
                try:
                    product_id = int(product_id)
                except (ValueError, TypeError):
                    return False, f"ID prodotto non valido: {product_id}"
            
            product = Product.query.get(product_id)
            if not product:
                return False, f"Prodotto con ID {product_id} non trovato"
            
            if product.venue_id != self.id:
                return False, f"Prodotto con ID {product_id} non appartiene a questo locale"
            
            if not product.is_available:
                return False, f"Prodotto con ID {product_id} non è disponibile"
        
        # Update preferences
        if not self.preferences or not isinstance(self.preferences, dict):
            self.preferences = {}
        
        self.preferences['featured_wines'] = product_ids
        return True, "Vini in evidenza aggiornati con successo"
    
    def get_annual_conversation_count(self):
        """
        Count B2C conversations (sessions) created since the limit start date.
        If no start date is set, uses January 1st of current year as fallback.
        
        Returns:
            Integer count of conversations
        """
        from app.models import Session
        from datetime import datetime, timedelta
        
        # Determine the start date for counting
        if self.annual_conversation_limit_start_date:
            # Use the tracked start date
            period_start = self.annual_conversation_limit_start_date
        else:
            # Fallback to January 1st of current year (legacy behavior)
            period_start = datetime(datetime.now().year, 1, 1)
        
        # Query directly from Session model to ensure correct filtering
        return Session.query.filter(
            Session.venue_id == self.id,
            Session.mode == 'b2c',
            Session.created_at >= period_start
        ).count()
    
    def get_conversation_limit_renewal_date(self):
        """
        Calculate the date when the conversation limit will renew.
        This is exactly 1 year after the start date.
        
        Returns:
            datetime object representing the renewal date, or None if no limit is set
        """
        if self.annual_conversation_limit is None:
            return None
        
        if self.annual_conversation_limit_start_date:
            from datetime import timedelta
            # Renewal is exactly 1 year after start date
            return self.annual_conversation_limit_start_date + timedelta(days=365)
        else:
            # Fallback: if no start date, assume it started on Jan 1st of current year
            from datetime import datetime
            current_year_start = datetime(datetime.now().year, 1, 1)
            from datetime import timedelta
            return current_year_start + timedelta(days=365)
    
    def initialize_conversation_limit_period(self):
        """
        Initialize or reset the conversation limit period start date to today.
        This should be called when:
        - A limit is first set for a venue
        - The limit period needs to be reset (e.g., after renewal)
        
        Returns:
            The new start date
        """
        from datetime import datetime
        self.annual_conversation_limit_start_date = datetime.utcnow()
        return self.annual_conversation_limit_start_date
    
    def can_create_conversation(self):
        """
        Check if venue can create a new conversation (B2C session).
        
        Returns:
            Tuple (can_create: bool, message: str)
        """
        if self.annual_conversation_limit is None:
            return True, "Unlimited"
        
        current_count = self.get_annual_conversation_count()
        
        if current_count >= self.annual_conversation_limit:
            return False, f"Limite annuale raggiunto ({self.annual_conversation_limit} conversazioni)"
        
        return True, f"{current_count}/{self.annual_conversation_limit} conversazioni utilizzate"
    
    @staticmethod
    def generate_slug(name):
        """Generate a URL-friendly slug from venue name"""
        import re
        import uuid
        
        # Convert to lowercase and replace spaces with hyphens
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Add a short unique identifier
        unique_id = str(uuid.uuid4())[:8]
        return f"{slug}-{unique_id}"


# Indexes for better query performance
db.Index('idx_venues_slug', Venue.slug)
db.Index('idx_venues_is_active', Venue.is_active)
db.Index('idx_venues_created_at', Venue.created_at)

