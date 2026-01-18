"""
Product Model - Represents a wine or beverage product
"""
from datetime import datetime
from app import db


class Product(db.Model):
    """
    Product entity representing a wine or beverage in a venue's catalog.
    
    NOTE: Only core columns are defined here. Additional columns (grape_variety, 
    description, region, etc.) may or may not exist in the database depending 
    on when it was created. We use getattr() in to_dict() to safely access 
    these optional columns.
    """
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Core fields - guaranteed to exist
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # red, white, rose, sparkling, dessert, fortified
    price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Fields that might exist in older databases
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)
    margin = db.Column(db.Numeric(10, 2), nullable=True)
    is_available = db.Column(db.Boolean, default=True, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def _safe_get(self, attr_name, default=None):
        """Safely get an attribute that may not exist as a column in the database."""
        try:
            value = getattr(self, attr_name, default)
            # If it's a SQLAlchemy instrumented attribute that would cause a DB query, return default
            return value if value is not None else default
        except Exception:
            return default
    
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
        
        # Optional fields - use raw SQL query to get all columns for this product
        # This avoids SQLAlchemy trying to lazy-load undefined columns
        try:
            from sqlalchemy import text
            from app import db as database
            
            result = database.session.execute(
                text("SELECT * FROM products WHERE id = :id"),
                {"id": self.id}
            ).fetchone()
            
            if result:
                # Convert to dict - result is a Row object
                row_dict = result._asdict() if hasattr(result, '_asdict') else dict(result._mapping)
                
                # Wine details
                if row_dict.get('region'):
                    data['region'] = row_dict['region']
                if row_dict.get('country'):
                    data['country'] = row_dict['country']
                if row_dict.get('appellation'):
                    data['appellation'] = row_dict['appellation']
                if row_dict.get('grape_variety'):
                    data['grape_variety'] = row_dict['grape_variety']
                if row_dict.get('vintage'):
                    data['vintage'] = row_dict['vintage']
                if row_dict.get('producer'):
                    data['producer'] = row_dict['producer']
                
                # Description and notes
                if row_dict.get('description'):
                    data['description'] = row_dict['description']
                if row_dict.get('tasting_notes'):
                    data['tasting_notes'] = row_dict['tasting_notes']
                if row_dict.get('aromas'):
                    data['aromas'] = row_dict['aromas']
                
                # Wine Identity Card fields
                if row_dict.get('color'):
                    data['color'] = row_dict['color']
                if row_dict.get('body') is not None:
                    data['body'] = row_dict['body']
                if row_dict.get('tannin_level') is not None:
                    data['tannin_level'] = row_dict['tannin_level']
                if row_dict.get('acidity_level') is not None:
                    data['acidity_level'] = row_dict['acidity_level']
                if row_dict.get('alcohol_content') is not None:
                    data['alcohol_content'] = row_dict['alcohol_content']
                if row_dict.get('sweetness'):
                    data['sweetness'] = row_dict['sweetness']
                
                # Food pairings
                if row_dict.get('food_pairings'):
                    data['food_pairings'] = row_dict['food_pairings']
                
                # Image
                if row_dict.get('image_url'):
                    data['image_url'] = row_dict['image_url']
                
                # Detailed fields (only if detailed=True)
                if detailed:
                    if row_dict.get('cost_price'):
                        data['cost_price'] = float(row_dict['cost_price'])
                    if row_dict.get('margin'):
                        data['margin'] = float(row_dict['margin'])
                    if row_dict.get('price_glass'):
                        data['price_glass'] = float(row_dict['price_glass'])
                    if row_dict.get('stock_quantity') is not None:
                        data['stock_quantity'] = row_dict['stock_quantity']
                    if row_dict.get('is_featured') is not None:
                        data['is_featured'] = row_dict['is_featured']
                    if row_dict.get('created_at'):
                        data['created_at'] = row_dict['created_at'].isoformat() if hasattr(row_dict['created_at'], 'isoformat') else str(row_dict['created_at'])
                    if row_dict.get('updated_at'):
                        data['updated_at'] = row_dict['updated_at'].isoformat() if hasattr(row_dict['updated_at'], 'isoformat') else str(row_dict['updated_at'])
        except Exception:
            # If raw query fails, just return basic data
            # Add image_url from model if available
            if self.image_url:
                data['image_url'] = self.image_url
        
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
        
        # Get additional details via to_dict
        data = self.to_dict()
        
        if data.get('region'):
            parts.append(f"Regione: {data['region']}")
        if data.get('grape_variety'):
            parts.append(f"Uvaggio: {data['grape_variety']}")
        if data.get('description'):
            parts.append(f"Descrizione: {data['description']}")
        if data.get('tasting_notes'):
            parts.append(f"Note: {data['tasting_notes']}")
        
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
