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
        
        # Total conversations
        total_conversations = sessions_query.count()
        
        # Count total selected products (wines)
        total_selected_products = db.session.query(
            func.count(WineProposal.id)
        ).join(
            Session, WineProposal.session_id == Session.id
        ).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            WineProposal.is_selected == True
        ).scalar() or 0
        
        # Selection rate: NUMERO DI PRODOTTI SELECTED / SOMMA SESSIONI
        selection_rate = (total_selected_products / total_conversations * 100) if total_conversations > 0 else 0
        
        # Sessions with selection: count sessions where products_selected is not null
        sessions_with_selection = db.session.query(
            func.count(Session.id)
        ).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            Session.products_selected.isnot(None)
        ).scalar()
        
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
        # Get distinct sessions that have selections and num_bottiglie_target
        sessions_with_selection_ids_subq = db.session.query(
            Session.id
        ).join(
            WineProposal, Session.id == WineProposal.session_id
        ).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            WineProposal.is_selected == True,
            Session.num_bottiglie_target.isnot(None)
        ).distinct().subquery()
        
        avg_bottles_per_table = db.session.query(
            func.avg(Session.num_bottiglie_target)
        ).filter(
            Session.id.in_(db.session.query(sessions_with_selection_ids_subq.c.id))
        ).scalar() or 0
        
        # Total products in venue's wine list
        total_products = Product.query.filter_by(venue_id=venue_id).count()
        
        return {
            'total_conversations': total_conversations,
            'sessions_with_selection': sessions_with_selection,
            'total_selected_products': total_selected_products,  # Numero totale di bottiglie selezionate
            'total_products': total_products,  # Numero totale di prodotti in carta
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
        session_ids_subq = db.session.query(Session.id).filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date
        ).subquery()
        
        # Price distribution (buckets: 20-30, 31-40, 41-50, 51-60, oltre 60)
        price_range_case = case(
            (and_(WineProposal.price >= 20, WineProposal.price <= 30), '20-30€'),
            (and_(WineProposal.price >= 31, WineProposal.price <= 40), '31-40€'),
            (and_(WineProposal.price >= 41, WineProposal.price <= 50), '41-50€'),
            (and_(WineProposal.price >= 51, WineProposal.price <= 60), '51-60€'),
            (WineProposal.price > 60, 'Oltre 60€'),
            else_=None
        ).label('price_range')
        
        price_distribution_query = db.session.query(
            price_range_case,
            func.count(WineProposal.id).label('count')
        ).filter(
            WineProposal.session_id.in_(db.session.query(session_ids_subq.c.id)),
            WineProposal.is_selected == True,
            WineProposal.price >= 20  # Only wines >= 20€
        ).group_by(price_range_case).having(
            price_range_case.isnot(None)
        ).all()
        
        # Filter out None values and sort by price range
        price_distribution_raw = [{'range': r, 'count': c} for r, c in price_distribution_query if r is not None]
        
        # Sort by price range order
        range_order = ['20-30€', '31-40€', '41-50€', '51-60€', 'Oltre 60€']
        price_distribution = sorted(price_distribution_raw, key=lambda x: range_order.index(x['range']) if x['range'] in range_order else 999)
        
        # Wine type distribution
        wine_type_query = db.session.query(
            Product.type,
            func.count(WineProposal.id).label('count')
        ).join(
            WineProposal, Product.id == WineProposal.product_id
        ).filter(
            WineProposal.session_id.in_(db.session.query(session_ids_subq.c.id)),
            WineProposal.is_selected == True
        ).group_by(Product.type).all()
        
        wine_type_distribution = [{'type': t, 'count': c} for t, c in wine_type_query]
        
        # Top selected wines (all wines, no limit)
        top_selected_query = db.session.query(
            Product.id,
            Product.name,
            func.count(WineProposal.id).label('selection_count')
        ).join(
            WineProposal, Product.id == WineProposal.product_id
        ).filter(
            WineProposal.session_id.in_(db.session.query(session_ids_subq.c.id)),
            WineProposal.is_selected == True,
            Product.venue_id == venue_id
        ).group_by(Product.id, Product.name).order_by(
            func.count(WineProposal.id).desc()
        ).all()
        
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
            WineProposal.session_id.in_(db.session.query(session_ids_subq.c.id)),
            Product.venue_id == venue_id
        ).group_by(Product.id, Product.name).subquery()
        
        selected_count_query = db.session.query(
            Product.id,
            func.count(WineProposal.id).label('selection_count')
        ).join(
            WineProposal, Product.id == WineProposal.product_id
        ).filter(
            WineProposal.session_id.in_(db.session.query(session_ids_subq.c.id)),
            WineProposal.is_selected == True,
            Product.venue_id == venue_id
        ).group_by(Product.id).subquery()
        
        # Join and calculate difference (all wines, no limit)
        top_not_selected_query = db.session.query(
            proposed_count_query.c.id,
            proposed_count_query.c.name,
            (proposed_count_query.c.proposal_count - func.coalesce(selected_count_query.c.selection_count, 0)).label('not_selected_count')
        ).outerjoin(
            selected_count_query, proposed_count_query.c.id == selected_count_query.c.id
        ).order_by(
            (proposed_count_query.c.proposal_count - func.coalesce(selected_count_query.c.selection_count, 0)).desc()
        ).all()
        
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
        
        # Get sessions with budget_initial (for average budget calculation)
        all_sessions_with_budget = Session.query.filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            Session.budget_initial.isnot(None)
        ).all()
        
        # Calculate average budget from all sessions with budget_initial
        budgets = [float(s.budget_initial) for s in all_sessions_with_budget if s.budget_initial is not None]
        avg_budget_initial = sum(budgets) / len(budgets) if budgets else 0
        
        # Get sessions with both budget_initial and selected wines (for elasticity calculation)
        sessions_with_budget = all_sessions_with_budget
        
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
        
        # Budget distribution by ranges (20-25, 26-30, 31-35, ..., oltre 100)
        budget_ranges = []
        for start in range(20, 101, 5):
            end = start + 4
            if end <= 100:
                budget_ranges.append((start, end, f'{start}-{end}€'))
        budget_ranges.append((101, 9999, 'Oltre 100€'))
        
        budget_distribution = []
        for start, end, label in budget_ranges:
            if end == 9999:
                count = Session.query.filter(
                    Session.venue_id == venue_id,
                    Session.mode == 'b2c',
                    Session.created_at >= start_date,
                    Session.created_at <= end_date,
                    Session.budget_initial.isnot(None),
                    Session.budget_initial > 100
                ).count()
            else:
                count = Session.query.filter(
                    Session.venue_id == venue_id,
                    Session.mode == 'b2c',
                    Session.created_at >= start_date,
                    Session.created_at <= end_date,
                    Session.budget_initial.isnot(None),
                    Session.budget_initial >= start,
                    Session.budget_initial <= end
                ).count()
            
            if count > 0:
                budget_distribution.append({
                    'range': label,
                    'count': count,
                    'start': start,
                    'end': end if end != 9999 else None
                })
        
        # Sort by start value
        budget_distribution.sort(key=lambda x: x['start'] if x['start'] else 999)
        
        return {
            'price_elasticity_rate': round(price_elasticity_rate, 1),
            'avg_price_delta_pct': round(avg_price_delta, 1),
            'avg_budget_initial': round(avg_budget_initial, 2),
            'sessions_analyzed': total_sessions_with_selection,
            'budget_distribution': budget_distribution,
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
        
        session_ids_subq = db.session.query(Session.id).filter(
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
            WineProposal.session_id.in_(db.session.query(session_ids_subq.c.id)),
            Product.venue_id == venue_id
        ).group_by(Product.id, Product.name).subquery()
        
        selections_query = db.session.query(
            Product.id,
            func.count(WineProposal.id).label('selections')
        ).join(
            WineProposal, Product.id == WineProposal.product_id
        ).filter(
            WineProposal.session_id.in_(db.session.query(session_ids_subq.c.id)),
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
        - extra_vendita: Total extra revenue from wines sold above customer budget (€)
        - estimated_lost_margin: Estimated margin from conversations without selection
        """
        start_date, end_date = self._get_date_range(period, start_date, end_date)
        
        session_ids_subq = db.session.query(Session.id).filter(
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
            WineProposal.session_id.in_(db.session.query(session_ids_subq.c.id)),
            WineProposal.is_selected == True,
            WineProposal.margin.isnot(None)
        ).group_by(WineProposal.session_id).all()
        
        if margin_per_session_query:
            avg_margin_per_conversation = sum(m[1] for m in margin_per_session_query) / len(margin_per_session_query)
        else:
            avg_margin_per_conversation = 0
        
        # Extra vendita: total extra revenue from wines sold above customer budget
        # For each selected wine, calculate (price - budget) if price > budget, and sum all positive differences
        sessions_with_budget = Session.query.filter(
            Session.venue_id == venue_id,
            Session.mode == 'b2c',
            Session.created_at >= start_date,
            Session.created_at <= end_date,
            Session.budget_initial.isnot(None)
        ).all()
        
        extra_vendita = 0.0
        
        for session in sessions_with_budget:
            selected_wines = WineProposal.query.filter(
                WineProposal.session_id == session.id,
                WineProposal.is_selected == True
            ).all()
            
            if not selected_wines:
                continue
            
            budget = float(session.budget_initial)
            
            # For each selected wine, add the difference if price > budget
            for wine in selected_wines:
                wine_price = float(wine.price)
                if wine_price > budget:
                    extra_vendita += (wine_price - budget)
        
        # Estimated lost margin: sessions without selection * avg_margin_per_conversation
        # Count sessions with products_selected not null
        sessions_with_selection = db.session.query(func.count(Session.id)).filter(
            Session.id.in_(db.session.query(session_ids_subq.c.id)),
            Session.products_selected.isnot(None)
        ).scalar()
        
        total_sessions = db.session.query(func.count(Session.id)).filter(
            Session.id.in_(db.session.query(session_ids_subq.c.id))
        ).scalar()
        
        sessions_without_selection = total_sessions - sessions_with_selection
        estimated_lost_margin = sessions_without_selection * avg_margin_per_conversation
        
        return {
            'avg_margin_per_conversation': round(float(avg_margin_per_conversation), 2),
            'extra_vendita': round(float(extra_vendita), 2),
            'estimated_lost_margin': round(estimated_lost_margin, 2),
            'sessions_without_selection': sessions_without_selection,
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

