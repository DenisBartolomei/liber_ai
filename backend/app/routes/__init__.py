"""
API Routes for Bacco Sommelier AI
"""
from app.routes.auth import auth_bp
from app.routes.venues import venues_bp
from app.routes.products import products_bp
from app.routes.chat import chat_bp
from app.routes.b2b import b2b_bp

__all__ = ['auth_bp', 'venues_bp', 'products_bp', 'chat_bp', 'b2b_bp']

