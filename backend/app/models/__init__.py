"""
Database Models for LIBER
"""
from app.models.venue import Venue
from app.models.product import Product
from app.models.wine import Wine
from app.models.venue_wine import VenueWine
from app.models.user import User
from app.models.session import Session
from app.models.message import Message
from app.models.menu_item import MenuItem
from app.models.wine_proposal import WineProposal
from app.models.access_token import AccessToken

__all__ = [
    'Venue',
    'Product',  # Legacy - will be deprecated
    'Wine',  # New master wine catalog
    'VenueWine',  # New venue-wine association
    'User',
    'Session',
    'Message',
    'MenuItem',
    'WineProposal',
    'AccessToken'
]

