"""
AI Agent Service for LIBER
Orchestrates conversations with OpenAI GPT and vector search
"""
import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI, APIError, AuthenticationError, RateLimitError
from flask import current_app
from app.services.vector_search import VectorSearchService
from app.prompts.b2b_system import get_b2b_system_prompt
from app.prompts.b2c_system import get_b2c_system_prompt, get_b2c_opening_prompt, calculate_bottles_needed

logger = logging.getLogger(__name__)


class AIAgentService:
    """
    AI Agent that handles both B2B (restaurant owner) and B2C (customer) conversations.
    Uses OpenAI for language generation and Qdrant for semantic wine search.
    """
    
    def __init__(self):
        # #region agent log
        import json
        import os
        log_path = r"c:\Users\utente\OneDrive - UNIVERSITA' CARLO CATTANEO - LIUC\Desktop\Bacco Sommelier AI\.cursor\debug.log"
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "ai_agent.py:23",
                    "message": "AIAgentService_init_entry",
                    "data": {},
                    "timestamp": int(__import__('time').time() * 1000)
                }, ensure_ascii=False) + "\n")
        except: pass
        # #endregion
        
        api_key = current_app.config.get('OPENAI_API_KEY', '')
        
        # #region agent log
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "location": "ai_agent.py:30",
                    "message": "api_key_retrieved",
                    "data": {
                        "api_key_length": len(api_key) if api_key else 0,
                        "api_key_is_empty": not api_key or len(api_key.strip()) == 0,
                        "api_key_preview": api_key[:10] + "..." if api_key and len(api_key) > 10 else (api_key if api_key else "EMPTY")
                    },
                    "timestamp": int(__import__('time').time() * 1000)
                }, ensure_ascii=False) + "\n")
        except: pass
        # #endregion
        
        if not api_key or not api_key.strip():
            logger.error("OPENAI_API_KEY is not configured!")
            raise ValueError("OPENAI_API_KEY non configurata. Contatta l'amministratore del sistema.")
        
        # #region agent log
        try:
            import openai
            import httpx
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                    "location": "ai_agent.py:45",
                    "message": "before_openai_init",
                    "data": {
                        "openai_version": getattr(openai, '__version__', 'unknown'),
                        "httpx_version": getattr(httpx, '__version__', 'unknown'),
                        "api_key_provided": True
                    },
                    "timestamp": int(__import__('time').time() * 1000)
                }, ensure_ascii=False) + "\n")
        except Exception as e:
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "location": "ai_agent.py:45",
                        "message": "version_check_failed",
                        "data": {"error": str(e)},
                        "timestamp": int(__import__('time').time() * 1000)
                    }, ensure_ascii=False) + "\n")
            except: pass
        # #endregion
        
        try:
            # Try initializing without explicit api_key parameter (uses env var)
            self.client = OpenAI(api_key=api_key)
        except TypeError as e:
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "C",
                        "location": "ai_agent.py:60",
                        "message": "openai_init_failed_typeerror",
                        "data": {"error": str(e), "error_type": type(e).__name__},
                        "timestamp": int(__import__('time').time() * 1000)
                    }, ensure_ascii=False) + "\n")
            except: pass
            # #endregion
            # Try alternative initialization
            import os
            os.environ['OPENAI_API_KEY'] = api_key
            self.client = OpenAI()
        except Exception as e:
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "D",
                        "location": "ai_agent.py:70",
                        "message": "openai_init_failed_general",
                        "data": {"error": str(e), "error_type": type(e).__name__},
                        "timestamp": int(__import__('time').time() * 1000)
                    }, ensure_ascii=False) + "\n")
            except: pass
            # #endregion
            raise
        
        # #region agent log
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "ai_agent.py:80",
                    "message": "openai_client_initialized",
                    "data": {"client_created": self.client is not None},
                    "timestamp": int(__import__('time').time() * 1000)
                }, ensure_ascii=False) + "\n")
        except: pass
        # #endregion
        
        self.model = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini')
        self.vector_service = VectorSearchService()
        self.max_history = current_app.config.get('MAX_CONVERSATION_HISTORY', 20)
        
        logger.info(f"AIAgentService initialized with model: {self.model}")
        logger.info(f"OPENAI_MODEL from config: {current_app.config.get('OPENAI_MODEL')}")
    
    def process_b2c_message(
        self, 
        session, 
        venue, 
        user_message: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a customer message (B2C mode).
        
        All preferences are now collected deterministically via the UI:
        - dishes, guest_count
        - wine_type, journey_preference, budget
        
        This method just makes recommendations based on the provided context.
        
        Args:
            session: The current chat session
            venue: The venue object
            user_message: The customer's message
            context: Context with dishes, guest_count, and preferences
            
        Returns:
            Dict with 'message', 'wines', 'suggestions', 'metadata'
        """
        # Get conversation history
        history = session.get_conversation_history(limit=self.max_history)
        
        # Determine if this is first message (no history or only system messages)
        # Check if current user message looks like initial automatic message (contains context summary)
        is_first_message = len([m for m in history if m.get('role') in ['user', 'assistant']]) == 0
        is_empty_message = not user_message or not user_message.strip()
        
        # Detect if this is the initial automatic message from frontend (contains context summary patterns)
        is_initial_context_message = False
        if user_message:
            initial_patterns = [
                'abbiamo ordinato:', 'preferiamo', 'vogliamo', 'siamo in',
                'al tavolo', 'budget:', 'persona', 'persone', 'bottigli'
            ]
            msg_lower = user_message.lower()
            # If message contains multiple context indicators, it's likely the initial auto-message
            pattern_count = sum(1 for pattern in initial_patterns if pattern in msg_lower)
            is_initial_context_message = pattern_count >= 3  # At least 3 patterns = initial message
        
        # Use opening prompt if: first message AND (empty message OR initial context message)
        if is_first_message and (is_empty_message or is_initial_context_message):
            is_first_message = True
        elif is_first_message and not is_empty_message and not is_initial_context_message:
            # First message with actual customer content - they might be skipping opening
            is_first_message = False
        
        # Use provided context or session context
        active_context = context or getattr(session, 'context', None) or {}
        
        # Extract preferences from context (collected via UI, not LLM)
        preferences = active_context.get('preferences', {})
        gathered_info = {
            'wine_type': preferences.get('wine_type', 'any'),
            'journey_preference': preferences.get('journey_preference', 'single'),
            'budget': preferences.get('budget', 'spinto')
        }
        
        logger.info(f"B2C Context: dishes={len(active_context.get('dishes', []))}, guests={active_context.get('guest_count')}, prefs={gathered_info}, is_first_message={is_first_message}, history_length={len(history)}")
        
        # Check if customer has confirmed (for switching from opening to recommendation)
        # Look for confirmation signals in the current message or history
        customer_confirmed = False
        
        # Check current user message for confirmation
        user_msg_lower = user_message.lower().strip()
        confirmation_signals = [
            'sì', 'si', 'ok', 'va bene', 'perfetto', 'confermo', 'procedi', 
            'va bene così', 'corretto', 'esatto', 'conferma', 'perfetto così',
            'procediamo', 'vai', 'andiamo', 'giusto', 'sì procedi'
        ]
        customer_confirmed = any(signal in user_msg_lower for signal in confirmation_signals)
        
        # Also check history if not confirmed in current message
        if not customer_confirmed and not is_first_message:
            user_messages = [m for m in history if m.get('role') == 'user']
            if user_messages:
                last_user_msg = user_messages[-1].get('content', '').lower()
                customer_confirmed = any(signal in last_user_msg for signal in confirmation_signals)
        
        # Use opening prompt ONLY for first message AND if customer hasn't confirmed yet
        use_opening_prompt = is_first_message and not customer_confirmed
        
        if use_opening_prompt:
            # Use simple opening prompt (no wine list needed, just welcome and recap)
            system_prompt = get_b2c_opening_prompt(
                venue_name=venue.name,
                sommelier_style=venue.sommelier_style or 'professional',
                context=active_context,
                gathered_info=gathered_info
            )
            
            # For opening, we don't need to load wines or pass them to AI
            # Just return the AI response without wine recommendations
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in history:
                messages.append({"role": msg['role'], "content": msg['content']})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call GPT
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=800
                )
                
                ai_response = response.choices[0].message.content
                
                return {
                    'message': ai_response,
                    'wines': [],
                    'wine_ids': [],
                    'journeys': [],
                    'suggestions': [],
                    'mode': 'single',
                    'metadata': {
                        'model': self.model,
                        'tokens_used': response.usage.total_tokens if response.usage else 0,
                        'gathered_info': gathered_info,
                        'is_recommending': False,
                        'is_opening': True
                    }
                }
                
            except Exception as e:
                logger.error(f"Error in opening message: {e}")
                raise
        
        # Use the recommendation prompt (customer has confirmed or not first message)
        system_prompt = get_b2c_system_prompt(
            venue_name=venue.name,
            cuisine_type=venue.cuisine_type,
            sommelier_style=venue.sommelier_style or 'professional',
            context=active_context,
            gathered_info=gathered_info,
            is_first_message=False  # Always False here since we're past opening
        )
        
        # Get ALL available wines from the venue's catalog (NO vector search)
        # The entire wine list must ALWAYS be passed to the AI
        from app.models import Product
        all_products = Product.query.filter_by(
            venue_id=venue.id,
            is_available=True
        ).order_by(Product.type, Product.name).all()
        
        # Convert to dict format
        all_wines = [p.to_dict() for p in all_products]
        logger.info(f"Loaded {len(all_wines)} wines from venue {venue.id} catalog (entire catalog)")
        
        # Filter out dessert wines if dishes are savory (but still pass all wines to AI context)
        dishes = active_context.get('dishes', [])
        dish_categories = [d.get('category', '').lower() for d in dishes]
        dish_names_text = ' '.join([d.get('name', '').lower() for d in dishes])
        has_savory_dishes = any(cat in ['antipasto', 'primo', 'secondo', 'contorno'] for cat in dish_categories) or \
                           any(word in dish_names_text for word in ['pasta', 'risotto', 'ragù', 'carne', 'pesce', 'antipasto', 'primo', 'secondo'])
        has_dessert_only = all(cat in ['dolce', 'dessert'] for cat in dish_categories if cat) or \
                          all(word in dish_names_text for word in ['dolce', 'dessert', 'torta', 'tiramisu'])
        
        # wines_to_use: all wines for AI context (entire catalog)
        # wines_for_suggestions: filtered wines for actual recommendations (excluding dessert wines if needed)
        wines_to_use = all_wines
        wines_for_suggestions = all_wines
        
        if has_savory_dishes and not has_dessert_only:
            # Remove dessert wines from suggestions (but AI still sees full catalog in context)
            wines_for_suggestions = [w for w in all_wines if w.get('type', '').lower() not in ['dessert', 'passito', 'dolce', 'liquoroso']]
            # Also check description/name for dessert indicators
            wines_for_suggestions = [w for w in wines_for_suggestions if not any(word in (w.get('name', '') + ' ' + (w.get('description', '') or '')).lower() 
                                                                                for word in ['passito', 'dolce', 'dessert', 'liquoroso', 'moscato'])]
            if len(wines_for_suggestions) < len(all_wines):
                logger.info(f"Filtered out {len(all_wines) - len(wines_for_suggestions)} dessert wines for suggestions, but full catalog ({len(all_wines)} wines) passed to AI")
        
        # Build context about available wines for the AI
        wines_context = f"""## Carta dei Vini Disponibili

⚠️ REGOLA CRITICA: Puoi proporre SOLO i vini elencati qui sotto. NON inventare MAI vini, nomi, cantine, annate o caratteristiche che non sono in questa lista. Se non c'è il vino ideale, proponi il più adatto tra quelli disponibili.

{self._build_wines_context(wines_to_use)}

⚠️ RICORDA: DEVI SEMPRE proporre qualcosa se ci sono vini nella lista sopra. Anche se non sono perfetti, proponi i migliori disponibili."""
        
        # Prepare messages for GPT
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "system", "content": wines_context})
        
        # Add conversation history
        for msg in history:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call GPT
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1200
            )
            
            ai_response = response.choices[0].message.content
            
            # Determine if this is a journey or single wine recommendation
            journey_pref = gathered_info.get('journey_preference', 'single')
            bottles_count = preferences.get('bottles_count')
            
            # Check if the AI is making wine recommendations
            wines_to_return = []
            wine_ids = []
            is_recommending = self._is_making_recommendations(ai_response)
            
            # CRITICAL: For single wine mode, extract wines ONLY from what AI actually mentions in the text
            # NO fallback - if extraction fails, return empty array (cards won't show)
            if journey_pref == 'single' and wines_for_suggestions:
                # Extract wines from AI response (search in full catalog)
                wines_to_return = self._extract_recommended_wines(ai_response, wines_to_use)
                
                # NO FALLBACK: If extraction failed, return empty array
                # Cards will only show if wines are actually mentioned and extracted from the text
                if not wines_to_return:
                    logger.warning(f"Wine extraction failed for single mode - no wines found in AI response. Not using fallback - cards will not be shown.")
            
            elif is_recommending:
                # For journey mode or when explicitly recommending, extract wines from full catalog
                wines_to_return = self._extract_recommended_wines(ai_response, wines_to_use)
                
                # NO FALLBACK: If extraction failed, return empty array
                # This ensures cards only show wines actually mentioned in the text
                if not wines_to_return:
                    logger.warning(f"Wine extraction failed - no wines found in AI response. Not using fallback - cards will not be shown.")
            
            wine_ids = [w.get('id') for w in wines_to_return if w.get('id')]
            
            # Handle journey vs single mode
            if journey_pref == 'journey':
                # For journeys, use filtered suggestions (excludes dessert wines if needed) to ensure variety
                # But AI has seen full catalog in context, so it knows all available wines
                wines_for_journey = wines_for_suggestions if wines_for_suggestions else wines_to_return
                
                if wines_for_journey:
                    logger.info(f"Creating journeys from {len(wines_for_journey)} available wines (from {len(wines_to_use)} total in catalog)")
                    # Create journeys from wines - use filtered wines to ensure variety
                    journeys = self._create_wine_journeys(wines_for_journey, bottles_count or calculate_bottles_needed(active_context.get('guest_count', 2)))
                    
                    if journeys:  # Only return journey mode if we have valid journeys
                        all_wine_ids = []
                        for journey in journeys:
                            all_wine_ids.extend([w.get('id') for w in journey.get('wines', []) if w.get('id')])
                        
                        logger.info(f"Created {len(journeys)} journeys with {len(all_wine_ids)} unique wines")
                        return {
                            'message': ai_response,
                            'journeys': journeys,
                            'wine_ids': list(set(all_wine_ids)),  # Remove duplicates
                            'suggestions': [],
                            'mode': 'journey',
                            'metadata': {
                                'model': self.model,
                                'tokens_used': response.usage.total_tokens if response.usage else 0,
                                'gathered_info': gathered_info,
                                'is_recommending': True
                            }
                        }
            
            # Single wine mode - ALWAYS return wines if we have any
            # Even if is_recommending is False, if we have wines we should show them
            if wines_to_return:
                return {
                    'message': ai_response,
                    'wines': wines_to_return,
                    'wine_ids': wine_ids,
                    'suggestions': [],
                    'mode': 'single',
                    'metadata': {
                        'model': self.model,
                        'tokens_used': response.usage.total_tokens if response.usage else 0,
                        'gathered_info': gathered_info,
                        'is_recommending': True  # Set to True if we have wines to show
                    }
                }
            else:
                # No wines found - this shouldn't happen if we have wines in catalog
                logger.warning(f"No wines to return for single mode, wines_to_use count: {len(wines_to_use)}, wines_for_suggestions count: {len(wines_for_suggestions)}")
                return {
                    'message': ai_response,
                    'wines': [],
                    'wine_ids': [],
                    'suggestions': [],
                    'mode': 'single',
                    'metadata': {
                        'model': self.model,
                        'tokens_used': response.usage.total_tokens if response.usage else 0,
                        'gathered_info': gathered_info,
                        'is_recommending': False
                    }
                }
            
        except AuthenticationError as e:
            logger.error(f"OpenAI Authentication Error: {e}")
            raise ValueError("Errore di autenticazione con il servizio AI. Verifica la configurazione API.")
        
        except RateLimitError as e:
            logger.error(f"OpenAI Rate Limit Error: {e}")
            raise ValueError("Servizio AI momentaneamente sovraccarico. Riprova tra qualche secondo.")
        
        except APIError as e:
            logger.error(f"OpenAI API Error: {e}")
            raise ValueError(f"Errore del servizio AI: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in process_b2c_message: {e}")
            raise ValueError(f"Si è verificato un errore imprevisto. Riprova.")
    
    def process_b2b_message(
        self, 
        session, 
        venue, 
        user_message: str
    ) -> Dict[str, Any]:
        """
        Process a restaurant owner message (B2B mode).
        
        Args:
            session: The current chat session
            venue: The venue object
            user_message: The owner's message
            
        Returns:
            Dict with 'message', 'wines', 'suggestions', 'metadata'
        """
        # Get conversation history
        history = session.get_conversation_history(limit=self.max_history)
        
        # Get system prompt
        system_prompt = get_b2b_system_prompt(
            venue_name=venue.name,
            cuisine_type=venue.cuisine_type,
            target_audience=venue.target_audience,
            menu_style=venue.menu_style
        )
        
        # Search for relevant wines
        suggested_wines = self._search_wines_for_catalog(
            query=user_message,
            venue=venue
        )
        
        wines_context = self._build_wines_context(suggested_wines)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Vini suggeriti per la carta:\n{wines_context}"}
        ]
        
        for msg in history:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            return {
                'message': ai_response,
                'wines': suggested_wines[:5],
                'wine_ids': [w.get('id') for w in suggested_wines[:5] if w.get('id')],
                'suggestions': [
                    'Vini per ampliare la selezione rossi',
                    'Bollicine alternative al Prosecco',
                    'Vini naturali e biodinamici'
                ],
                'metadata': {
                    'model': self.model,
                    'tokens_used': response.usage.total_tokens if response.usage else 0
                }
            }
            
        except AuthenticationError as e:
            logger.error(f"OpenAI Authentication Error: {e}")
            raise ValueError("Errore di autenticazione con il servizio AI.")
        
        except Exception as e:
            logger.error(f"Error in process_b2b_message: {e}")
            raise ValueError(f"Si è verificato un errore. Riprova.")
    
    def _build_search_query(
        self, 
        user_message: str, 
        context: Dict,
        history: List[Dict]
    ) -> str:
        """
        Build an enhanced search query for vector search.
        
        Combines user message with dish context for better wine matching.
        """
        query_parts = [user_message]
        
        # Add dish context if available
        if context and context.get('dishes'):
            dish_names = [d.get('name', '') for d in context['dishes'] if d.get('name')]
            if dish_names:
                query_parts.append(f"Piatti: {', '.join(dish_names)}")
        
        # Extract preferences from conversation history
        for msg in history[-4:]:  # Last 4 messages
            content = msg.get('content', '').lower()
            if any(word in content for word in ['rosso', 'bianco', 'bollicine', 'spumante', 'rosato']):
                query_parts.append(msg.get('content', ''))
        
        return ' '.join(query_parts)
    
    def _search_relevant_wines(
        self, 
        query: str, 
        venue_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """Search for wines relevant to the query from venue's catalog."""
        try:
            results = self.vector_service.search(
                query=query,
                venue_id=venue_id,
                limit=limit
            )
            # Ensure we always return at least some wines if available in the venue
            if not results:
                logger.info(f"No vector search results, trying database fallback for venue {venue_id}")
                from app.models import Product
                products = Product.query.filter_by(
                    venue_id=venue_id, 
                    is_available=True
                ).limit(10).all()
                results = [p.to_dict() for p in products]
            return results
        except Exception as e:
            logger.warning(f"Vector search error, falling back to database: {e}")
            # Fallback to database search
            from app.models import Product
            products = Product.query.filter_by(
                venue_id=venue_id, 
                is_available=True
            ).limit(10).all()
            return [p.to_dict() for p in products]
    
    def _search_wines_for_catalog(
        self, 
        query: str, 
        venue
    ) -> List[Dict]:
        """Search for wines to suggest for the restaurant's catalog."""
        try:
            results = self.vector_service.search(
                query=query,
                venue_id=venue.id,
                limit=10
            )
            return results
        except Exception:
            from app.models import Product
            products = Product.query.filter_by(venue_id=venue.id).limit(5).all()
            return [p.to_dict() for p in products]
    
    def _is_making_recommendations(self, ai_response: str) -> bool:
        """
        Check if the AI response contains actual wine recommendations.
        
        The AI can make recommendations in two formats:
        1. Single wine with alternatives (3 options)
        2. Wine journey/tasting path (2-3 wines in sequence)
        
        This function is more permissive to catch various recommendation patterns.
        """
        # Single wine recommendation markers
        single_wine_markers = [
            'il mio consiglio',
            'vi consiglio',
            'vi propongo',
            'consiglio',
            'raccomando',
            'mio preferito',
            'vi propongo tre vini',
            'alternativa interessante',
            'per chi ama osare',
            'per chi vuole osare',
            'cosa vi ispira',
            'vi suggerisco',
            'suggerisco',
            'proporre',
            'proposta',
        ]
        
        # Wine journey/tasting path markers
        journey_markers = [
            'percorso di degustazione',
            'percorso',
            'piccolo viaggio',
            'viaggio',
            'vi porto in un',
            'per iniziare',
            'per proseguire',
            'come si beve',
            'ordine suggerito',
            'iniziate con',
            'poi passate',
        ]
        
        # General wine mention indicators
        wine_indicators = [
            'vino',
            'bottiglia',
            'etichetta',
            'd.o.c.',
            'doc',
            'igp',
            'dop',
        ]
        
        # Price marker - wines are often mentioned with price
        has_price = '€' in ai_response
        has_wine_mention = any(indicator in ai_response.lower() for indicator in wine_indicators)
        
        response_lower = ai_response.lower()
        
        # Check for explicit recommendation markers
        for marker in single_wine_markers:
            if marker in response_lower:
                return True
        
        # Check for journey markers
        for marker in journey_markers:
            if marker in response_lower:
                return True
        
        # More permissive: if there's a wine mention AND price, likely a recommendation
        if has_wine_mention and has_price:
            return True
        
        # Very permissive: if there's explicit wine name patterns (e.g., "Pinot Noir D.O.C. 2014")
        import re
        wine_name_pattern = r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:D\.O\.C\.|DOC|IGP|DOP))?(?:\s+\d{4})?'
        if re.search(wine_name_pattern, ai_response):
            return True
        
        return False
    
    def _extract_recommended_wines(
        self, 
        ai_response: str, 
        available_wines: List[Dict]
    ) -> List[Dict]:
        """
        Extract recommended wines from the AI response by matching wine names.
        
        CRITICAL: Must match EXACTLY the wines mentioned in the text, in the order they appear.
        
        Works for both:
        - Single wine recommendations (3 alternatives)
        - Wine journeys (2-3 wines in sequence)
        
        Uses multiple matching strategies to be more robust.
        
        Args:
            ai_response: The AI's response text
            available_wines: List of wines from the venue's catalog
            
        Returns:
            List of matched wine dictionaries (max 3, in order of appearance)
        """
        if not available_wines:
            return []
        
        response_lower = ai_response.lower()
        response_original = ai_response  # Keep original for exact matching
        
        # Score each wine by how well it matches and where it appears in the response
        wine_matches = []
        
        for wine in available_wines:
            wine_name = wine.get('name', '').strip()
            if not wine_name:
                continue
            
            wine_name_lower = wine_name.lower()
            wine_name_original = wine_name  # Keep original for exact matching
            position = -1
            match_score = 0
            
            # Strategy 1: Exact name match (highest priority) - check in original case too
            if wine_name_lower in response_lower:
                position = response_lower.find(wine_name_lower)
                match_score = 100  # Very high score for exact match
                # Also check if exact name appears in original response (case-insensitive but preserve case)
                if wine_name_original.lower() in response_original.lower():
                    match_score = 100  # Perfect match
            elif wine_name_original.lower() in response_original.lower():
                # Try with original case variations
                position = response_original.lower().find(wine_name_original.lower())
                match_score = 95  # Almost perfect
            
            # Strategy 2: Match by significant words (words longer than 3 chars)
            if match_score < 50:  # Only if exact match failed
                name_parts = [p.strip() for p in wine_name.split() 
                            if len(p.strip()) > 3 
                            and not p.lower() in ['d.o.c', 'doc', 'igp', 'dop', 'del', 'di', 'la', 'le', 'il', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024']]
                matching_parts = []
                
                for part in name_parts:
                    # Find the word as a whole word (surrounded by word boundaries or spaces)
                    import re
                    pattern = r'\b' + re.escape(part.lower()) + r'\b'
                    matches = list(re.finditer(pattern, response_lower))
                    if matches:
                        matching_parts.extend([m.start() for m in matches])
                
                if matching_parts:
                    position = min(matching_parts)
                    # Score based on how many parts matched relative to total parts
                    if len(name_parts) > 0:
                        matched_parts_count = len(set([p.lower() for p in name_parts 
                                                       if any(p.lower() in response_lower[max(0, pos-10):pos+len(p)+10] 
                                                             for pos in matching_parts)]))
                        match_score = (matched_parts_count / len(name_parts)) * 50  # Max 50 for partial match
                    else:
                        match_score = 30
            
            # Strategy 3: Partial match for compound names (e.g., "Pinot Noir" might be mentioned as just "Pinot")
            if match_score < 20:
                # Try matching first significant word (longer than 4 chars)
                first_significant_word = next((p for p in wine_name.split() if len(p) > 4), None)
                if first_significant_word:
                    word_lower = first_significant_word.lower()
                    if word_lower in response_lower:
                        # Check if it's mentioned near price or other wine indicators
                        word_pos = response_lower.find(word_lower)
                        context_around = response_lower[max(0, word_pos-30):word_pos+len(first_significant_word)+30]
                        if '€' in context_around or any(indicator in context_around for indicator in ['vino', 'etichetta', 'bottiglia']):
                            position = word_pos
                            match_score = 20  # Lower score for partial match with context
            
            # Only include wines with match score > 80 (exact or very high-confidence matches only)
            # This ensures we only return wines that are actually mentioned clearly in the text
            if position >= 0 and match_score > 80:
                wine_matches.append({
                    'wine': wine,
                    'position': position,
                    'score': match_score
                })
        
        # Sort by position first (order in response), then by score (descending)
        wine_matches.sort(key=lambda x: (x['position'], -x['score']))
        
        # Detailed logging for debugging
        if wine_matches:
            logger.info(f"Extracted {len(wine_matches)} wine matches from response (score > 80):")
            for idx, match in enumerate(wine_matches[:5], 1):  # Log top 5 matches
                logger.info(f"  {idx}. {match['wine'].get('name')} (score: {match['score']:.1f}, position: {match['position']})")
        else:
            logger.warning(f"No wines found with match score > 80. Extracted wines will be empty.")
            # Log potential matches with lower scores for debugging
            all_potential_matches = []
            for wine in available_wines[:10]:  # Check first 10 wines for debugging
                wine_name = wine.get('name', '').strip()
                if wine_name and wine_name.lower() in response_lower:
                    all_potential_matches.append(wine_name)
            if all_potential_matches:
                logger.warning(f"Potential wine names found in text (but score <= 80): {all_potential_matches[:3]}")
        
        # Return top 3 unique matches in order of appearance
        seen_ids = set()
        unique_wines = []
        for match in wine_matches:
            wine = match['wine']
            wine_id = wine.get('id')
            if wine_id and wine_id not in seen_ids:
                seen_ids.add(wine_id)
                unique_wines.append(wine)
            if len(unique_wines) >= 3:
                break
        
        return unique_wines
    
    def _build_wines_context(self, wines: List[Dict]) -> str:
        """Build a text context of wines for the GPT prompt."""
        if not wines:
            return "⚠️ ATTENZIONE: La carta è vuota o non ci sono vini disponibili. DEVI comunque cercare di aiutare il cliente. Suggerisci di consultare la carta fisica del ristorante, ma mantieni un tono accogliente e professionale."
        
        context_parts = []
        for idx, wine in enumerate(wines, 1):
            parts = [f"**{wine.get('name', 'N/D')}**"]
            
            if wine.get('vintage'):
                parts[0] += f" {wine['vintage']}"
            
            details = []
            if wine.get('type'):
                details.append(wine['type'])
            if wine.get('grape_variety'):
                details.append(wine['grape_variety'])
            if wine.get('region'):
                details.append(wine['region'])
            
            if details:
                parts.append(f"({', '.join(details)})")
            
            if wine.get('price'):
                parts.append(f"- €{wine['price']}")
            
            if wine.get('description'):
                desc = wine['description'][:100]
                parts.append(f"| {desc}...")
            
            if wine.get('food_pairings'):
                pairings = wine['food_pairings']
                if isinstance(pairings, list):
                    parts.append(f"| Abbinamenti: {', '.join(pairings[:3])}")
            
            context_parts.append(f"{idx}. " + " ".join(parts))
        
        return "\n".join(context_parts)
    
    def _extract_gathered_info(self, history: List[Dict], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract gathered preferences from conversation history.
        
        Analyzes the chat history to determine what info has been collected:
        - wine_type: red, white, sparkling, rose, any (sommelier's choice)
        - journey_preference: single (one bottle) or journey (multiple wines)
        - budget: low, medium, high, any
        
        Args:
            history: List of conversation messages
            context: Current session context (may contain previously extracted info)
            
        Returns:
            Dict with gathered_info and phase
        """
        # Start with any previously extracted info
        existing_info = {}
        if context and context.get('gathered_info'):
            existing_info = context['gathered_info'].copy()
        
        gathered_info = {
            'wine_type': existing_info.get('wine_type'),
            'journey_preference': existing_info.get('journey_preference'),
            'budget': existing_info.get('budget')
        }
        
        # Combine all messages into text for analysis
        all_text = ""
        for msg in history:
            if msg.get('role') == 'user':
                all_text += " " + msg.get('content', '').lower()
        
        # Extract wine type preference
        if gathered_info['wine_type'] is None:
            if any(word in all_text for word in ['rosso', 'rossi', 'red']):
                gathered_info['wine_type'] = 'red'
            elif any(word in all_text for word in ['bianco', 'bianchi', 'white']):
                gathered_info['wine_type'] = 'white'
            elif any(word in all_text for word in ['bollicine', 'spumante', 'prosecco', 'champagne', 'sparkling']):
                gathered_info['wine_type'] = 'sparkling'
            elif any(word in all_text for word in ['rosato', 'rosé', 'rose']):
                gathered_info['wine_type'] = 'rose'
            elif any(word in all_text for word in ['affido a te', 'decidi tu', 'scegli tu', 'lascia fare', 'sorprendimi', 'consiglia tu']):
                gathered_info['wine_type'] = 'any'
        
        # Extract journey preference (single bottle vs wine journey)
        if gathered_info['journey_preference'] is None:
            # Check for journey preference
            if any(phrase in all_text for phrase in ['percorso', 'viaggio', 'più vini', 'più etichette', 'diverse bottiglie', 'vini diversi']):
                gathered_info['journey_preference'] = 'journey'
            # Check for single bottle preference
            elif any(phrase in all_text for phrase in ['una bottiglia', 'un solo vino', 'unica etichetta', 'singola bottiglia', 'una sola', 'un vino solo']):
                gathered_info['journey_preference'] = 'single'
            # Check for agreement patterns
            elif any(phrase in all_text for phrase in ['sì percorso', 'ok percorso', 'va bene percorso', 'mi piace percorso']):
                gathered_info['journey_preference'] = 'journey'
            elif any(phrase in all_text for phrase in ['sì una', 'ok una', 'va bene una']):
                gathered_info['journey_preference'] = 'single'
        
        # Extract budget preference
        if gathered_info['budget'] is None:
            # Check for high budget
            if any(phrase in all_text for phrase in ['senza limiti', 'nessun limite', 'spendere bene', 'importante', 'speciale', 'alto', 'premium']):
                gathered_info['budget'] = 'high'
            # Check for low budget
            elif any(phrase in all_text for phrase in ['economico', 'poco', 'risparmiare', 'basso', 'contenuto', 'accessibile']):
                gathered_info['budget'] = 'low'
            # Check for medium budget
            elif any(phrase in all_text for phrase in ['medio', 'normale', 'standard', 'giusto', 'ragionevole']):
                gathered_info['budget'] = 'medium'
            # Check for specific price mentions
            elif '€' in all_text or 'euro' in all_text:
                # Try to extract price and categorize
                import re
                prices = re.findall(r'(\d+)\s*(?:€|euro)', all_text)
                if prices:
                    max_price = max(int(p) for p in prices)
                    if max_price < 20:
                        gathered_info['budget'] = 'low'
                    elif max_price < 40:
                        gathered_info['budget'] = 'medium'
                    else:
                        gathered_info['budget'] = 'high'
            # Check for "any budget" signals
            elif any(phrase in all_text for phrase in ['qualsiasi', 'libero', 'non importa', 'scegli tu']):
                gathered_info['budget'] = 'any'
        
        # Determine phase based on what's been gathered
        all_gathered = all(v is not None for v in gathered_info.values())
        phase = 'recommending' if all_gathered else 'gathering'
        
        return {
            'gathered_info': gathered_info,
            'phase': phase,
            'missing': [k for k, v in gathered_info.items() if v is None]
        }
    
    def _create_wine_journeys(self, wines: List[Dict], bottles_count: int) -> List[Dict]:
        """
        Create wine journeys from a list of wines.
        
        IMPORTANT: Uses diverse wines from the list to avoid always suggesting the same wines.
        Shuffles and selects different wines for variety.
        
        Args:
            wines: List of wine dictionaries (should be diverse, up to 30 wines)
            bottles_count: Number of bottles needed for the journey
            
        Returns:
            List of journey dictionaries, each containing:
            - id: unique journey ID
            - wines: list of wines in the journey
            - description: brief description of the journey
        """
        if not wines:
            return []
        
        import random
        
        # Shuffle wines to ensure variety (but keep it deterministic for same input)
        # Use a seed based on bottles_count to get consistent but varied results
        wines_copy = wines.copy()
        random.seed(bottles_count * 42)  # Deterministic but varied
        random.shuffle(wines_copy)
        
        journeys = []
        used_wine_ids = set()
        
        # Helper to get next unused wine
        def get_next_unused_wine():
            for wine in wines_copy:
                wine_id = wine.get('id')
                if wine_id and wine_id not in used_wine_ids:
                    used_wine_ids.add(wine_id)
                    return wine
            return None
        
        # Logic based on bottles_count
        if bottles_count == 2:
            # 1-2 journeys with 2 wines each
            wine1 = get_next_unused_wine()
            wine2 = get_next_unused_wine()
            if wine1 and wine2:
                journeys.append({
                    'id': 1,
                    'wines': [wine1, wine2],
                    'description': 'Percorso di degustazione dal più delicato al più strutturato'
                })
            
            # Create second journey if we have enough wines
            wine3 = get_next_unused_wine()
            wine4 = get_next_unused_wine()
            if wine3 and wine4 and len(wines) >= 4:
                journeys.append({
                    'id': 2,
                    'wines': [wine3, wine4],
                    'description': 'Percorso alternativo con caratteri diversi'
                })
                
        elif bottles_count == 3:
            # 1-2 journeys with 3 wines each
            journey1_wines = []
            for _ in range(3):
                wine = get_next_unused_wine()
                if wine:
                    journey1_wines.append(wine)
            
            if len(journey1_wines) == 3:
                journeys.append({
                    'id': 1,
                    'wines': journey1_wines,
                    'description': 'Percorso completo di tre vini che si evolvono con le portate'
                })
                
                # Create second journey if we have enough wines (6+)
                if len(wines) >= 6:
                    journey2_wines = []
                    for _ in range(3):
                        wine = get_next_unused_wine()
                        if wine:
                            journey2_wines.append(wine)
                    
                    if len(journey2_wines) == 3:
                        journeys.append({
                            'id': 2,
                            'wines': journey2_wines,
                            'description': 'Percorso alternativo con focus su sapori diversi'
                        })
                        
        elif bottles_count >= 4:
            # 1-2 journeys (each with bottles_count wines, or distribute evenly)
            wines_per_journey = bottles_count
            
            # First journey
            journey1_wines = []
            for _ in range(wines_per_journey):
                wine = get_next_unused_wine()
                if wine:
                    journey1_wines.append(wine)
            
            if len(journey1_wines) >= 2:  # At least 2 wines
                journeys.append({
                    'id': 1,
                    'wines': journey1_wines,
                    'description': 'Percorso classico dal più delicato al più corposo'
                })
                
                # Second journey if we have enough wines (at least double)
                if len(wines) >= wines_per_journey * 2:
                    journey2_wines = []
                    for _ in range(wines_per_journey):
                        wine = get_next_unused_wine()
                        if wine:
                            journey2_wines.append(wine)
                    
                    if len(journey2_wines) >= 2:
                        journeys.append({
                            'id': 2,
                            'wines': journey2_wines,
                            'description': 'Percorso alternativo con caratteri diversi'
                        })
        
        # Fallback: if no journeys created, create one with available wines
        if not journeys and wines:
            # Use first bottles_count wines
            journey_wines = wines[:bottles_count] if len(wines) >= bottles_count else wines
            journeys.append({
                'id': 1,
                'wines': journey_wines,
                'description': 'Percorso di degustazione selezionato'
            })
        
        return journeys
