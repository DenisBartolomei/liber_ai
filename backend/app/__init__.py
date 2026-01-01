"""
LIBER - Flask Application Factory
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['FRONTEND_URL'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.venues import venues_bp
    from app.routes.products import products_bp
    from app.routes.chat import chat_bp
    from app.routes.menu import menu_bp
    from app.routes.analytics import analytics_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(venues_bp, url_prefix='/api/venues')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(menu_bp, url_prefix='/api/menu')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'service': 'liber-sommelier-ai'}
    
    # Note: Label images are now served directly from Supabase Storage (public bucket)
    # QR codes are served via signed URLs through the venues API endpoints
    
    return app

