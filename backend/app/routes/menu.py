"""
Menu Routes for LIBER
Handles food menu management and parsing
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import MenuItem, User, Venue
from app.services.menu_parser import MenuParserService

menu_bp = Blueprint('menu', __name__)


@menu_bp.route('/venue/<int:venue_id>', methods=['GET'])
def get_menu(venue_id):
    """
    Get all menu items for a venue.
    Public endpoint for customer access.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"GET /menu/venue/{venue_id} - Fetching menu items")
    
    venue = Venue.query.get(venue_id)
    if not venue:
        logger.warning(f"Venue {venue_id} not found")
        return jsonify({'message': 'Locale non trovato'}), 404
    
    # Get query params
    category = request.args.get('category')
    available_only = request.args.get('available', 'true').lower() == 'true'
    
    # Build query
    query = MenuItem.query.filter_by(venue_id=venue_id)
    
    if available_only:
        query = query.filter_by(is_available=True)
    
    if category:
        query = query.filter_by(category=category)
    
    items = query.order_by(MenuItem.category, MenuItem.display_order, MenuItem.name).all()
    logger.info(f"Found {len(items)} menu items for venue {venue_id}")
    
    # Group by category
    grouped = {}
    for item in items:
        cat = item.category or 'Altro'
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(item.to_dict())
    
    response_data = {
        'items': [item.to_dict() for item in items],
        'grouped': grouped,
        'categories': list(grouped.keys())
    }
    logger.info(f"Returning {len(response_data['items'])} items, {len(response_data['categories'])} categories")
    
    return jsonify(response_data), 200


@menu_bp.route('/venue/<int:venue_id>/items', methods=['POST'])
@jwt_required()
def add_menu_item(venue_id):
    """Add a single menu item."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'message': 'Nome piatto obbligatorio'}), 400
    
    item = MenuItem(
        venue_id=venue_id,
        name=data['name'],
        description=data.get('description'),
        category=data.get('category'),
        main_ingredient=data.get('main_ingredient'),
        cooking_method=data.get('cooking_method'),
        flavor_profile=data.get('flavor_profile'),
        price=data.get('price'),
        is_available=data.get('is_available', True),
        display_order=data.get('display_order', 0)
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify({
        'message': 'Piatto aggiunto',
        'item': item.to_dict()
    }), 201


@menu_bp.route('/venue/<int:venue_id>/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_menu_item(venue_id, item_id):
    """Update a menu item."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    item = MenuItem.query.get(item_id)
    
    if not item or item.venue_id != venue_id:
        return jsonify({'message': 'Piatto non trovato'}), 404
    
    data = request.get_json()
    
    # Update fields
    updatable = ['name', 'description', 'category', 'main_ingredient', 
                 'cooking_method', 'flavor_profile', 'price', 'is_available', 'display_order']
    
    for field in updatable:
        if field in data:
            setattr(item, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Piatto aggiornato',
        'item': item.to_dict()
    }), 200


@menu_bp.route('/venue/<int:venue_id>/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_menu_item(venue_id, item_id):
    """Delete a menu item."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    item = MenuItem.query.get(item_id)
    
    if not item or item.venue_id != venue_id:
        return jsonify({'message': 'Piatto non trovato'}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Piatto eliminato'}), 200


@menu_bp.route('/venue/<int:venue_id>/parse', methods=['POST'])
@jwt_required()
def parse_menu(venue_id):
    """
    Parse a menu text/file and extract dishes.
    Uses AI to intelligently extract dish info.
    
    Expected JSON:
    {
        "menu_text": "Antipasti:\n- Bruschetta al pomodoro €8\n- Carpaccio di manzo €14\n..."
    }
    
    Or file upload with menu image/PDF (future).
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    data = request.get_json()
    menu_text = data.get('menu_text', '')
    
    if not menu_text:
        return jsonify({'message': 'Testo menù obbligatorio'}), 400
    
    # Parse menu using AI
    parser = MenuParserService()
    
    try:
        parsed_items = parser.parse_menu_text(menu_text)
        
        # Save parsed items
        created_items = []
        for item_data in parsed_items:
            item = MenuItem(
                venue_id=venue_id,
                name=item_data.get('name'),
                description=item_data.get('description'),
                category=item_data.get('category'),
                main_ingredient=item_data.get('main_ingredient'),
                cooking_method=item_data.get('cooking_method'),
                flavor_profile=item_data.get('flavor_profile'),
                price=item_data.get('price'),
                is_available=True
            )
            db.session.add(item)
            created_items.append(item)
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(created_items)} piatti estratti e salvati',
            'items': [item.to_dict() for item in created_items]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': f'Errore nel parsing: {str(e)}'
        }), 500


@menu_bp.route('/venue/<int:venue_id>/bulk', methods=['POST'])
@jwt_required()
def bulk_add_items(venue_id):
    """
    Bulk add menu items.
    
    Expected JSON:
    {
        "items": [
            {"name": "Bruschetta", "category": "antipasto", ...},
            ...
        ]
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    data = request.get_json()
    items_data = data.get('items', [])
    
    if not items_data:
        return jsonify({'message': 'Nessun piatto da aggiungere'}), 400
    
    created = 0
    for item_data in items_data:
        if item_data.get('name'):
            item = MenuItem(
                venue_id=venue_id,
                name=item_data['name'],
                description=item_data.get('description'),
                category=item_data.get('category'),
                main_ingredient=item_data.get('main_ingredient'),
                cooking_method=item_data.get('cooking_method'),
                flavor_profile=item_data.get('flavor_profile'),
                price=item_data.get('price'),
                is_available=item_data.get('is_available', True),
                display_order=item_data.get('display_order', created)
            )
            db.session.add(item)
            created += 1
    
    db.session.commit()
    
    return jsonify({
        'message': f'{created} piatti aggiunti',
        'created': created
    }), 201


@menu_bp.route('/venue/<int:venue_id>/clear', methods=['DELETE'])
@jwt_required()
def clear_menu(venue_id):
    """Clear all menu items for a venue (before re-import)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    deleted = MenuItem.query.filter_by(venue_id=venue_id).delete()
    db.session.commit()
    
    return jsonify({
        'message': f'{deleted} piatti eliminati'
    }), 200

