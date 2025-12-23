"""
Analytics Service for LIBER
Calculates analytics indicators for Free and Premium tiers
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, and_, or_, case
from sqlalchemy.sql import text
from app import db
from app.models import Session, WineProposal, Product, Venue, MenuItem


class AnalyticsService:
    """
    Service for calculating analytics indicators.
    Provides methods for both Free (monitoring) and Premium (consulting) tiers.
    """
    
    def __init__(self):
        pass
    
    def _get_date_range(self, period: str = 'month', start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """
        Get date range based on period or explicit dates.
        
        Args:
            period: 'week', 'month', 'quarter', or 'year'
            start_date: Explicit start date (overrides period)
            end_date: Explicit end date (overrides period)
            
        Returns:
            Tuple of (start_date, end_date)
        """
        if end_date is None:
            end_date = datetime.utcnow()
        
        if start_date is None:
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'quarter':
                start_date = end_date - timedelta(days=90)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)  # Default to month
        
        return start_date, end_date
    
    # ==========================================
    # FREE TIER: Overview Stats
    # ==========================================
    
    def get_overview_stats(self, venue_id: int, period: str = 'month', 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> Dict:
        """
        Get overview statistics (FREE tier).
        
        Returns:
        - total_conversations: Total number of conversations
        - selection_rate: % of conversations with at least one selection
        - avg_bottle_value: Average price of selected bottles
        - avg_margin: Average margin per selected bottle
        - avg_bottles_per_table: Average bottles per table (for sessions with selection)
        """
        start_date, end_date = self._get_date_range(period, start_date, end_date)
        
        # Get all B2C sessions in date range
        sessions_query = Session.query.filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date
        )
        
        total_conversations = sessions_query.count()
        
        # Get sessions with at least one selected wine
        sessions_with_selection = sessions_query.join(
            WineProposal,
            Session.id == WineProposal.session_id
        ).filter(
            WineProposal.is_selected == True
        ).distinct(Session.id).count()
        
        selection_rate = (sessions_with_selection / total_conversations * 100) if total_conversations > 0 else 0
        
        # Average bottle value (price of selected wines)
        avg_bottle_value = db.session.query(
            func.avg(WineProposal.price)
        ).join(
            Session, WineProposal.session_id == Session.id
        ).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            WineProposal.is_selected == True
        ).scalar() or 0
        
        # Average margin per selected bottle
        avg_margin = db.session.query(
            func.avg(WineProposal.margin)
        ).join(
            Session, WineProposal.session_id == Session.id
        ).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            WineProposal.is_selected == True,
            WineProposal.margin.isnot(None)
        ).scalar() or 0
        
        # Average bottles per table (sessions with selection)
        avg_bottles_per_table = db.session.query(
            func.avg(Session.num_bottiglie_target)
        ).join(
            WineProposal, Session.id == WineProposal.session_id
        ).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            WineProposal.is_selected == True,
            Session.num_bottiglie_target.isnot(None)
        ).distinct(Session.id).scalar() or 0
        
        return {
            'total_conversations': total_conversations,
            'sessions_with_selection': sessions_with_selection,
            'selection_rate': round(selection_rate, 1),
            'avg_bottle_value': round(float(avg_bottle_value), 2),
            'avg_margin': round(float(avg_margin), 2),
            'avg_bottles_per_table': round(float(avg_bottles_per_table), 1),
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    
    # ==========================================
    # FREE TIER: Operational Monitoring
    # ==========================================
    
    def get_operational_monitoring(self, venue_id: int, period: str = 'month',
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> Dict:
        """
        Get operational monitoring data (FREE tier).
        
        Returns:
        - price_distribution: Distribution of selected wines by price range
        - wine_type_distribution: Distribution by wine type (red, white, etc.)
        - top_selected_wines: Most selected wines
        - top_proposed_not_selected: Wines proposed but not selected
        - dishes_association: Most frequently associated dishes (from context)
        """
        start_date, end_date = self._get_date_range(period, start_date, end_date)
        
        # Get session IDs in date range
        session_ids = db.session.query(Session.id).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date
        ).subquery()
        
        # Price distribution (buckets: 0-20, 20-40, 40-60, 60-100, 100+)
        price_distribution_query = db.session.query(
            case(
                (WineProposal.price < 20, '0-20€'),
                (and_(WineProposal.price >= 20, WineProposal.price < 40), '20-40€'),
                (and_(WineProposal.price >= 40, WineProposal.price < 60), '40-60€'),
                (and_(WineProposal.price >= 60, WineProposal.price < 100), '60-100€'),
                else_='100€+'
            ).label('price_range'),
            func.count(WineProposal.id).label('count')
        ).filter(
            WineProposal.session_id.in_(session_ids),
            WineProposal.is_selected == True
        ).group_by('price_range').all()
        
        price_distribution = [{'range': r, 'count': c} for r, c in price_distribution_query]
        
        # Wine type distribution
        wine_type_query = db.session.query(
            Product.type,
            func.count(WineProposal.id).label('count')
        ).join(
            WineProposal, Product.id == WineProposal.product_id
        ).filter(
            WineProposal.session_id.in_(session_ids),
            WineProposal.is_selected == True
        ).group_by(Product.type).all()
        
        wine_type_distribution = [{'type': t, 'count': c} for t, c in wine_type_query]
        
        # Top selected wines
        top_selected_query = db.session.query(
            Product.id,
            Product.name,
            func.count(WineProposal.id).label('selection_count')
        ).join(
            WineProposal, Product.id == WineProposal.product_id
        ).filter(
            WineProposal.session_id.in_(session_ids),
            WineProposal.is_selected == True,
            Product.venue_id == venue_id
        ).group_by(Product.id, Product.name).order_by(
            func.count(WineProposal.id).desc()
        ).limit(10).all()
        
        top_selected_wines = [
            {'id': w[0], 'name': w[1], 'count': w[2]}
            for w in top_selected_query
        ]
        
        # Top proposed but not selected wines
        # Count proposals - count selections for each wine
        proposed_count_query = db.session.query(
            Product.id,
            Product.name,
            func.count(WineProposal.id).label('proposal_count')
        ).join(
            WineProposal, Product.id == WineProposal.product_id
        ).filter(
            WineProposal.session_id.in_(session_ids),
            Product.venue_id == venue_id
        ).group_by(Product.id, Product.name).subquery()
        
        selected_count_query = db.session.query(
            Product.id,
            func.count(WineProposal.id).label('selection_count')
        ).join(
            WineProposal, Product.id == WineProposal.product_id
        ).filter(
            WineProposal.session_id.in_(session_ids),
            WineProposal.is_selected == True,
            Product.venue_id == venue_id
        ).group_by(Product.id).subquery()
        
        # Join and calculate difference
        top_not_selected_query = db.session.query(
            proposed_count_query.c.id,
            proposed_count_query.c.name,
            (proposed_count_query.c.proposal_count - func.coalesce(selected_count_query.c.selection_count, 0)).label('not_selected_count')
        ).outerjoin(
            selected_count_query, proposed_count_query.c.id == selected_count_query.c.id
        ).order_by(
            (proposed_count_query.c.proposal_count - func.coalesce(selected_count_query.c.selection_count, 0)).desc()
        ).limit(10).all()
        
        top_proposed_not_selected = [
            {'id': w[0], 'name': w[1], 'proposed_not_selected': w[2]}
            for w in top_not_selected_query if w[2] > 0
        ]
        
        # Dishes association (from session context)
        # This requires parsing JSON context - simplified version
        # In production, might want to normalize dishes into separate table
        dishes_data = {}
        sessions = Session.query.filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            Session.context.isnot(None)
        ).all()
        
        for session in sessions:
            if session.context and 'dishes' in session.context:
                dishes = session.context.get('dishes', [])
                for dish in dishes:
                    dish_name = dish.get('name', '') if isinstance(dish, dict) else str(dish)
                    if dish_name:
                        dishes_data[dish_name] = dishes_data.get(dish_name, 0) + 1
        
        top_dishes = sorted(dishes_data.items(), key=lambda x: x[1], reverse=True)[:10]
        dishes_association = [{'name': d[0], 'count': d[1]} for d in top_dishes]
        
        return {
            'price_distribution': price_distribution,
            'wine_type_distribution': wine_type_distribution,
            'top_selected_wines': top_selected_wines,
            'top_proposed_not_selected': top_proposed_not_selected,
            'dishes_association': dishes_association,
            'period': period
        }
    
    # ==========================================
    # PREMIUM TIER: Customer Intelligence
    # ==========================================
    
    def get_customer_intelligence(self, venue_id: int, period: str = 'month',
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict:
        """
        Get customer intelligence analytics (PREMIUM tier).
        
        Returns:
        - price_elasticity: % of customers accepting wines above initial budget
        - avg_price_delta: Average difference between selected price and initial budget
        - experimentation_rate: % of customers selecting wines outside initial preferences
        """
        start_date, end_date = self._get_date_range(period, start_date, end_date)
        
        # Get sessions with both budget_initial and selected wines
        sessions_with_budget = Session.query.filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            Session.budget_initial.isnot(None)
        ).all()
        
        elasticities = []
        total_sessions_with_selection = 0
        
        for session in sessions_with_budget:
            # Get selected wines for this session
            selected_wines = WineProposal.query.filter(
                WineProposal.session_id == session.id,
                WineProposal.is_selected == True
            ).all()
            
            if not selected_wines:
                continue
            
            total_sessions_with_selection += 1
            avg_selected_price = sum(float(w.price) for w in selected_wines) / len(selected_wines)
            budget = float(session.budget_initial)
            
            if budget > 0:
                delta = avg_selected_price - budget
                elasticity_pct = (delta / budget) * 100
                elasticities.append(elasticity_pct)
        
        avg_price_delta = sum(elasticities) / len(elasticities) if elasticities else 0
        price_elasticity_rate = sum(1 for e in elasticities if e > 0) / len(elasticities) * 100 if elasticities else 0
        
        return {
            'price_elasticity_rate': round(price_elasticity_rate, 1),
            'avg_price_delta_pct': round(avg_price_delta, 1),
            'sessions_analyzed': total_sessions_with_selection,
            'period': period
        }
    
    # ==========================================
    # PREMIUM TIER: Wine Performance
    # ==========================================
    
    def get_wine_performance(self, venue_id: int, period: str = 'month',
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict:
        """
        Get wine performance analytics (PREMIUM tier).
        
        Returns:
        - conversion_rates: Conversion rate per wine (selections / proposals)
        - blocking_wines: Wines that seem to block conversation (high proposals, no selections)
        """
        start_date, end_date = self._get_date_range(period, start_date, end_date)
        
        session_ids = db.session.query(Session.id).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date
        ).subquery()
        
        # Conversion rates per wine
        proposals_query = db.session.query(
            Product.id,
            Product.name,
            func.count(WineProposal.id).label('proposals')
        ).join(
            WineProposal, Product.id == WineProposal.product_id
        ).filter(
            WineProposal.session_id.in_(session_ids),
            Product.venue_id == venue_id
        ).group_by(Product.id, Product.name).subquery()
        
        selections_query = db.session.query(
            Product.id,
            func.count(WineProposal.id).label('selections')
        ).join(
            WineProposal, Product.id == WineProposal.product_id
        ).filter(
            WineProposal.session_id.in_(session_ids),
            WineProposal.is_selected == True,
            Product.venue_id == venue_id
        ).group_by(Product.id).subquery()
        
        conversion_query = db.session.query(
            proposals_query.c.id,
            proposals_query.c.name,
            proposals_query.c.proposals,
            func.coalesce(selections_query.c.selections, 0).label('selections'),
            (func.coalesce(selections_query.c.selections, 0).cast(db.Float) / 
             proposals_query.c.proposals.cast(db.Float) * 100).label('conversion_rate')
        ).outerjoin(
            selections_query, proposals_query.c.id == selections_query.c.id
        ).filter(
            proposals_query.c.proposals >= 3  # Only wines with at least 3 proposals
        ).order_by(
            (func.coalesce(selections_query.c.selections, 0).cast(db.Float) / 
             proposals_query.c.proposals.cast(db.Float)).asc()  # Lowest conversion first
        ).limit(20).all()
        
        conversion_rates = [
            {
                'id': w[0],
                'name': w[1],
                'proposals': w[2],
                'selections': w[3],
                'conversion_rate': round(float(w[4]), 1)
            }
            for w in conversion_query
        ]
        
        # Blocking wines: high proposals, zero or very low selections
        blocking_wines = [
            w for w in conversion_rates 
            if w['proposals'] >= 5 and w['conversion_rate'] < 10
        ]
        
        return {
            'conversion_rates': conversion_rates,
            'blocking_wines': blocking_wines,
            'period': period
        }
    
    # ==========================================
    # PREMIUM TIER: Revenue Intelligence
    # ==========================================
    
    def get_revenue_intelligence(self, venue_id: int, period: str = 'month',
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> Dict:
        """
        Get revenue intelligence analytics (PREMIUM tier).
        
        Returns:
        - avg_margin_per_conversation: Average margin per conversation
        - upsell_rate: % of conversations with selected price > initial budget
        - estimated_lost_margin: Estimated margin from conversations without selection
        """
        start_date, end_date = self._get_date_range(period, start_date, end_date)
        
        session_ids = db.session.query(Session.id).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date
        ).subquery()
        
        # Average margin per conversation (only sessions with selections)
        margin_per_session_query = db.session.query(
            WineProposal.session_id,
            func.sum(WineProposal.margin).label('total_margin')
        ).filter(
            WineProposal.session_id.in_(session_ids),
            WineProposal.is_selected == True,
            WineProposal.margin.isnot(None)
        ).group_by(WineProposal.session_id).all()
        
        if margin_per_session_query:
            avg_margin_per_conversation = sum(m[1] for m in margin_per_session_query) / len(margin_per_session_query)
        else:
            avg_margin_per_conversation = 0
        
        # Upsell rate: sessions where selected price > budget_initial
        sessions_with_budget = Session.query.filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            Session.budget_initial.isnot(None)
        ).all()
        
        upsell_count = 0
        total_sessions_with_budget = 0
        
        for session in sessions_with_budget:
            selected_wines = WineProposal.query.filter(
                WineProposal.session_id == session.id,
                WineProposal.is_selected == True
            ).all()
            
            if not selected_wines:
                continue
            
            total_sessions_with_budget += 1
            avg_selected_price = sum(float(w.price) for w in selected_wines) / len(selected_wines)
            budget = float(session.budget_initial)
            
            if avg_selected_price > budget:
                upsell_count += 1
        
        upsell_rate = (upsell_count / total_sessions_with_budget * 100) if total_sessions_with_budget > 0 else 0
        
        # Estimated lost margin: sessions without selection * avg_margin_per_conversation
        sessions_with_selection = db.session.query(func.count(func.distinct(WineProposal.session_id))).filter(
            WineProposal.session_id.in_(session_ids),
            WineProposal.is_selected == True
        ).scalar()
        
        total_sessions = db.session.query(func.count(Session.id)).filter(
            Session.id.in_(session_ids)
        ).scalar()
        
        sessions_without_selection = total_sessions - sessions_with_selection
        estimated_lost_margin = sessions_without_selection * avg_margin_per_conversation
        
        return {
            'avg_margin_per_conversation': round(float(avg_margin_per_conversation), 2),
            'upsell_rate': round(upsell_rate, 1),
            'estimated_lost_margin': round(estimated_lost_margin, 2),
            'sessions_without_selection': sessions_without_selection,
            'period': period
        }
    
    # ==========================================
    # PREMIUM TIER: Menu Pairing Analytics
    # ==========================================
    
    def get_menu_pairing_analytics(self, venue_id: int, period: str = 'month',
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict:
        """
        Get menu-wine pairing analytics (PREMIUM tier).
        
        Returns:
        - dishes_facilitating_selection: Dishes that lead to higher selection rates
        - dishes_blocking_selection: Dishes that seem to block selection
        """
        start_date, end_date = self._get_date_range(period, start_date, end_date)
        
        # Analyze sessions with dishes in context
        sessions = Session.query.filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            Session.context.isnot(None)
        ).all()
        
        dish_stats = {}
        
        for session in sessions:
            if not session.context or 'dishes' not in session.context:
                continue
            
            dishes = session.context.get('dishes', [])
            has_selection = WineProposal.query.filter(
                WineProposal.session_id == session.id,
                WineProposal.is_selected == True
            ).first() is not None
            
            for dish in dishes:
                dish_name = dish.get('name', '') if isinstance(dish, dict) else str(dish)
                if not dish_name:
                    continue
                
                if dish_name not in dish_stats:
                    dish_stats[dish_name] = {'total': 0, 'with_selection': 0}
                
                dish_stats[dish_name]['total'] += 1
                if has_selection:
                    dish_stats[dish_name]['with_selection'] += 1
        
        # Calculate selection rates
        dishes_with_rates = []
        for dish_name, stats in dish_stats.items():
            if stats['total'] >= 3:  # Only dishes with at least 3 occurrences
                selection_rate = (stats['with_selection'] / stats['total']) * 100
                dishes_with_rates.append({
                    'name': dish_name,
                    'total_sessions': stats['total'],
                    'sessions_with_selection': stats['with_selection'],
                    'selection_rate': round(selection_rate, 1)
                })
        
        # Sort by selection rate
        dishes_with_rates.sort(key=lambda x: x['selection_rate'], reverse=True)
        
        # Top facilitating (high selection rate)
        dishes_facilitating = [d for d in dishes_with_rates if d['selection_rate'] >= 60][:10]
        
        # Top blocking (low selection rate)
        dishes_blocking = [d for d in dishes_with_rates if d['selection_rate'] < 40][:10]
        
        return {
            'dishes_facilitating_selection': dishes_facilitating,
            'dishes_blocking_selection': dishes_blocking,
            'period': period
        }
    
    # ==========================================
    # PREMIUM TIER: Benchmark (placeholder)
    # ==========================================
    
    def get_benchmark_comparison(self, venue_id: int, period: str = 'month',
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> Dict:
        """
        Get benchmark comparison (PREMIUM tier).
        
        Note: This requires aggregated data from other venues.
        For now, returns placeholder structure.
        """
        # TODO: Implement benchmark logic when we have aggregated data
        # This would compare venue metrics against similar venues
        
        start_date, end_date = self._get_date_range(period, start_date, end_date)
        
        # Get venue's metrics
        overview = self.get_overview_stats(venue_id, period, start_date, end_date)
        revenue = self.get_revenue_intelligence(venue_id, period, start_date, end_date)
        
        return {
            'venue_metrics': {
                'avg_bottle_value': overview['avg_bottle_value'],
                'avg_margin': overview['avg_margin'],
                'selection_rate': overview['selection_rate']
            },
            'benchmark_metrics': {
                'avg_bottle_value': None,  # Would be calculated from peer data
                'avg_margin': None,
                'selection_rate': None
            },
            'percentile_ranking': {
                'price': None,  # Would show percentile (e.g., "Top 25%")
                'margin': None,
                'conversion': None
            },
            'note': 'Benchmark data requires aggregated statistics from peer venues'
        }

