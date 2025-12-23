"""
WineProposal Model - Represents a wine proposal made by AI to a customer
"""
from datetime import datetime
from app import db


class WineProposal(db.Model):
    """
    WineProposal entity representing a wine proposed by AI in a conversation.
    Tracks every wine recommendation with full analytics data.
    
    IMPORTANT:
    - A wine is SELECTED only when customer clicks the card and confirms
    - In MULTI-LABEL (journey) case, when customer selects a journey, ALL wines 
      in the journey must be marked as SELECTED
    - Wines PROPOSED but NOT SELECTED go into "Vini proposti ma non selezionati" metric
    """
    __tablename__ = 'wine_proposals'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='SET NULL'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    proposal_group_id = db.Column(db.String(100), index=True)  # UUID per raggruppare proposte dello stesso batch
    proposal_rank = db.Column(db.Integer, nullable=False)  # 1-based rank nella lista completa del messaggio
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Prezzo al momento della proposta
    margin = db.Column(db.Numeric(10, 2))  # Margine stimato (price - cost_price)
    proposal_reason = db.Column(db.Text)  # Motivazione della proposta (estratto da metadata o context)
    mode = db.Column(db.String(20))  # 'single' o 'journey'
    journey_id = db.Column(db.Integer)  # Se fa parte di un journey (0, 1, 2, etc. per distinguere percorsi diversi)
    is_selected = db.Column(db.Boolean, default=False, index=True)  # TRUE solo quando cliente clicca e conferma
    selected_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    session = db.relationship('Session', backref='wine_proposals')
    product = db.relationship('Product', backref='proposals')
    message = db.relationship('Message', backref='wine_proposals')
    
    def __repr__(self):
        return f'<WineProposal session={self.session_id} product={self.product_id} selected={self.is_selected}>'
    
    def to_dict(self):
        """Convert wine proposal to dictionary for API responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'message_id': self.message_id,
            'product_id': self.product_id,
            'proposal_group_id': self.proposal_group_id,
            'proposal_rank': self.proposal_rank,
            'price': float(self.price) if self.price else None,
            'margin': float(self.margin) if self.margin else None,
            'proposal_reason': self.proposal_reason,
            'mode': self.mode,
            'journey_id': self.journey_id,
            'is_selected': self.is_selected,
            'selected_at': self.selected_at.isoformat() if self.selected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def mark_as_selected(self):
        """Mark this proposal as selected by the customer"""
        self.is_selected = True
        self.selected_at = datetime.utcnow()


# Indexes for better query performance
db.Index('idx_wine_proposals_session', WineProposal.session_id)
db.Index('idx_wine_proposals_product', WineProposal.product_id)
db.Index('idx_wine_proposals_group', WineProposal.proposal_group_id)
db.Index('idx_wine_proposals_rank', WineProposal.proposal_rank)
db.Index('idx_wine_proposals_selected', WineProposal.is_selected)
db.Index('idx_wine_proposals_created', WineProposal.created_at)

