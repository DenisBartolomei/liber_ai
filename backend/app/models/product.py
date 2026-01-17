"""
Product Model - Represents a wine or beverage product
"""
from datetime import datetime
from app import db


class Product(db.Model):
    """
    Product entity representing a wine or beverage in a venue's catalog.
    Only includes fields that exist in the database.
    """
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Basic Info
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # red, white, rose, sparkling, dessert, fortified
    
    # Wine Details
    region = db.Column(db.String(255), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    appellation = db.Column(db.String(255), nullable=True)
    grape_variety = db.Column(db.String(255), nullable=True)
    vintage = db.Column(db.Integer, nullable=True)
    
    # Producer Info
    producer = db.Column(db.String(255), nullable=True)
    winemaker = db.Column(db.String(255), nullable=True)
    
    # Wine Identity Card fields
    alcohol_content = db.Column(db.Float, nullable=True)
    body = db.Column(db.Integer, nullable=True)  # 1-10 scale
    sweetness = db.Column(db.String(50), nullable=True)
    tannin_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    acidity_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    color = db.Column(db.String(255), nullable=True)  # Wine color description
    aromas = db.Column(db.Text, nullable=True)  # Wine aromas description
    
    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False)
    price_glass = db.Column(db.Numeric(10, 2), nullable=True)
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)  # For margin calculations
    margin = db.Column(db.Numeric(10, 2), nullable=True)  # Calculated margin (price - cost_price)
    
    # Description and notes
    description = db.Column(db.Text, nullable=True)
    tasting_notes = db.Column(db.Text, nullable=True)
    aroma_profile = db.Column(db.JSON, nullable=True)
    
    # Food Pairings
    food_pairings = db.Column(db.JSON, nullable=True)
    
    # Inventory
    is_available = db.Column(db.Boolean, default=True, nullable=True)
    stock_quantity = db.Column(db.Integer, nullable=True)
    
    # Metadata
    image_url = db.Column(db.String(500), nullable=True)  # URL for label image
    is_featured = db.Column(db.Boolean, default=False, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def to_dict(self, detailed=False):
        """Convert product to dictionary for API responses"""
        data = {
            'id': self.id,
            'venue_id': self.venue_id,
            'name': self.name,
            'type': self.type,
            'price': float(self.price) if self.price else None,
            'is_available': self.is_available if self.is_available is not None else True
        }
        
        # Wine details - always include if available
        if self.region:
            data['region'] = self.region
        if self.country:
            data['country'] = self.country
        if self.appellation:
            data['appellation'] = self.appellation
        if self.grape_variety:
            data['grape_variety'] = self.grape_variety
        if self.vintage:
            data['vintage'] = self.vintage
        if self.producer:
            data['producer'] = self.producer
            
        # Description and notes - important for AI context
        if self.description:
            data['description'] = self.description
        if self.tasting_notes:
            data['tasting_notes'] = self.tasting_notes
        if self.aromas:
            data['aromas'] = self.aromas
            
        # Wine Identity Card fields
        if self.color:
            data['color'] = self.color
        if self.body is not None:
            data['body'] = self.body
        if self.tannin_level is not None:
            data['tannin_level'] = self.tannin_level
        if self.acidity_level is not None:
            data['acidity_level'] = self.acidity_level
        if self.alcohol_content is not None:
            data['alcohol_content'] = self.alcohol_content
        if self.sweetness:
            data['sweetness'] = self.sweetness
            
        # Food pairings
        if self.food_pairings:
            data['food_pairings'] = self.food_pairings
            
        # Image
        if self.image_url:
            data['image_url'] = self.image_url
        
        if detailed:
            if self.cost_price:
                data['cost_price'] = float(self.cost_price)
            if self.margin:
                data['margin'] = float(self.margin)
            if self.price_glass:
                data['price_glass'] = float(self.price_glass)
            if self.stock_quantity is not None:
                data['stock_quantity'] = self.stock_quantity
            if self.is_featured is not None:
                data['is_featured'] = self.is_featured
            if self.created_at:
                data['created_at'] = self.created_at.isoformat()
            if self.updated_at:
                data['updated_at'] = self.updated_at.isoformat()
        
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
            f"Prezzo: €{self.price}" if self.price else ""
        ]
        
        # Add region if available
        if self.region:
            parts.append(f"Regione: {self.region}")
        
        # Add grape variety if available
        if self.grape_variety:
            parts.append(f"Uvaggio: {self.grape_variety}")
        
        # Add description if available
        if self.description:
            parts.append(f"Descrizione: {self.description}")
        
        # Add tasting notes if available
        if self.tasting_notes:
            parts.append(f"Note: {self.tasting_notes}")
        
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
db.Index('idx_products_is_available', Product.is_available)
db.Index('idx_products_price', Product.price)
db.Index('idx_products_venue_type', Product.venue_id, Product.type)

