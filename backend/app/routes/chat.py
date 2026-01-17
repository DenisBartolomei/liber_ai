"""
Chat Routes for LIBER (B2C Customer Chat)
"""
from datetime import datetime, timedelta
import uuid
import json
import time
import threading
import hashlib
import logging
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Venue, Session, Message, WineProposal, Product, AccessToken
from app.services.ai_agent import AIAgentService
from app.services.communication_model import CommunicationModelService
from app.services.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/start-token', methods=['GET'])
def create_start_token():
    """
    Create a new access token for a venue.
    This endpoint is called when a customer first accesses the venue page.
    The token is one-time use and expires after 10 minutes.
    
    Query params:
        venue_slug: The venue slug
    """
    venue_slug = request.args.get('venue_slug')
    
    if not venue_slug:
        return jsonify({'message': 'venue_slug è obbligatorio'}), 400
    
    venue = Venue.query.filter_by(slug=venue_slug, is_active=True).first()
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    # Check annual conversation limit (informational, doesn't block token creation)
    can_create, limit_message = venue.can_create_conversation()
    if not can_create:
        # Still allow token creation, but return warning
        logger.warning(f"Venue {venue.id} reached conversation limit, but allowing token creation")
    
    # Create access token (valid for 10 minutes, one-time use)
    access_token = AccessToken.create_for_venue(
        venue_id=venue.id,
        expires_in_minutes=10
    )
    
    logger.info(f"Created start token {access_token.token[:8]}... for venue {venue.id}")
    
    return jsonify({
        'access_token': access_token.token,
        'expires_at': access_token.expires_at.isoformat(),
        'venue': {
            'id': venue.id,
            'name': venue.name,
            'slug': venue.slug
        }
    }), 201


def track_wine_proposals(session_id, message_id, response_data):
    """
    Track wine proposals in WineProposal table for analytics.
    
    Args:
        session_id: Session ID
        message_id: Message ID that contains the proposals
        response_data: Response dict from AI agent with 'mode', 'wine_ids', 'journeys', 'wines'
    """
    try:
        mode = response_data.get('mode', 'single')
        proposal_group_id = str(uuid.uuid4())  # Unique ID for this batch of proposals
        
        proposals_to_create = []
        rank_counter = 1  # Global rank counter across all wines in this message
        
        if mode == 'journey':
            # Handle journey mode
            journeys = response_data.get('journeys', [])
            for journey_idx, journey in enumerate(journeys):
                journey_id = journey.get('id', journey_idx)
                wines = journey.get('wines', [])
                
                for wine in wines:
                    product_id = wine.get('id')
                    if not product_id:
                        continue
                    
                    product = Product.query.get(product_id)
                    if not product:
                        continue
                    
                    proposal = WineProposal(
                        session_id=session_id,
                        message_id=message_id,
                        product_id=product_id,
                        proposal_group_id=proposal_group_id,
                        proposal_rank=rank_counter,
                        price=product.price,
                        margin=product.margin,
                        mode='journey',
                        journey_id=journey_id,
                        proposal_reason=journey.get('reason', ''),  # Save journey reason
                        is_selected=False
                    )
                    proposals_to_create.append(proposal)
                    rank_counter += 1
        
        else:
            # Handle single mode
            # PRIORITY: Use all_rankings if available (contains ALL ranked wines)
            all_rankings = response_data.get('all_rankings', [])
            wines_to_return = response_data.get('wines', [])
            wine_ids = response_data.get('wine_ids', [])
            
            # Use all_rankings if available (has ALL wines with rank, reason, best)
            if all_rankings:
                for wine in all_rankings:
                    product_id = wine.get('id')
                    if not product_id:
                        continue
                    
                    product = Product.query.get(product_id)
                    if not product:
                        continue
                    
                    # Use explicit rank from JSON, fallback to position if not available
                    wine_rank = wine.get('rank')
                    if wine_rank is None:
                        wine_rank = rank_counter
                    
                    proposal = WineProposal(
                        session_id=session_id,
                        message_id=message_id,
                        product_id=product_id,
                        proposal_group_id=proposal_group_id,
                        proposal_rank=wine_rank,  # Use explicit rank from JSON
                        price=product.price,
                        margin=product.margin,
                        mode='single',
                        journey_id=None,
                        proposal_reason=wine.get('reason', ''),  # Save wine reason from JSON
                        is_selected=False
                    )
                    proposals_to_create.append(proposal)
                    rank_counter += 1
            # Fallback: use wines list if available (has full data)
            elif wines_to_return:
                for wine in wines_to_return:
                    product_id = wine.get('id')
                    if not product_id:
                        continue
                    
                    product = Product.query.get(product_id)
                    if not product:
                        continue
                    
                    # Use explicit rank from JSON if available, otherwise use counter
                    wine_rank = wine.get('rank')
                    if wine_rank is None:
                        wine_rank = rank_counter
                    
                    proposal = WineProposal(
                        session_id=session_id,
                        message_id=message_id,
                        product_id=product_id,
                        proposal_group_id=proposal_group_id,
                        proposal_rank=wine_rank,
                        price=product.price,
                        margin=product.margin,
                        mode='single',
                        journey_id=None,
                        proposal_reason=wine.get('reason', ''),  # Save wine reason from JSON
                        is_selected=False
                    )
                    proposals_to_create.append(proposal)
                    rank_counter += 1
            # Last fallback: use wine_ids if wines list not available
            elif wine_ids:
                for product_id in wine_ids:
                    product = Product.query.get(product_id)
                    if not product:
                        continue
                    
                    proposal = WineProposal(
                        session_id=session_id,
                        message_id=message_id,
                        product_id=product_id,
                        proposal_group_id=proposal_group_id,
                        proposal_rank=rank_counter,
                        price=product.price,
                        margin=product.margin,
                        mode='single',
                        journey_id=None,
                        is_selected=False
                    )
                    proposals_to_create.append(proposal)
                    rank_counter += 1
        
        # Bulk insert all proposals
        if proposals_to_create:
            db.session.add_all(proposals_to_create)
            db.session.flush()  # Flush to get IDs but don't commit yet (will be committed in caller)
            
    except Exception as e:
        import logging
        logging.error(f"Error tracking wine proposals: {e}", exc_info=True)
        # Don't raise - analytics tracking failure shouldn't break the request


def _compute_filters_hash(venue_id: int, context: dict) -> str:
    base = {
        'venue_id': venue_id,
        'dishes': context.get('dishes', []),
        'guest_count': context.get('guest_count'),
        'preferences': context.get('preferences', {})
    }
    payload = json.dumps(base, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


@chat_bp.route('/sessions', methods=['POST'])
def create_session():
    """
    Create a new chat session for a customer (B2C).
    Requires a valid access token (one-time use).
    
    Expected JSON:
    {
        "venue_slug": "ristorante-da-mario-abc123",
        "access_token": "uuid-v4-string"  # Token obtained from /start-token
    }
    """
    data = request.get_json()
    venue_slug = data.get('venue_slug')
    access_token_str = data.get('access_token')
    
    if not venue_slug:
        return jsonify({'message': 'venue_slug è obbligatorio'}), 400
    
    if not access_token_str:
        return jsonify({
            'message': 'access_token è obbligatorio',
            'detail': 'Devi ottenere un token di accesso prima di creare una sessione'
        }), 400
    
    venue = Venue.query.filter_by(slug=venue_slug, is_active=True).first()
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    # Check annual conversation limit
    can_create, limit_message = venue.can_create_conversation()
    if not can_create:
        return jsonify({
            'message': 'Limite conversazioni annuali raggiunto',
            'detail': limit_message
        }), 429
    
    # ============================================
    # VALIDATE ACCESS TOKEN
    # ============================================
    access_token = AccessToken.query.filter_by(token=access_token_str).first()
    
    if not access_token:
        return jsonify({
            'message': 'Token di accesso non valido',
            'detail': 'Il token fornito non esiste'
        }), 403
    
    # Verify token belongs to this venue
    if access_token.venue_id != venue.id:
        return jsonify({
            'message': 'Token di accesso non valido per questo locale',
            'detail': 'Il token non corrisponde al locale richiesto'
        }), 403
    
    # Check if token is valid (not used and not expired)
    if not access_token.is_valid():
        if access_token.is_used:
            return jsonify({
                'message': 'Token di accesso già utilizzato',
                'detail': 'Questo token è stato già usato per creare una sessione. Ogni token può essere usato una sola volta.'
            }), 403
        else:
            return jsonify({
                'message': 'Token di accesso scaduto',
                'detail': 'Il token è scaduto. Scansiona nuovamente il QR code per ottenere un nuovo token.'
            }), 403
    
    # ============================================
    # CREATE SESSION
    # ============================================
    conversation_manager = ConversationManager()
    session = conversation_manager.create_session(
        venue_id=venue.id,
        mode='b2c',
        device_type=request.headers.get('X-Device-Type'),
        user_agent=request.headers.get('User-Agent'),
        ip_address=request.remote_addr,
        context={'access_token_id': access_token.id}  # Track which token was used
    )
    
    # Mark token as used (one-time use)
    access_token.mark_as_used(session.id)
    
    logger.info(f"Created session {session.id} for venue {venue.id} using access token {access_token.token[:8]}...")
    
    welcome_message = venue.welcome_message or \
        'Benvenuto! Sono il tuo sommelier virtuale. Come posso aiutarti nella scelta del vino oggi?'
    
    return jsonify({
        'session_token': session.session_token,
        'venue': {
            'name': venue.name,
            'logo_url': venue.logo_url
        },
        'welcome_message': welcome_message
    }), 201


@chat_bp.route('/precompute-rankings', methods=['POST'])
def precompute_rankings():
    """
    Precompute wine rankings in background for a session.
    """
    data = request.get_json()
    session_token = data.get('session_token')

    if not session_token:
        return jsonify({'message': 'session_token è obbligatorio'}), 400

    session = Session.query.filter_by(session_token=session_token).first()
    if not session:
        return jsonify({'message': 'Sessione non trovata'}), 404

    if session.status != 'active':
        return jsonify({'message': 'Sessione terminata'}), 400

    venue = Venue.query.get(session.venue_id)
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404

    context = session.context or {}
    filters_hash = _compute_filters_hash(venue.id, context)

    existing = context.get('precomputed_rankings', {})
    if existing.get('filters_hash') == filters_hash and existing.get('status') in ['pending', 'ready']:
        return jsonify({
            'status': existing.get('status'),
            'filters_hash': filters_hash
        }), 200

    context['precomputed_rankings'] = {
        'status': 'pending',
        'started_at': datetime.utcnow().isoformat(),
        'filters_hash': filters_hash
    }
    session.context = context
    db.session.commit()

    def _background_job(app, session_id, venue_id, expected_hash):
        with app.app_context():
            start_time = time.time()
            try:
                worker_session = Session.query.get(session_id)
                worker_venue = Venue.query.get(venue_id)
                if not worker_session or not worker_venue:
                    return

                worker_context = worker_session.context or {}
                ai_agent = AIAgentService()
                result = ai_agent.compute_rankings_for_context(
                    session=worker_session,
                    venue=worker_venue,
                    active_context=worker_context,
                    user_message="Precompute ranking"
                )

                precomputed = worker_context.get('precomputed_rankings', {})
                precomputed.update({
                    'status': 'ready',
                    'completed_at': datetime.utcnow().isoformat(),
                    'filters_hash': expected_hash,
                    'filtered_wines_snapshot': result.get('all_wines', []),
                    'ranking_json': result.get('wine_selection', {}),
                    'gathered_info': result.get('gathered_info', {}),
                    'journey_pref': result.get('journey_pref', 'single'),
                    'precompute_latency_ms': int((time.time() - start_time) * 1000)
                })
                worker_context['precomputed_rankings'] = precomputed
                worker_session.context = worker_context
                db.session.commit()
            except Exception as e:
                try:
                    worker_session = Session.query.get(session_id)
                    if worker_session:
                        worker_context = worker_session.context or {}
                        precomputed = worker_context.get('precomputed_rankings', {})
                        precomputed.update({
                            'status': 'error',
                            'completed_at': datetime.utcnow().isoformat(),
                            'filters_hash': expected_hash,
                            'error': str(e),
                            'precompute_latency_ms': int((time.time() - start_time) * 1000)
                        })
                        worker_context['precomputed_rankings'] = precomputed
                        worker_session.context = worker_context
                        db.session.commit()
                except Exception:
                    pass
            finally:
                db.session.remove()

    app = current_app._get_current_object()
    thread = threading.Thread(
        target=_background_job,
        args=(app, session.id, venue.id, filters_hash),
        daemon=True
    )
    thread.start()

    return jsonify({
        'status': 'pending',
        'filters_hash': filters_hash
    }), 202


@chat_bp.route('/precompute-rankings/status', methods=['GET'])
def precompute_rankings_status():
    session_token = request.args.get('session_token')
    if not session_token:
        return jsonify({'message': 'session_token è obbligatorio'}), 400

    session = Session.query.filter_by(session_token=session_token).first()
    if not session:
        return jsonify({'message': 'Sessione non trovata'}), 404

    context = session.context or {}
    precomputed = context.get('precomputed_rankings', {})

    return jsonify({
        'status': precomputed.get('status', 'none'),
        'filters_hash': precomputed.get('filters_hash'),
        'error': precomputed.get('error')
    }), 200


@chat_bp.route('/proceed-recommendations', methods=['POST'])
def proceed_recommendations():
    """
    Proceed to recommendations using precomputed rankings if available.
    """
    start_time = time.time()
    data = request.get_json()
    session_token = data.get('session_token')

    if not session_token:
        return jsonify({'message': 'session_token è obbligatorio'}), 400

    session = Session.query.filter_by(session_token=session_token).first()
    if not session:
        return jsonify({'message': 'Sessione non trovata'}), 404

    if session.status != 'active':
        return jsonify({'message': 'Sessione terminata'}), 400

    venue = Venue.query.get(session.venue_id)
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404

    context = session.context or {}
    precomputed = context.get('precomputed_rankings', {})
    status = precomputed.get('status')

    if status == 'pending':
        return jsonify({
            'status': 'pending',
            'message': 'Sto preparando i suggerimenti, tra pochi secondi saranno pronti.'
        }), 202

    ai_agent = AIAgentService()
    communication_service = CommunicationModelService()

    if status != 'ready':
        result = ai_agent.compute_rankings_for_context(
            session=session,
            venue=venue,
            active_context=context,
            user_message="Procedi al suggerimento"
        )
        precomputed = {
            'ranking_json': result.get('wine_selection', {}),
            'filtered_wines_snapshot': result.get('all_wines', []),
            'gathered_info': result.get('gathered_info', {}),
            'journey_pref': result.get('journey_pref', 'single'),
            'status': 'ready'
        }

    wine_selection = precomputed.get('ranking_json', {})
    filtered_wines_snapshot = precomputed.get('filtered_wines_snapshot', [])
    gathered_info = precomputed.get('gathered_info', {})
    journey_pref = precomputed.get('journey_pref', gathered_info.get('journey_preference', 'single'))

    has_wines = wine_selection.get('wines') and len(wine_selection.get('wines', [])) > 0
    has_journeys = wine_selection.get('journeys') and len(wine_selection.get('journeys', [])) > 0

    if not has_wines and not has_journeys:
        return jsonify({'message': 'Non sono riuscito a preparare i suggerimenti. Riprova.'}), 503

    wine_selection_for_communication = wine_selection.copy()
    if journey_pref == 'single' and has_wines:
        wine_selection_for_communication['wines'] = wine_selection.get('wines', [])[:3]

    history = session.get_conversation_history(limit=20)
    try:
        ai_message = communication_service.generate_message(
            venue_name=venue.name,
            sommelier_style=venue.sommelier_style or 'professional',
            wine_selection=wine_selection_for_communication,
            context=context,
            gathered_info=gathered_info,
            history=history,
            user_message="Procedi al suggerimento"
        )
    except Exception as e:
        logger.warning(f"Communication model failed in proceed: {e}")
        ai_message = ai_agent._generate_fallback_message(wine_selection, journey_pref)

    if journey_pref == 'journey' and has_journeys:
        all_wine_ids = []
        for journey in wine_selection.get('journeys', []):
            all_wine_ids.extend([w.get('id') for w in journey.get('wines', []) if w.get('id')])

        response_payload = {
            'message': ai_message,
            'journeys': wine_selection.get('journeys', []),
            'wine_ids': list(set(all_wine_ids)),
            'wines': [],
            'suggestions': [],
            'mode': 'journey',
            'metadata': {
                'model': communication_service.model,
                'tokens_used': 0,
                'gathered_info': gathered_info,
                'is_recommending': True,
                'precomputed': True
            }
        }
    else:
        all_ranked_wines = wine_selection.get('wines', [])
        wines_for_display = all_ranked_wines[:3]
        wine_ids = [w.get('id') for w in all_ranked_wines if w.get('id')]

        response_payload = {
            'message': ai_message,
            'wines': wines_for_display,
            'all_rankings': all_ranked_wines,
            'wine_ids': wine_ids,
            'journeys': [],
            'suggestions': [],
            'mode': 'single',
            'metadata': {
                'model': communication_service.model,
                'tokens_used': 0,
                'gathered_info': gathered_info,
                'is_recommending': True,
                'precomputed': True
            }
        }

    conversation_manager = ConversationManager()
    assistant_message = conversation_manager.add_message(
        session=session,
        role='assistant',
        content=ai_message,
        metadata=response_payload.get('metadata'),
        products=response_payload.get('wine_ids')
    )

    if response_payload.get('metadata', {}).get('is_recommending'):
        track_wine_proposals(session.id, assistant_message.id, response_payload)

    context = session.context or {}
    context['wines_proposed'] = True
    if filtered_wines_snapshot:
        context['filtered_wines'] = filtered_wines_snapshot
    context['proceed_clicked_at'] = datetime.utcnow().isoformat()
    context['proceed_latency_ms'] = int((time.time() - start_time) * 1000)
    session.context = context
    session.update_activity()
    db.session.commit()

    response_payload['message_id'] = assistant_message.id
    return jsonify(response_payload), 200


@chat_bp.route('/confirm-wines', methods=['POST'])
def confirm_wines():
    """
    Track wines as selected/requested when customer confirms selection.
    
    Expected JSON:
    {
        "session_token": "abc123...",
        "wine_ids": [1, 5, 8]  # List of product IDs that were confirmed
    }
    """
    data = request.get_json()
    session_token = data.get('session_token')
    wine_ids = data.get('wine_ids', [])
    
    if not session_token:
        return jsonify({'message': 'session_token è obbligatorio'}), 400
    
    if not wine_ids or not isinstance(wine_ids, list):
        return jsonify({'message': 'wine_ids deve essere una lista di ID'}), 400
    
    # Find session
    session = Session.query.filter_by(session_token=session_token).first()
    
    if not session:
        return jsonify({'message': 'Sessione non trovata'}), 404
    
    if session.status != 'active':
        return jsonify({'message': 'Sessione terminata'}), 400
    
    # Track each wine as sold (confirmed by user) with timestamp
    selected_proposals = []
    for wine_id in wine_ids:
        # Track as sold with timestamp (legacy tracking)
        if hasattr(session, 'add_sale'):
            session.add_sale(wine_id)
        # Also track as selected and recommended for analytics (legacy)
        if hasattr(session, 'add_selection'):
            session.add_selection(wine_id)
        if hasattr(session, 'add_recommendation'):
            session.add_recommendation(wine_id)
        
        # NEW: Track in WineProposal table for analytics
        # Find the most recent proposal for this wine in this session
        proposal = WineProposal.query.filter_by(
            session_id=session.id,
            product_id=wine_id
        ).order_by(WineProposal.created_at.desc()).first()
        
        if proposal:
            # Mark existing proposal as selected
            proposal.mark_as_selected()
            selected_proposals.append(proposal.id)
        else:
            # Edge case: wine was not tracked as proposal, create new proposal with is_selected=True
            from app.models import Product
            product = Product.query.get(wine_id)
            if product:
                proposal = WineProposal(
                    session_id=session.id,
                    product_id=wine_id,
                    proposal_rank=1,  # Default rank
                    price=product.price,
                    margin=product.margin,
                    mode='single',  # Default mode
                    is_selected=True,
                    selected_at=datetime.utcnow()
                )
                db.session.add(proposal)
                selected_proposals.append(proposal.id)
    
    db.session.commit()
    
    return jsonify({
        'message': f'{len(wine_ids)} vini confermati e tracciati come venduti',
        'confirmed_count': len(wine_ids),
        'proposals_updated': len(selected_proposals),
        'sold_at': datetime.utcnow().isoformat()
    }), 200


@chat_bp.route('/messages', methods=['POST'])
def send_message():
    """
    Send a message in a chat session and get AI response.
    
    Expected JSON:
    {
        "session_token": "abc123...",
        "message": "Che vino mi consigli con il pesce?",
        "context": {  // Optional, for first message with setup data
            "dishes": [{"name": "Tagliata", "category": "secondo", ...}],
            "guest_count": 4,
            "budget": "media",  // "base" | "media" | "nessuna"
            "wine_count": 2     // 1 = single wine, 2+ = tasting journey
        }
    }
    """
    data = request.get_json()
    session_token = data.get('session_token')
    message_content = data.get('message')
    message_context = data.get('context')  # New: structured context from setup flow
    
    if not session_token or not message_content:
        return jsonify({'message': 'session_token e message sono obbligatori'}), 400
    
    # Find session
    session = Session.query.filter_by(session_token=session_token).first()
    
    if not session:
        return jsonify({'message': 'Sessione non trovata'}), 404
    
    if session.status != 'active':
        return jsonify({'message': 'Sessione terminata'}), 400
    
    # Update session context if provided
    if message_context:
        current_context = session.context or {}
        
        # Merge context intelligently - preserve existing data, update with new
        # Handle nested structures (preferences, dishes)
        if 'preferences' in message_context:
            if 'preferences' not in current_context:
                current_context['preferences'] = {}
            current_context['preferences'].update(message_context['preferences'])
        
        if 'dishes' in message_context:
            current_context['dishes'] = message_context['dishes']
        
        if 'guest_count' in message_context:
            current_context['guest_count'] = message_context['guest_count']
        
        # Update other context fields
        for key, value in message_context.items():
            if key not in ['preferences', 'dishes', 'guest_count']:
                current_context[key] = value
        
        session.context = current_context
        
        # Extract and save all preferences from context (budget, bottles, and normalize structure)
        session.save_preferences_from_context()
        
        db.session.commit()
    
    # Get venue for context
    venue = Venue.query.get(session.venue_id)
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    # Save user message first
    conversation_manager = ConversationManager()
    user_message = conversation_manager.add_message(
        session=session,
        role='user',
        content=message_content
    )
    
    # Refresh session to get updated message_count
    db.session.refresh(session)
    
    # Process message through AI agent
    try:
        ai_agent = AIAgentService()
        response = ai_agent.process_b2c_message(
            session=session,
            venue=venue,
            user_message=message_content,
            context=session.context  # Pass context with dishes and guest_count
        )
        
        # Log response structure for debugging
        import logging
        logging.info(f"AI Agent response received: type={type(response)}, keys={list(response.keys()) if isinstance(response, dict) else 'not a dict'}")
        logging.info(f"AI Agent response: has_message={bool(response.get('message'))}, message_type={type(response.get('message'))}, message_length={len(str(response.get('message', '')))}, is_opening={response.get('metadata', {}).get('is_opening', False)}, wines_count={len(response.get('wines', []))}, journeys_count={len(response.get('journeys', []))}")
        
        # Ensure message is always a string - handle None, empty, or non-string values
        raw_message = response.get('message')
        if raw_message is None:
            logging.warning("Response message is None")
            message_content = ''
        elif not isinstance(raw_message, str):
            logging.warning(f"Response message is not a string: type={type(raw_message)}, value={repr(raw_message)}")
            message_content = str(raw_message) if raw_message else ''
        else:
            message_content = raw_message
        
        logging.info(f"Extracted message_content: type={type(message_content)}, length={len(message_content)}, is_empty={not message_content or not message_content.strip()}, preview={message_content[:100] if message_content else 'empty'}")
        if not message_content:
            # Generate fallback message if empty
            is_opening = response.get('metadata', {}).get('is_opening', False)
            
            if is_opening:
                # Opening message fallback - should not mention recommendations
                message_content = "Benvenuti! Sono qui per aiutarvi a scegliere il vino perfetto per la vostra serata. Avete esigenze particolari o preferenze da comunicarmi?"
            elif response.get('wines'):
                wines = response.get('wines', [])
                best_wine = next((w for w in wines if w.get('best')), wines[0] if wines else None)
                if best_wine:
                    message_content = f"Ecco il mio consiglio: {best_wine.get('name', 'Vino')} - €{best_wine.get('price', 'N/D')}"
                else:
                    message_content = "Ecco le mie raccomandazioni per voi."
            elif response.get('journeys'):
                message_content = "Ecco i percorsi di degustazione che ho preparato per voi."
            else:
                message_content = "Ecco le mie raccomandazioni per voi."
        
        # Save assistant message
        assistant_message = conversation_manager.add_message(
            session=session,
            role='assistant',
            content=message_content,
            metadata=response.get('metadata'),
            products=response.get('wine_ids')
        )
        
        # Track wine proposals for analytics (if AI recommended wines)
        # Check is_recommending from metadata or directly, and ensure we have wines/journeys
        is_recommending = response.get('metadata', {}).get('is_recommending', False) or response.get('is_recommending', False)
        has_wines = response.get('wines') and len(response.get('wines', [])) > 0
        has_journeys = response.get('journeys') and len(response.get('journeys', [])) > 0
        has_wine_ids = response.get('wine_ids') and len(response.get('wine_ids', [])) > 0
        
        if is_recommending and (has_wines or has_journeys or has_wine_ids):
            track_wine_proposals(session.id, assistant_message.id, response)
            
            # Save wines_proposed flag and filtered_wines in context for clarification mode
            filtered_wines = response.get('metadata', {}).get('filtered_wines', [])
            if filtered_wines:
                current_context = session.context or {}
                current_context['wines_proposed'] = True
                current_context['filtered_wines'] = filtered_wines
                session.context = current_context
                logging.info(f"Saved wines_proposed=True and {len(filtered_wines)} filtered wines in session context")
        
        # Update session activity
        session.update_activity()
        db.session.commit()
        
        return jsonify({
            'message': message_content,
            'message_id': assistant_message.id,  # Include message ID for fetching rankings
            'wines': response.get('wines', []),
            'all_rankings': response.get('all_rankings', []),  # Include all rankings
            'journeys': response.get('journeys', []),
            'suggestions': response.get('suggestions', []),
            'mode': response.get('mode', 'single'),
            'metadata': response.get('metadata', {})
        }), 200
        
    except ValueError as e:
        # Configuration or expected errors from AI agent
        db.session.rollback()
        return jsonify({
            'message': str(e)
        }), 503
        
    except Exception as e:
        # Unexpected errors
        db.session.rollback()
        import logging
        import traceback
        logging.error(f"Unexpected error in send_message: {e}")
        traceback.print_exc()
        return jsonify({
            'message': 'Si è verificato un errore imprevisto. Riprova tra qualche secondo.'
        }), 500


@chat_bp.route('/messages/<int:message_id>/rankings', methods=['GET'])
def get_message_rankings(message_id):
    """
    Get all ranked wines for a specific message.
    
    Returns all WineProposals for the message, ordered by rank,
    with full product details.
    """
    try:
        # Find message
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'message': 'Messaggio non trovato'}), 404
        
        # Get all wine proposals for this message, ordered by rank
        proposals = WineProposal.query.filter_by(
            message_id=message_id
        ).order_by(WineProposal.proposal_rank.asc()).all()
        
        if not proposals:
            return jsonify({
                'message_id': message_id,
                'wines': []
            }), 200
        
        # Enrich proposals with full product data
        wines = []
        for proposal in proposals:
            product = proposal.product
            if not product:
                continue
            
            # Get product details (using safe access for optional fields)
            wine_data = {
                'id': product.id,
                'name': product.name,
                'price': float(product.price) if product.price else None,
                'type': product.type,
                'rank': proposal.proposal_rank,
                'reason': proposal.proposal_reason or '',
                'best': proposal.proposal_rank == 1,  # Rank 1 is best
                'is_selected': proposal.is_selected,
                'image_url': product.image_url
            }
            
            # Add optional fields if they exist
            try:
                # Use getattr to safely access optional fields
                if hasattr(product, 'region') and product.region:
                    wine_data['region'] = product.region
                if hasattr(product, 'grape_variety') and product.grape_variety:
                    wine_data['grape_variety'] = product.grape_variety
                if hasattr(product, 'vintage') and product.vintage:
                    wine_data['vintage'] = product.vintage
                if hasattr(product, 'description') and product.description:
                    wine_data['description'] = product.description
                if hasattr(product, 'tasting_notes') and product.tasting_notes:
                    wine_data['tasting_notes'] = product.tasting_notes
            except Exception as e:
                # If optional fields don't exist, continue without them
                import logging
                logging.debug(f"Could not access optional fields for product {product.id}: {e}")
            
            wines.append(wine_data)
        
        return jsonify({
            'message_id': message_id,
            'wines': wines
        }), 200
        
    except Exception as e:
        import logging
        logging.error(f"Error fetching message rankings: {e}", exc_info=True)
        return jsonify({
            'message': 'Errore nel recupero dei rankings',
            'error': str(e)
        }), 500


@chat_bp.route('/sessions/<session_token>/history', methods=['GET'])
def get_session_history(session_token):
    """Get message history for a session."""
    session = Session.query.filter_by(session_token=session_token).first()
    
    if not session:
        return jsonify({'message': 'Sessione non trovata'}), 404
    
    messages = Message.query.filter_by(session_id=session.id)\
        .order_by(Message.created_at)\
        .all()
    
    return jsonify({
        'session': session.to_dict(),
        'messages': [m.to_dict() for m in messages]
    }), 200


@chat_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit feedback (rating and text) for a session.
    
    Expected JSON:
    {
        "session_token": "abc123...",
        "rating": 5,  # 1-5
        "feedback": "Ottima esperienza!"  # Optional
    }
    """
    data = request.get_json()
    session_token = data.get('session_token')
    rating = data.get('rating')
    feedback_text = data.get('feedback', '')
    
    if not session_token:
        return jsonify({'message': 'session_token è obbligatorio'}), 400
    
    if rating is None or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'message': 'rating deve essere un numero tra 1 e 5'}), 400
    
    # Find session
    session = Session.query.filter_by(session_token=session_token).first()
    
    if not session:
        return jsonify({'message': 'Sessione non trovata'}), 404
    
    # Update session with feedback
    session.rating = rating
    if feedback_text:
        session.feedback = feedback_text
    
    # Optionally end the session
    if session.status == 'active':
        session.end_session('completed')
    
    db.session.commit()
    
    return jsonify({
        'message': 'Feedback salvato. Grazie!',
        'rating': rating
    }), 200


@chat_bp.route('/sessions/<session_token>/end', methods=['POST'])
def end_session(session_token):
    """End a chat session."""
    session = Session.query.filter_by(session_token=session_token).first()
    
    if not session:
        return jsonify({'message': 'Sessione non trovata'}), 404
    
    session.end_session(status='completed')
    db.session.commit()
    
    return jsonify({'message': 'Sessione terminata'}), 200




@chat_bp.route('/sessions/<session_token>/context', methods=['PUT'])
def update_context(session_token):
    """
    Update session context (e.g., selected dishes).
    
    Expected JSON:
    {
        "selected_dishes": ["Tagliata di manzo", "Risotto ai funghi"],
        "preferences": {
            "budget": "medium",
            "wine_types": ["red"]
        }
    }
    """
    session = Session.query.filter_by(session_token=session_token).first()
    
    if not session:
        return jsonify({'message': 'Sessione non trovata'}), 404
    
    data = request.get_json()
    
    # Merge with existing context
    current_context = session.context or {}
    current_context.update(data)
    session.context = current_context
    
    db.session.commit()
    
    return jsonify({
        'message': 'Contesto aggiornato',
        'context': session.context
    }), 200

