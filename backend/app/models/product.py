"""
Product Model - Represents a wine or beverage product
"""
from datetime import datetime
from app import db


class Product(db.Model):
    """
    Product entity representing a wine or beverage in a venue's catalog.
    Includes all information needed for AI recommendations and vector search.
    """
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Basic Info
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # red, white, rose, sparkling, dessert, fortified
    category = db.Column(db.String(100))  # Still, Sparkling, Fortified, etc.
    
    # Wine Details
    region = db.Column(db.String(255))
    country = db.Column(db.String(100), default='Italia')
    appellation = db.Column(db.String(255))  # DOC, DOCG, IGT, etc.
    grape_variety = db.Column(db.String(255))  # Can be multiple: "Sangiovese, Merlot"
    vintage = db.Column(db.Integer)
    
    # Producer Info
    producer = db.Column(db.String(255))
    winemaker = db.Column(db.String(255))
    
    # Characteristics
    alcohol_content = db.Column(db.Float)
    body = db.Column(db.String(50))  # light, medium, full
    sweetness = db.Column(db.String(50))  # dry, off-dry, sweet
    tannin_level = db.Column(db.String(50))  # low, medium, high
    acidity_level = db.Column(db.String(50))  # low, medium, high
    
    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False)
    price_glass = db.Column(db.Numeric(10, 2))
    cost_price = db.Column(db.Numeric(10, 2))  # For margin calculations
    margin = db.Column(db.Numeric(10, 2))  # Calculated margin (price - cost_price)
    
    # Descriptions
    description = db.Column(db.Text)
    tasting_notes = db.Column(db.Text)
    aroma_profile = db.Column(db.JSON)  # ['cherry', 'oak', 'vanilla']
    
    # Food Pairings
    food_pairings = db.Column(db.JSON)  # ['beef', 'pasta', 'aged cheese']
    pairing_notes = db.Column(db.Text)
    
    # Service
    serving_temperature = db.Column(db.String(50))  # "16-18°C"
    decanting_time = db.Column(db.String(50))  # "1-2 hours"
    glass_type = db.Column(db.String(100))  # "Burgundy glass"
    
    # Vector DB
    qdrant_id = db.Column(db.String(100), unique=True, index=True)
    embedding_updated_at = db.Column(db.DateTime)
    
    # Inventory
    is_available = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer)
    
    # Metadata
    image_url = db.Column(db.String(500))
    external_id = db.Column(db.String(100))  # For imports from external systems
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def to_dict(self, detailed=False):
        """Convert product to dictionary for API responses"""
        data = {
            'id': self.id,
            'venue_id': self.venue_id,
            'name': self.name,
            'type': self.type,
            'region': self.region,
            'grape_variety': self.grape_variety,
            'vintage': self.vintage,
            'price': float(self.price) if self.price else None,
            'description': self.description,
            'is_available': self.is_available
        }
        
        if detailed:
            data.update({
                'category': self.category,
                'country': self.country,
                'appellation': self.appellation,
                'producer': self.producer,
                'winemaker': self.winemaker,
                'alcohol_content': self.alcohol_content,
                'body': self.body,
                'sweetness': self.sweetness,
                'tannin_level': self.tannin_level,
                'acidity_level': self.acidity_level,
                'price_glass': float(self.price_glass) if self.price_glass else None,
                'tasting_notes': self.tasting_notes,
                'aroma_profile': self.aroma_profile,
                'food_pairings': self.food_pairings,
                'pairing_notes': self.pairing_notes,
                'serving_temperature': self.serving_temperature,
                'decanting_time': self.decanting_time,
                'glass_type': self.glass_type,
                'image_url': self.image_url,
                'stock_quantity': self.stock_quantity,
                'cost_price': float(self.cost_price) if self.cost_price else None,
                'margin': float(self.margin) if self.margin else None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            })
        
        return data
    
    def calculate_margin(self):
        """Calculate margin from price and cost_price"""
        if self.price and self.cost_price:
            try:
                margin_value = float(self.price) - float(self.cost_price)
                return max(0, margin_value)  # Margin cannot be negative
            except (TypeError, ValueError):
                return None
        return None
    
    def update_margin(self):
        """Update margin field based on current price and cost_price"""
        self.margin = self.calculate_margin()
    
    def get_embedding_text(self):
        """Generate text representation for creating embeddings"""
        parts = [
            f"Vino: {self.name}",
            f"Tipo: {self.type}" if self.type else "",
            f"Regione: {self.region}" if self.region else "",
            f"Vitigno: {self.grape_variety}" if self.grape_variety else "",
            f"Annata: {self.vintage}" if self.vintage else "",
            f"Produttore: {self.producer}" if self.producer else "",
            f"Descrizione: {self.description}" if self.description else "",
            f"Note degustazione: {self.tasting_notes}" if self.tasting_notes else "",
            f"Abbinamenti: {', '.join(self.food_pairings)}" if self.food_pairings else "",
            f"Corpo: {self.body}" if self.body else "",
            f"Prezzo: €{self.price}" if self.price else ""
        ]
        return " | ".join([p for p in parts if p])


# SQLAlchemy event listeners to auto-calculate margin when price or cost_price changes
@db.event.listens_for(Product, 'before_insert', propagate=True)
def calculate_margin_on_insert(mapper, connection, target):
    """Calculate margin before inserting a new product"""
    target.update_margin()


@db.event.listens_for(Product, 'before_update', propagate=True)
def calculate_margin_on_update(mapper, connection, target):
    """Calculate margin before updating a product if price or cost_price changed"""
    # Check if price or cost_price has changed
    state = db.inspect(target)
    if state.attrs.price.history.has_changes() or state.attrs.cost_price.history.has_changes():
        target.update_margin()


# Indexes for better query performance
db.Index('idx_products_venue_id', Product.venue_id)
db.Index('idx_products_type', Product.type)
db.Index('idx_products_region', Product.region)
db.Index('idx_products_is_available', Product.is_available)
db.Index('idx_products_price', Product.price)
db.Index('idx_products_venue_type', Product.venue_id, Product.type)

