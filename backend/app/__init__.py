"""
LIBER - Flask Application Factory
"""
import os
import logging
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from app.config import Config

# Configure structured logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cache = Cache()

# Initialize rate limiter with Redis support (falls back to memory if unavailable)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute", "5000 per hour"],
    storage_uri=os.getenv('REDIS_URL', 'memory://'),
    storage_options={"socket_connect_timeout": 2},
    strategy="fixed-window"
)


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure Redis URL for caching and rate limiting
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        app.config['REDIS_URL'] = redis_url
        app.config['CACHE_TYPE'] = 'RedisCache'
        app.config['CACHE_REDIS_URL'] = redis_url
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    else:
        app.config['CACHE_TYPE'] = 'SimpleCache'
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # Configure CORS - strict in production, permissive in development
    frontend_url = app.config.get('FRONTEND_URL', '')
    if app.config.get('DEBUG') or not frontend_url:
        # Development: allow common local origins
        allowed_origins = [
            'http://localhost:5173',
            'http://localhost:3000',
            'http://127.0.0.1:5173',
            'http://127.0.0.1:3000'
        ]
        if frontend_url and frontend_url not in allowed_origins:
            allowed_origins.append(frontend_url)
    else:
        # Production: strict origin checking
        allowed_origins = [frontend_url]
        # Also allow the Cloud Run URLs if they exist
        backend_url = os.getenv('BACKEND_URL', '')
        if backend_url:
            allowed_origins.append(backend_url)

    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
            "supports_credentials": True
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

    # Simple health check (fast, for load balancer)
    @app.route('/api/health')
    @limiter.exempt
    def health_check():
        return {'status': 'healthy', 'service': 'liber-sommelier-ai'}

    # Comprehensive health check (for monitoring)
    @app.route('/api/health/full')
    @limiter.exempt
    def health_check_full():
        from app.services.resilience import HealthCheckService
        return jsonify(HealthCheckService.get_full_health())

    # Readiness check (for Kubernetes/Cloud Run)
    @app.route('/api/ready')
    @limiter.exempt
    def readiness_check():
        from app.services.resilience import HealthCheckService
        db_health = HealthCheckService.check_database()
        if db_health['status'] == 'healthy':
            return {'status': 'ready'}, 200
        return {'status': 'not_ready', 'reason': 'database'}, 503

    # Rate limit exceeded handler
    @app.errorhandler(429)
    def ratelimit_handler(e):
        logger.warning(f"Rate limit exceeded for IP: {get_remote_address()}")
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please wait before trying again.',
            'retry_after': e.description
        }), 429

    # Global error handler for circuit breaker errors
    @app.errorhandler(503)
    def service_unavailable_handler(e):
        logger.error(f"Service unavailable: {e}")
        return jsonify({
            'error': 'Service temporarily unavailable',
            'message': 'One or more external services are temporarily unavailable. Please try again later.'
        }), 503

    # Request logging middleware
    @app.before_request
    def log_request_info():
        if request.path.startswith('/api/') and not request.path.startswith('/api/health'):
            logger.info(
                f"Request: {request.method} {request.path} "
                f"IP: {get_remote_address()} "
                f"User-Agent: {request.headers.get('User-Agent', 'unknown')[:50]}"
            )

    @app.after_request
    def log_response_info(response):
        if request.path.startswith('/api/') and not request.path.startswith('/api/health'):
            logger.info(
                f"Response: {request.method} {request.path} "
                f"Status: {response.status_code}"
            )
        return response

    # Note: Label images are now served directly from Supabase Storage (public bucket)
    # QR codes are served via signed URLs through the venues API endpoints

    logger.info(f"LIBER app initialized in {'DEBUG' if app.config.get('DEBUG') else 'PRODUCTION'} mode")

    return app

