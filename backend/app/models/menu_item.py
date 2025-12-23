"""
MenuItem Model - Represents a dish/food item in a venue's menu
"""
from datetime import datetime
from app import db


class MenuItem(db.Model):
    """
    MenuItem entity representing a dish in the restaurant's food menu.
    Used for wine pairing suggestions.
    """
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Basic Info
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Category for grouping
    category = db.Column(db.String(100))  # antipasto, primo, secondo, contorno, dolce, etc.
    
    # Main ingredients (for pairing logic)
    main_ingredient = db.Column(db.String(100))  # pesce, carne_rossa, carne_bianca, verdure, formaggio, etc.
    cooking_method = db.Column(db.String(100))  # grigliato, fritto, al forno, crudo, brasato, etc.
    
    # Flavor profile (helps with pairing)
    flavor_profile = db.Column(db.JSON)  # ['grasso', 'speziato', 'delicato', 'affumicato', 'piccante']
    
    # Price (optional, for context)
    price = db.Column(db.Numeric(10, 2))
    
    # Status
    is_available = db.Column(db.Boolean, default=True)
    
    # Display order
    display_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MenuItem {self.name}>'
    
    def to_dict(self):
        """Convert menu item to dictionary for API responses"""
        return {
            'id': self.id,
            'venue_id': self.venue_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'main_ingredient': self.main_ingredient,
            'cooking_method': self.cooking_method,
            'flavor_profile': self.flavor_profile,
            'price': float(self.price) if self.price else None,
            'is_available': self.is_available,
            'display_order': self.display_order
        }
    
    def get_pairing_context(self):
        """Generate text for wine pairing AI"""
        parts = [
            f"Piatto: {self.name}",
            f"Categoria: {self.category}" if self.category else "",
            f"Ingrediente principale: {self.main_ingredient}" if self.main_ingredient else "",
            f"Cottura: {self.cooking_method}" if self.cooking_method else "",
            f"Descrizione: {self.description}" if self.description else ""
        ]
        if self.flavor_profile:
            parts.append(f"Profilo: {', '.join(self.flavor_profile)}")
        return " | ".join([p for p in parts if p])


# Indexes
db.Index('idx_menu_items_venue_id', MenuItem.venue_id)
db.Index('idx_menu_items_category', MenuItem.category)
db.Index('idx_menu_items_is_available', MenuItem.is_available)

