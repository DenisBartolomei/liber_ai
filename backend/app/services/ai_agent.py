"""
AI Agent Service for LIBER
Orchestrates conversations with OpenAI GPT and vector search
"""
import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI, APIError, AuthenticationError, RateLimitError
from flask import current_app
from app import db
from app.services.vector_search import VectorSearchService
from app.services.fine_tuned_selector import FineTunedWineSelector
from app.services.communication_model import CommunicationModelService
from app.prompts.b2b_system import get_b2b_system_prompt
from app.prompts.b2c_system import get_b2c_system_prompt, get_b2c_opening_prompt, calculate_bottles_needed

logger = logging.getLogger(__name__)


class AIAgentService:
    """
    AI Agent that handles both B2B (restaurant owner) and B2C (customer) conversations.
    Uses OpenAI for language generation and Qdrant for semantic wine search.
    """
    
    def __init__(self):
        api_key = current_app.config.get('OPENAI_API_KEY', '')
        
        if not api_key or not api_key.strip():
            logger.error("OPENAI_API_KEY is not configured!")
            raise ValueError("OPENAI_API_KEY non configurata. Contatta l'amministratore del sistema.")
        
        try:
            # Try initializing without explicit api_key parameter (uses env var)
            self.client = OpenAI(api_key=api_key, timeout=30.0)  # 30 second timeout
        except TypeError as e:
            # Try alternative initialization
            import os
            os.environ['OPENAI_API_KEY'] = api_key
            self.client = OpenAI(timeout=30.0)  # 30 second timeout
        except Exception as e:
            raise
        
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
        
        # Simple logic: if message_count <= 1, use opening prompt, otherwise use recommendation prompt
        message_count = session.message_count or 0
        use_opening_prompt = message_count <= 1
        
        # Use provided context or session context
        # Priority: provided context > session context > empty dict
        active_context = context
        if not active_context:
            active_context = getattr(session, 'context', None) or {}
        
        # Extract preferences from context (collected via UI, not LLM)
        # Ensure we have a preferences structure
        preferences = active_context.get('preferences', {})
        if not preferences and active_context:
            # Try to reconstruct preferences from session if not in context
            # This handles cases where context was saved but preferences structure is missing
            preferences = {}
        
        # Build gathered_info with all preferences, including bottles_count
        gathered_info = {
            'wine_type': preferences.get('wine_type', 'any'),
            'journey_preference': preferences.get('journey_preference', 'single'),
            'budget': preferences.get('budget'),
            'bottles_count': preferences.get('bottles_count')
        }
        
        # If bottles_count is not in preferences but journey_preference is 'journey',
        # try to get it from session.num_bottiglie_target
        if gathered_info['journey_preference'] == 'journey' and not gathered_info['bottles_count']:
            if hasattr(session, 'num_bottiglie_target') and session.num_bottiglie_target:
                gathered_info['bottles_count'] = session.num_bottiglie_target
        
        # Ensure guest_count is in active_context
        if 'guest_count' not in active_context:
            # Try to get from session context if available
            session_context = getattr(session, 'context', None)
            if session_context and 'guest_count' in session_context:
                active_context['guest_count'] = session_context['guest_count']
            else:
                active_context['guest_count'] = 2  # Default
        
        logger.info(f"B2C Context: dishes={len(active_context.get('dishes', []))}, guests={active_context.get('guest_count')}, prefs={gathered_info}, use_opening_prompt={use_opening_prompt}, message_count={message_count}")
        logger.info(f"Using model for {'opening' if use_opening_prompt else 'recommendation'}: {self.model if use_opening_prompt else 'fine-tuned'}")
        
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
            
            # Call GPT - opening message, keep it brief
            try:
                logger.info(f"Calling OpenAI API with model: {self.model}, messages count: {len(messages)}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_completion_tokens=600  # Increased for more complete opening messages
                )
                
                logger.info(f"OpenAI API response received: has_choices={bool(response.choices)}, choices_count={len(response.choices) if response.choices else 0}")
                
                # Safely extract response content
                if not response.choices or len(response.choices) == 0:
                    logger.error("OpenAI API returned no choices in response")
                    raise ValueError("La risposta dell'API non contiene scelte valide")
                
                choice = response.choices[0]
                if not choice.message:
                    logger.error("OpenAI API response choice has no message")
                    raise ValueError("La risposta dell'API non contiene un messaggio valido")
                
                ai_response = choice.message.content
                logger.info(f"Extracted AI response: length={len(ai_response) if ai_response else 0}, preview={ai_response[:100] if ai_response else 'None'}")
                
                # Ensure response is not empty
                if not ai_response or not ai_response.strip():
                    logger.warning("Opening message returned empty response, generating fallback")
                    # Generate a simple opening message as fallback
                    dish_list = [d.get('name', 'Piatto') for d in active_context.get('dishes', [])]
                    guest_count = active_context.get('guest_count', 2)
                    journey_text = "un percorso di vini" if gathered_info.get('journey_preference') == 'journey' else "una singola etichetta"
                    wine_type_text = "si affida alla mia esperienza" if gathered_info.get('wine_type') == 'any' else gathered_info.get('wine_type', '')
                    
                    ai_response = f"Benvenuti! Ho visto che avete ordinato {', '.join(dish_list) if dish_list else 'alcuni piatti'} per {guest_count} {('persona' if guest_count == 1 else 'persone')}. Preferite {journey_text}? Avete esigenze particolari o preferenze da comunicarmi?"
                
                # Final validation before returning
                if not ai_response or not isinstance(ai_response, str) or not ai_response.strip():
                    logger.error(f"AI response is invalid: type={type(ai_response)}, value={repr(ai_response)}")
                    raise ValueError("La risposta dell'AI è vuota o non valida")
                
                logger.info(f"Returning opening message: length={len(ai_response)}, preview={ai_response[:150]}")
                
                result = {
                    'message': ai_response.strip(),
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
                
                logger.info(f"Opening message result: message_length={len(result['message'])}, is_opening={result['metadata']['is_opening']}")
                return result
                
            except Exception as e:
                logger.error(f"Error in opening message: {e}", exc_info=True)
                # Generate fallback opening message instead of raising
                dish_list = [d.get('name', 'Piatto') for d in active_context.get('dishes', [])]
                guest_count = active_context.get('guest_count', 2)
                journey_text = "un percorso di vini" if gathered_info.get('journey_preference') == 'journey' else "una singola etichetta"
                
                fallback_message = f"Benvenuti! Ho visto che avete ordinato {', '.join(dish_list) if dish_list else 'alcuni piatti'} per {guest_count} {('persona' if guest_count == 1 else 'persone')}. Preferite {journey_text}? Avete esigenze particolari o preferenze da comunicarmi?"
                
                return {
                    'message': fallback_message,
                    'wines': [],
                    'wine_ids': [],
                    'journeys': [],
                    'suggestions': [],
                    'mode': 'single',
                    'metadata': {
                        'model': self.model,
                        'tokens_used': 0,
                        'gathered_info': gathered_info,
                        'is_recommending': False,
                        'is_opening': True,
                        'error': str(e)
                    }
                }
        
        # NEW ARCHITECTURE: Two-phase approach
        # Phase 1: Fine-tuned model selects wines and returns structured JSON
        # Phase 2: Communication model generates natural language message
        
        # Get preferences for filtering
        wine_type_pref = gathered_info.get('wine_type', 'any')
        budget_pref = gathered_info.get('budget')
        
        # Get filtered wines from the venue's catalog based on preferences
        from app.models import Product
        
        # Build query with filters
        query = Product.query.filter_by(
            venue_id=venue.id,
            is_available=True
        )
        
        # Filter by wine type - CRITICAL: Do NOT filter if wine_type == 'any' (lascia fare a te)
        if wine_type_pref and wine_type_pref != 'any':
            query = query.filter_by(type=wine_type_pref)
            logger.info(f"Applied wine type filter: {wine_type_pref}")
        else:
            logger.info(
                f"NO wine type filter applied (wine_type='{wine_type_pref}' means 'any' - all types included). "
                f"This is correct behavior when user selects 'lascia fare a te'."
            )
        
        # Filter by budget (0 to budget + 15%)
        budget_max = None
        if budget_pref and budget_pref != 'nolimit':
            if isinstance(budget_pref, (int, float)):
                budget_max = float(budget_pref)
            elif budget_pref == 'base' or budget_pref == 'low':
                budget_max = 20.0
            elif budget_pref == 'spinto' or budget_pref == 'medium':
                budget_max = 40.0
            
            if budget_max:
                max_price = budget_max * 1.15  # budget + 15%
                query = query.filter(Product.price <= max_price)
        
        # Use load_only to select only core columns that exist in all databases
        # This avoids errors if optional columns (color, aromas, etc.) don't exist
        all_products = query.options(
            db.load_only(
                Product.id,
                Product.venue_id,
                Product.name,
                Product.type,
                Product.price,
                Product.cost_price,
                Product.margin,
                Product.is_available,
                Product.image_url,
                Product.created_at,
                Product.updated_at
            )
        ).order_by(Product.type, Product.name).all()
        
        # Convert to dict format
        all_wines = [p.to_dict() for p in all_products]
        if budget_max:
            max_price = budget_max * 1.15
            logger.info(f"Filtered wines: type={wine_type_pref}, budget_range=€0.00-€{max_price:.2f} (budget €{budget_max:.2f} +15%), result={len(all_wines)} wines from venue {venue.id}")
        else:
            logger.info(f"Filtered wines: type={wine_type_pref}, budget_max=none, result={len(all_wines)} wines from venue {venue.id}")
        
        if not all_wines:
            logger.warning("No wines available in catalog")
            return {
                'message': 'Mi dispiace, al momento non ci sono vini disponibili nella carta.',
                'wines': [],
                'wine_ids': [],
                'journeys': [],
                'suggestions': [],
                'mode': 'single',
                'metadata': {
                    'model': self.model,
                    'tokens_used': 0,
                    'gathered_info': gathered_info,
                    'is_recommending': False
                }
            }
        
        try:
            # PHASE 1: Fine-tuned model selects wines
            # Get featured wines from venue preferences
            featured_wines = venue.get_featured_wines() if hasattr(venue, 'get_featured_wines') else []
            
            # Log detailed information about wines being passed to model
            logger.info(
                f"Passing {len(all_wines)} filtered wines to fine-tuned model. "
                f"Filters applied: type={wine_type_pref} (any={wine_type_pref == 'any'}, "
                f"no_type_filter={'YES' if wine_type_pref == 'any' else 'NO'}), "
                f"budget_max={budget_max if budget_max else 'none'}, "
                f"price_range=0-{max_price if budget_max else 'unlimited'}"
            )
            
            # Log wine type distribution for debugging
            if all_wines:
                wine_types = {}
                for wine in all_wines:
                    wine_type = wine.get('type', 'unknown')
                    wine_types[wine_type] = wine_types.get(wine_type, 0) + 1
                logger.info(
                    f"Wine type distribution in filtered set: {wine_types}. "
                    f"Total wines: {len(all_wines)}"
                )
            
            fine_tuned_selector = FineTunedWineSelector()
            wine_selection = fine_tuned_selector.select_wines(
                venue_name=venue.name,
                venue_id=venue.id,
                context=active_context,
                gathered_info=gathered_info,
                all_wines=all_wines,
                history=history,
                user_message=user_message,
                featured_wines=featured_wines
            )
            
            # Log detailed information about wines returned from model
            wines_returned = len(wine_selection.get('wines', []))
            journeys_returned = len(wine_selection.get('journeys', []))
            
            logger.info(
                f"Fine-tuned model returned {wines_returned} wines and {journeys_returned} journeys "
                f"from {len(all_wines)} wines passed. "
                f"Match: {wines_returned}/{len(all_wines)} "
                f"({(wines_returned/len(all_wines)*100) if all_wines else 0:.1f}%)"
            )
            
            if wines_returned < len(all_wines):
                missing = len(all_wines) - wines_returned
                missing_percentage = (missing / len(all_wines) * 100) if all_wines else 0
                logger.warning(
                    f"CRITICAL: Model returned fewer wines ({wines_returned}) than passed ({len(all_wines)}). "
                    f"Missing {missing} wines ({missing_percentage:.1f}%). "
                    f"This is a business-critical issue."
                )
            
            # Check if we got valid selections
            has_wines = wine_selection.get('wines') and len(wine_selection['wines']) > 0
            has_journeys = wine_selection.get('journeys') and len(wine_selection['journeys']) > 0
            
            if not has_wines and not has_journeys:
                logger.warning("Fine-tuned model returned no wines/journeys, falling back to legacy method")
                # Fallback to legacy method if fine-tuned returns nothing
                return self._fallback_to_legacy_method(
                    venue, active_context, gathered_info, history, user_message, all_wines
                )
            
            # PHASE 2: Communication model generates message
            journey_pref = gathered_info.get('journey_preference', 'single')
            
            # Create a limited wine_selection with only first 3 wines for CommunicationModel
            wine_selection_for_communication = wine_selection.copy()
            if journey_pref == 'single' and has_wines:
                # Limit to first 3 wines for communication model
                wine_selection_for_communication['wines'] = wine_selection.get('wines', [])[:3]
                logger.info(f"Passing first 3 wines to CommunicationModel (out of {len(wine_selection.get('wines', []))} total)")
            
            communication_service = CommunicationModelService()
            try:
                ai_message = communication_service.generate_message(
                    venue_name=venue.name,
                    sommelier_style=venue.sommelier_style or 'professional',
                    wine_selection=wine_selection_for_communication,
                    context=active_context,
                    gathered_info=gathered_info,
                    history=history,
                    user_message=user_message
                )
                
                # Ensure message is not empty
                if not ai_message or not ai_message.strip():
                    logger.warning("Communication model returned empty message, using fallback")
                    ai_message = self._generate_fallback_message(wine_selection, journey_pref)
                else:
                    logger.info(f"Communication model generated message: {len(ai_message)} chars")
            except Exception as e:
                logger.warning(f"Communication model failed, using fallback: {e}")
                ai_message = self._generate_fallback_message(wine_selection, journey_pref)
            
            # Prepare response based on mode
            
            if journey_pref == 'journey' and has_journeys:
                # Journey mode
                all_wine_ids = []
                for journey in wine_selection['journeys']:
                    all_wine_ids.extend([w.get('id') for w in journey.get('wines', []) if w.get('id')])
                
                logger.info(f"Returning {len(wine_selection['journeys'])} journeys with {len(all_wine_ids)} unique wines")
                return {
                    'message': ai_message,
                    'journeys': wine_selection['journeys'],
                    'wine_ids': list(set(all_wine_ids)),
                    'wines': [],  # Empty for journey mode
                    'suggestions': [],
                    'mode': 'journey',
                    'metadata': {
                        'model': self.model,
                        'tokens_used': 0,  # TODO: Track tokens from both models
                        'gathered_info': gathered_info,
                        'is_recommending': True
                    }
                }
            else:
                # Single mode
                all_ranked_wines = wine_selection.get('wines', [])
                # First 3 wines for initial display (max 3)
                wines_for_display = all_ranked_wines[:3]
                wine_ids = [w.get('id') for w in all_ranked_wines if w.get('id')]
                
                logger.info(f"Returning {len(wines_for_display)} wines for display, {len(all_ranked_wines)} total ranked wines")
                
                return {
                    'message': ai_message,
                    'wines': wines_for_display,  # Primi 3 vini per display iniziale
                    'all_rankings': all_ranked_wines,  # TUTTI i vini rankati per il modal "Valuta tutti i vini"
                    'wine_ids': wine_ids,
                    'journeys': [],
                    'suggestions': [],
                    'mode': 'single',
                    'metadata': {
                        'model': self.model,
                        'tokens_used': 0,  # TODO: Track tokens from both models
                        'gathered_info': gathered_info,
                        'is_recommending': True
                    }
                }
            
        except ValueError as e:
            # Configuration or expected errors - try fallback
            logger.warning(f"Error in two-phase architecture, falling back: {e}")
            return self._fallback_to_legacy_method(
                venue, active_context, gathered_info, history, user_message, all_wines
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in process_b2c_message: {e}")
            # Try fallback before giving up
            try:
                return self._fallback_to_legacy_method(
                    venue, active_context, gathered_info, history, user_message, all_wines
                )
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise ValueError(f"Si è verificato un errore imprevisto. Riprova.")
    
    def _generate_fallback_message(self, wine_selection: Dict, journey_pref: str) -> str:
        """
        Generate a simple fallback message from wine selection JSON.
        Used when communication model fails or returns empty.
        """
        if journey_pref == 'journey' and wine_selection.get('journeys'):
            journeys = wine_selection['journeys']
            messages = []
            for journey in journeys:
                journey_name = journey.get('name', 'Percorso di Degustazione')
                wines = journey.get('wines', [])
                wine_names = [f"{w.get('name', 'Vino')} - €{w.get('price', 'N/D')}" for w in wines]
                messages.append(f"**{journey_name}**:\n" + "\n".join([f"- {name}" for name in wine_names]))
            return "\n\n".join(messages)
        elif wine_selection.get('wines'):
            wines = wine_selection['wines']
            best_wine = next((w for w in wines if w.get('best')), wines[0] if wines else None)
            other_wines = [w for w in wines if not w.get('best')]
            
            message_parts = []
            if best_wine:
                reason = best_wine.get('reason', '')
                message_parts.append(f"**Il mio consiglio** - {best_wine.get('name')} - €{best_wine.get('price')}")
                if reason:
                    message_parts.append(reason)
            
            for wine in other_wines[:2]:  # Max 2 alternatives
                reason = wine.get('reason', '')
                message_parts.append(f"**Un'alternativa interessante** - {wine.get('name')} - €{wine.get('price')}")
                if reason:
                    message_parts.append(reason)
            
            return "\n\n".join(message_parts)
        else:
            return "Ecco le mie raccomandazioni per voi."
    
    def _fallback_to_legacy_method(
        self,
        venue,
        active_context: Dict,
        gathered_info: Dict,
        history: List[Dict],
        user_message: str,
        all_wines: List[Dict]
    ) -> Dict[str, Any]:
        """
        Fallback to legacy method if fine-tuned architecture fails.
        Uses the old extraction-based approach.
        """
        logger.info("Using legacy fallback method for wine recommendations")
        
        # Use the recommendation prompt (legacy)
        system_prompt = get_b2c_system_prompt(
            venue_name=venue.name,
            cuisine_type=venue.cuisine_type,
            sommelier_style=venue.sommelier_style or 'professional',
            context=active_context,
            gathered_info=gathered_info,
            is_first_message=False
        )
        
        # Build context about available wines
        wines_context = f"""## Carta dei Vini Disponibili

⚠️ REGOLA CRITICA: Puoi proporre SOLO i vini elencati qui sotto. NON inventare MAI vini, nomi, cantine, annate o caratteristiche che non sono in questa lista.

{self._build_wines_context(all_wines)}

⚠️ RICORDA: DEVI SEMPRE proporre qualcosa se ci sono vini nella lista sopra."""
        
        # Prepare messages for GPT
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "system", "content": wines_context})
        
        # Add conversation history
        for msg in history:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call GPT - fallback method, allow more descriptive responses
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=800  # Increased for more complete responses
        )
        
        ai_response = response.choices[0].message.content
        
        # Extract wines (legacy method)
        journey_pref = gathered_info.get('journey_preference', 'single')
        preferences = active_context.get('preferences', {})
        bottles_count = preferences.get('bottles_count')
        
        wines_to_return = []
        wine_ids = []
        
        if journey_pref == 'single':
            wines_to_return = self._extract_recommended_wines(ai_response, all_wines)
        else:
            wines_to_return = self._extract_recommended_wines(ai_response, all_wines)
            if wines_to_return:
                journeys = self._create_wine_journeys(
                    wines_to_return,
                    bottles_count or calculate_bottles_needed(active_context.get('guest_count', 2))
                )
                if journeys:
                    all_wine_ids = []
                    for journey in journeys:
                        all_wine_ids.extend([w.get('id') for w in journey.get('wines', []) if w.get('id')])
                    
                    return {
                        'message': ai_response,
                        'journeys': journeys,
                        'wine_ids': list(set(all_wine_ids)),
                        'wines': [],
                        'suggestions': [],
                        'mode': 'journey',
                        'metadata': {
                            'model': self.model,
                            'tokens_used': response.usage.total_tokens if response.usage else 0,
                            'gathered_info': gathered_info,
                            'is_recommending': True
                        }
                    }
        
        wine_ids = [w.get('id') for w in wines_to_return if w.get('id')]
        
        return {
            'message': ai_response,
            'wines': wines_to_return,
            'wine_ids': wine_ids,
            'journeys': [],
            'suggestions': [],
            'mode': 'single',
            'metadata': {
                'model': self.model,
                'tokens_used': response.usage.total_tokens if response.usage else 0,
                'gathered_info': gathered_info,
                'is_recommending': len(wines_to_return) > 0
            }
        }
    
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
                max_tokens=400  # Reduced for faster, more direct responses
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
        
        # Return all unique matches in order of appearance (at least 2, but can return more)
        seen_ids = set()
        unique_wines = []
        for match in wine_matches:
            wine = match['wine']
            wine_id = wine.get('id')
            if wine_id and wine_id not in seen_ids:
                seen_ids.add(wine_id)
                unique_wines.append(wine)
            # No limit - extract all matched wines (AI should suggest at least 2)
        
        return unique_wines
    
    def _build_wines_context(self, wines: List[Dict]) -> str:
        """Build a text context of wines for the GPT prompt - includes name, type, price, grape_variety, and description."""
        if not wines:
            return "⚠️ ATTENZIONE: La carta è vuota o non ci sono vini disponibili. DEVI comunque cercare di aiutare il cliente. Suggerisci di consultare la carta fisica del ristorante, ma mantieni un tono accogliente e professionale."
        
        context_parts = []
        for idx, wine in enumerate(wines, 1):
            name = wine.get('name', 'N/D')
            wine_type = wine.get('type', 'N/D')
            price = wine.get('price', 'N/D')
            grape_variety = wine.get('grape_variety', '')
            description = wine.get('description', '')
            
            wine_line = f"{idx}. {name} | {wine_type} | €{price}"
            
            if grape_variety:
                wine_line += f" | Uvaggio: {grape_variety}"
            
            if description:
                wine_line += f" | Descrizione: {description}"
            
            context_parts.append(wine_line)
        
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
