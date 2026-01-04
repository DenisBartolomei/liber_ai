"""
Venue Routes for LIBER Sommelier AI
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Venue, User
from app.services.qr_generator import QRGeneratorService

logger = logging.getLogger(__name__)

venues_bp = Blueprint('venues', __name__)


@venues_bp.route('/<slug>', methods=['GET'])
def get_venue_by_slug(slug):
    """
    Get venue information by slug.
    Public endpoint for customer access via QR code.
    """
    venue = Venue.query.filter_by(slug=slug, is_active=True).first()
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    # Return limited info for public access
    return jsonify({
        'id': venue.id,
        'name': venue.name,
        'slug': venue.slug,
        'description': venue.description,
        'cuisine_type': venue.cuisine_type,
        'logo_url': venue.logo_url,
        'primary_color': venue.primary_color,
        'welcome_message': venue.welcome_message or 'Benvenuto! Sono il tuo sommelier virtuale. Come posso aiutarti nella scelta del vino oggi?'
    }), 200


@venues_bp.route('/<int:venue_id>', methods=['GET'])
@jwt_required()
def get_venue(venue_id):
    """Get venue details (authenticated - owner only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    venue = Venue.query.get(venue_id)
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    return jsonify(venue.to_dict(include_stats=True)), 200


@venues_bp.route('/<int:venue_id>', methods=['PUT'])
@jwt_required()
def update_venue(venue_id):
    """Update venue information."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        logger.warning(f"Unauthorized venue update attempt: user {current_user_id} for venue {venue_id}")
        return jsonify({'message': 'Non autorizzato'}), 403
    
    venue = Venue.query.get(venue_id)
    
    if not venue:
        logger.warning(f"Venue not found for update: {venue_id}")
        return jsonify({'message': 'Locale non trovato'}), 404
    
    data = request.get_json()
    logger.info(f"Updating venue {venue_id} with data: {list(data.keys()) if data else 'None'}")
    
    # Handle featured_wines separately with validation
    if 'featured_wines' in data:
        featured_wines = data.get('featured_wines', [])
        success, message = venue.set_featured_wines(featured_wines)
        if not success:
            return jsonify({'message': message}), 400
        # featured_wines is now saved in venue.preferences via set_featured_wines
        # Remove from data to avoid double processing
        data.pop('featured_wines')
    
    # Handle annual_conversation_limit separately to initialize start date
    if 'annual_conversation_limit' in data:
        new_limit = data.get('annual_conversation_limit')
        # If limit is being set and start date is not set, initialize it
        if new_limit is not None and venue.annual_conversation_limit_start_date is None:
            venue.initialize_conversation_limit_period()
            logger.info(f"Initialized conversation limit start date for venue {venue_id}")
        # Update the limit
        venue.annual_conversation_limit = new_limit
        data.pop('annual_conversation_limit')
    
    # Update allowed fields
    updatable_fields = [
        'name', 'description', 'cuisine_type', 'menu_style', 
        'preferences', 'target_audience', 'logo_url', 'primary_color',
        'welcome_message', 'sommelier_style', 'is_onboarded'
    ]
    
    changes = {}
    for field in updatable_fields:
        if field in data:
            old_value = getattr(venue, field)
            new_value = data[field]
            if old_value != new_value:
                setattr(venue, field, new_value)
                changes[field] = {'old': old_value, 'new': new_value}
    
    if changes:
        logger.info(f"Venue {venue_id} changes: {changes}")
        try:
            db.session.commit()
            logger.info(f"Venue {venue_id} updated successfully. is_onboarded: {venue.is_onboarded}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating venue {venue_id}: {e}", exc_info=True)
            return jsonify({'message': f'Errore durante il salvataggio: {str(e)}'}), 500
    else:
        logger.info(f"No changes detected for venue {venue_id}")
    
    return jsonify({
        'message': 'Locale aggiornato',
        'venue': venue.to_dict(include_stats=True)
    }), 200


@venues_bp.route('/<int:venue_id>/qrcode', methods=['GET'])
@jwt_required()
def get_qr_code(venue_id):
    """Get or generate QR code for the venue."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    venue = Venue.query.get(venue_id)
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    # Generate QR code as base64 for immediate display
    qr_service = QRGeneratorService()
    qr_base64 = qr_service.generate_base64(venue)
    
    # Also save file version if not exists (returns storage path like "qrcodes/qr_slug.png")
    storage_path = None
    if not venue.qr_code_url:
        storage_path = qr_service.generate_for_venue(venue)
        venue.qr_code_url = storage_path
        db.session.commit()
    else:
        storage_path = venue.qr_code_url
    
    # Generate signed URL for download (bucket is private)
    signed_url = None
    if storage_path:
        # Extract filename from storage path (format: "qrcodes/qr_slug.png" or "qrcodes/qr_slug.png")
        from app.services.supabase_storage import SupabaseStorageService
        storage_service = SupabaseStorageService()
        qr_bucket = current_app.config.get('SUPABASE_STORAGE_BUCKET_QRCODES', 'qrcodes')
        
        # Extract filename (everything after the bucket name and slash)
        if '/' in storage_path:
            filename = storage_path.split('/', 1)[1] if storage_path.startswith(f"{qr_bucket}/") else storage_path
        else:
            filename = storage_path
        
        # Generate signed URL (valid for 1 hour)
        signed_url = storage_service.get_signed_url(qr_bucket, filename, expires_in=3600)
    
    return jsonify({
        'qr_code_url': f"data:image/png;base64,{qr_base64}",
        'qr_code_storage_path': storage_path,
        'qr_code_download_url': signed_url,  # Signed URL for download (bucket is private)
        'venue_url': f"/v/{venue.slug}"
    }), 200


@venues_bp.route('/<int:venue_id>/qrcode/regenerate', methods=['POST'])
@jwt_required()
def regenerate_qr_code(venue_id):
    """Regenerate QR code for the venue."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    venue = Venue.query.get(venue_id)
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    qr_service = QRGeneratorService()
    
    # Regenerate file and get base64
    storage_path = qr_service.generate_for_venue(venue, force_regenerate=True)
    venue.qr_code_url = storage_path
    qr_base64 = qr_service.generate_base64(venue)
    db.session.commit()
    
    # Generate signed URL for download (bucket is private)
    signed_url = None
    if storage_path:
        from app.services.supabase_storage import SupabaseStorageService
        storage_service = SupabaseStorageService()
        qr_bucket = current_app.config.get('SUPABASE_STORAGE_BUCKET_QRCODES', 'qrcodes')
        
        # Extract filename from storage path
        if '/' in storage_path:
            filename = storage_path.split('/', 1)[1] if storage_path.startswith(f"{qr_bucket}/") else storage_path
        else:
            filename = storage_path
        
        # Generate signed URL (valid for 1 hour)
        signed_url = storage_service.get_signed_url(qr_bucket, filename, expires_in=3600)
    
    return jsonify({
        'message': 'QR code rigenerato',
        'qr_code_url': f"data:image/png;base64,{qr_base64}",
        'qr_code_storage_path': storage_path,
        'qr_code_download_url': signed_url,  # Signed URL for download (bucket is private)
        'venue_url': f"/v/{venue.slug}"
    }), 200


@venues_bp.route('/<int:venue_id>/onboarding', methods=['POST'])
@jwt_required()
def complete_onboarding(venue_id):
    """Complete venue onboarding with preferences."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    venue = Venue.query.get(venue_id)
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    data = request.get_json()
    
    # Update onboarding data
    if 'cuisine_type' in data:
        venue.cuisine_type = data['cuisine_type']
    if 'target_audience' in data:
        venue.target_audience = data['target_audience']
    if 'menu_style' in data:
        venue.menu_style = {'style': data['menu_style']}
    if 'preferences' in data:
        venue.preferences = data['preferences']
    
    venue.is_onboarded = True
    
    # Generate QR code
    qr_service = QRGeneratorService()
    venue.qr_code_url = qr_service.generate_for_venue(venue)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Onboarding completato',
        'venue': venue.to_dict()
    }), 200

