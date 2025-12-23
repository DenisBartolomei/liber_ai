"""
Authentication Routes for LIBER Sommelier AI
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    jwt_required, 
    get_jwt_identity
)
from sqlalchemy.exc import IntegrityError, OperationalError
from app import db
from app.models import User, Venue

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new venue and owner account.
    
    Expected JSON:
    {
        "venue_name": "Ristorante Da Mario",
        "email": "mario@example.com",
        "password": "securepassword"
    }
    """
    data = request.get_json()
    
    # Validate required fields
    if not data:
        logger.warning("Registration attempt with no data")
        return jsonify({'message': 'Dati mancanti'}), 400
    
    venue_name = data.get('venue_name')
    email = data.get('email')
    password = data.get('password')
    
    logger.info(f"Registration attempt for venue: '{venue_name}', email: '{email}'")
    
    if not all([venue_name, email, password]):
        logger.warning(f"Registration failed - missing fields. venue_name: {bool(venue_name)}, email: {bool(email)}, password: {bool(password)}")
        return jsonify({'message': 'Tutti i campi sono obbligatori'}), 400
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        logger.warning(f"Registration failed - email already exists: {email}")
        return jsonify({'message': 'Email già registrata'}), 409
    
    # Validate password
    if len(password) < 8:
        logger.warning(f"Registration failed - password too short for: {email}")
        return jsonify({'message': 'La password deve essere di almeno 8 caratteri'}), 400
    
    try:
        # Generate unique slug
        slug = Venue.generate_slug(venue_name)
        logger.info(f"Generated slug: '{slug}' for venue: '{venue_name}'")
        
        # Create venue
        venue = Venue(
            name=venue_name,
            slug=slug,
            is_active=True,
            is_onboarded=False,
            plan='trial'
        )
        db.session.add(venue)
        logger.info(f"Venue object created, attempting flush...")
        
        # Flush to get venue ID - wrap in try/except for specific error handling
        try:
            db.session.flush()
        except IntegrityError as flush_error:
            logger.error(f"Venue flush failed - IntegrityError: {flush_error}")
            db.session.rollback()
            return jsonify({'message': 'Errore nella creazione del locale. Slug potrebbe essere duplicato. Riprova.'}), 500
        except OperationalError as op_error:
            logger.error(f"Venue flush failed - OperationalError: {op_error}")
            db.session.rollback()
            return jsonify({'message': 'Errore di connessione al database. Riprova.'}), 500
        
        # Verify venue was actually created with an ID
        if not venue.id:
            logger.error(f"Venue creation failed - no ID assigned after flush for: '{venue_name}'")
            db.session.rollback()
            return jsonify({'message': 'Errore nella creazione del locale. Riprova.'}), 500
        
        logger.info(f"Venue created successfully with ID: {venue.id}")
        
        # Create user with the venue_id
        user = User(
            venue_id=venue.id,
            email=email,
            role='owner',
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        logger.info(f"User object created with venue_id: {venue.id}")
        
        # Commit the entire transaction
        try:
            db.session.commit()
        except IntegrityError as commit_error:
            logger.error(f"Commit failed - IntegrityError: {commit_error}")
            db.session.rollback()
            if 'email' in str(commit_error).lower():
                return jsonify({'message': 'Email già registrata'}), 409
            return jsonify({'message': 'Errore durante il salvataggio. Riprova.'}), 500
        
        logger.info(f"Registration complete! User ID: {user.id}, Venue ID: {venue.id}, Email: {email}")
        
        # Verify both were created by re-querying
        saved_venue = Venue.query.get(venue.id)
        saved_user = User.query.get(user.id)
        
        if not saved_venue:
            logger.error(f"CRITICAL: Venue {venue.id} not found after commit!")
        if not saved_user:
            logger.error(f"CRITICAL: User {user.id} not found after commit!")
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'Registrazione completata',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
            'venue': venue.to_dict()
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Registration failed - IntegrityError: {e}", exc_info=True)
        if 'email' in str(e).lower():
            return jsonify({'message': 'Email già registrata'}), 409
        if 'slug' in str(e).lower():
            return jsonify({'message': 'Errore nella creazione del locale. Riprova.'}), 500
        return jsonify({'message': 'Errore durante la registrazione. Verifica i dati inseriti.'}), 500
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"Registration failed - OperationalError (DB connection?): {e}", exc_info=True)
        return jsonify({'message': 'Errore di connessione al database. Riprova tra qualche secondo.'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration failed - Unexpected error: {e}", exc_info=True)
        return jsonify({'message': f'Errore durante la registrazione: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return tokens.
    
    Expected JSON:
    {
        "email": "mario@example.com",
        "password": "securepassword"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Dati mancanti'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({'message': 'Email e password sono obbligatori'}), 400
    
    # Find user
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        logger.warning(f"Failed login attempt for email: {email}")
        return jsonify({'message': 'Credenziali non valide'}), 401
    
    if not user.is_active:
        logger.warning(f"Login attempt for inactive account: {email}")
        return jsonify({'message': 'Account disattivato'}), 403
    
    # Refresh venue from database to ensure we have latest data
    if user.venue_id:
        db.session.refresh(user.venue)
        logger.info(f"User {user.id} logged in. Venue {user.venue_id} is_onboarded: {user.venue.is_onboarded}")
    
    # Record login
    user.record_login()
    db.session.commit()
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    venue_data = user.venue.to_dict() if user.venue else None
    logger.info(f"Login successful for user {user.id}. Returning venue data with is_onboarded: {venue_data.get('is_onboarded') if venue_data else 'N/A'}")
    
    return jsonify({
        'message': 'Login effettuato',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(),
        'venue': venue_data
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        'access_token': access_token
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user's profile."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Utente non trovato'}), 404
    
    return jsonify({
        'user': user.to_dict(),
        'venue': user.venue.to_dict(include_stats=True) if user.venue else None
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user's profile."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Utente non trovato'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'phone' in data:
        user.phone = data['phone']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profilo aggiornato',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change current user's password."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Utente non trovato'}), 404
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not all([current_password, new_password]):
        return jsonify({'message': 'Password corrente e nuova password sono obbligatorie'}), 400
    
    if not user.check_password(current_password):
        return jsonify({'message': 'Password corrente non valida'}), 401
    
    if len(new_password) < 8:
        return jsonify({'message': 'La nuova password deve essere di almeno 8 caratteri'}), 400
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password aggiornata'}), 200


@auth_bp.route('/debug/venue/<int:venue_id>', methods=['GET'])
@jwt_required()
def debug_venue(venue_id):
    """
    Debug endpoint to check venue status directly from database.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    # Query venue fresh from database
    venue = Venue.query.get(venue_id)
    
    if not venue:
        return jsonify({'message': 'Venue non trovato', 'venue_id': venue_id}), 404
    
    logger.info(f"[DEBUG] Venue {venue_id} status check:")
    logger.info(f"  - name: {venue.name}")
    logger.info(f"  - slug: {venue.slug}")
    logger.info(f"  - is_onboarded: {venue.is_onboarded}")
    logger.info(f"  - is_active: {venue.is_active}")
    
    return jsonify({
        'debug': True,
        'venue_id': venue.id,
        'name': venue.name,
        'slug': venue.slug,
        'is_onboarded': venue.is_onboarded,
        'is_active': venue.is_active,
        'created_at': venue.created_at.isoformat() if venue.created_at else None,
        'full_venue': venue.to_dict()
    }), 200

