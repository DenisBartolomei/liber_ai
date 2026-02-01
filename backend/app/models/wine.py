"""
Wine Model - Represents a wine in the master catalog
"""
from datetime import datetime
from app import db


class Wine(db.Model):
    """
    Wine entity representing a unique wine in the global catalog.

    This is the master wine database - each wine exists only once here,
    regardless of how many venues have it in their wine list.

    Venue-specific data (price, availability, vintage) is stored in VenueWine.
    """
    __tablename__ = 'wines'

    id = db.Column(db.Integer, primary_key=True)

    # Identification
    name = db.Column(db.String(255), nullable=False)
    producer = db.Column(db.String(255), nullable=True)
    type = db.Column(db.String(50), nullable=False)  # red, white, rose, sparkling, dessert, fortified
    category = db.Column(db.String(100), nullable=True)

    # Origin
    region = db.Column(db.String(255), nullable=True)
    country = db.Column(db.String(100), default='Italia')
    appellation = db.Column(db.String(255), nullable=True)  # DOC, DOCG, IGT, etc.

    # Characteristics
    grape_variety = db.Column(db.String(255), nullable=True)
    alcohol_content = db.Column(db.Float, nullable=True)

    # Sensory profile
    body = db.Column(db.Integer, nullable=True)  # 1-10 scale
    sweetness = db.Column(db.String(50), nullable=True)
    tannin_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    acidity_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    color = db.Column(db.String(255), nullable=True)
    aromas = db.Column(db.Text, nullable=True)
    aroma_profile = db.Column(db.JSON, nullable=True)

    # Descriptions
    description = db.Column(db.Text, nullable=True)
    tasting_notes = db.Column(db.Text, nullable=True)

    # Food pairings
    food_pairings = db.Column(db.JSON, nullable=True)
    pairing_notes = db.Column(db.Text, nullable=True)

    # Service
    serving_temperature = db.Column(db.String(50), nullable=True)
    decanting_time = db.Column(db.String(50), nullable=True)
    glass_type = db.Column(db.String(100), nullable=True)

    # Producer info
    winemaker = db.Column(db.String(255), nullable=True)

    # Image (generic wine label image)
    image_url = db.Column(db.String(500), nullable=True)

    # Vector DB (for future use)
    qdrant_id = db.Column(db.String(100), unique=True, nullable=True)
    embedding_updated_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    venue_wines = db.relationship('VenueWine', back_populates='wine', lazy='dynamic')

    def __repr__(self):
        return f'<Wine {self.id}: {self.name}>'

    def to_dict(self, detailed=False):
        """Convert wine to dictionary for API responses"""
        data = {
            'id': self.id,
            'name': self.name,
            'producer': self.producer,
            'type': self.type,
            'category': self.category,
            'region': self.region,
            'country': self.country,
            'appellation': self.appellation,
            'grape_variety': self.grape_variety,
            'alcohol_content': self.alcohol_content,
            'body': self.body,
            'sweetness': self.sweetness,
            'tannin_level': self.tannin_level,
            'acidity_level': self.acidity_level,
            'color': self.color,
            'aromas': self.aromas,
            'aroma_profile': self.aroma_profile,
            'description': self.description,
            'tasting_notes': self.tasting_notes,
            'food_pairings': self.food_pairings,
            'pairing_notes': self.pairing_notes,
            'serving_temperature': self.serving_temperature,
            'decanting_time': self.decanting_time,
            'glass_type': self.glass_type,
            'winemaker': self.winemaker,
            'image_url': self.image_url
        }

        if detailed:
            data['qdrant_id'] = self.qdrant_id
            data['embedding_updated_at'] = self.embedding_updated_at.isoformat() if self.embedding_updated_at else None
            data['created_at'] = self.created_at.isoformat() if self.created_at else None
            data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None

        return data

    def get_embedding_text(self):
        """Generate text representation for creating embeddings"""
        parts = [
            f"Vino: {self.name}",
            f"Tipo: {self.type}" if self.type else "",
            f"Produttore: {self.producer}" if self.producer else "",
            f"Regione: {self.region}" if self.region else "",
            f"Paese: {self.country}" if self.country else "",
            f"Uvaggio: {self.grape_variety}" if self.grape_variety else "",
            f"Descrizione: {self.description}" if self.description else "",
            f"Note: {self.tasting_notes}" if self.tasting_notes else ""
        ]
        return " | ".join([p for p in parts if p])


# Indexes for better query performance
db.Index('idx_wines_name', Wine.name)
db.Index('idx_wines_producer', Wine.producer)
db.Index('idx_wines_type', Wine.type)
db.Index('idx_wines_region', Wine.region)
db.Index('idx_wines_country', Wine.country)
db.Index('idx_wines_grape', Wine.grape_variety)
db.Index('idx_wines_qdrant_id', Wine.qdrant_id)
