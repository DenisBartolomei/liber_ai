"""
Analytics Routes for LIBER
Provides analytics endpoints for Free and Premium tiers
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Venue
from app.services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics', __name__)


def _get_user_venue():
    """Helper to get current user and venue"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return None, None, jsonify({'message': 'Non autorizzato'}), 403
    
    venue = Venue.query.get(user.venue_id)
    if not venue:
        return None, None, jsonify({'message': 'Locale non trovato'}), 404
    
    return user, venue, None, None


def _check_premium(user, venue):
    """Check if venue has Premium plan"""
    premium_plans = ['premium', 'enterprise', 'professional']
    return venue.plan in premium_plans


@analytics_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """
    Get overview statistics (FREE tier).
    
    Query params:
    - period: 'week', 'month', 'quarter', 'year' (default: 'month')
    - start_date: ISO format date (optional)
    - end_date: ISO format date (optional)
    """
    user, venue, error_response, error_code = _get_user_venue()
    if error_response:
        return error_response, error_code
    
    period = request.args.get('period', 'month')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    service = AnalyticsService()
    stats = service.get_overview_stats(
        venue_id=venue.id,
        period=period,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return jsonify(stats), 200


@analytics_bp.route('/operational', methods=['GET'])
@jwt_required()
def get_operational():
    """
    Get operational monitoring data (FREE tier).
    
    Query params:
    - period: 'week', 'month', 'quarter', 'year' (default: 'month')
    - start_date: ISO format date (optional)
    - end_date: ISO format date (optional)
    """
    user, venue, error_response, error_code = _get_user_venue()
    if error_response:
        return error_response, error_code
    
    period = request.args.get('period', 'month')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    service = AnalyticsService()
    data = service.get_operational_monitoring(
        venue_id=venue.id,
        period=period,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return jsonify(data), 200


@analytics_bp.route('/customer-intelligence', methods=['GET'])
@jwt_required()
def get_customer_intelligence():
    """
    Get customer intelligence analytics (PREMIUM tier).
    
    Query params:
    - period: 'week', 'month', 'quarter', 'year' (default: 'month')
    - start_date: ISO format date (optional)
    - end_date: ISO format date (optional)
    """
    user, venue, error_response, error_code = _get_user_venue()
    if error_response:
        return error_response, error_code
    
    # Check Premium access
    if not _check_premium(user, venue):
        return jsonify({
            'message': 'Questa funzione è disponibile solo con piano Premium',
            'current_plan': venue.plan
        }), 403
    
    period = request.args.get('period', 'month')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    service = AnalyticsService()
    data = service.get_customer_intelligence(
        venue_id=venue.id,
        period=period,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return jsonify(data), 200


@analytics_bp.route('/wine-performance', methods=['GET'])
@jwt_required()
def get_wine_performance():
    """
    Get wine performance analytics (PREMIUM tier).
    
    Query params:
    - period: 'week', 'month', 'quarter', 'year' (default: 'month')
    - start_date: ISO format date (optional)
    - end_date: ISO format date (optional)
    """
    user, venue, error_response, error_code = _get_user_venue()
    if error_response:
        return error_response, error_code
    
    # Check Premium access
    if not _check_premium(user, venue):
        return jsonify({
            'message': 'Questa funzione è disponibile solo con piano Premium',
            'current_plan': venue.plan
        }), 403
    
    period = request.args.get('period', 'month')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    service = AnalyticsService()
    data = service.get_wine_performance(
        venue_id=venue.id,
        period=period,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return jsonify(data), 200


@analytics_bp.route('/revenue', methods=['GET'])
@jwt_required()
def get_revenue():
    """
    Get revenue intelligence analytics (PREMIUM tier).
    
    Query params:
    - period: 'week', 'month', 'quarter', 'year' (default: 'month')
    - start_date: ISO format date (optional)
    - end_date: ISO format date (optional)
    """
    user, venue, error_response, error_code = _get_user_venue()
    if error_response:
        return error_response, error_code
    
    # Check Premium access
    if not _check_premium(user, venue):
        return jsonify({
            'message': 'Questa funzione è disponibile solo con piano Premium',
            'current_plan': venue.plan
        }), 403
    
    period = request.args.get('period', 'month')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    service = AnalyticsService()
    data = service.get_revenue_intelligence(
        venue_id=venue.id,
        period=period,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return jsonify(data), 200


@analytics_bp.route('/benchmark', methods=['GET'])
@jwt_required()
def get_benchmark():
    """
    Get benchmark comparison (PREMIUM tier).
    
    Query params:
    - period: 'week', 'month', 'quarter', 'year' (default: 'month')
    - start_date: ISO format date (optional)
    - end_date: ISO format date (optional)
    """
    user, venue, error_response, error_code = _get_user_venue()
    if error_response:
        return error_response, error_code
    
    # Check Premium access
    if not _check_premium(user, venue):
        return jsonify({
            'message': 'Questa funzione è disponibile solo con piano Premium',
            'current_plan': venue.plan
        }), 403
    
    period = request.args.get('period', 'month')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    service = AnalyticsService()
    data = service.get_benchmark_comparison(
        venue_id=venue.id,
        period=period,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return jsonify(data), 200

