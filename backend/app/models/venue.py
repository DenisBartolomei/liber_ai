"""
Venue Model - Represents a restaurant/venue in the system
"""
from datetime import datetime
from app import db


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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'featured_wines': self.get_featured_wines()  # Include featured wines for easy access
        }
        
        if include_stats:
            data['stats'] = {
                'total_products': self.products.count(),
                'total_sessions': self.sessions.count(),
                'total_users': self.users.count()
            }
        
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

