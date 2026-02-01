"""
Wine Routes for LIBER Sommelier AI
New architecture with separate wines (master catalog) and venue_wines (venue-specific)
"""
import logging
import csv
import io
import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, limiter
from app.models import User, Venue, Wine, VenueWine
from app.services.wine_parser import WineParserService
from app.services.wine_description_generator import WineDescriptionGenerator

logger = logging.getLogger(__name__)

wines_bp = Blueprint('wines', __name__)

# Rate limits for AI-intensive operations
AI_OPERATION_LIMIT = "5 per minute"


# ===========================================
# WINE CATALOG (Master wines)
# ===========================================

@wines_bp.route('/catalog', methods=['GET'])
def get_wine_catalog():
    """
    Get the master wine catalog.
    Public endpoint for browsing available wines.
    Supports filtering by type, region, country.
    """
    wine_type = request.args.get('type')
    region = request.args.get('region')
    country = request.args.get('country')
    search = request.args.get('search')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    query = Wine.query

    if wine_type:
        query = query.filter(Wine.type == wine_type)
    if region:
        query = query.filter(Wine.region.ilike(f'%{region}%'))
    if country:
        query = query.filter(Wine.country.ilike(f'%{country}%'))
    if search:
        query = query.filter(
            db.or_(
                Wine.name.ilike(f'%{search}%'),
                Wine.producer.ilike(f'%{search}%'),
                Wine.grape_variety.ilike(f'%{search}%')
            )
        )

    total = query.count()
    wines = query.order_by(Wine.name).offset(offset).limit(limit).all()

    return jsonify({
        'wines': [w.to_dict() for w in wines],
        'total': total,
        'limit': limit,
        'offset': offset
    }), 200


@wines_bp.route('/catalog/<int:wine_id>', methods=['GET'])
def get_wine_from_catalog(wine_id):
    """Get a single wine from the master catalog."""
    wine = Wine.query.get(wine_id)
    if not wine:
        return jsonify({'message': 'Vino non trovato'}), 404
    return jsonify(wine.to_dict(detailed=True)), 200


@wines_bp.route('/catalog', methods=['POST'])
@jwt_required()
def add_wine_to_catalog():
    """
    Add a new wine to the master catalog.
    Requires authentication. In production, this should be admin-only.
    """
    data = request.get_json()

    # Validate required fields
    if not data.get('name') or not data.get('type'):
        return jsonify({'message': 'Nome e tipo sono obbligatori'}), 400

    # Check if wine already exists (by name + producer + type)
    existing = Wine.query.filter(
        Wine.name == data['name'],
        Wine.producer == data.get('producer'),
        Wine.type == data['type']
    ).first()

    if existing:
        return jsonify({
            'message': 'Vino gi\u00e0 presente nel catalogo',
            'wine': existing.to_dict()
        }), 409

    wine = Wine(
        name=data['name'],
        type=data['type'],
        producer=data.get('producer'),
        category=data.get('category'),
        region=data.get('region'),
        country=data.get('country', 'Italia'),
        appellation=data.get('appellation'),
        grape_variety=data.get('grape_variety'),
        alcohol_content=data.get('alcohol_content'),
        body=data.get('body'),
        sweetness=data.get('sweetness'),
        tannin_level=data.get('tannin_level'),
        acidity_level=data.get('acidity_level'),
        color=data.get('color'),
        aromas=data.get('aromas'),
        aroma_profile=data.get('aroma_profile'),
        description=data.get('description'),
        tasting_notes=data.get('tasting_notes'),
        food_pairings=data.get('food_pairings'),
        pairing_notes=data.get('pairing_notes'),
        serving_temperature=data.get('serving_temperature'),
        decanting_time=data.get('decanting_time'),
        glass_type=data.get('glass_type'),
        winemaker=data.get('winemaker'),
        image_url=data.get('image_url')
    )

    db.session.add(wine)
    db.session.commit()

    return jsonify({
        'message': 'Vino aggiunto al catalogo',
        'wine': wine.to_dict()
    }), 201


# ===========================================
# VENUE WINES (Venue-specific wine list)
# ===========================================

@wines_bp.route('/venue/<venue_identifier>', methods=['GET'])
def get_venue_wines(venue_identifier):
    """
    Get wines for a venue.
    Can be accessed by venue_id or slug.
    Returns full wine details merged with venue-specific data.
    """
    # Find venue by slug or ID
    venue = Venue.query.filter_by(slug=venue_identifier, is_active=True).first()
    if not venue:
        try:
            venue_id = int(venue_identifier)
            venue = Venue.query.get(venue_id)
        except ValueError:
            return jsonify({'message': 'Locale non trovato'}), 404

    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404

    # Get query parameters
    wine_type = request.args.get('type')
    available_only = request.args.get('available', 'true').lower() == 'true'
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    # Build query
    query = VenueWine.query.filter_by(venue_id=venue.id)

    if available_only:
        query = query.filter_by(is_available=True)

    if min_price is not None:
        query = query.filter(VenueWine.price >= min_price)

    if max_price is not None:
        query = query.filter(VenueWine.price <= max_price)

    # Join with Wine to filter by type
    if wine_type:
        query = query.join(Wine).filter(Wine.type == wine_type)

    # Get results with eager loading
    venue_wines = query.options(db.joinedload(VenueWine.wine)).all()

    # Sort by type and name
    venue_wines.sort(key=lambda vw: (vw.wine.type if vw.wine else '', vw.wine.name if vw.wine else ''))

    return jsonify([vw.to_full_dict() for vw in venue_wines]), 200


@wines_bp.route('/venue/<int:venue_id>/wine/<int:venue_wine_id>', methods=['GET'])
def get_venue_wine(venue_id, venue_wine_id):
    """Get a single venue wine with full details."""
    venue_wine = VenueWine.query.filter_by(id=venue_wine_id, venue_id=venue_id).first()

    if not venue_wine:
        return jsonify({'message': 'Vino non trovato'}), 404

    return jsonify(venue_wine.to_full_dict(detailed=True)), 200


@wines_bp.route('/venue/<int:venue_id>/add', methods=['POST'])
@jwt_required()
def add_wine_to_venue(venue_id):
    """
    Add a wine to venue's wine list.
    Can either:
    1. Link an existing wine from catalog (wine_id provided)
    2. Create a new wine and link it (wine data provided)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403

    data = request.get_json()

    # Validate required venue-specific fields
    if data.get('price') is None:
        return jsonify({'message': 'Prezzo obbligatorio'}), 400

    wine = None

    # Option 1: Link existing wine from catalog
    if data.get('wine_id'):
        wine = Wine.query.get(data['wine_id'])
        if not wine:
            return jsonify({'message': 'Vino non trovato nel catalogo'}), 404
    else:
        # Option 2: Create new wine or find existing by name/type
        if not data.get('name') or not data.get('type'):
            return jsonify({'message': 'Nome e tipo obbligatori per nuovo vino'}), 400

        # Try to find existing wine
        wine = Wine.query.filter(
            Wine.name == data['name'],
            Wine.type == data['type'],
            Wine.producer == data.get('producer')
        ).first()

        if not wine:
            # Create new wine in catalog
            wine = Wine(
                name=data['name'],
                type=data['type'],
                producer=data.get('producer'),
                region=data.get('region'),
                country=data.get('country', 'Italia'),
                appellation=data.get('appellation'),
                grape_variety=data.get('grape_variety'),
                alcohol_content=data.get('alcohol_content'),
                body=data.get('body'),
                sweetness=data.get('sweetness'),
                tannin_level=data.get('tannin_level'),
                acidity_level=data.get('acidity_level'),
                color=data.get('color'),
                aromas=data.get('aromas'),
                aroma_profile=data.get('aroma_profile'),
                description=data.get('description'),
                tasting_notes=data.get('tasting_notes'),
                food_pairings=data.get('food_pairings'),
                image_url=data.get('image_url')
            )
            db.session.add(wine)
            db.session.flush()  # Get wine.id

    # Check if venue already has this wine (same vintage)
    existing = VenueWine.query.filter_by(
        venue_id=venue_id,
        wine_id=wine.id,
        vintage=data.get('vintage')
    ).first()

    if existing:
        return jsonify({
            'message': 'Questo vino \u00e8 gi\u00e0 presente nella carta',
            'venue_wine': existing.to_full_dict()
        }), 409

    # Create venue_wine association
    venue_wine = VenueWine(
        venue_id=venue_id,
        wine_id=wine.id,
        vintage=data.get('vintage'),
        price=data['price'],
        price_glass=data.get('price_glass'),
        cost_price=data.get('cost_price'),
        is_available=data.get('is_available', True),
        stock_quantity=data.get('stock_quantity'),
        image_url=data.get('venue_image_url'),  # Venue-specific image
        external_id=data.get('external_id'),
        notes=data.get('notes')
    )

    db.session.add(venue_wine)
    db.session.commit()

    return jsonify({
        'message': 'Vino aggiunto alla carta',
        'venue_wine': venue_wine.to_full_dict()
    }), 201


@wines_bp.route('/venue/<int:venue_id>/wine/<int:venue_wine_id>', methods=['PUT'])
@jwt_required()
def update_venue_wine(venue_id, venue_wine_id):
    """Update venue-specific wine data (price, availability, etc.)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403

    venue_wine = VenueWine.query.filter_by(id=venue_wine_id, venue_id=venue_id).first()

    if not venue_wine:
        return jsonify({'message': 'Vino non trovato'}), 404

    data = request.get_json()

    # Update venue-specific fields
    if 'price' in data:
        venue_wine.price = data['price']
    if 'price_glass' in data:
        venue_wine.price_glass = data['price_glass']
    if 'cost_price' in data:
        venue_wine.cost_price = data['cost_price']
    if 'vintage' in data:
        venue_wine.vintage = data['vintage']
    if 'is_available' in data:
        venue_wine.is_available = data['is_available']
    if 'stock_quantity' in data:
        venue_wine.stock_quantity = data['stock_quantity']
    if 'image_url' in data:
        venue_wine.image_url = data['image_url']
    if 'notes' in data:
        venue_wine.notes = data['notes']

    db.session.commit()

    return jsonify({
        'message': 'Vino aggiornato',
        'venue_wine': venue_wine.to_full_dict()
    }), 200


@wines_bp.route('/venue/<int:venue_id>/wine/<int:venue_wine_id>', methods=['DELETE'])
@jwt_required()
def remove_wine_from_venue(venue_id, venue_wine_id):
    """Remove a wine from venue's wine list (does not delete from catalog)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403

    venue_wine = VenueWine.query.filter_by(id=venue_wine_id, venue_id=venue_id).first()

    if not venue_wine:
        return jsonify({'message': 'Vino non trovato'}), 404

    # Delete associated wine proposals
    from app.models import WineProposal
    WineProposal.query.filter_by(venue_wine_id=venue_wine_id).delete()

    db.session.delete(venue_wine)
    db.session.commit()

    return jsonify({'message': 'Vino rimosso dalla carta'}), 200


@wines_bp.route('/venue/<int:venue_id>/clear', methods=['DELETE'])
@jwt_required()
def clear_venue_wines(venue_id):
    """Clear all wines from venue's wine list."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403

    try:
        # Delete associated wine proposals first
        from app.models import WineProposal
        venue_wine_ids = [vw.id for vw in VenueWine.query.filter_by(venue_id=venue_id).all()]
        if venue_wine_ids:
            WineProposal.query.filter(WineProposal.venue_wine_id.in_(venue_wine_ids)).delete(synchronize_session=False)

        # Delete all venue_wines
        deleted_count = VenueWine.query.filter_by(venue_id=venue_id).delete()
        db.session.commit()

        return jsonify({
            'message': f'{deleted_count} vini rimossi dalla carta',
            'deleted': deleted_count
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error clearing venue wines: {e}")
        return jsonify({'message': f'Errore: {str(e)}'}), 500


# ===========================================
# BULK OPERATIONS
# ===========================================

@wines_bp.route('/venue/<int:venue_id>/bulk', methods=['POST'])
@jwt_required()
def bulk_import_wines(venue_id):
    """
    Bulk import wines to venue's wine list.
    Automatically creates wines in catalog if they don't exist.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403

    data = request.get_json()
    wines_data = data.get('wines', [])

    if not wines_data:
        return jsonify({'message': 'Nessun vino da importare'}), 400

    created_count = 0
    skipped_count = 0
    errors = []

    for idx, wine_data in enumerate(wines_data):
        try:
            # Validate required fields
            if not wine_data.get('name') or not wine_data.get('type') or wine_data.get('price') is None:
                errors.append({'index': idx, 'error': 'Nome, tipo e prezzo sono obbligatori'})
                continue

            # Find or create wine in catalog
            wine = Wine.query.filter(
                Wine.name == wine_data['name'],
                Wine.type == wine_data['type'],
                Wine.producer == wine_data.get('producer')
            ).first()

            if not wine:
                wine = Wine(
                    name=wine_data['name'],
                    type=wine_data['type'],
                    producer=wine_data.get('producer'),
                    region=wine_data.get('region'),
                    country=wine_data.get('country', 'Italia'),
                    appellation=wine_data.get('appellation'),
                    grape_variety=wine_data.get('grape_variety'),
                    alcohol_content=wine_data.get('alcohol_content'),
                    description=wine_data.get('description'),
                    tasting_notes=wine_data.get('tasting_notes'),
                    food_pairings=wine_data.get('food_pairings'),
                    body=wine_data.get('body'),
                    tannin_level=wine_data.get('tannin_level'),
                    acidity_level=wine_data.get('acidity_level'),
                    color=wine_data.get('color'),
                    aromas=wine_data.get('aromas')
                )
                db.session.add(wine)
                db.session.flush()

            # Check if venue already has this wine
            existing = VenueWine.query.filter_by(
                venue_id=venue_id,
                wine_id=wine.id,
                vintage=wine_data.get('vintage')
            ).first()

            if existing:
                skipped_count += 1
                continue

            # Create venue_wine
            venue_wine = VenueWine(
                venue_id=venue_id,
                wine_id=wine.id,
                vintage=wine_data.get('vintage'),
                price=wine_data['price'],
                price_glass=wine_data.get('price_glass'),
                cost_price=wine_data.get('cost_price'),
                is_available=wine_data.get('is_available', True),
                stock_quantity=wine_data.get('stock_quantity'),
                external_id=wine_data.get('external_id')
            )
            db.session.add(venue_wine)
            created_count += 1

        except Exception as e:
            logger.error(f"Error importing wine {idx}: {e}")
            errors.append({'index': idx, 'error': str(e)})

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Errore database: {str(e)}'}), 500

    return jsonify({
        'message': f'{created_count} vini importati, {skipped_count} gi\u00e0 presenti',
        'created': created_count,
        'skipped': skipped_count,
        'errors': errors
    }), 201


@wines_bp.route('/batch', methods=['POST'])
@jwt_required()
def parse_wine_csv():
    """
    Parse CSV file with wine list and save to venue's wine list.
    Expected columns: nome, tipo, prezzo, regione (opt), vitigno (opt), anno (opt), produttore (opt)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403

    venue_id = user.venue_id

    if 'file' not in request.files:
        return jsonify({'message': 'Nessun file fornito'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'message': 'File CSV non valido'}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        required_columns = ['nome', 'tipo', 'prezzo']
        if not csv_reader.fieldnames:
            return jsonify({'message': 'File CSV vuoto'}), 400

        fieldnames_lower = {f.lower(): f for f in csv_reader.fieldnames}
        missing = [c for c in required_columns if c.lower() not in fieldnames_lower]
        if missing:
            return jsonify({'message': f'Colonne mancanti: {", ".join(missing)}'}), 400

        saved_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                nome = row.get(fieldnames_lower.get('nome', 'nome'), '').strip()
                tipo = row.get(fieldnames_lower.get('tipo', 'tipo'), '').strip().lower()
                prezzo_str = row.get(fieldnames_lower.get('prezzo', 'prezzo'), '').strip()

                if not nome or not tipo:
                    errors.append({'row': row_num, 'error': 'Nome o tipo mancante'})
                    continue

                valid_types = ['red', 'white', 'rose', 'sparkling', 'dessert', 'fortified']
                if tipo not in valid_types:
                    errors.append({'row': row_num, 'error': f'Tipo non valido: {tipo}'})
                    continue

                try:
                    prezzo = float(prezzo_str.replace('€', '').replace(',', '.').strip())
                except:
                    errors.append({'row': row_num, 'error': f'Prezzo non valido: {prezzo_str}'})
                    continue

                regione = row.get(fieldnames_lower.get('regione', 'regione'), '').strip() or None
                vitigno = row.get(fieldnames_lower.get('vitigno', 'vitigno'), '').strip() or None
                anno_str = row.get(fieldnames_lower.get('anno', 'anno'), '').strip() or None
                produttore = row.get(fieldnames_lower.get('produttore', 'produttore'), '').strip() or None
                descrizione = row.get(fieldnames_lower.get('description', 'description'), '').strip() or None

                anno = None
                if anno_str:
                    try:
                        anno = int(anno_str)
                        if anno < 1900 or anno > 2100:
                            anno = None
                    except:
                        pass

                # Find or create wine in catalog
                wine = Wine.query.filter(
                    Wine.name == nome,
                    Wine.type == tipo,
                    Wine.producer == produttore
                ).first()

                if not wine:
                    wine = Wine(
                        name=nome,
                        type=tipo,
                        producer=produttore,
                        region=regione,
                        grape_variety=vitigno,
                        description=descrizione
                    )
                    db.session.add(wine)
                    db.session.flush()

                # Check for existing venue_wine
                existing = VenueWine.query.filter_by(
                    venue_id=venue_id,
                    wine_id=wine.id,
                    vintage=anno
                ).first()

                if not existing:
                    venue_wine = VenueWine(
                        venue_id=venue_id,
                        wine_id=wine.id,
                        vintage=anno,
                        price=prezzo,
                        is_available=True
                    )
                    db.session.add(venue_wine)
                    saved_count += 1

            except Exception as e:
                errors.append({'row': row_num, 'error': str(e)})

        db.session.commit()

        return jsonify({
            'message': f'{saved_count} vini salvati',
            'saved': saved_count,
            'errors': errors
        }), 200 if saved_count > 0 else 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error parsing CSV: {e}")
        return jsonify({'message': f'Errore: {str(e)}'}), 500


# ===========================================
# AI OPERATIONS
# ===========================================

@wines_bp.route('/venue/<int:venue_id>/parse', methods=['POST'])
@jwt_required()
@limiter.limit(AI_OPERATION_LIMIT)
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
        return jsonify({'message': f'Errore: {str(e)}'}), 500


@wines_bp.route('/venue/<int:venue_id>/parse-images', methods=['POST'])
@jwt_required()
@limiter.limit(AI_OPERATION_LIMIT)
def parse_wine_images(venue_id):
    """Parse wine list from images using GPT-4 Vision."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403

    data = request.get_json()
    images = data.get('images', [])

    if not images or len(images) > 10:
        return jsonify({'message': 'Fornire da 1 a 10 immagini'}), 400

    try:
        parser = WineParserService()
        wines = parser.parse_wine_images(images)

        return jsonify({
            'message': f'{len(wines)} vini estratti',
            'wines': wines
        }), 200
    except Exception as e:
        logger.error(f"Error parsing wine images: {e}")
        return jsonify({'message': f'Errore: {str(e)}'}), 500


@wines_bp.route('/venue/<int:venue_id>/generate-descriptions', methods=['POST'])
@jwt_required()
@limiter.limit(AI_OPERATION_LIMIT)
def generate_wine_descriptions(venue_id):
    """Generate professional wine descriptions using AI."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403

    data = request.get_json()
    wines_data = data.get('wines', [])

    if not wines_data:
        return jsonify({'message': 'Nessun vino fornito'}), 400

    try:
        generator = WineDescriptionGenerator()
        wines_with_descriptions = generator.generate_descriptions_batch(wines_data)

        # Update wines in catalog if they have IDs
        for wine_data in wines_with_descriptions:
            if wine_data.get('description_status') == 'completed' and wine_data.get('wine_id'):
                wine = Wine.query.get(wine_data['wine_id'])
                if wine:
                    if 'description' in wine_data:
                        wine.description = wine_data.get('description')
                    if 'color' in wine_data:
                        wine.color = wine_data.get('color')
                    if 'aromas' in wine_data:
                        wine.aromas = wine_data.get('aromas')
                    if 'body' in wine_data:
                        wine.body = wine_data.get('body')
                    if 'acidity_level' in wine_data:
                        wine.acidity_level = wine_data.get('acidity_level')
                    if 'tannin_level' in wine_data:
                        wine.tannin_level = wine_data.get('tannin_level')

        db.session.commit()

        completed = sum(1 for w in wines_with_descriptions if w.get('description_status') == 'completed')
        errors = sum(1 for w in wines_with_descriptions if w.get('description_status') == 'error')

        return jsonify({
            'message': f'Descrizioni generate: {completed} completate, {errors} errori',
            'wines': wines_with_descriptions,
            'stats': {'total': len(wines_with_descriptions), 'completed': completed, 'errors': errors}
        }), 200

    except Exception as e:
        logger.error(f"Error generating descriptions: {e}")
        return jsonify({'message': f'Errore: {str(e)}'}), 500


# ===========================================
# COMPATIBILITY ENDPOINT (for gradual migration)
# ===========================================

@wines_bp.route('/<int:venue_wine_id>', methods=['GET'])
def get_wine_by_id(venue_wine_id):
    """
    Get a wine by venue_wine_id.
    Compatibility endpoint - works like old GET /products/<id>
    """
    venue_wine = VenueWine.query.get(venue_wine_id)

    if not venue_wine:
        return jsonify({'message': 'Vino non trovato'}), 404

    return jsonify(venue_wine.to_full_dict(detailed=True)), 200
