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
    
    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)  # For margin calculations
    margin = db.Column(db.Numeric(10, 2), nullable=True)  # Calculated margin (price - cost_price)
    
    # Inventory
    is_available = db.Column(db.Boolean, default=True, nullable=True)
    
    # Metadata
    image_url = db.Column(db.String(500), nullable=True)  # URL for label image
    
    # Wine Identity Card fields (optional - may not exist in all databases)
    # These are accessed via getattr() in to_dict() to avoid errors if columns don't exist
    # Note: If these columns exist in your database, you can uncomment them:
    # color = db.Column(db.String(255), nullable=True)  # Wine color description
    # aromas = db.Column(db.Text, nullable=True)  # Wine aromas description
    # body = db.Column(db.Integer, nullable=True)  # Body level 1-10
    # tannin_level = db.Column(db.Integer, nullable=True)  # Tannin level 1-10
    # acidity_level = db.Column(db.Integer, nullable=True)  # Acidity level 1-10
    
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
            'is_available': self.is_available if hasattr(self, 'is_available') else True
        }
        
        # Try to get optional fields using getattr (they may not exist in DB)
        # These will be None if the column doesn't exist
        region = getattr(self, 'region', None)
        if region:
            data['region'] = region
            
        grape_variety = getattr(self, 'grape_variety', None)
        if grape_variety:
            data['grape_variety'] = grape_variety
            
        vintage = getattr(self, 'vintage', None)
        if vintage:
            data['vintage'] = vintage
            
        description = getattr(self, 'description', None)
        if description:
            data['description'] = description
            
        image_url = getattr(self, 'image_url', None)
        if image_url:
            data['image_url'] = image_url
            
        # Wine Identity Card fields
        color = getattr(self, 'color', None)
        if color:
            data['color'] = color
            
        aromas = getattr(self, 'aromas', None)
        if aromas:
            data['aromas'] = aromas
            
        body = getattr(self, 'body', None)
        if body is not None:
            data['body'] = body
            
        tannin_level = getattr(self, 'tannin_level', None)
        if tannin_level is not None:
            data['tannin_level'] = tannin_level
            
        acidity_level = getattr(self, 'acidity_level', None)
        if acidity_level is not None:
            data['acidity_level'] = acidity_level
        
        if detailed:
            cost_price = getattr(self, 'cost_price', None)
            if cost_price:
                data['cost_price'] = float(cost_price)
            margin = getattr(self, 'margin', None)
            if margin:
                data['margin'] = float(margin)
            if hasattr(self, 'created_at') and self.created_at:
                data['created_at'] = self.created_at.isoformat()
            if hasattr(self, 'updated_at') and self.updated_at:
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
        
        # Add grape variety if available
        grape_variety = getattr(self, 'grape_variety', None)
        if grape_variety:
            parts.append(f"Uvaggio: {grape_variety}")
        
        # Add description if available
        description = getattr(self, 'description', None)
        if description:
            parts.append(f"Descrizione: {description}")
        
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

