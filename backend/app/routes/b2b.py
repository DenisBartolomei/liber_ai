"""
B2B Routes for LIBER (Restaurant Owner Dashboard)
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app import db
from app.models import User, Venue, Session, Message, Product
from app.services.ai_agent import AIAgentService
from app.services.conversation_manager import ConversationManager

b2b_bp = Blueprint('b2b', __name__)


@b2b_bp.route('/chat', methods=['POST'])
@jwt_required()
def send_b2b_message():
    """
    Send a message to the AI assistant for B2B (product selection help).
    
    Expected JSON:
    {
        "message": "Quali vini rossi consigli per un menu a base di carne?"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    data = request.get_json()
    message_content = data.get('message')
    
    if not message_content:
        return jsonify({'message': 'message è obbligatorio'}), 400
    
    venue = Venue.query.get(user.venue_id)
    
    if not venue:
        return jsonify({'message': 'Locale non trovato'}), 404
    
    # Get or create B2B session for this user
    conversation_manager = ConversationManager()
    session = conversation_manager.get_or_create_b2b_session(user)
    
    # Save user message
    user_message = conversation_manager.add_message(
        session=session,
        role='user',
        content=message_content
    )
    
    try:
        # Get AI response
        ai_agent = AIAgentService()
        response = ai_agent.process_b2b_message(
            session=session,
            venue=venue,
            user_message=message_content
        )
        
        # Save assistant message
        assistant_message = conversation_manager.add_message(
            session=session,
            role='assistant',
            content=response['message'],
            metadata=response.get('metadata'),
            products=response.get('wine_ids')
        )
        
        session.update_activity()
        db.session.commit()
        
        return jsonify({
            'message': response['message'],
            'wines': response.get('wines', []),
            'suggestions': response.get('suggestions', [])
        }), 200
        
    except ValueError as e:
        # Configuration errors (e.g., missing API key)
        db.session.rollback()
        return jsonify({
            'message': str(e),
            'error': 'configuration_error'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'message': 'Si è verificato un errore. Riprova.',
            'error': str(e)
        }), 500


@b2b_bp.route('/chat/history', methods=['GET'])
@jwt_required()
def get_b2b_history():
    """Get B2B chat history for the current user."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    # Get the user's B2B session
    session = Session.query.filter_by(
        user_id=user.id,
        mode='b2b',
        status='active'
    ).first()
    
    if not session:
        return jsonify({
            'messages': []
        }), 200
    
    messages = Message.query.filter_by(session_id=session.id)\
        .order_by(Message.created_at)\
        .all()
    
    return jsonify({
        'messages': [m.to_dict() for m in messages]
    }), 200


@b2b_bp.route('/chat/clear', methods=['POST'])
@jwt_required()
def clear_b2b_history():
    """Clear B2B chat history and start fresh."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    # End any existing B2B sessions
    Session.query.filter_by(
        user_id=user.id,
        mode='b2b',
        status='active'
    ).update({'status': 'completed', 'ended_at': datetime.utcnow()})
    
    db.session.commit()
    
    return jsonify({'message': 'Chat cancellata'}), 200


@b2b_bp.route('/analytics/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics for the venue."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    venue_id = user.venue_id
    
    # Get date range (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Total conversations (B2C only)
    total_conversations = Session.query.filter(
        Session.venue_id == venue_id,
        Session.mode == 'b2c',
        Session.created_at >= start_date
    ).count()
    
    # Total products
    total_products = Product.query.filter_by(venue_id=venue_id).count()
    
    # Average messages per conversation
    avg_messages = db.session.query(func.avg(Session.message_count))\
        .filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date
        ).scalar() or 0
    
    # Top requested wines (from session.products_recommended)
    # This is a simplified version - in production, you'd aggregate properly
    top_wines_query = Product.query.filter_by(
        venue_id=venue_id,
        is_available=True
    ).order_by(Product.id).limit(5).all()
    
    top_wines = [
        {'name': w.name, 'count': 10 + (5 - idx) * 3}  # Mock counts
        for idx, w in enumerate(top_wines_query)
    ]
    
    return jsonify({
        'totalConversations': total_conversations,
        'totalProducts': total_products,
        'avgConversationLength': round(avg_messages, 1),
        'topWines': top_wines,
        'recentActivity': [
            {'type': 'conversation', 'message': 'Nuova conversazione completata', 'time': '5 min fa'},
            {'type': 'product', 'message': 'Carta vini aggiornata', 'time': '2 ore fa'},
            {'type': 'suggestion', 'message': 'Nuovi suggerimenti disponibili', 'time': '1 giorno fa'}
        ]
    }), 200


@b2b_bp.route('/analytics/conversations', methods=['GET'])
@jwt_required()
def get_conversation_stats():
    """Get detailed conversation analytics."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    venue_id = user.venue_id
    period = request.args.get('period', 'week')
    
    # Calculate date range
    end_date = datetime.utcnow()
    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    else:  # quarter
        start_date = end_date - timedelta(days=90)
    
    # Get sessions in period
    sessions = Session.query.filter(
        Session.venue_id == venue_id,
        Session.mode == 'b2c',
        Session.created_at >= start_date
    ).all()
    
    total_conversations = len(sessions)
    total_messages = sum(s.message_count or 0 for s in sessions)
    avg_messages = total_messages / total_conversations if total_conversations > 0 else 0
    
    # Satisfaction rate (from ratings)
    rated_sessions = [s for s in sessions if s.rating]
    satisfaction_rate = (
        sum(1 for s in rated_sessions if s.rating >= 4) / len(rated_sessions) * 100
        if rated_sessions else 85  # Default
    )
    
    # Conversations by day of week
    day_counts = {}
    for s in sessions:
        day = s.created_at.strftime('%a')
        day_counts[day] = day_counts.get(day, 0) + 1
    
    days_order = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    day_map = {'Mon': 'Lun', 'Tue': 'Mar', 'Wed': 'Mer', 'Thu': 'Gio', 
               'Fri': 'Ven', 'Sat': 'Sab', 'Sun': 'Dom'}
    
    conversations_by_day = [
        {'day': d, 'count': day_counts.get(day_map.get(d[:3], d), 0)}
        for d in days_order
    ]
    
    return jsonify({
        'totalConversations': total_conversations,
        'avgMessagesPerConversation': round(avg_messages, 1),
        'satisfactionRate': round(satisfaction_rate),
        'peakHours': ['19:00', '20:00', '21:00'],
        'conversationsByDay': conversations_by_day,
        'topQueries': [
            {'query': 'Vino rosso corposo', 'count': 34},
            {'query': 'Abbinamento pesce', 'count': 28},
            {'query': 'Bollicine aperitivo', 'count': 22},
            {'query': 'Vino biologico', 'count': 18},
            {'query': 'Dolce per dessert', 'count': 15}
        ],
        'topWines': [
            {'name': 'Brunello di Montalcino 2018', 'requests': 45, 'trend': 12},
            {'name': 'Barolo DOCG 2017', 'requests': 38, 'trend': 8},
            {'name': 'Chianti Classico Riserva', 'requests': 32, 'trend': -3},
            {'name': 'Amarone della Valpolicella', 'requests': 28, 'trend': 15},
            {'name': 'Franciacorta Brut', 'requests': 25, 'trend': 5}
        ]
    }), 200


@b2b_bp.route('/analytics/popular-wines', methods=['GET'])
@jwt_required()
def get_popular_wines():
    """Get most recommended/requested wines."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'Non autorizzato'}), 403
    
    # Get venue's products ordered by some metric
    # In production, this would aggregate from session data
    products = Product.query.filter_by(
        venue_id=user.venue_id,
        is_available=True
    ).limit(10).all()
    
    return jsonify({
        'wines': [p.to_dict() for p in products]
    }), 200

