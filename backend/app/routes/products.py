"""
Product Routes for LIBER Sommelier AI
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Product, User, Venue
from app.services.vector_search import VectorSearchService
from app.services.wine_parser import WineParserService

logger = logging.getLogger(__name__)

products_bp = Blueprint('products', __name__)


@products_bp.route('/venue/<venue_identifier>', methods=['GET'])
def get_products(venue_identifier):
    """
    Get products for a venue.
    Can be accessed by venue_id (authenticated) or slug (public).
    """
    # Try to find venue by slug first (public access)
    venue = Venue.query.filter_by(slug=venue_identifier, is_active=True).first()
    
    # If not found by slug, try by ID (requires auth check)
    if not venue:
        try:
            venue_id = int(venue_identifier)
            venue = Venue.query.get(venue_id)
        except ValueError:
            return jsonify({'message': 'Locale non trovato'}), 404
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    # Get query parameters for filtering
    wine_type = request.args.get('type')
    available_only = request.args.get('available', 'true').lower() == 'true'
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    # Build query
    query = Product.query.filter_by(venue_id=venue.id)
    
    if available_only:
        query = query.filter_by(is_available=True)
    
    if wine_type:
        query = query.filter_by(type=wine_type)
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Order by type and name
    products = query.order_by(Product.type, Product.name).all()
    
    return jsonify([p.to_dict() for p in products]), 200


@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID."""
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'message': 'Prodotto non trovato'}), 404
    
    return jsonify(product.to_dict(detailed=True)), 200


@products_bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    """Create a new product."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name') or not data.get('type') or not data.get('price'):
        return jsonify({'message': 'Nome, tipo e prezzo sono obbligatori'}), 400
    
    product = Product(
        venue_id=user.venue_id,
        name=data['name'],
        type=data['type'],
        category=data.get('category'),
        region=data.get('region'),
        country=data.get('country', 'Italia'),
        appellation=data.get('appellation'),
        grape_variety=data.get('grape_variety'),
        vintage=data.get('vintage'),
        producer=data.get('producer'),
        alcohol_content=data.get('alcohol_content'),
        body=data.get('body'),
        sweetness=data.get('sweetness'),
        price=data['price'],
        price_glass=data.get('price_glass'),
        description=data.get('description'),
        tasting_notes=data.get('tasting_notes'),
        aroma_profile=data.get('aroma_profile'),
        food_pairings=data.get('food_pairings'),
        serving_temperature=data.get('serving_temperature'),
        is_available=data.get('is_available', True)
    )
    
    db.session.add(product)
    db.session.commit()
    
    # Add to vector database
    try:
        vector_service = VectorSearchService()
        vector_service.index_product(product)
    except Exception as e:
        print(f"Error indexing product: {e}")
    
    return jsonify({
        'message': 'Prodotto creato',
        'product': product.to_dict(detailed=True)
    }), 201


@products_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update a product."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'message': 'Prodotto non trovato'}), 404
    
    if product.venue_id != user.venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    data = request.get_json()
    
    # Update fields
    updatable_fields = [
        'name', 'type', 'category', 'region', 'country', 'appellation',
        'grape_variety', 'vintage', 'producer', 'alcohol_content', 'body',
        'sweetness', 'tannin_level', 'acidity_level', 'price', 'price_glass',
        'description', 'tasting_notes', 'aroma_profile', 'food_pairings',
        'pairing_notes', 'serving_temperature', 'decanting_time', 'glass_type',
        'is_available', 'stock_quantity', 'image_url'
    ]
    
    for field in updatable_fields:
        if field in data:
            setattr(product, field, data[field])
    
    db.session.commit()
    
    # Update in vector database
    try:
        vector_service = VectorSearchService()
        vector_service.index_product(product)
    except Exception as e:
        print(f"Error updating product in vector DB: {e}")
    
    return jsonify({
        'message': 'Prodotto aggiornato',
        'product': product.to_dict(detailed=True)
    }), 200


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Delete a product."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'message': 'Prodotto non trovato'}), 404
    
    if product.venue_id != user.venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    # Remove from vector database
    try:
        vector_service = VectorSearchService()
        vector_service.delete_product(product)
    except Exception as e:
        print(f"Error deleting product from vector DB: {e}")
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'message': 'Prodotto eliminato'}), 200


@products_bp.route('/venue/<int:venue_id>/bulk', methods=['POST'])
@jwt_required()
def bulk_import(venue_id):
    """Bulk import products."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    logger.info(f"Bulk import request for venue {venue_id} by user {current_user_id}")
    
    if not user or user.venue_id != venue_id:
        logger.warning(f"Unauthorized bulk import attempt: user {current_user_id} for venue {venue_id}")
        return jsonify({'message': 'Non autorizzato'}), 403
    
    data = request.get_json()
    products_data = data.get('products', [])
    
    logger.info(f"Received {len(products_data)} products to import for venue {venue_id}")
    
    if not products_data:
        logger.warning(f"Empty products list for venue {venue_id}")
        return jsonify({'message': 'Nessun prodotto da importare'}), 400
    
    created_count = 0
    errors = []
    
    for idx, p_data in enumerate(products_data):
        try:
            logger.debug(f"Creating product {idx}: {p_data.get('name')}")
            product = Product(
                venue_id=venue_id,
                name=p_data.get('name'),
                type=p_data.get('type', 'red'),
                region=p_data.get('region'),
                grape_variety=p_data.get('grape_variety'),
                vintage=p_data.get('vintage'),
                price=p_data.get('price', 0),
                description=p_data.get('description'),
                tasting_notes=p_data.get('tasting_notes'),
                food_pairings=p_data.get('food_pairings'),
                is_available=p_data.get('is_available', True)
            )
            db.session.add(product)
            created_count += 1
        except Exception as e:
            logger.error(f"Error creating product {idx} ({p_data.get('name')}): {e}")
            errors.append({'index': idx, 'error': str(e)})
    
    try:
        db.session.commit()
        logger.info(f"Bulk import complete for venue {venue_id}: {created_count} created, {len(errors)} errors")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database commit failed for venue {venue_id}: {e}")
        return jsonify({'message': f'Errore database: {str(e)}'}), 500
    
    return jsonify({
        'message': f'{created_count} prodotti importati',
        'created': created_count,
        'errors': errors
    }), 201


@products_bp.route('/venue/<int:venue_id>/sync-vectors', methods=['POST'])
@jwt_required()
def sync_vectors(venue_id):
    """Sync all products to vector database."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    products = Product.query.filter_by(venue_id=venue_id).all()
    
    try:
        vector_service = VectorSearchService()
        synced_count = vector_service.bulk_index(products)
        
        return jsonify({
            'message': f'{synced_count} prodotti sincronizzati',
            'synced': synced_count
        }), 200
    except Exception as e:
        return jsonify({
            'message': f'Errore durante la sincronizzazione: {str(e)}'
        }), 500


@products_bp.route('/venue/<int:venue_id>/parse', methods=['POST'])
@jwt_required()
def parse_wine_list(venue_id):
    """Parse wine list text and extract structured wine data using AI."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    data = request.get_json()
    wine_text = data.get('wine_text', '')
    
    if not wine_text.strip():
        return jsonify({'message': 'Testo della carta vini mancante'}), 400
    
    try:
        parser = WineParserService()
        wines = parser.parse_wine_list(wine_text)
        
        return jsonify({
            'message': f'{len(wines)} vini estratti',
            'wines': wines
        }), 200
    except Exception as e:
        return jsonify({
            'message': f'Errore durante il parsing: {str(e)}'
        }), 500


@products_bp.route('/venue/<int:venue_id>/parse-images', methods=['POST'])
@jwt_required()
def parse_wine_images(venue_id):
    """Parse wine list from images using GPT-4 Vision."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    data = request.get_json()
    images = data.get('images', [])
    
    if not images:
        return jsonify({'message': 'Nessuna immagine fornita'}), 400
    
    if len(images) > 10:
        return jsonify({'message': 'Massimo 10 immagini consentite'}), 400
    
    logger.info(f"Parsing {len(images)} wine list images for venue {venue_id}")
    
    try:
        parser = WineParserService()
        wines = parser.parse_wine_images(images)
        
        logger.info(f"Extracted {len(wines)} wines from images for venue {venue_id}")
        
        return jsonify({
            'message': f'{len(wines)} vini estratti dalle immagini',
            'wines': wines
        }), 200
    except Exception as e:
        logger.error(f"Error parsing wine images for venue {venue_id}: {e}")
        return jsonify({
            'message': f'Errore durante il parsing delle immagini: {str(e)}'
        }), 500


@products_bp.route('/venue/<int:venue_id>/clear', methods=['DELETE'])
@jwt_required()
def clear_products(venue_id):
    """Clear all products for a venue."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    try:
        # Delete all products for this venue
        deleted_count = Product.query.filter_by(venue_id=venue_id).delete()
        db.session.commit()
        
        return jsonify({
            'message': f'{deleted_count} prodotti eliminati',
            'deleted': deleted_count
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': f'Errore durante l\'eliminazione: {str(e)}'
        }), 500

