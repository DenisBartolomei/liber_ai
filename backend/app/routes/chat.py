"""
Chat Routes for LIBER (B2C Customer Chat)
"""
from datetime import datetime
import uuid
from flask import Blueprint, request, jsonify
from app import db
from app.models import Venue, Session, Message, WineProposal, Product
from app.services.ai_agent import AIAgentService
from app.services.conversation_manager import ConversationManager

chat_bp = Blueprint('chat', __name__)


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
                        is_selected=False
                    )
                    proposals_to_create.append(proposal)
                    rank_counter += 1
        
        else:
            # Handle single mode
            wines_to_return = response_data.get('wines', [])
            wine_ids = response_data.get('wine_ids', [])
            
            # Use wines list if available (has full data), otherwise use wine_ids
            if wines_to_return:
                for wine in wines_to_return:
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
                        mode='single',
                        journey_id=None,
                        is_selected=False
                    )
                    proposals_to_create.append(proposal)
                    rank_counter += 1
            elif wine_ids:
                # Fallback: use wine_ids if wines list not available
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


@chat_bp.route('/sessions', methods=['POST'])
def create_session():
    """
    Create a new chat session for a customer (B2C).
    
    Expected JSON:
    {
        "venue_slug": "ristorante-da-mario-abc123"
    }
    """
    data = request.get_json()
    venue_slug = data.get('venue_slug')
    
    if not venue_slug:
        return jsonify({'message': 'venue_slug è obbligatorio'}), 400
    
    venue = Venue.query.filter_by(slug=venue_slug, is_active=True).first()
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    # Create new session
    conversation_manager = ConversationManager()
    session = conversation_manager.create_session(
        venue_id=venue.id,
        mode='b2c',
        device_type=request.headers.get('X-Device-Type'),
        user_agent=request.headers.get('User-Agent'),
        ip_address=request.remote_addr
    )
    
    # Generate welcome message
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
        current_context.update(message_context)
        session.context = current_context
        
        # Extract and save budget_initial and num_bottiglie_target from context
        session.extract_budget_from_context()
        session.extract_bottiglie_from_context()
        
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
    
    # Process message through AI agent
    try:
        ai_agent = AIAgentService()
        response = ai_agent.process_b2c_message(
            session=session,
            venue=venue,
            user_message=message_content,
            context=session.context  # Pass context with dishes and guest_count
        )
        
        # Save assistant message
        assistant_message = conversation_manager.add_message(
            session=session,
            role='assistant',
            content=response['message'],
            metadata=response.get('metadata'),
            products=response.get('wine_ids')
        )
        
        # Track wine proposals for analytics (if AI recommended wines)
        if response.get('is_recommending') and (response.get('wine_ids') or response.get('journeys')):
            track_wine_proposals(session.id, assistant_message.id, response)
        
        # Update session activity
        session.update_activity()
        db.session.commit()
        
        return jsonify({
            'message': response['message'],
            'wines': response.get('wines', []),
            'suggestions': response.get('suggestions', [])
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

