"""
Product Routes for LIBER Sommelier AI
"""
import logging
import csv
import io
import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Product, User, Venue
from app.services.vector_search import VectorSearchService
from app.services.wine_parser import WineParserService
from app.services.wine_description_generator import WineDescriptionGenerator

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
    # Use raw SQL to select only fields that exist in DB
    # First, try to get products with a safe query
    try:
        # Use with_entities to select only core fields that should exist
        products = query.with_entities(
            Product.id,
            Product.venue_id,
            Product.name,
            Product.type,
            Product.price,
            Product.is_available
        ).order_by(Product.type, Product.name).all()
        
        # Convert to dict
        result = []
        for p in products:
            product_dict = {
                'id': p.id,
                'venue_id': p.venue_id,
                'name': p.name,
                'type': p.type,
                'price': float(p.price) if p.price else None,
                'is_available': p.is_available if hasattr(p, 'is_available') else True
            }
            
            # Try to get optional fields using raw SQL
            try:
                from sqlalchemy import text
                optional_query = text("""
                    SELECT region, grape_variety, vintage, description 
                    FROM products 
                    WHERE id = :product_id
                """)
                optional_result = db.session.execute(optional_query, {'product_id': p.id}).fetchone()
                if optional_result:
                    if optional_result[0]:  # region
                        product_dict['region'] = optional_result[0]
                    if optional_result[1]:  # grape_variety
                        product_dict['grape_variety'] = optional_result[1]
                    if optional_result[2]:  # vintage
                        product_dict['vintage'] = optional_result[2]
                    if optional_result[3]:  # description
                        product_dict['description'] = optional_result[3]
            except Exception as e:
                logger.debug(f"Could not fetch optional fields for product {p.id}: {e}")
            
            result.append(product_dict)
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        # Fallback: try with raw SQL
        try:
            from sqlalchemy import text
            sql_query = text("""
                SELECT id, venue_id, name, type, price, is_available,
                       region, grape_variety, vintage, description
                FROM products 
                WHERE venue_id = :venue_id
                ORDER BY type, name
            """)
            results = db.session.execute(sql_query, {'venue_id': venue.id}).fetchall()
            
            products_list = []
            for row in results:
                product_dict = {
                    'id': row[0],
                    'venue_id': row[1],
                    'name': row[2],
                    'type': row[3],
                    'price': float(row[4]) if row[4] else None,
                    'is_available': row[5] if len(row) > 5 else True
                }
                # Add optional fields if they exist
                if len(row) > 6 and row[6]:  # region
                    product_dict['region'] = row[6]
                if len(row) > 7 and row[7]:  # grape_variety
                    product_dict['grape_variety'] = row[7]
                if len(row) > 8 and row[8]:  # vintage
                    product_dict['vintage'] = row[8]
                if len(row) > 9 and row[9]:  # description
                    product_dict['description'] = row[9]
                products_list.append(product_dict)
            
            return jsonify(products_list), 200
        except Exception as sql_error:
            logger.error(f"Raw SQL query also failed: {sql_error}")
            return jsonify({'message': 'Errore nel caricamento dei prodotti', 'error': str(sql_error)}), 500


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
    
    # Only set fields that exist in the database
    product = Product(
        venue_id=user.venue_id,
        name=data['name'],
        type=data['type'],
        price=data['price'],
        is_available=data.get('is_available', True)
    )
    
    # Set optional fields only if they exist in the model
    if 'region' in data:
        try:
            product.region = data.get('region')
        except:
            pass
    if 'grape_variety' in data:
        try:
            product.grape_variety = data.get('grape_variety')
        except:
            pass
    if 'vintage' in data:
        try:
            product.vintage = data.get('vintage')
        except:
            pass
    if 'description' in data:
        try:
            product.description = data.get('description')
        except:
            pass
    if 'cost_price' in data:
        try:
            product.cost_price = data.get('cost_price')
        except:
            pass
    if 'image_url' in data:
        try:
            product.image_url = data.get('image_url')
        except:
            pass
    # Wine Identity Card fields
    if 'color' in data:
        try:
            product.color = data.get('color')
        except:
            pass
    if 'aromas' in data:
        try:
            product.aromas = data.get('aromas')
        except:
            pass
    if 'body' in data:
        try:
            body_val = data.get('body')
            if body_val is not None:
                product.body = int(body_val) if 1 <= int(body_val) <= 10 else None
        except:
            pass
    if 'acidity_level' in data:
        try:
            acidity_val = data.get('acidity_level')
            if acidity_val is not None:
                product.acidity_level = int(acidity_val) if 1 <= int(acidity_val) <= 10 else None
        except:
            pass
    if 'tannin_level' in data:
        try:
            tannin_val = data.get('tannin_level')
            if tannin_val is not None:
                product.tannin_level = int(tannin_val) if 1 <= int(tannin_val) <= 10 else None
        except:
            pass
    
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
    
    # Update fields (only fields that exist in DB)
    # Core fields that should always exist
    if 'name' in data:
        product.name = data['name']
    if 'type' in data:
        product.type = data['type']
    if 'price' in data:
        product.price = data['price']
    if 'is_available' in data:
        product.is_available = data['is_available']
    
    # Optional fields - only set if they exist in the model
    if 'region' in data and hasattr(Product, 'region'):
        product.region = data['region']
    if 'grape_variety' in data and hasattr(Product, 'grape_variety'):
        product.grape_variety = data['grape_variety']
    if 'vintage' in data and hasattr(Product, 'vintage'):
        product.vintage = data['vintage']
    if 'description' in data and hasattr(Product, 'description'):
        product.description = data['description']
    if 'cost_price' in data and hasattr(Product, 'cost_price'):
        product.cost_price = data['cost_price']
    if 'image_url' in data and hasattr(Product, 'image_url'):
        product.image_url = data['image_url']
    
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
    
    # Delete associated wine proposals first (to avoid foreign key constraint issues)
    from app.models import WineProposal
    WineProposal.query.filter_by(product_id=product_id).delete()
    
    # Remove from vector database
    try:
        vector_service = VectorSearchService()
        vector_service.delete_product(product)
    except Exception as e:
        logger.warning(f"Error deleting product from vector DB: {e}")
    
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
                price=p_data.get('price', 0),
                is_available=p_data.get('is_available', True)
            )
            
            # Set optional fields only if they exist
            if 'region' in p_data and hasattr(Product, 'region'):
                product.region = p_data.get('region')
            if 'grape_variety' in p_data and hasattr(Product, 'grape_variety'):
                product.grape_variety = p_data.get('grape_variety')
            if 'vintage' in p_data and hasattr(Product, 'vintage'):
                product.vintage = p_data.get('vintage')
            if 'description' in p_data and hasattr(Product, 'description'):
                product.description = p_data.get('description')
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


@products_bp.route('/venue/<int:venue_id>/parse-csv', methods=['POST'])
@jwt_required()
def parse_wine_csv(venue_id):
    """
    Parse CSV file with wine list and return structured data.
    Expected CSV columns: nome, tipo, prezzo, regione (opt), vitigno (opt), anno (opt), produttore (opt)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'message': 'Nessun file fornito'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'Nessun file selezionato'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'message': 'Il file deve essere un CSV'}), 400
    
    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        # Required columns
        required_columns = ['nome', 'tipo', 'prezzo']
        optional_columns = ['regione', 'vitigno', 'anno', 'produttore']
        
        # Validate header
        if not csv_reader.fieldnames:
            return jsonify({'message': 'File CSV vuoto o non valido'}), 400
        
        # Check for required columns (case insensitive)
        fieldnames_lower = {f.lower(): f for f in csv_reader.fieldnames}
        missing_columns = []
        for req_col in required_columns:
            if req_col.lower() not in fieldnames_lower:
                missing_columns.append(req_col)
        
        if missing_columns:
            return jsonify({
                'message': f'Colonne obbligatorie mancanti: {", ".join(missing_columns)}',
                'required': required_columns,
                'found': list(csv_reader.fieldnames)
            }), 400
        
        # Parse wines
        wines = []
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Get values (case insensitive)
                nome = row.get(fieldnames_lower.get('nome', 'nome'), '').strip()
                tipo = row.get(fieldnames_lower.get('tipo', 'tipo'), '').strip().lower()
                prezzo_str = row.get(fieldnames_lower.get('prezzo', 'prezzo'), '').strip()
                
                # Validate required fields
                if not nome:
                    errors.append({'row': row_num, 'error': 'Nome vino mancante'})
                    continue
                
                if not tipo:
                    errors.append({'row': row_num, 'error': 'Tipo vino mancante'})
                    continue
                
                # Validate wine type
                valid_types = ['red', 'white', 'rose', 'sparkling', 'dessert', 'fortified']
                if tipo not in valid_types:
                    errors.append({
                        'row': row_num, 
                        'error': f'Tipo vino non valido: {tipo}. Valori accettati: {", ".join(valid_types)}'
                    })
                    continue
                
                # Parse price
                try:
                    # Remove currency symbols and spaces
                    prezzo_clean = prezzo_str.replace('€', '').replace('$', '').replace(',', '.').strip()
                    prezzo = float(prezzo_clean)
                    if prezzo <= 0:
                        raise ValueError('Prezzo deve essere positivo')
                except (ValueError, AttributeError):
                    errors.append({'row': row_num, 'error': f'Prezzo non valido: {prezzo_str}'})
                    continue
                
                # Get optional fields
                regione = row.get(fieldnames_lower.get('regione', 'regione'), '').strip() or None
                vitigno = row.get(fieldnames_lower.get('vitigno', 'vitigno'), '').strip() or None
                anno_str = row.get(fieldnames_lower.get('anno', 'anno'), '').strip() or None
                produttore = row.get(fieldnames_lower.get('produttore', 'produttore'), '').strip() or None
                
                # Parse vintage
                anno = None
                if anno_str:
                    try:
                        anno = int(anno_str)
                        # Basic validation for reasonable years
                        if anno < 1900 or anno > 2100:
                            anno = None  # Invalid year, ignore
                    except (ValueError, TypeError):
                        pass  # Invalid year format, ignore
                
                wine = {
                    'name': nome,
                    'type': tipo,
                    'price': prezzo,
                    'region': regione,
                    'grape_variety': vitigno,
                    'vintage': anno,
                    'producer': produttore
                }
                
                wines.append(wine)
                
            except Exception as e:
                errors.append({'row': row_num, 'error': f'Errore parsing riga: {str(e)}'})
                logger.error(f"Error parsing CSV row {row_num}: {e}")
        
        if not wines and not errors:
            return jsonify({'message': 'Nessun vino trovato nel file CSV'}), 400
        
        return jsonify({
            'message': f'{len(wines)} vini estratti dal CSV',
            'wines': wines,
            'errors': errors,
            'total_rows': len(wines) + len(errors)
        }), 200
        
    except Exception as e:
        logger.error(f"Error parsing CSV file: {e}")
        return jsonify({
            'message': f'Errore durante il parsing del CSV: {str(e)}'
        }), 500


@products_bp.route('/venue/<int:venue_id>/generate-descriptions', methods=['POST'])
@jwt_required()
def generate_wine_descriptions(venue_id):
    """
    Generate professional wine descriptions using fine-tuned GPT model.
    Accepts list of wines with basic info, returns wines with generated descriptions.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.venue_id != venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    data = request.get_json()
    wines = data.get('wines', [])
    
    if not wines:
        return jsonify({'message': 'Nessun vino fornito'}), 400
    
    if not isinstance(wines, list):
        return jsonify({'message': 'wines deve essere un array'}), 400
    
    # Validate wines structure
    for wine in wines:
        if not wine.get('name') or not wine.get('type'):
            return jsonify({
                'message': 'Ogni vino deve avere almeno nome e tipo'
            }), 400
    
    try:
        generator = WineDescriptionGenerator()
        wines_with_descriptions = generator.generate_descriptions_batch(wines)
        
        # Save structured data to database if wines have IDs (already saved)
        # Otherwise, return data for frontend to save later
        wines_to_save = []
        for wine_data in wines_with_descriptions:
            if wine_data.get('description_status') == 'completed' and wine_data.get('id'):
                # Wine already exists, update it
                try:
                    product = Product.query.get(wine_data['id'])
                    if product and product.venue_id == venue_id:
                        if 'description' in wine_data:
                            product.description = wine_data.get('description')
                        if 'color' in wine_data:
                            product.color = wine_data.get('color')
                        if 'aromas' in wine_data:
                            product.aromas = wine_data.get('aromas')
                        if 'body' in wine_data and wine_data.get('body') is not None:
                            product.body = wine_data.get('body')
                        if 'acidity_level' in wine_data and wine_data.get('acidity_level') is not None:
                            product.acidity_level = wine_data.get('acidity_level')
                        if 'tannin_level' in wine_data and wine_data.get('tannin_level') is not None:
                            product.tannin_level = wine_data.get('tannin_level')
                        wines_to_save.append(product)
                except Exception as e:
                    logger.error(f"Error updating product {wine_data.get('id')}: {e}")
        
        if wines_to_save:
            db.session.commit()
        
        # Count success/errors
        completed = sum(1 for w in wines_with_descriptions if w.get('description_status') == 'completed')
        errors = sum(1 for w in wines_with_descriptions if w.get('description_status') == 'error')
        
        return jsonify({
            'message': f'Descrizioni generate: {completed} completate, {errors} errori',
            'wines': wines_with_descriptions,
            'stats': {
                'total': len(wines_with_descriptions),
                'completed': completed,
                'errors': errors
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating wine descriptions: {e}")
        return jsonify({
            'message': f'Errore durante la generazione delle descrizioni: {str(e)}'
        }), 500


@products_bp.route('/<int:product_id>/label-image', methods=['POST'])
@jwt_required()
def upload_label_image(product_id):
    """
    Upload label image for a wine product.
    Stores image and updates product.image_url
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'message': 'Prodotto non trovato'}), 404
    
    if product.venue_id != user.venue_id:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'message': 'Nessun file fornito'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'Nessun file selezionato'}), 400
    
    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if file_ext not in allowed_extensions:
        return jsonify({
            'message': f'Formato file non supportato. Formati consentiti: {", ".join(allowed_extensions)}'
        }), 400
    
    # Validate file size (max 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    max_size = 5 * 1024 * 1024  # 5MB
    if file_size > max_size:
        return jsonify({'message': 'File troppo grande. Dimensione massima: 5MB'}), 400
    
    try:
        # Initialize Supabase Storage service
        from app.services.supabase_storage import SupabaseStorageService
        storage_service = SupabaseStorageService()
        wine_labels_bucket = current_app.config.get('SUPABASE_STORAGE_BUCKET_WINE_LABELS', 'wine-labels')
        
        # Generate unique filename
        safe_product_name = secure_filename(product.name)[:50]  # Limit length
        unique_filename = f"{product_id}_{safe_product_name}_{os.urandom(8).hex()}.{file_ext}"
        
        # Read file data
        file.seek(0)
        file_data = file.read()
        
        # Determine content type
        content_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        content_type = content_type_map.get(file_ext, 'image/jpeg')
        
        # Upload to Supabase Storage (public bucket)
        public_url = storage_service.upload_file(
            bucket=wine_labels_bucket,
            file_path=unique_filename,
            file_data=file_data,
            content_type=content_type,
            upsert=True
        )
        
        if not public_url:
            # Fallback: try to get public URL using get_public_url
            public_url = storage_service.get_public_url(wine_labels_bucket, unique_filename)
        
        if not public_url:
            logger.error(f"Failed to upload label image to Supabase Storage for product {product_id}")
            return jsonify({
                'message': 'Errore durante il caricamento su Supabase Storage'
            }), 500
        
        # Update product with public URL
        product.image_url = public_url
        db.session.commit()
        
        logger.info(f"Label image uploaded to Supabase Storage for product {product_id}: {public_url}")
        
        return jsonify({
            'message': 'Immagine caricata con successo',
            'image_url': public_url,
            'product': product.to_dict(detailed=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading label image: {e}")
        return jsonify({
            'message': f'Errore durante il caricamento dell\'immagine: {str(e)}'
        }), 500

