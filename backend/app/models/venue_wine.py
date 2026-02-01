"""
VenueWine Model - Represents a wine in a venue's wine list
"""
from datetime import datetime
from app import db


class VenueWine(db.Model):
    """
    VenueWine entity representing a wine in a specific venue's wine list.

    This table links venues to wines from the master catalog, storing
    venue-specific data like price, availability, and vintage.

    This replaces the old 'products' table approach where each venue
    had duplicate wine records.
    """
    __tablename__ = 'venue_wines'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False, index=True)
    wine_id = db.Column(db.Integer, db.ForeignKey('wines.id', ondelete='CASCADE'), nullable=False, index=True)

    # Venue-specific data
    vintage = db.Column(db.Integer, nullable=True)  # Year can vary per venue

    # Pricing (venue-specific)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    price_glass = db.Column(db.Numeric(10, 2), nullable=True)
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)
    margin = db.Column(db.Numeric(10, 2), nullable=True)

    # Availability
    is_available = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, nullable=True)

    # Venue-specific image (e.g., photo of their specific bottle label)
    image_url = db.Column(db.String(500), nullable=True)

    # Tracking
    external_id = db.Column(db.String(100), nullable=True)  # ID from client's system
    notes = db.Column(db.Text, nullable=True)  # Restaurant-specific notes

    # Migration reference (temporary, for data migration)
    legacy_product_id = db.Column(db.Integer, nullable=True, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    venue = db.relationship('Venue', back_populates='venue_wines')
    wine = db.relationship('Wine', back_populates='venue_wines')
    proposals = db.relationship('WineProposal', back_populates='venue_wine', lazy='dynamic')

    # Unique constraint: one wine per venue per vintage
    __table_args__ = (
        db.UniqueConstraint('venue_id', 'wine_id', 'vintage', name='unique_venue_wine_vintage'),
    )

    def __repr__(self):
        return f'<VenueWine {self.id}: venue={self.venue_id} wine={self.wine_id}>'

    def calculate_margin(self):
        """Calculate margin from price and cost_price"""
        if self.price and self.cost_price:
            try:
                margin_value = float(self.price) - float(self.cost_price)
                return max(0, margin_value)
            except (TypeError, ValueError):
                return None
        return None

    def update_margin(self):
        """Update margin field based on current price and cost_price"""
        self.margin = self.calculate_margin()

    def to_dict(self, detailed=False):
        """
        Convert venue_wine to dictionary for API responses.
        Returns only venue-specific data.
        """
        data = {
            'id': self.id,
            'venue_id': self.venue_id,
            'wine_id': self.wine_id,
            'vintage': self.vintage,
            'price': float(self.price) if self.price else None,
            'price_glass': float(self.price_glass) if self.price_glass else None,
            'is_available': self.is_available if self.is_available is not None else True,
            'stock_quantity': self.stock_quantity,
            'image_url': self.image_url,
            'external_id': self.external_id
        }

        if detailed:
            data['cost_price'] = float(self.cost_price) if self.cost_price else None
            data['margin'] = float(self.margin) if self.margin else None
            data['notes'] = self.notes
            data['created_at'] = self.created_at.isoformat() if self.created_at else None
            data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None

        return data

    def to_full_dict(self, detailed=False):
        """
        Convert venue_wine to dictionary with full wine details.
        This is the main method for API responses - combines wine master data
        with venue-specific data.

        Returns a structure compatible with the old 'products' API.
        """
        # Get wine data
        wine = self.wine
        if not wine:
            return self.to_dict(detailed)

        data = {
            # ID fields
            'id': self.id,  # This is venue_wine_id (used as product_id equivalent)
            'venue_wine_id': self.id,
            'wine_id': wine.id,
            'venue_id': self.venue_id,

            # Wine identification
            'name': wine.name,
            'producer': wine.producer,
            'type': wine.type,
            'category': wine.category,

            # Origin
            'region': wine.region,
            'country': wine.country,
            'appellation': wine.appellation,
            'grape_variety': wine.grape_variety,

            # Venue-specific data
            'vintage': self.vintage,
            'price': float(self.price) if self.price else None,
            'price_glass': float(self.price_glass) if self.price_glass else None,
            'is_available': self.is_available if self.is_available is not None else True,

            # Characteristics
            'alcohol_content': wine.alcohol_content,
            'body': wine.body,
            'sweetness': wine.sweetness,
            'tannin_level': wine.tannin_level,
            'acidity_level': wine.acidity_level,
            'color': wine.color,
            'aromas': wine.aromas,
            'aroma_profile': wine.aroma_profile,

            # Descriptions
            'description': wine.description,
            'tasting_notes': wine.tasting_notes,

            # Pairings
            'food_pairings': wine.food_pairings,
            'pairing_notes': wine.pairing_notes,

            # Service
            'serving_temperature': wine.serving_temperature,
            'decanting_time': wine.decanting_time,
            'glass_type': wine.glass_type,

            # Producer
            'winemaker': wine.winemaker,

            # Image (prefer venue-specific, fallback to wine master)
            'image_url': self.image_url or wine.image_url
        }

        if detailed:
            data['cost_price'] = float(self.cost_price) if self.cost_price else None
            data['margin'] = float(self.margin) if self.margin else None
            data['stock_quantity'] = self.stock_quantity
            data['external_id'] = self.external_id
            data['notes'] = self.notes
            data['qdrant_id'] = wine.qdrant_id
            data['embedding_updated_at'] = wine.embedding_updated_at.isoformat() if wine.embedding_updated_at else None
            data['created_at'] = self.created_at.isoformat() if self.created_at else None
            data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None

        return data

    def get_embedding_text(self):
        """Generate text representation for creating embeddings"""
        wine = self.wine
        if not wine:
            return f"Vino: sconosciuto | Prezzo: {self.price}"

        parts = [
            f"Vino: {wine.name}",
            f"Tipo: {wine.type}" if wine.type else "",
            f"Produttore: {wine.producer}" if wine.producer else "",
            f"Annata: {self.vintage}" if self.vintage else "",
            f"Prezzo: {self.price}" if self.price else "",
            f"Regione: {wine.region}" if wine.region else "",
            f"Uvaggio: {wine.grape_variety}" if wine.grape_variety else "",
            f"Descrizione: {wine.description}" if wine.description else "",
            f"Note: {wine.tasting_notes}" if wine.tasting_notes else ""
        ]
        return " | ".join([p for p in parts if p])


# SQLAlchemy event listeners to auto-calculate margin
@db.event.listens_for(VenueWine, 'before_insert', propagate=True)
def calculate_margin_on_insert(mapper, connection, target):
    """Calculate margin before inserting a new venue_wine"""
    target.update_margin()


@db.event.listens_for(VenueWine, 'before_update', propagate=True)
def calculate_margin_on_update(mapper, connection, target):
    """Calculate margin before updating a venue_wine if price or cost_price changed"""
    state = db.inspect(target)
    price_changed = state.attrs.price.history.has_changes() if hasattr(state.attrs, 'price') else False
    cost_changed = state.attrs.cost_price.history.has_changes() if hasattr(state.attrs, 'cost_price') else False
    if price_changed or cost_changed:
        target.update_margin()


# Indexes for better query performance
db.Index('idx_venue_wines_venue_id', VenueWine.venue_id)
db.Index('idx_venue_wines_wine_id', VenueWine.wine_id)
db.Index('idx_venue_wines_available', VenueWine.is_available)
db.Index('idx_venue_wines_price', VenueWine.price)
db.Index('idx_venue_wines_venue_available', VenueWine.venue_id, VenueWine.is_available)
